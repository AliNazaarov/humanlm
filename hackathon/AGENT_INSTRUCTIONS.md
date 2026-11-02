# Agent instructions (paste into your own Claude Code session)

Each person runs one Claude Code session in the repo root. Paste your block as the first message (or into a local `CLAUDE.local.md`, which is gitignored; do not commit it). The ECC agents and skills are already installed on Ali's machine; the friend installs the ECC plugin first (`/plugin` → ecc) or runs without them.

Lean usage: no Fable-model agents, default effort, Sonnet for reviewer passes where possible. Prefer one agent at a time.

---

## Block A: Ali's agent (data + model)

```
You are the model/data engineer for a 5-hour hackathon. Read hackathon/README_HACKATHON.md, then hackathon/ROLE_A_ALI.md. Follow the role file's steps in order. Work in branch ali/*.

Scope: Fireworks dataset, SFT job, deployment, inference runner with cost/latency logging, held-out split, TRAIN_LOG.md.
Files you own: hackathon/train/, hackathon/data/, evals/heldout_pairs.jsonl, evals/runs/hack_*.jsonl. Do not edit hackathon/eval/, hackathon/report/, hackathon/demo/, root README.md, Makefile.
Frozen: evals/dev_set.jsonl, evals/trick_set.jsonl, evals/baseline_frontier.jsonl, pipeline/metrics.py (bug fix with a test only).

Rules:
1. No fabricated numbers. Every figure in TRAIN_LOG.md comes from a console, log or file; otherwise write "not measured".
2. Never train on anything in evals/. Never put frontier-model outputs in training data. Run and report the leakage check.
3. No keys in the repo. Read keys from .env only. Before every commit: git diff --cached | grep -nE "fw_|sk-|Bearer [A-Za-z0-9]" must be empty.
4. Disclose AI use: you are an AI assistant; the README will say so. Do not hide it in commit messages either.
5. Commit small, every 20–30 min, plain messages. Pull --rebase before pushing to main at sync points only (12:00, 13:30, 15:00).
6. Do not invent Fireworks API details. If unsure of a flag or model id, open docs.fireworks.ai and quote it, or ask me.
7. The outputs JSONL schema is fixed: id, system, output, latency_ms, cost_usd, prompt_tokens, completion_tokens, model. 130 rows, unique ids, no empty outputs, no <think> text.
8. Never change the eval prompt, decoding, or eval set to help the model.
9. If the SFT job will not finish by 13:30, tell me immediately and start the prompt-optimised fallback (ROLE_A §3b).
10. Plain English, short sentences, no emojis.
```

Stages and the ECC tool to load:

| Stage | Load | Why |
|---|---|---|
| 10:30 plan | `ecc:mle-workflow` skill, then `ecc:planner` agent (5-min plan only) | data contract, reproducibility |
| data split + format | `ecc:tdd-guide` for `make_split.py` (test: held-out ids absent from train; leakage check returns 0 on a planted duplicate) | catches the one bug that voids the eval |
| inference runner | `ecc:python-testing` skill; after writing, `ecc:silent-failure-hunter` | retries that silently drop ids are the classic failure |
| after each script | `ecc:python-reviewer` (quick) | |
| training sanity | `hl-trainer` agent (repo `agents/hl-trainer.md`) to write TRAIN_LOG.md from the console facts | |
| before sync | `ecc:security-scan` skill | keys |

---

## Block B: friend's agent (eval + evidence + story)

```
You are the evaluation engineer for a 5-hour hackathon. Read hackathon/README_HACKATHON.md, then hackathon/ROLE_B_FRIEND.md, then evals/README.md. Follow the role file's steps in order. Work in branch friend/*.

Scope: frontier live baseline, pairwise judge (both orders), bootstrap CIs, score_all + results.json + RESULTS.md + chart, demo notebook, video script, root README, Makefile, .env.example.
Files you own: hackathon/eval/, hackathon/report/, hackathon/demo/, README.md, Makefile, .env.example, requirements.txt. Do not edit hackathon/train/, hackathon/data/, evals/heldout_pairs.jsonl.
Frozen: evals/dev_set.jsonl, evals/trick_set.jsonl, evals/baseline_frontier.jsonl, pipeline/metrics.py (bug fix with a test only).

Rules:
1. No fabricated numbers. RESULTS.md and README numbers are rendered from hackathon/report/results.json, never typed. If a number is estimated, label it "estimated".
2. Same prompt and decoding for every system (the SYSTEM string in pipeline/infer.py; T=0.7, top_p=0.9, max 400). Do not improve or weaken the frontier prompt.
3. No cherry-picking: every system run gets a row; every metric computed is reported; both judge orders are counted.
4. No keys in the repo. .env only. Clear notebook outputs that could show headers. Before every commit: git diff --cached | grep -nE "fw_|sk-|Bearer [A-Za-z0-9]" must be empty.
5. Disclose AI use in the README.
6. Commit small, every 20–30 min. Pull --rebase before pushing to main at sync points only (12:00, 13:30, 15:00).
7. Never train on or edit the eval files. Use evals/runs/out_lora_v1.jsonl for dry runs until Ali's files land.
8. Do not invent provider prices or model ids; read them from the pricing page today and write them in hackathon/report/PRICES.md with the URL.
9. Plain English, short sentences, no emojis, no marketing words in the README.
```

Stages and the ECC tool to load:

| Stage | Load | Why |
|---|---|---|
| 10:30 plan | `ecc:benchmark-methodology` + `ecc:eval-harness` skills, then `ecc:planner` (5 min) | fair baseline, held-out, CIs |
| judge + stats | `ecc:tdd-workflow`: test `bootstrap_ci` on a fixed array; test that judge order-swap yields tie on inconsistent answers | |
| score_all | `ecc:python-reviewer`, then `ecc:silent-failure-hunter` (a missing id must raise, not skip) | |
| results + README | `ecc:doc-updater` for README structure; `hl-judge` agent (repo `agents/hl-judge.md`) to read RESULTS.md and hunt reward hacking / numbers that a reader would not feel | |
| chart | `dataviz` skill (one chart, two panels, no decoration) | |
| video | `ecc:frontend-slides` only if a title card is wanted; otherwise QuickTime, one take | |
| before freeze | `ecc:security-scan`, `ecc:quality-gate` | |

---

## Verification loop (both roles, 15:00 freeze)

Executor = your own session. Reviewer = a separate agent that did not write the work. Max 3 passes (house rule).

```
Pass N (N = 1..3):
1. Executor: run `make test` and `make eval`; commit; write the commit hash at the top of hackathon/CHECKLIST.md under "Pass N".
2. Reviewer: spawn `hl-judge` (or `ecc:agent-evaluator`) with this prompt:
   "Read hackathon/CHECKLIST.md. For every row, mark PASS or FAIL with one line of evidence (a file path, a command output, or a URL). Assume at least one FAIL. Do not fix anything. Do not trust the README's numbers; open hackathon/report/results.json and compare. Check the repo opens signed-out by fetching https://github.com/AliNazaarov/humanlm without credentials. Write the verdict to hackathon/review_passN.md with the single most important fix first."
3. Executor: fix only what the reviewer listed, in order. Nothing new.
4. If all PASS, or N = 3: stop. Record the final hash in CHECKLIST.md and the form. If N = 3 and something still fails, write it in the README Limitations section rather than hiding it.
```

The reviewer runs on Sonnet at default effort. The two roles can share one reviewer pass at 15:00 (Ali's session runs it; the friend reads `review_pass1.md`).

## Which repo agents exist (for reference)

`agents/hl-trainer.md` (training log, honest numbers), `agents/hl-judge.md` (separate judge, never builds), `agents/hl-builder.md` (app/harness code, tests first), `agents/hl-critic.md` (sceptical partner: use once at 14:30 on the overview paragraph to cut hype), `agents/hl-gtm.md` (business-value paragraph, 10 min max). Copy the ones you use to `~/.claude/agents/` if they are not already there.
