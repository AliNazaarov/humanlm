# HumanLM at "Fireworks: Deploy with Microsoft & NVIDIA" (Mon 2026-11-02)

Read this first. Then your role file: `ROLE_A_ALI.md` or `ROLE_B_FRIEND.md`. Paste your block from `AGENT_INSTRUCTIONS.md` into your Claude Code session. `CHECKLIST.md` is the definition of done.


## How our agents talk (no human relay)
Both agents use the repo as a mailbox: `hackathon/bus/bus.sh` (send, recv, status, board). Start each agent with the `/loop 5m` line in [bus/PROTOCOL.md](bus/PROTOCOL.md). Agents settle hand-offs, schema changes and blockers between themselves, and send `NEEDS-HUMAN:` only for keys, spending, going public, the video and Submit. Sync messages go out at 12:00, 1:30 and 3:00.

## First 10 minutes (both)
1. `git clone https://github.com/AliNazaarov/humanlm && cd humanlm`
2. `cp agents/hl-*.md ~/.claude/agents/` and install the ECC plugin in Claude Code.
3. `cp .env.example .env` and add your keys (never commit `.env`).
4. Read this file, then your role file (`ROLE_A_ALI.md` or `ROLE_B_FRIEND.md`) and `AGENT_INSTRUCTIONS.md`.
5. Start your agent loop from `bus/PROTOCOL.md`.

## 1. The event, distilled to what matters

| Item | Rule |
|---|---|
| Task | Open-model system for a meaningful task with a **measurable** improvement vs a **frontier-model baseline** (quality, cost or latency). Cost/latency wins must keep useful quality. Disclose tradeoffs. |
| Eval | Same cases for both systems. Eval cases must be separate from training data. Aim for 100+ varied held-out examples. Uncertainty estimates (CIs) encouraged. |
| Must use Fireworks | Every prize requires it. Serverless inference, SFT/LoRA, or deployments. Redeem credits at the event. |
| Judging | Benchmark evidence 40%, business value 25%, technical execution 20%, presentation/demo 10%, docs 5%. "A strong presentation cannot substitute for benchmark evidence." |
| Prizes | $10k / $5k / $3k, plus NVIDIA Best-Use Award (DGX Spark). |
| Submission | Project overview; **public** GitHub repo (works signed-out; private = unscored) with setup + eval instructions; evaluation evidence (baseline + model details, dataset source/size, metrics, method, before/after, limitations); demo video < 120 s (aim < 60 s); team info; sponsor track; **commit hash to be judged**. |
| Honesty | Disclose pre-existing work and what was built today. Disclose AI assistants. No keys, credentials or personal data in the repo. No fabricated results, no weakened baseline, no cherry-picking. |
| Clock | Build from 10:30. Start submitting by 15:30. Video done by 16:00. Submissions close 16:30. |

## 2. Our pitch (3 lines)

1. Frontier models can scrub AI tells from marketing copy, but they break facts (53/130 strict fact fails) and cut length by 40%.
2. HumanLM is a small open model, fine-tuned on Fireworks, that removes the tells **and** keeps every fact.
3. Same 130-item eval, same prompt: better faithfulness, equal or better human-range score, at a fraction of the cost and latency.

Task: rewrite AI-sounding marketing copy (landing pages, emails, LinkedIn) so it reads human while keeping every fact. User: founders and marketers who paste a draft and need it to sound like them without inventing claims. Business value: a fact-safe rewrite is the one thing a frontier model with a prompt does not give you; cheap enough to run on every draft.

## 3. Definition of done (mapped to judging)

| Judging criterion | Weight | Done when |
|---|---|---|
| Benchmark evaluation | 40% | `hackathon/report/RESULTS.md` has: a table of frontier vs base open model vs HumanLM-FT on the same 130 items (+ the held-out pair split if time), with fact hard-fails, in-human-range %, stock-phrase rate, length ratio, pairwise judge win rate with both orders, bootstrap 95% CIs, cost per 1k rewrites, p50/p95 latency. Method and limitations written. |
| Business value | 25% | Overview states user, task, why fact-safety matters, cost per 1k rewrites vs frontier, and a 2-line tradeoff disclosure. |
| Technical execution | 20% | Fine-tune ran on Fireworks (job id in report), inference through the Fireworks API, `make eval` reproduces the scores from committed outputs, metrics unit tests pass. |
| Presentation/demo | 10% | Video < 60 s, one before/after example, one results chart, one sentence on Fireworks. |
| Documentation | 5% | Root `README.md`: setup, `.env.example`, eval instructions, pre-existing vs built-today, AI-use disclosure, licence note on data. |
| Submission form | gate | All fields filled, public repo URL opens in an incognito window, commit hash recorded in `CHECKLIST.md`. |

## 4. Timeline (PT), 30-minute blocks

| Time | Ali (A: data + model) | Friend (B: eval + evidence + story) |
|---|---|---|
| 10:30 | Redeem Fireworks credits, `firectl` login, pick base model, confirm SFT is available for it. Start carving the held-out pair split. | Clone repo, create `friend/eval` branch, make root README skeleton, write `.env.example`, `Makefile` target `eval`. |
| 11:00 | Build train JSONL in Fireworks chat format from `data/build_mix.py` output (held-out ids excluded). Upload dataset. | Write `hackathon/eval/run_frontier.py` (identical prompt, logs latency/cost). Decide frontier model (see §7). Start the run. |
| 11:30 | Launch SFT job. While it runs: write `hackathon/train/infer_fireworks.py` (outputs schema in §6). Run the **untrained** base model on the eval set as the second baseline. | Write `hackathon/eval/judge.py` (pairwise, both orders) and `hackathon/eval/stats.py` (bootstrap CIs). Dry-run on `baseline_frontier.jsonl` vs `evals/runs/out_lora_v1.jsonl`. |
| **12:00 SYNC 1** | Both: is the SFT job running? Is the frontier run producing rows? Agree the exact metric list for the table. Merge to main. | |
| 12:30 | Poll the job. If it will not finish by 13:30, trigger Risk R1 (§8). Write the job id, base model, hyperparams into `hackathon/train/TRAIN_LOG.md`. | Build `hackathon/eval/score_all.py`: metrics.py + judge + stats → `hackathon/report/results.json` and `RESULTS.md` table. |
| 13:00 | Deploy the fine-tuned model (or serverless LoRA). Smoke-test 3 prompts. | Draft the results section with the two baselines already in hand. Start the demo notebook `hackathon/demo/demo.ipynb`. |
| **13:30 SYNC 2** | Both: run HumanLM-FT on all 130 (+ held-out). Hand the JSONL to B. Merge to main. | |
| 14:00 | Run the held-out pair split through all three systems if time. Record cost/latency. Second SFT config only if the first is clearly weak and there is 60+ min left. | Score everything. Fill the table. Make the one chart (`hackathon/report/results.png`). |
| 14:30 | Write limitations and tradeoffs with B. Pre-existing vs built-today list in README. | Write the 60-s video script. Record screen (notebook + chart + one example). |
| **15:00 SYNC 3: FREEZE** | Both: no more model or eval changes. Reviewer pass with `CHECKLIST.md` (max 3 passes). Repo public check in incognito. Record commit hash. | |
| 15:30 | Submit the form. Fix anything the form reveals. | Finish the video, upload, add link to README and form. |
| 16:00 | Video done. Final re-check of the form. | Buffer. |
| 16:30 | Closed. | |

## 5. Git workflow

- Repo: `https://github.com/AliNazaarov/humanlm` (currently has one commit from 2026-11-01). Make it **public** at SYNC 3 at the latest; earlier is fine.
- Branches: `ali/*` and `friend/*`. Direct push to `main` only at sync points, after `git pull --rebase`. Small commits, every 20–30 min, plain messages ("eval: add bootstrap CIs").
- Never commit keys. `.env` is gitignored; `.env.example` lists `FIREWORKS_API_KEY=`, `ANTHROPIC_API_KEY=` (or `OPENAI_API_KEY=`) with empty values. Before the freeze, run `git grep -nE "fw_|sk-ant-|sk-"` and `ecc:security-scan`.
- Never commit model weights (`.gitignore` already blocks `*.safetensors`, `*.gguf`, `lora_*/`). Do commit eval outputs and score JSONs (they are the evidence).
- The judged commit is the last one on `main` before 15:30. Write its hash in `CHECKLIST.md` and the form.

## 6. Interface contracts (so A and B do not block each other)

**Directory ownership**

| Owner | Paths |
|---|---|
| A (Ali) | `hackathon/train/`, `hackathon/data/`, `evals/heldout_pairs.jsonl`, `evals/runs/hack_*.jsonl` |
| B (friend) | `hackathon/eval/`, `hackathon/report/`, `hackathon/demo/`, root `README.md`, `Makefile`, `.env.example` |
| Shared, edit only at syncs | `hackathon/CHECKLIST.md`, `hackathon/README_HACKATHON.md` |
| Frozen, nobody edits | `evals/dev_set.jsonl`, `evals/trick_set.jsonl`, `evals/baseline_frontier.jsonl`, `pipeline/metrics.py` (bug fixes only, with a test) |

**Outputs JSONL** (one row per eval item, written by any system runner):

```json
{"id": "dev-001", "system": "fireworks:humanlm-ft-llama8b", "output": "...", "latency_ms": 812, "cost_usd": 0.00021, "prompt_tokens": 310, "completion_tokens": 140, "model": "accounts/<acct>/models/<id>"}
```

Rules: `id` matches the eval file; one row per id, 130 rows for the main set; `output` is the raw text with no `<think>` block; `latency_ms` is wall-clock for the single request; `cost_usd` is computed from the provider's listed price per token at run time (put the price used in `hackathon/report/PRICES.md`). File names: `evals/runs/hack_<system>.jsonl`.

**Prompt**: all systems use the exact SYSTEM string from `pipeline/infer.py` and the user turn = `ai_draft`. Temperature 0.7, top_p 0.9, max 400 new tokens, thinking off. Any change is agreed at a sync and applied to all systems.

**Eval set**: `evals/eval_all.jsonl` = dev (100) + trick (30). Optional second set: `evals/heldout_pairs.jsonl` (A carves 100–150 pairs by `pid` hash before building the training data; the training builder refuses those ids).

**Scores**: `hackathon/report/results.json` with per-system aggregates and CIs; `RESULTS.md` is rendered from it, never hand-typed.

## 7. Decisions the founder makes at 10:30

1. Base model for SFT. Preference order: an NVIDIA Nemotron model if Fireworks lists it for SFT (NVIDIA award angle), else Llama 3.1 8B Instruct, else Qwen 2.5/3 7–8B Instruct. Check docs.fireworks.ai for the current SFT-supported list; do not guess.
2. Frontier baseline for the live run. The existing `baseline_frontier.jsonl` (Claude Opus persona) has no latency or cost. Either re-run Claude (needs an Anthropic key) or GPT (OpenAI key) with the identical prompt. The persona-prompt file stays in the table as "frontier + strong prompt (pre-existing)".
3. Judge model. Prefer a large open model on Fireworks (so Fireworks is used for the judge too and the frontier is not judging itself). Note the bias in limitations either way.
4. Make the repo public now or at the freeze.

## 8. Risk plan

| Risk | Signal | Fallback |
|---|---|---|
| R1: SFT queue slow or job fails | Not running by 12:30, or not done by 13:30 | Switch to prompt-optimised open model on Fireworks serverless (same base, plus 3 gold examples and an anti-slop rule list) and the faithfulness harness as the "system". Keep the SFT job running; if it lands by 14:30, add it as a row. State plainly which rows are fine-tuned. |
| R2: fine-tuned model worse than frontier on tells | FT stock-phrase rate > frontier by a lot | Lead with faithfulness + cost + latency, and the length-controlled comparison; show tells as "within human range" rather than "lowest". Never drop a metric. |
| R3: eval noisy | CIs overlap on the headline metric | Report it. Bootstrap 1,000 resamples, both judge orders, also report the held-out pair split. Noise disclosed beats a cherry-picked number. |
| R4: frontier API key or rate limits | Rows stop | Use the pre-existing persona baseline for quality (it has no cost/latency) and estimate cost from list prices with a clear "estimated" label; latency from the rows that did complete. |
| R5: repo not public / keys leaked | Incognito check fails, `git grep` hits | Make public; rotate the key at the provider, rewrite the commit before pushing further. |
| R6: time | Behind by 14:00 | Cut the held-out pair split and the second SFT config. Never cut the CI, the limitations section, or the video. |

## 9. Pre-existing vs built today (disclosure plan)

Pre-existing (2026-10-31 to 11-01, in the first commit): corpus pipeline, ~7.8k reverse-distillation pairs, `data/build_mix.py`, `pipeline/metrics.py` and its 29 tests, the 130-item eval set, the Claude persona baseline file, CPU LoRA v0/v1 on Qwen3-0.6B and their scores.
Built today: everything under `hackathon/`, the Fireworks dataset format + upload + SFT job + deployment, Fireworks inference runner with cost/latency logging, frontier live re-run, pairwise judge, bootstrap CIs, results table/chart, demo notebook, video, public README. AI assistants (Claude Code) used throughout; say so in the README.
