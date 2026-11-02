# Checklist: v2 free training run (2026-11-02)

Goal: train HumanLM v2 on a bigger model **with no paid compute**, score it against v1 and the baselines, and leave a free path for an 8–9B run. Executor: main session. Checker: hl-judge (separate agent, never edits). Max 3 verification passes.

Each item is PASS or FAIL with evidence (a file path, a number or a log line). "Looks fine" is not evidence.

## A. Deliverables
| # | Deliverable | Where | Done when |
|---|---|---|---|
| D1 | v2 training data | `~/models/hl/mlx_data/{train,valid}.jsonl` | Built from `data/pairs/*` via `data/build_mix.py` with the attribution filter; news ≤25%; train/valid disjoint |
| D2 | v2 LoRA adapter (free, local) | `~/models/hl/lora_v2/` | MLX LoRA on `mlx-community/Qwen3.5-4B-4bit`, 1 epoch over D1 (HF lesson: 1 SFT epoch), training log saved |
| D3 | Eval outputs | `HumanLM/evals/runs/out_mlx_base4b.jsonl`, `out_lora_v2.jsonl` | 130/130 rows each, same SYSTEM prompt as v0/v1, thinking off |
| D4 | Scores | `HumanLM/evals/runs/score3_*.json` | Same `metrics.py` + `band_v0.json` for base-4B, v1, v2 and frontier |
| D5 | Free 8–9B path | `HumanLM/model/free_gpu/` | Kaggle/Colab notebook + README: free T4/P100, Unsloth QLoRA, same data and eval, no paid steps |
| D6 | Report section | `HumanLM/MORNING_REPORT_2026-11-01.md` | v2 table and an honest verdict, plus what's free vs paid |

## B. QA (the checker verifies each one)
| # | Check | Pass rule |
|---|---|---|
| Q1 | No spend | No paid GPU or API was used: Tinker is unused (billing blocked), no RunPod. Compute = Mac M4 + Tenki CPU only |
| Q2 | Licence-clean data | Every D1 row's source is in {news, gutenberg, public_domain_review, foodista, cccc} `_filtered` (Common Pile). No frontier outputs in the training data |
| Q3 | No eval leakage | No `eval_all.jsonl` ai_draft text appears in the D1 train/valid user turns |
| Q4 | Mix rules | news ≤25% of D1; zero D1 rows fail `gen_pairs.keep()` (incl. attribution) |
| Q5 | Training sane | Loss falls (first report > last report); val loss logged; no NaN in the log |
| Q6 | Eval complete | D3 files have 130 rows, unique ids that match eval_all, no empty outputs, no `<think>` leftovers |
| Q7 | Fair comparison | Base-4B and v2 use the same SYSTEM prompt, temperature and max tokens; metrics run with the same band file |
| Q8 | Fact gate | v2 strict fact fails (`faith_hard_fails`) ≤ v1's (6) **or** the report says plainly that it got worse |
| Q9 | Tells | v2 is better than base-4B on ≥3 of: stock_rate, em_dash_rate, emoji_rate, one_line_para_share, in-band share |
| Q10 | Honest report | Every number in D6 matches the score files; limits stated (metrics ≠ human preference) |
| Q11 | Free path real | D5 notebook installs only open-source packages, reads our data and eval files, writes outputs in the same format; README lists exact free quotas and the one manual step (login) |
| Q12 | Tests | `python3 -m unittest tests.test_metrics` passes in `HumanLM/pipeline` |
| Q13 | Housekeeping | Tenki hl-train/hl-data paused; Mac generation restarted after training; no stray training processes |
