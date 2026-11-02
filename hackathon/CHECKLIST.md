# Hackathon checklist (definition of done)

The reviewer marks each row PASS or FAIL with evidence (path, command output, URL). Executor fixes in order. Max 3 passes.

Judged commit hash: `________________` (fill at 15:00 freeze; also in the form)

| Pass | Commit | Result |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

## A. Required submission items

| # | Item | Pass rule | Evidence |
|---|---|---|---|
| S1 | Project overview | README has task, user, approach, business value in ≤ 200 words, no hype words | |
| S2 | Public repo | `https://github.com/AliNazaarov/humanlm` opens in an incognito window; README renders; setup + eval instructions present | |
| S3 | Setup instructions | Fresh clone, `pip install -r requirements.txt`, `make test` passes; `.env.example` lists every key needed | |
| S4 | Eval instructions | `make eval` regenerates `hackathon/report/results.json` and `RESULTS.md` from committed outputs, no network | |
| S5 | Evaluation evidence | RESULTS.md states: baseline model ids, our model id + Fireworks job id, dataset source and size, metrics, method, before/after table, limitations | |
| S6 | Demo video | < 120 s (aim < 60 s), link in README and form, plays signed-out | |
| S7 | Team info | Names and roles in README and form | |
| S8 | Sponsor track | Fireworks named; NVIDIA award angle stated if Nemotron base was used; what was used on Fireworks (SFT, inference, judge) | |
| S9 | Commit hash | Hash recorded at the top of this file and in the form; `git log -1` on main matches | |
| S10 | Pre-existing work disclosed | README section lists what existed before 10:30 today (first commit `59f70c4`) and what was built during the event | |
| S11 | AI assistants disclosed | README says Claude Code was used, for what | |
| S12 | No keys / credentials / personal data | `git grep -nE "fw_|sk-ant-|sk-|Bearer [A-Za-z0-9]"` returns nothing across history (`git log -p \| grep`); `.env` untracked; no emails or names beyond the team | |

## B. Judging criteria

| # | Criterion (weight) | Pass rule | Evidence |
|---|---|---|---|
| J1 | Benchmark: same cases (40%) | Every system has 130 rows with the same ids from `evals/eval_all.jsonl`; `score_all.py` raises on a missing id | |
| J2 | Benchmark: eval separate from training | `hackathon/data/SPLIT.md` shows the leakage check result (0 dev/trick drafts in train); `evals/heldout_pairs.jsonl` ids absent from `hackathon/data/train.jsonl` (command output pasted) | |
| J3 | Benchmark: frontier baseline not weakened | Frontier live run uses the identical SYSTEM prompt and decoding; the pre-existing persona arm is also in the table; no prompt edits in git history for the frontier runner after the first run | |
| J4 | Benchmark: uncertainty | Bootstrap 95% CIs on fact-fail rate, in-band share, judge win rate; paired difference CI for FeatherLM-FT vs frontier | |
| J5 | Benchmark: judge protocol | Both orders run, inconsistent = tie, judge model id recorded, judge ≠ either compared system | |
| J6 | Benchmark: no cherry-picking | Every `evals/runs/hack_*.jsonl` file has a row in RESULTS.md; every metric in results.json appears in the table; n = 130 everywhere | |
| J7 | Benchmark: quality kept for cost/latency claims | Cost and latency rows sit next to the quality columns in the same table; the headline sentence names the quality tradeoff if any | |
| J8 | Business value (25%) | README states who pays, why fact-safety matters, cost per 1k rewrites for both systems, and one honest tradeoff | |
| J9 | Technical execution (20%) | Fireworks SFT job id and base model in TRAIN_LOG.md; inference via `api.fireworks.ai`; runner has retries and resume; `make test` green; 29 metrics tests + new stats/split tests pass | |
| J10 | Presentation (10%) | Video shows one real before/after, one chart, the three headline numbers with a CI; says Fireworks | |
| J11 | Documentation (5%) | README sections all filled; no placeholders; PRICES.md has URLs and the date | |

## C. Integrity and hygiene

| # | Check | Pass rule | Evidence |
|---|---|---|---|
| I1 | No fabricated numbers | Every number in README and RESULTS.md is found in results.json or TRAIN_LOG.md; TRAIN_LOG numbers trace to a console screenshot or log file | |
| I2 | Training data is licence-clean | Every train row's `source` is a Common Pile subset; no frontier outputs; README says so | |
| I3 | Prompt parity | `grep` the SYSTEM string: identical bytes in `pipeline/infer.py`, `hackathon/train/infer_fireworks.py`, `hackathon/eval/run_frontier.py` | |
| I4 | Outputs clean | No `<think>`, no empty outputs, no echoed input, per system (script check in score_all) | |
| I5 | Model weights not committed | `git ls-files \| grep -E "safetensors\|gguf\|\.bin$"` empty | |
| I6 | Fireworks deployments cleaned | Any on-demand deployment deleted after the final run (console screenshot or `firectl list deployments` output) | |
| I7 | Branch state | `main` contains both roles' work; no uncommitted changes at freeze; hash recorded | |
| I8 | Limitations honest | Lists: n=130 agent-written items, reverse-distilled drafts from one model family, judge bias, metrics ≠ human preference, any CI overlap, anything that failed in pass 3 | |
| I9 | Fallback disclosed (if used) | If the prompt-optimised variant replaced the fine-tune, the table column "Fine-tuned on Fireworks?" says No and the overview says why | |

## D. Submission timing

| Time | Done? |
|---|---|
| 15:00 freeze, pass 1 started | |
| 15:30 form submitted (can be edited after if the form allows; otherwise this is final) | |
| 16:00 video linked | |
| 16:30 close | |
