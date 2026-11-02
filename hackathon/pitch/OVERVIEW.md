# Submission form text: FeatherLM

Paste each field as is. Every `[RESULT: ...]` placeholder must be filled from `hackathon/report/results.json` (never typed from memory); audit numbers come from `hackathon/audit/AUDIT.md`. Each field is under 250 words.

## Project name

FeatherLM: fact-safe human rewrites of AI copy, on an open model.

## Task (what the system does)

Marketing copy written by AI reads like AI: "seamlessly", "unlock", em dashes, "it's not just X, it's Y", three adjectives in a row. Founders and marketers paste that draft into a frontier model and ask for a human rewrite. The frontier model cleans the style, but it also cuts sentences, drops numbers and sometimes adds a claim. For copy that goes on a website or in a customer email, a changed fact is a legal and trust problem, not a style problem.

FeatherLM rewrites AI-sounding copy so it reads like a skilled human wrote it while keeping every fact, number, name and quote and adding nothing. The headline metric is the **fact-safe human rewrite rate**: the share of rewrites that pass four gates at once (G1 nothing invented, G2 nothing lost, G3 no AI tells inside the human band, G4 not gutted, 0.7 to 1.3x the draft length). The gates are defined once in `hackathon/harness/gates.py` and scored by `pipeline/metrics.py` on 250 items: 130 agent-written founder drafts (100 dev + 30 trick) and 120 held-out real human passages with their AI-polished drafts. Every system sees the same system prompt and the same items.

## Intended user

Founders, marketers and agencies who publish copy (landing pages, launch and cold emails, LinkedIn and X posts), and the growing set of AI agents that draft and post copy for companies. They need two things at once: text that does not read as AI, and a guarantee that the rewrite did not change what the company claims. Today they choose between a frontier model (good style, facts at risk) and "humanizer" tools (paraphrase, no fact guarantee).

## Approach

Three layers, all on Fireworks:

1. **Open base.** GLM-5.3 Flash on Fireworks serverless with the shared system prompt (row O1).
2. **Prompting.** A rules-plus-examples prompt built from three training pairs and a banned-phrase list (row O2).
3. **Agentic harness.** Draft, check against the four gates with `pipeline/metrics.py`, ask the model to fix only the listed problems, up to 3 revisions, keep the best candidate (rows O3, O3b, O3c). The verifier is the same code that scores the leaderboard, so we audited it with signals the harness never sees (`hackathon/audit/AUDIT.md`).

Fine-tuning: SFT on 5,000 licence-clean reverse-distillation pairs (Common Pile human text; an open model wrote the AI draft; we train draft -> human). `[RESULT: SFT job id and status from hackathon/train/TRAIN_LOG.md, or "dataset upload blocked on our Fireworks account; SFT not completed, disclosed"]`. RL with the gates as reward is designed (`hackathon/harness/gates.py` is the reward function) and `[RESULT: run / not run]`.

Baselines, same prompt and items: Claude Opus 5.5 (live, and with a strong rewrite prompt), GPT-6.1 Terra, and Claude Opus 5.5 plus our harness (the fairness row).

## Results (fill from results.json)

Fact-safe human rewrite rate on all 250 items, 95% CIs, paired bootstrap vs Claude Opus 5.5 strong:

- FeatherLM harness (O3, GLM-5.3 Flash): `[RESULT: pass rate, CI]`, `[RESULT: delta pp, CI, p]`, `[RESULT: $ per 1k]`, `[RESULT: p50 latency]`
- Claude Opus 5.5 strong prompt: `[RESULT]`
- GPT-6.1 Terra: `[RESULT]`
- Open base without harness: `[RESULT]`

Audit (`hackathon/audit/AUDIT.md`): with the gates' regex artefacts forgiven, the harness still leads the best frontier row by `[AUDIT: lenient gap pp]`; near-copies of the draft `[AUDIT: %]`; deleted-sentence rate `[AUDIT: %]` vs Claude `[AUDIT: %]`.

## Business value

Who pays: founders, marketers and agencies, and companies running copy-writing agents. The pain is concrete: AI copy reads fake and loses trust, and the tools that fix the style quietly change claims, which is an FTC exposure (fake or unsubstantiated claims) and a brand risk. FeatherLM is an API that returns a human-sounding rewrite with a machine-checked guarantee that no fact was added, dropped or changed, at open-model prices: `[RESULT: $ per 1k rewrites, harness]` vs `[RESULT: $ per 1k, Claude strong]` per 1,000 rewrites, at `[RESULT: p50]` latency.

Tradeoffs, stated plainly: the harness calls the model up to four times per item; the guarantee is a verifier over numbers, names, quotes and attributions, not a general fact checker; and the current tell-rate advantage over Claude on tells outside the gates is not there (the audit shows Claude slightly better on burstiness and lexical variety).

Moat: licence-clean reverse-distillation data no closed lab can copy without the same pipeline, a verifier that doubles as eval and RL reward, and the pick/edit loop from users that becomes preference data.

## Built today vs pre-existing

Pre-existing (first commit, 2026-10-31 to 11-01, disclosed in the README): corpus pipeline and ~7.8k raw reverse-distillation pairs, `pipeline/metrics.py` with its tests, the 130-item eval set, the Claude persona baseline file.

Built today (2026-11-02): everything under `hackathon/`: the held-out split and leakage check, the Fireworks runners, the gates and the agentic harness, the frontier runs (Claude, GPT), the scoring script with paired bootstrap CIs, the leaderboard and report, the independent audit, the demo, the video, this submission. No trained model was brought in. AI assistants (Claude Code) were used throughout; the README says so.

## Sponsor tracks

**Fireworks**: every open-model row runs on Fireworks serverless (GLM-5.3 Flash); the harness is an OpenAI-compatible loop against `api.fireworks.ai`; training data was prepared in Fireworks chat format `[RESULT: SFT job id if it ran]`.

**NVIDIA best-use**: we attempted Nemotron (`nemotron-lightning-3p5-30b-a3b`) on Fireworks serverless as rows N1 (base) and N3 (harness). Serverless latency reached several minutes per item and the runs did not complete before the freeze (`hackathon/runs/logs/N1_nemotron_base.log`), so there is no Nemotron row in the leaderboard and we do not claim this track. `[RESULT: update if a hack_N*.jsonl file landed before the freeze; the audit script picks it up automatically]`

## Team

Ali Nazarov (data, model, harness, pitch) and Ruslan (eval, frontier baselines, report, demo). Two people, two Claude Code agents talking through `hackathon/bus/`.

## Links

Repo: `[RESULT: public GitHub URL]`. Judged commit: `[RESULT: hash from hackathon/CHECKLIST.md]`. Video: `[RESULT: URL]`.
