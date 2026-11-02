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
| Session / run | `ts-f12d2e58613c483c9421bf2c13307cc8` / `run-903ab80912a5489a8d5fba5b370cab42` |
| Final checkpoint | `step-313` (sampler snapshot `run-903ab80912a5489a8d5fba5b370cab42-step-313-8a920662`) |
| Promoted model | `accounts/ali-wry88cc4wb07/models/humanlm-glm-sft-v1` (HF_PEFT_ADDON, READY 13:07 PT) |
| Steps | 313 (11:29 → 13:07 PT) |
| Loss | step 1: 1.2393 · mean of first 10 steps: 0.849 · mean of last 10 steps: 0.686 · step 313: 0.6429 |
| Held-out loss | not measured (the recipe logged no eval loss) |
| Train tokens | 1,856,167 (sum of logged step tokens) → est. cost $16.50 at $8.89/M (serverless GLM-5.3 Flash train rate) |
| Smoke test | 20 rows, 3 steps, loss 1.08 → 1.04 (session deleted after) |

Command:
```bash
cd cookbook/training && python -m examples.sft.train_sft_serverless --base-model accounts/fireworks/models/glm-5p3-flash \
  --tokenizer-model zai-org/GLM-5.3-Flash --dataset <repo>/hackathon/data/train.jsonl --lora-rank 16 --max-seq-len 4096 \
  --epochs 1 --batch-size 16 --learning-rate 1.5e-4 --dcp-save-interval 50 --log-path <dir> --output-model-id humanlm-glm-sft-v1
```

## SFT model B (O4m, data ablation)
Status: **trained and promoted; not evaluated** (no sampling path worked, see below). Same recipe as model A; only the data changes. Times are PT (UTC-8).

| Field | Value |
|---|---|
| Base | `accounts/fireworks/models/glm-5p3-flash` (tokenizer zai-org/GLM-5.3-Flash) |
| Renderer | `glm53_flash` (inferred), loss on all assistant messages |
| Data | `hackathon/data/train_modern.jsonl`, 2,924 rows, Creative Commons modern web only (model A: 5,000 rows, full licensed mix) |
| LoRA | rank 16, alpha 32 (recipe default) |
| Optimizer | 1 epoch, batch 16 → 183 steps, LR 1.5e-4 constant, max_seq_len 4096, DCP save every 50 steps |
| Account | Ruslan's Fireworks account (`ruslan-kan-1eth024hr`) |
| Session / run | `ts-6280bbf355554eb2b30467b0ea3f7d58` (left open) / `run-a2c41c59ec1b46629d4bcc6008c2f6fb` |
| Checkpoints | DCP `step-50`, `step-100`, `step-150`, `step-183`; sampler `ruslan-kan-1eth024hr/run-a2c41c59ec1b46629d4bcc6008c2f6fb/step-183` (server name `run-a2c41c59ec1b46629d4bcc6008c2f6fb-step-183-382158dc`) |
| Output model | `accounts/ruslan-kan-1eth024hr/models/humanlm-glm-sft-modern` (HF_PEFT_ADDON, READY, promoted 13:22 PT; not deployed) |
| Time | started 12:09:50, step 1 at 12:11:03, step 183 at 13:20:27, promoted 13:22:06 (about 72 min; 25-60 s/step) |
| Loss | step 1: 1.144 · step 34: 0.646 · step 82: 0.536 · step 183: 0.699 (mean of the last 10 steps 0.699). Per-step loss is noisy, mostly 0.5-0.9 after step 30 |
| Tokens | 1,077,157 (183 steps, mean 5,886/step) |
| Cost | **estimate**: 1.077M tokens × $8.89/M ≈ $9.58 (not from a bill) |
| Smoke test | 20 rows, batch 8, 3 steps, loss 1.218 → 1.120 → 0.787; session deleted afterwards |

Run on Windows: the cookbook was used unchanged through a small runner (`run_sft.py`, kept outside the repo). The runner does three things: truststore for the HTTPS proxy, a stub for the Unix-only `resource` module (used only for peak-RSS logging in `utils/memlog.py`), and an `if __name__ == "__main__"` guard so the DataLoader workers that Windows spawns don't start new sessions. The first smoke attempt had no guard and leaked 5 sessions; all of them were deleted. pip couldn't fetch the `mcp` index page through the proxy, so mcp 1.30.0 was installed from its wheel URL.

Sampling, not working on this account:
- `harness.py --provider fwsampler` (serverless sampler on a LoRA snapshot): the client builds without error, but `POST /training/v1/serverless/inference/v1/completions` never answers. This happened on the smoke snapshot (`.../run-0b655a009eb8440790a78fa85f077cf6/step-3`: the SDK retried after a 10-minute ReadTimeout) and on the final step-183 snapshot while its session was still open (60 s timeouts over both HTTP/1.1 and HTTP/2). A made-up checkpoint name hangs the same way, so the request seems to hang before any snapshot lookup.
- The promoted model through the normal chat completions API returns 404 "Model not found, inaccessible, and/or not deployed": the model has no deployment, and the account has no serverless LoRA.
- On-demand deployment: `deploymentShapeVersions:match` with `enableAddons` returns 0 shapes for glm-5p3-flash, so multi-LoRA is not offered. The smallest shape without addons is `glm-5p3-flash-rft-b300-fp8block128-w4-p1`: 4x NVIDIA B300 FP8, $15/GPU-h on fireworks.ai/pricing, about $60/h.
  - Ruslan approved a brief live-merge deployment (cap $45). The first create call at 13:38 PT returned "payment method is required".
  - After a payment method was added, the retry was blocked by the agent's permission system (spending money needs the user's own go-ahead in that session).
  - **No deployment was ever created**; the deployment list was empty at 13:44 PT.
- So there are no O4m eval rows.

## DPO toward human references (O7)
Status: **stopped at step 1; no model.** The serverless DPO reference sampler hangs, the same problem as above.

| Field | Value |
|---|---|
| Pairs | `hackathon/data/dpo_humanref_pairs.jsonl`, 800 pairs from train_modern (rule, 8-gram overlap check and reader-tell selection in `hackathon/data/DPO_HUMANREF.md`) |
| Script | `hackathon/train/dpo_serverless.py`, run from a Temp copy with only `ROOT`/`HR` paths changed (pairs instead of Ali's labels) |
| Warm start | `init_from_checkpoint = ruslan-kan-1eth024hr/run-a2c41c59ec1b46629d4bcc6008c2f6fb/step-183` (SFT B weights + optimizer); frozen reference = SFT B sampler snapshot `.../step-183` |
| Hyperparameters | beta 0.1, LR 1e-5, batch 4, 1 epoch = 200 steps, LoRA r16/α32, max_seq_len 4096 (script defaults, except epochs 1); output id `humanlm-glm-dpo-humanref` |
| Attempts (PT) | 13:28: crashed (Windows `resource` stub did not reach spawned workers; fixed with a `resource.py` on PYTHONPATH) · 13:29: 409 capacity_exhausted · 13:31: trainer state restored, then reference logprobs through `trainingSamplers/checkpoints/.../step-183` got HTTP 504 and ReadTimeout after 600 s on every request. Stopped at 13:43 PT with 0 optimizer steps |
| Sessions | all DPO sessions deleted (`ts-e09d964c…`, `ts-2873f12e…`, `ts-f264bbb5…`); SFT B session `ts-6280bbf3…` kept |
| Cost | no optimizer steps; only trainer-state restore and timed-out sampler calls (no token count logged) |

**Status: trained and promoted; not evaluated.** Serving a trained LoRA on Fireworks requires an on-demand deployment, which needs a payment method on this account (deployment creation refused). Serverless LoRA serving is "not enabled for this account" (HTTP 404 for the promoted model on the chat endpoint). The serverless sampler on the snapshot hung in our tests. Ruslan's SFT B / O7 rows are the evaluated fine-tunes.

## O6 DPO-RLAIF (prepared, not trained)
- Preference source: GLM-5.3 (`accounts/fireworks/models/glm-5p3`, reasoning low) pairwise judge on 120 training-prompt pairs (`hackathon/train/human_rl/cand1.jsonl` vs `cand2.jsonl`), both orders; kept only where both orders agree and both candidates pass the gates: 65 kept, 51 orders disagreed, 4 failed gates (`ai_labels_summary.json`).
- Ali's labels override per id: 3 Ali labels; AI agreed with Ali on 2/2 overlapping ids.
- Final: 66 DPO pairs in `hackathon/train/human_rl/dpo_pairs.jsonl` (`ai_labels.jsonl`). Script: `hackathon/train/dpo_serverless.py` (beta 0.1, LR 1e-5 = 15x below SFT, 2 epochs, warm start = SFT state + SFT sampler as frozen reference).
- Not trained: the SFT model it would start from cannot be served or evaluated on this account (same reason as above).

## O4/O5 rows
Not produced (see status above). The harness supports `--provider fwsampler` for serverless sampler snapshots, but sampling the SFT snapshot did not return within 10 minutes.
