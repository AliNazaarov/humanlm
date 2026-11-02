"""DPO on Ali's human preference labels, Fireworks serverless training, starting from the SFT LoRA.

Pairs: hackathon/train/human_rl/ai_labels.jsonl (GLM-5.3 RLAIF labels, both orders agree, both candidates pass gates;
Ali's own labels override per id, an edited row's `chosen` is Ali's edit). --labels labels.jsonl for Ali-only. Prompt = `ai_draft` for that id in
hackathon/train/human_rl/pref_prompts.jsonl (training prompts tr-*, never eval). System = pipeline/infer.py SYSTEM.

Warm start from SFT: serverless DPO in the cookbook only "resumes", so we hand it the SFT run as the run to
resume: init_from_checkpoint = SFT training state (weights + optimizer), and the persisted frozen reference
= the SFT sampler snapshot. The DPO reference is therefore the SFT model, as DPO-after-SFT should be.

  cd ~/models/hl/fwtrain/cookbook/training
  ~/models/hl/fwtrain/.venv/bin/python <repo>/hackathon/train/dpo_serverless.py --dry-run
  ~/models/hl/fwtrain/.venv/bin/python <repo>/hackathon/train/dpo_serverless.py \
      --sft-state <acct>/<run>/step-313 --sft-sampler <sampler path> --log-path <dir> [--output-model-id humanlm-glm-dpo-v1]
"""
import argparse, json, logging, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HR = ROOT / "hackathon/train/human_rl"
sys.path.insert(0, str(ROOT / "hackathon/harness"))
from harness import SYSTEM  # noqa: E402  (same string as pipeline/infer.py)


def build_pairs(out_path, labels_file):
    prompts = {json.loads(l)["id"]: json.loads(l)["ai_draft"] for l in open(HR / "pref_prompts.jsonl")}
    n = edited = skipped = ali = 0
    with open(out_path, "w") as o:
        for l in open(labels_file) if labels_file.exists() else []:
            r = json.loads(l)
            ch, rj = (r.get("chosen") or "").strip(), (r.get("rejected") or "").strip()
            if not ch or not rj or ch == rj or r["id"] not in prompts or not r["id"].startswith("tr-"):
                skipped += 1
                continue
            p = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompts[r["id"]]}]
            o.write(json.dumps({"chosen": {"messages": p + [{"role": "assistant", "content": ch}]},
                                "rejected": {"messages": p + [{"role": "assistant", "content": rj}]}}) + "\n")
            n += 1
            edited += bool(r.get("edited"))
            ali += r.get("judge") == "ali"
    return n, edited, skipped, ali


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sft-state"); ap.add_argument("--sft-sampler"); ap.add_argument("--log-path")
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--lr", type=float, default=1e-5)      # SFT used 1.5e-4: 15x lower (HF lesson: 5-20x)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--output-model-id")
    ap.add_argument("--labels", default=str(HR / "ai_labels.jsonl"),
                    help="ai_labels.jsonl (GLM-5.3 RLAIF + Ali overrides) or labels.jsonl (Ali only)")
    a = ap.parse_args()
    pairs = HR / "dpo_pairs.jsonl"
    n, edited, skipped, ali = build_pairs(pairs, Path(a.labels))
    print(f"pairs={n} ali={ali} edited={edited} skipped={skipped} -> {pairs}")
    if a.dry_run or n == 0:
        return
    import training.recipes.dpo_loop as dpo_loop
    from training.utils import RunnerConfig, WandBConfig
    os.makedirs(a.log_path, exist_ok=True)
    ref_file = os.path.join(a.log_path, "reference_checkpoint.json")
    if not os.path.exists(ref_file):
        json.dump({"reference_checkpoint": a.sft_sampler}, open(ref_file, "w"))
    cfg = dpo_loop.Config(
        serverless=True, log_path=a.log_path, base_model="accounts/fireworks/models/glm-5p3-flash",
        tokenizer_model="zai-org/GLM-5.3-Flash", renderer_name="glm53_flash", dataset=str(pairs),
        lora_rank=16, lora_alpha=32, max_seq_len=4096, epochs=a.epochs, batch_size=a.batch_size,
        learning_rate=a.lr, beta=a.beta, dcp_save_interval=0, init_from_checkpoint=a.sft_state,
        output_model_id=a.output_model_id, runner=RunnerConfig(reference_checkpoint_file=ref_file),
        wandb=WandBConfig(project="humanlm-dpo"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print("DPO_DONE", json.dumps(dpo_loop.main(cfg), default=str)[:2000])


if __name__ == "__main__":
    main()
