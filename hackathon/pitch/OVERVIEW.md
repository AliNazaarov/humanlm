# Submission form text: FeatherLM

Paste each field as is. Every number is from `hackathon/report/results.json` (or the file named next to it) and is listed with its source in `hackathon/pitch/FINAL_CHECK.md`. Each field is under 250 words.

## Project name

FeatherLM: fact-safe human rewrites of AI copy, on an open model.

## Task (what the system does)

AI-written marketing copy reads like AI. People paste it into a frontier model and ask for a human rewrite. The frontier model cleans the style, but it also cuts sentences, drops numbers and sometimes adds a claim. For copy on a website or in a customer email, a changed fact is a legal and trust problem.

FeatherLM rewrites AI-sounding copy so it reads like a person wrote it, keeping every number, name and quote and adding nothing. Headline metric: the **fact-safe human rewrite rate**, the share of rewrites that pass four gates at once (G1 nothing invented, G2 nothing lost, G3 no AI tells beyond the human band, G4 length 0.7 to 1.3x the draft). Gates: `hackathon/harness/gates.py`; scoring: `hackathon/eval/score_all.py`. 247 items: 130 founder drafts (100 dev + 30 trick) and 117 held-out real human passages with AI-polished drafts, plus 80 real GitHub READMEs never used for tuning. Every system gets the same system prompt and items.

## Intended user

Founders, marketers and agencies who publish copy (landing pages, launch and cold emails, LinkedIn and X posts), and the AI agents that now draft and post copy for companies. They need text that does not read as AI and proof that the rewrite did not change what the company claims.

## Approach

Open model on Fireworks (GLM-5.3 Flash) inside an agentic harness: draft, check against the four gates, ask the model to fix only what failed, up to 3 rounds, plus one style round, keep the best candidate. Main row: **O3c**.

Results, all 247 items, 95% CI, paired bootstrap vs Claude Opus 5.5 with a strong rewrite prompt:
- FeatherLM (O3c): **96.8% [93.7, 98.6]** vs Claude strong **71.3% [65.2, 76.8]**, +26 pp [+20, +31], p<0.001. $0.81 vs $9.11 per 1k rewrites (about 11x cheaper), p50 3.4 s.
- 80 real READMEs: 97.5% vs 76.2%, +21 pp [+13, +31].
- Claude inside our harness (F1H): 93.5% at $15.85 per 1k. The harness is the contribution; Fireworks makes it cheap.
- Variants: ensemble E1 99.2% ($15.12/1k); same harness on DeepSeek V4.1 Flash (R3) 94.7%, so it transfers across model families.

Where we do not win: style. Blind human A/B (209 votes, 45 readers, frozen 15:15 PT): Claude 89, ours 64, both fine 56, p=0.052 (not significant at 0.05; p=0.029 after the stated reading-time rule). Judges are split and n.s. (Kimi K3 leans Claude, Qwen 3.8 Max leans ours). Readers flag choppy fragments in 37.7% of our outputs vs 10.0% of Claude's (`reader_tells.json`).

Training (toward real human writing): SFT A, B and C trained on Fireworks (Serverless Training API, LoRA on GLM-5.3 Flash, 5,000 licence-clean draft-to-human pairs). Serving a LoRA needs an on-demand deployment; only SFT B was served and evaluated: 32.8% without harness (base 26.7%). Local DPO (L2, Qwen3-4B on a Mac, human original as "chosen") trained 70 steps, not evaluated in time. All in `hackathon/train/TRAIN_LOG.md`.

## Business value

Who pays: founders, marketers, agencies and teams running copy agents. The pain: AI copy loses trust, and the tools that fix the style quietly change claims, which is FTC and brand exposure. FeatherLM is an API that returns a rewrite plus a machine-checked report that no number, name or quote was added, dropped or changed, at $0.81 per 1,000 rewrites against $9.11 for Claude with a strong prompt and $15.85 for Claude in the same harness (about 20x). Tradeoffs: up to four model calls per item; the check covers numbers, names, quotes and attributions, not general truth; and readers still prefer Claude's prose, which is the next training target.

## Built today vs pre-existing

Pre-existing (2026-10-31 to 11-01, first commit `59f70c4`, disclosed in the README): corpus pipeline and ~7.8k raw reverse-distillation pairs, `pipeline/metrics.py` with tests, the 130-item eval set, a Claude persona baseline file.

Built today (2026-11-02): everything under `hackathon/`: held-out split and leakage check, Fireworks runners, gates and harness, all variants and ensembles, frontier runs, scoring with paired bootstrap CIs, the real-README set, judges, the human A/B page, the audit, SFT A/B/C and DPO runs, the deck and video. AI assistants (Claude Code) were used throughout.

## Sponsor tracks

**Fireworks**: every open-model row runs on Fireworks serverless (GLM-5.3 Flash, DeepSeek V4.1 Flash); both judges (Kimi K3, Qwen 3.8 Max) run on Fireworks; SFT A/B/C were trained with the Fireworks Serverless Training API; SFT B was served on a Fireworks on-demand deployment (4x NVIDIA B300) for its evaluation.

**NVIDIA**: we attempted Nemotron on Fireworks serverless; the runs did not complete before the freeze, so there is no Nemotron row in `results.json` and we do not claim the track.

## Team

Muhammadali Nazarov (Ali: data, model, harness, pitch) and Ruslan Kan (eval, frontier baselines, report, training, demo). Two people, two Claude Code agents talking through `hackathon/bus/`.

## Links

Repo: `https://github.com/AliNazaarov/humanlm`. Judged commit: see `hackathon/CHECKLIST.md`. Video: add after recording.
