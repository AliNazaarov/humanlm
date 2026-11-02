"""Minimal DPO on Apple Silicon with mlx + mlx-lm, on top of an existing LoRA adapter (L1 -> L2).
Reference = the frozen L1 policy: its chosen/rejected log-probs are precomputed once (no grad) with the L1 adapter
loaded, then the same LoRA weights are trained with the sigmoid DPO loss (Rafailov et al. 2023), beta 0.1.
Chat-templated (system/user=AI draft/assistant=text), prompt masked, batch 1, max-seq 768, 1 epoch.
  mlxenv/bin/python dpo_mlx.py --model M --adapter L1_DIR --data DIR --out L2_DIR [--beta 0.1] [--lr 1e-5]
      [--max-pairs 400] [--max-seq 768] [--save-every 50] [--time-budget-min 0]
Writes OUT/adapters.safetensors + adapter_config.json (loadable by mlx_lm.server --adapter-path) and OUT/dpo_log.jsonl.
"""
import argparse, json, os, shutil, time

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten, tree_unflatten
from mlx_lm.utils import load
from mlx_lm.tuner.utils import load_adapters


def encode(tok, system, prompt, answer, max_seq):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    p = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True)
    full = tok.apply_chat_template(msgs + [{"role": "assistant", "content": answer}], tokenize=True,
                                   add_generation_prompt=False)
    if isinstance(p, dict):
        p = p["input_ids"]
    if isinstance(full, dict):
        full = full["input_ids"]
    full = list(full)[:max_seq]
    return mx.array(full)[None], len(p)


def seq_logp(model, toks, n_prompt):
    """Sum of log-probs of the answer tokens (positions >= n_prompt) under the model."""
    logits = model(toks[:, :-1])
    targets = toks[:, 1:]
    lp = nn.losses.cross_entropy(logits, targets, reduction="none")   # -log p
    mask = mx.arange(targets.shape[1])[None] >= (n_prompt - 1)
    return -(lp * mask).sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--adapter", required=True)
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--beta", type=float, default=0.1); ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--max-pairs", type=int, default=400); ap.add_argument("--max-seq", type=int, default=768)
    ap.add_argument("--save-every", type=int, default=50); ap.add_argument("--time-budget-min", type=float, default=0)
    ap.add_argument("--steps-per-report", type=int, default=5)
    a = ap.parse_args()
    t0 = time.time()
    model, tok = load(a.model)
    model = load_adapters(model, a.adapter)   # applies LoRA layers per adapter_config.json and loads L1 weights
    model.freeze()
    for n, m in model.named_modules():
        if hasattr(m, "lora_a"):
            m.unfreeze(keys=["lora_a", "lora_b"])
    params = tree_flatten(model.trainable_parameters())
    print(f"trainable params: {sum(p.size for _, p in params):,} in {len(params)} tensors", flush=True)
    rows = [json.loads(l) for l in open(os.path.join(a.data, "train.jsonl"))][: a.max_pairs]
    enc = []
    for r in rows:
        c, npc = encode(tok, r["system"], r["prompt"], r["chosen"], a.max_seq)
        j, npj = encode(tok, r["system"], r["prompt"], r["rejected"], a.max_seq)
        if c.shape[1] <= npc or j.shape[1] <= npj:   # answer fully truncated
            continue
        enc.append((c, npc, j, npj))
    print(f"pairs: {len(enc)} (of {len(rows)} rows)", flush=True)
    # Reference = frozen L1: a copy of the L1 LoRA weights is swapped in (no grad) for each pair's reference
    # log-probs, then the current trained weights are restored. Interleaved so a time-boxed stop wastes nothing.
    l1 = {k: mx.array(v) for k, v in tree_flatten(model.trainable_parameters())}
    mx.eval(l1)
    model.train()
    opt = optim.Adam(learning_rate=a.lr)
    os.makedirs(a.out, exist_ok=True)
    shutil.copy(os.path.join(a.adapter, "adapter_config.json"), os.path.join(a.out, "adapter_config.json"))
    log = open(os.path.join(a.out, "dpo_log.jsonl"), "a")

    def loss_fn(model, c, npc, j, npj, rc, rj):
        pc = seq_logp(model, c, npc); pj = seq_logp(model, j, npj)
        margin = a.beta * ((pc - rc) - (pj - rj))
        loss = -nn.log_sigmoid(margin)
        return loss, margin

    vg = nn.value_and_grad(model, loss_fn)
    losses, margins, acc, t_train = [], [], 0, time.time()
    step = 0
    for step, (c, npc, j, npj) in enumerate(enc, 1):
        cur = {k: v for k, v in tree_flatten(model.trainable_parameters())}
        model.update(tree_unflatten(list(l1.items())))
        rc = seq_logp(model, c, npc); rj = seq_logp(model, j, npj)
        mx.eval(rc, rj)
        model.update(tree_unflatten(list(cur.items())))
        (loss, margin), grads = vg(model, c, npc, j, npj, mx.stop_gradient(rc), mx.stop_gradient(rj))
        opt.update(model, grads)
        mx.eval(model.parameters(), opt.state, loss, margin)
        losses.append(loss.item()); margins.append(margin.item()); acc += int(margin.item() > 0)
        mx.clear_cache()
        if step % a.steps_per_report == 0:
            rec = {"step": step, "loss": round(sum(losses[-a.steps_per_report:]) / a.steps_per_report, 4),
                   "margin": round(sum(margins[-a.steps_per_report:]) / a.steps_per_report, 4),
                   "acc": round(acc / step, 3), "sec": round(time.time() - t_train)}
            print(json.dumps(rec), flush=True); log.write(json.dumps(rec) + "\n"); log.flush()
        if step % a.save_every == 0:
            mx.save_safetensors(os.path.join(a.out, "adapters.safetensors"), dict(tree_flatten(model.trainable_parameters())))
        if a.time_budget_min and (time.time() - t0) / 60 > a.time_budget_min:
            print(f"time budget reached at step {step}", flush=True)
            break
    mx.save_safetensors(os.path.join(a.out, "adapters.safetensors"), dict(tree_flatten(model.trainable_parameters())))
    summary = {"steps": step, "pairs_available": len(enc), "mean_loss": round(sum(losses) / max(len(losses), 1), 4),
               "final_acc": round(acc / max(step, 1), 3), "beta": a.beta, "lr": a.lr, "max_seq": a.max_seq,
               "train_sec": round(time.time() - t_train), "total_sec": round(time.time() - t0)}
    log.write(json.dumps({"summary": summary}) + "\n"); log.close()
    print("DONE", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
