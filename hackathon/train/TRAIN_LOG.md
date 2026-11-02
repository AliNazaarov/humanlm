# Training log (built 2026-11-02 during the hackathon)

Platform: Fireworks **Serverless Training API** (LoRA, per-token billing, no deployment). Managed dataset upload was disabled on our account; Fireworks staff pointed us to the Training API, which renders and sends data from our machine.
Code: fw-ai/cookbook `recipes/sft_loop.py` (serverless) via `examples.sft.train_sft_serverless`; RL: `hackathon/train/rl_serverless.py` on the cookbook's async serverless RL loop.

## SFT v1 (O4)
| Field | Value |
|---|---|
| Base | `accounts/fireworks/models/glm-5p3-flash` (GLM-5.3 Flash, open weights, zai-org/GLM-5.3-Flash) |
| Renderer | `glm53_flash` (inferred), loss on assistant turns only |
| Data | `hackathon/data/train.jsonl`, 5,000 rows (see `hackathon/data/SPLIT.md`; 0 eval overlap) |
| LoRA | rank 16, alpha 32 (recipe default) |
| Optimizer | 1 epoch, batch 16 → 313 steps, LR 1.5e-4, max_seq_len 4096 |
| Session / run | ts-… / run-… (filled from the log below) |
| Smoke test | 20 rows, 3 steps, loss 1.08 → 1.04 (session deleted after) |

Command:
```bash
cd cookbook/training && python -m examples.sft.train_sft_serverless --base-model accounts/fireworks/models/glm-5p3-flash \
  --tokenizer-model zai-org/GLM-5.3-Flash --dataset <repo>/hackathon/data/train.jsonl --lora-rank 16 --max-seq-len 4096 \
  --epochs 1 --batch-size 16 --learning-rate 1.5e-4 --dcp-save-interval 50 --log-path <dir> --output-model-id humanlm-glm-sft-v1
```

## SFT model B (O4m, data ablation)
Status: **running; not evaluated before the freeze.** Same recipe as model A; only the data changes.

| Field | Value |
|---|---|
| Base | `accounts/fireworks/models/glm-5p3-flash` (tokenizer zai-org/GLM-5.3-Flash) |
| Renderer | `glm53_flash` (inferred), loss on all assistant messages |
| Data | `hackathon/data/train_modern.jsonl`, 2,924 rows, Creative Commons modern web only (model A: 5,000 rows, full licensed mix) |
| LoRA | rank 16, alpha 32 (recipe default) |
| Optimizer | 1 epoch, batch 16 → 183 steps, LR 1.5e-4 constant, max_seq_len 4096, DCP save every 50 steps |
| Account | Ruslan's Fireworks account (`ruslan-kan-1eth024hr`) |
| Session / run | `ts-6280bbf355554eb2b30467b0ea3f7d58` / `run-a2c41c59ec1b46629d4bcc6008c2f6fb` |
| Output model id | `humanlm-glm-sft-modern` (promoted only when the final step completes) |
| Started | 2026-11-02 13:09:50 PT (step 1 at 13:11:03) |
| Loss so far | step 1: 1.144 (13:11) · step 34: 0.646 (13:24) · step 82: 0.536 (13:41) · step 85: 0.765 (13:42). Per-step loss is noisy, mostly 0.5-0.9 after step 30 |
| Speed | about 25 s/step early on, about 60 s/step from step 80 on; final step expected around 15:20 PT |
| Tokens | 499,769 over the first 85 steps (mean 5,880 tokens/step) |
| Cost | **estimate**: 183 × 5,880 ≈ 1.08M tokens × $8.89/M ≈ $9.6 (not from a bill) |
| Smoke test | 20 rows, batch 8, 3 steps, loss 1.218 → 1.120 → 0.787; session deleted afterwards |

Run on Windows: the cookbook was used unchanged through a small runner (`run_sft.py`, kept outside the repo). The runner does three things: truststore for the HTTPS proxy, a stub for the Unix-only `resource` module (used only for peak-RSS logging in `utils/memlog.py`), and an `if __name__ == "__main__"` guard so the DataLoader workers that Windows spawns don't start new sessions. The first smoke attempt had no guard and leaked 5 sessions; all of them were deleted. pip couldn't fetch the `mcp` index page through the proxy, so mcp 1.30.0 was installed from its wheel URL.

Sampler-hang finding: `harness.py --provider fwsampler` was tested on the smoke snapshot (`ruslan-kan-1eth024hr/run-0b655a009eb8440790a78fa85f077cf6/step-3`). The sampling client builds without error, but `POST /training/v1/serverless/inference/v1/completions` never answers: the SDK retried after a 10-minute ReadTimeout, and direct curl and httpx calls also timed out. A made-up checkpoint name hangs the same way. A likely cause is that deleting the smoke run's training session also ended its snapshot. The model B session is kept open, so its snapshot may still sample, but this is unverified.
