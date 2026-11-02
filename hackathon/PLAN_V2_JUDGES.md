# Plan v2: what the judges asked for (from the kickoff, 10:30)

This replaces the earlier plan where they conflict. The judges want five things:
1. **A harness:** off-the-shelf open models with better prompting and an agentic loop.
2. **A fine-tune:** SFT, plus RL if possible.
3. **One clear test** on a fixed held-out set, with repeatable runs.
4. **A leaderboard-style before/after chart**, with significance for each row.
5. **An investable problem.**

Closed models are allowed, with a budget of $30–50.

## Task and headline metric
**Task:** rewrite AI-written marketing copy so it reads like a skilled human wrote it, without changing any fact.

**Headline metric: fact-safe human rewrite rate** = % of rewrites that pass **all** of these:
| Gate | Rule (from `pipeline/metrics.py`) |
|---|---|
| G1 Nothing invented | `faithfulness.hard_fail == False` (no new number, name, quote or attribution) |
| G2 Nothing lost | `numbers_kept == 1.0` and `names_kept >= 0.9` |
| G3 No AI tells | `stock_rate`, `em_dash_rate`, `not_x_but_y_rate`, `emoji_rate`, `exclaim_share` all at or below the human band's upper bound (`evals/runs/band_v0.json`) |
| G4 Not gutted | output words / draft words between 0.7 and 1.3 |

We report the gates separately too, so nobody has to trust one composite number. Secondary metric: pairwise humanness judge against the frontier model (both orders, and a judge from a different model family than the frontier arm). Tertiary: the blind human mini-test (20 pairs).

**Why this test:** frontier models clean the style but change or drop facts and shorten the copy, so they score low on this rate. That leaves the most room for improvement, which is what the judges asked for. We confirm it with a pilot first: score the frontier on dev, trick and held-out, then put the weakest split in the headline next to the full set. The full set is always shown.

## Systems (one leaderboard, the same 250 items: eval_all 130 + held-out 120)
| # | System | Type | Owner |
|---|---|---|---|
| F1 | Claude Opus 5.5, strong rewrite prompt | frontier baseline (the bar to beat) | Friend |
| F2 | GPT (latest available), same prompt | frontier | Friend |
| F3 | Gemini (latest available), same prompt | frontier, if a key is available | Friend |
| O1 | Open base on Fireworks, SYSTEM only | open baseline | Ali |
| O2 | O1 + better prompt (3 train-set examples + banned slop list) | prompting | Ali |
| O3 | O1 + **agentic harness**: draft → check gates with metrics.py → targeted revise (max 3 loops) → pick best | harness | Ali |
| O4 | **SFT LoRA** on Fireworks (5k pairs) | fine-tune | Ali |
| O5 | O4 + harness | fine-tune + harness | Ali |
| O6 | **RL** (Fireworks reinforcement fine-tuning, reward = G1–G4 from metrics.py) on top of O4 | RL | Ali, only if the SFT finishes by 13:00 |
| F1+H | F1 + the same harness | fairness row: shows how much the harness alone adds | Friend |

Every row shows: rate, 95% CI, Δpp vs F1, paired significance (significant / n.s.), $ per 1k rewrites, and p50 latency. Failed variants stay in the chart.

## Closed-model budget ($30–50)
- Frontier arms F1–F3 on 250 items: a few dollars each.
- The judge: the largest share.
- No frontier text ever goes into training data.
- Log every call's cost to `hackathon/report/PRICES.md` and the run files.

## Repeatable runs
- Every run writes `evals/runs/hack_<system>.jsonl` plus `hackathon/runs/<system>.json` (model id, prompt file hash, decoding settings, harness settings, git commit, timestamp).
- `make eval` rebuilds every table and the chart from the run files.

## Business value (investable)
- **Who:** founders, marketers and agencies, plus the fast-growing set of AI agents that write and post copy for companies.
- **Pain:** AI copy reads as fake and loses trust. "Humanizer" tools paraphrase and quietly change facts, which is a legal risk (FTC rules on fake claims and reviews).
- **Product:** an API that makes copy sound human and is guaranteed not to change your facts, at open-model prices.
- **Moat:** licence-clean reverse-distillation data, the fact-safe verifier used both as eval and as RL reward, and the pick/edit data loop.

## Social prize ($100 per post, up to 15 posts)
Post an image and what we're building on LinkedIn or X. Tag Fireworks, NVIDIA and Microsoft. At 20 likes and 10 reshares, email a screenshot and the link to fireworks@hackersquad.io. Both of us post. Draft: `hackathon/social/LINKEDIN_POST.md`.

## Publishing
At the freeze, publish the judged repo from a single squashed snapshot of `main`, containing only what the submission uses. The pre-existing data pipeline and pairs are disclosed in the README.
