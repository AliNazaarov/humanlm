"""CPU smoke-test LoRA SFT: AI draft -> human text. Proves the pipeline end to end on a tiny model.

Real runs move to a rented GPU (Gemma-4-12B / Qwen3.5-9B, see model/BASE_MODELS.md); this one only
checks the data format, loss masking, saving, and that outputs move away from AI tells.
Usage: python3 train_lora_cpu.py PAIRS.jsonl OUT_DIR [max_pairs] [epochs]
"""
import json, sys, random, time, math, os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

PAIRS, OUT = sys.argv[1], sys.argv[2]
MAXP = int(sys.argv[3]) if len(sys.argv) > 3 else 600
EPOCHS = float(sys.argv[4]) if len(sys.argv) > 4 else 1
BASE = os.environ.get("BASE", "Qwen/Qwen3.5-0.8B")
SYSTEM = "Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, correct grammar. Keep every fact, name and number. Add nothing."
torch.set_num_threads(os.cpu_count())
random.seed(3)

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                                         target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.gradient_checkpointing_enable(); model.enable_input_require_grads(); model.print_trainable_parameters()

def encode(p):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": p["ai_draft"]}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full = prompt + p["human"] + tok.eos_token
    a = tok(prompt, add_special_tokens=False)["input_ids"]
    b = tok(full, add_special_tokens=False)["input_ids"][:512]
    labels = [-100] * len(a) + b[len(a):]          # loss on the human rewrite only
    return torch.tensor([b]), torch.tensor([labels[:len(b)]])

rows = [json.loads(l) for l in open(PAIRS)]
random.shuffle(rows)
H = min(30, len(rows) // 5); held = rows[:H]; rows = rows[H:MAXP + H]
json.dump(held, open(os.path.join(os.path.dirname(OUT) or ".", "heldout_pairs.json"), "w"))
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4)
steps = int(len(rows) * EPOCHS); accum = 4; log = []
model.train(); t0 = time.time()
for s in range(steps):
    ids, lab = encode(rows[s % len(rows)])
    if (lab != -100).sum() == 0:                    # prompt filled the window: no target tokens, loss would be NaN
        continue
    loss = model(input_ids=ids, labels=lab).loss / accum
    loss.backward()
    if (s + 1) % accum == 0:
        lr = 2e-4 * min(1, (s + 1) / 40) * 0.5 * (1 + math.cos(math.pi * s / steps))
        for g in opt.param_groups: g["lr"] = lr
        opt.step(); opt.zero_grad()
    log.append(loss.item() * accum)
    if (s + 1) % 20 == 0 or s < 3:
        print(f"step {s+1}/{steps} loss {sum(log[-20:])/20:.3f} {(time.time()-t0)/(s+1):.1f}s/step", flush=True)

def heldout_loss():
    model.eval(); tot = 0
    with torch.no_grad():
        for p in held:
            ids, lab = encode(p); tot += model(input_ids=ids, labels=lab).loss.item()
    model.train(); return tot / len(held)

model.save_pretrained(OUT); tok.save_pretrained(OUT)
json.dump({"base": BASE, "pairs": len(rows), "steps": steps, "train_loss_last50": sum(log[-50:]) / min(50, len(log)),
           "heldout_loss": heldout_loss(), "secs": round(time.time() - t0)}, open(os.path.join(OUT, "train_report.json"), "w"), indent=1)
print("TRAIN_DONE", open(os.path.join(OUT, "train_report.json")).read(), flush=True)
