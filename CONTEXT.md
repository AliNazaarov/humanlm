# HumanLM: start here (handoff, 2026-11-02)

**What it is:** our own model, plus a simple tool, that rewrites AI-sounding copy so it reads like a skilled human wrote it. It keeps every fact and adds nothing. It answers YC's Winter 2027 request "LLMs That Write Well". It's not a GPT wrapper: the model underneath is ours.

## Decisions so far (full log: `board/DECISIONS.md`)
- **Product order:** a simple copy tool for everyone first, then "sounds like you" (personal voice), then an API for agents.
- **First styles:** copywriting and social: landing pages, launch and cold emails, LinkedIn/X.
- **First buyer:** founders. Businesses only, no students.
- **Data:** licence-clean human text only (Common Pile). **Reverse distillation:** an open model writes the "AI-polished" version of a human passage, and we train AI draft → human original. Frontier-model outputs are for eval baselines only, never training data.
- **"Human" is defined and measured** in `PLAN_30D.md` §2: passes a blind A/B with skilled readers, no AI tells (stays inside the human range), specific, zero grammar errors, faithful (no new facts, names, numbers or quotes), not thinner. AI detectors are watched but never used as the reward.
- **Compute:** GPU budget under $2k. Free first: Mac M4 (MLX), Tenki CPU sandboxes, Kaggle/Colab free GPUs.

## Read in this order
1. `BRIEF.md`: the YC ask, research findings, ideas.
2. `PLAN_30D.md`: the "human" definition, training ladder, loop and 30-day plan.
3. `WHAT_ELSE.md`: what matters besides evals; kill rules.
4. `research/`, `market/`: competitors, Hugging Face RL lessons, benchmarks, base models (`model/BASE_MODELS.md`).

## Pipeline (`pipeline/`)
| Step | Script | Notes |
|---|---|---|
| Download corpus | `fetch.py` | Common Pile subsets |
| Cut passages | `passages.py` | 80–300 words, cleans out boilerplate; ~290k passages so far |
| Mix shards | `shard.py` | `{source:cap}` mixes |
| Make pairs | `gen_pairs.py SHARD OUT URL TAG` | Qwen3.5 GGUF on llama.cpp makes the AI draft. `keep()` filter: length, numbers, names, and the **attribution/quote check** |
| Build training mix | `data/build_mix.py OUT 0.25` | Re-filters, dedups, caps news at 25% |
| Generate | `infer.py EVAL OUT [adapter]` | Set `BASE` to the trained base |
| Score | `metrics.py score/band` | 13 tell metrics, human range, faithfulness hard fails. Tests: `python3 -m unittest tests.test_metrics` |
| Keep it running | `overnight_watchdog.sh` | Restarts generators, syncs pairs safely |

## Data and evals
- `data/pairs/*.jsonl`: ~7.8k raw pairs. Fields: pid, ai_draft, human, template, gen_model, source, licence, url, created. Raw pairs are not all clean; always build the training set with `data/build_mix.py`.
- `evals/`: dev set (100), trick set (30), frontier baseline (130). **Eval only: never train on these.** Scored runs are in `evals/runs/`.

## What's next
1. **v2 on free compute:** MLX LoRA on `mlx-community/Qwen3.5-4B-4bit` on a Mac (data: 5,982 pairs, 38% modern web text). Then an 8–9B run on a free Kaggle/Colab GPU (Unsloth QLoRA). See the checklist.
2. **Real founder copy:** 20 hand-written rewrites (landing pages, launch emails, LinkedIn) as the modern pairs and eval split C.
3. **Blind ratings by 2–3 paid copywriters:** the real test. The metrics are only a screen.

## Agents
`agents/hl-*.md` are Claude Code subagents: orchestrator, researcher, data-curator, trainer, writer-panel, judge, designer, builder, critic and gtm. Copy them to `~/.claude/agents/` to use them. Work is coordinated through `board/` (BOARD.md, OPEN.md, DECISIONS.md).

## Rules
- No pirated data (no Books3). No student essays without consent.
- Never use detector scores as a reward. Never market this as detector evasion.
- Never commit model weights or keys. Weights go in a private Hugging Face repo.
