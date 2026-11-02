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
