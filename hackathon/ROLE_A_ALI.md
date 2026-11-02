# Role A: Ali (data + model on Fireworks)

You own: `hackathon/train/`, `hackathon/data/`, `evals/heldout_pairs.jsonl`, `evals/runs/hack_*.jsonl`. Branch `ali/*`. Do not edit B's paths except at syncs.

Goal by 13:30: a fine-tuned open model on Fireworks, its 130 eval outputs in the agreed JSONL schema, with cost and latency, handed to B.

## Step 0 (10:30–10:45): Fireworks setup

1. Redeem credits at the event. Create an API key in the Fireworks console. Put it in `.env` (`FIREWORKS_API_KEY=...`). Never paste it into a file that is tracked.
2. Install the CLI: check docs.fireworks.ai for `firectl` install (likely `brew install fw-ai/firectl/firectl` or a download) and `pip install fireworks-ai`. `firectl signin`.
3. Pick the base model. Open the Fireworks fine-tuning docs and list the models supported for supervised fine-tuning right now. Preference: NVIDIA Nemotron (NVIDIA award angle; mention it in the overview) > `llama-v3p1-8b-instruct` > Qwen 7–8B instruct. Write the choice and the reason in `hackathon/train/TRAIN_LOG.md`.
4. Confirm the serverless model id for the **untrained** base (second baseline), e.g. `accounts/fireworks/models/llama-v3p1-8b-instruct`. Check the exact id on fireworks.ai/models.

Done when: `curl` to `https://api.fireworks.ai/inference/v1/chat/completions` with the base model returns a rewrite for one eval item.

## Step 1 (10:45–11:15): held-out split + training data

Script: `hackathon/data/make_split.py`

- Read `data/pairs/*.jsonl` through the same filter as `data/build_mix.py` (it already dedups, applies `gen_pairs.keep()`, caps news at 25%).
- Hold out 120 pairs by stable hash of `pid` (e.g. `md5(pid) % 100 < 2`, then take the first 120 in sorted order). Write them to `evals/heldout_pairs.jsonl` with fields `{id: "ho-001"..., ai_draft, human, source, licence, url}`. These are never trained on. They are a second eval set with real human references.
- Also check: no training row's `ai_draft` shares more than 8 consecutive words with any `ai_draft` in `evals/dev_set.jsonl` / `trick_set.jsonl` (reuse the rule from `evals/README.md`). Print the count removed.
- Write `hackathon/data/train.jsonl` in Fireworks chat JSONL format. Likely shape (check docs.fireworks.ai "dataset format"):

```json
{"messages": [{"role": "system", "content": "<SYSTEM from pipeline/infer.py>"}, {"role": "user", "content": "<ai_draft>"}, {"role": "assistant", "content": "<human>"}]}
```

- Use the identical SYSTEM string from `pipeline/infer.py`. Cap to ~5,000 rows if the job estimate is slow (1 epoch; a 5k × ~400-token job should be well under an hour on most SFT services, but check the console estimate).
- Save a small `hackathon/data/valid.jsonl` (200 rows, also excluded from train) if the SFT job accepts a validation file.

Done when: `wc -l` shows train rows, `evals/heldout_pairs.jsonl` = 120 rows, the leakage check prints 0 overlapping dev items, and `hackathon/data/SPLIT.md` records the counts, source mix and the hash rule.

## Step 2 (11:15–11:30): upload + launch SFT

Likely commands (verify flags on docs.fireworks.ai):

```bash
firectl create dataset humanlm-sft-v1 hackathon/data/train.jsonl
firectl create sftj --base-model <base-id> --dataset humanlm-sft-v1 \
  --output-model humanlm-ft-v1 --epochs 1 --learning-rate 1e-4 --lora-rank 16
firectl get sftj <job-id>     # poll
```

Record in `hackathon/train/TRAIN_LOG.md`: job id, base model, dataset size, epochs, LR, rank, start time, and later the loss curve or final loss from the console (screenshot into `hackathon/train/`). No numbers from memory; copy what the console shows.

If the console offers a validation loss, enable it. If the job is estimated past 13:30, go to README_HACKATHON §8 R1 now: build the prompt-optimised variant (Step 3b) while the job runs.

## Step 3 (11:30–12:30): the Fireworks inference runner

Script: `hackathon/train/infer_fireworks.py`

```
usage: python3 infer_fireworks.py EVAL.jsonl OUT.jsonl --model <model-id> --system-name <label> [--concurrency 4]
```

- OpenAI-compatible endpoint: `POST https://api.fireworks.ai/inference/v1/chat/completions`, header `Authorization: Bearer $FIREWORKS_API_KEY`, body `{"model": ..., "messages": [system, user], "temperature": 0.7, "top_p": 0.9, "max_tokens": 400}`. For Qwen-family models add whatever disables thinking (check docs) and strip any `<think>...</think>` defensively.
- Per row write the schema from README_HACKATHON §6: `id, system, output, latency_ms, cost_usd, prompt_tokens, completion_tokens, model`. Latency = wall clock around the single request. Cost = tokens × the per-token price you read from the Fireworks pricing page today; put the prices in `hackathon/report/PRICES.md` (B owns the folder; add the file and tell B).
- Retry with backoff on 429/5xx; never skip an id silently. At the end assert 130 rows, unique ids, no empty outputs.
- Resume support: skip ids already in OUT.

Runs:
1. `evals/runs/hack_base_<model>.jsonl` — untrained base on `evals/eval_all.jsonl` (build `eval_all.jsonl` by concatenating dev + trick if it does not exist; it is a derived file, fine to commit).
2. Smoke test the runner on 3 rows first.

Done when: base run has 130 rows, passes the assert, and `python3 pipeline/metrics.py score evals/runs/hack_base_<model>.jsonl --field output --band evals/runs/band_v0.json` runs (faithfulness needs the source: B's `score_all.py` joins on id; you can also pass `--source-field` after joining `ai_draft` in).

### Step 3b (only if R1 triggered): prompt-optimised open model

`hackathon/train/prompt_v2.txt`: SYSTEM + 3 gold examples from `hackathon/data/train.jsonl` (never from eval files) + the slop list from `pipeline/slop_phrases.txt` as "never use". Run it with the runner, `--system-name fireworks:base-prompted`. It counts as a Fireworks open-model system. Say in the report that it is prompted, not fine-tuned.

## Step 4 (12:30–13:30): deploy + run the fine-tuned model

- When the job is done: check whether the output model is callable directly (some LoRA outputs are served serverless as `accounts/<acct>/models/humanlm-ft-v1`) or needs `firectl create deployment` (on-demand GPU, costs credits; delete it after the runs). Check docs for "deploy fine-tuned model".
- Smoke test 3 prompts. Look at the outputs yourself: no `<think>`, no truncation, no echo of the input.
- Run all 130: `evals/runs/hack_humanlm_ft.jsonl`, `--system-name fireworks:humanlm-ft-<base>`.
- Run the held-out split: `evals/runs/hack_humanlm_ft_heldout.jsonl` and the base on the same.

Done when: both files have the right row counts; hand them to B at SYNC 2 with the exact model id and the prices used.

## Step 5 (13:30–14:30): second pass, only if clearly needed

- If the FT model still leaves stock phrases at the frontier's expense, options in order of cost: (1) run with temperature 0.3 as an extra row (disclose), (2) a second SFT with 2 epochs or rank 32 if 60+ minutes remain. Never change the eval set or the prompt to help the model.
- Log every run in `TRAIN_LOG.md`. All rows go in the table; nothing is dropped.

## Step 6 (14:30–15:00): disclosure + limitations

With B, write in root README: pre-existing vs built today (README_HACKATHON §9), data licence (Common Pile, licence-clean), the training/eval separation rule and the leakage check result, the Fireworks job id. Add 2 tradeoffs: training data is reverse-distilled (AI draft generated from human original, so the "AI draft" distribution is one model family), and tell metrics are a screen, not human preference.

## Hand-offs

| To B | When | What |
|---|---|---|
| base run JSONL | 12:00 | `evals/runs/hack_base_*.jsonl` + prices |
| FT run JSONL | 13:30 | `evals/runs/hack_humanlm_ft*.jsonl` + model id + job id |
| held-out set | 11:15 | `evals/heldout_pairs.jsonl` (B adds it to `score_all.py`) |
| training facts | 14:30 | dataset size, base model, hyperparams, cost of the job, for the overview |

## Rules
- Never train on `evals/*`. Never put frontier outputs in training data.
- Every number in `TRAIN_LOG.md` comes from a console, a log, or a file. Write "not measured" rather than a guess.
- Keys only in `.env`. Delete any on-demand deployment when done.
