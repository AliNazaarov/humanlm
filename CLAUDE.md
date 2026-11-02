# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FeatherLM: an open model that rewrites AI-sounding copy so it reads like a skilled human wrote it, keeping every fact and adding nothing. Today (2026-11-02) it is being entered in the Fireworks "Deploy with Microsoft & NVIDIA" hackathon: fine-tune an open model on Fireworks and beat a frontier baseline on the same 130 eval items. Start with `CONTEXT.md` for the product, `hackathon/README_HACKATHON.md` for the event rules and timeline.

## Commands

Python 3, stdlib-first. On Windows use `python` and set `PYTHONUTF8=1` (data files are UTF-8; some scripts call `open()` without an encoding).

```bash
pip install -r requirements.txt
cd pipeline && python -m unittest tests.test_metrics                 # metric tests
cd pipeline && python -m unittest tests.test_metrics.TestPhrases.test_curly_apostrophe_matches  # one test
python -m unittest discover -s hackathon/eval -p "test_*.py"         # eval-harness tests
make test / make eval                                                # same, PYTHON ?= python3
python pipeline/metrics.py score RUN.jsonl --field output --source-field ai_draft --band evals/runs/band_v0.json
PYTHONUTF8=1 python hackathon/data/make_split.py                     # rebuild train/valid/held-out (deterministic)
```

Keys live in `.env` (gitignored); names are in `.env.example`.

## Architecture

**Data flow:** Common Pile human passages (`pipeline/fetch.py` → `passages.py` → `shard.py`) → reverse distillation in `pipeline/gen_pairs.py` (an open model writes the "AI-polished" draft of each human passage) → pair `(ai_draft → human)`. `gen_pairs.keep()` is the single quality filter (length ratio, numbers/names preserved, attribution and quote checks); `data/build_mix.py` and `hackathon/data/make_split.py` both reuse it by `exec`-ing the top of `gen_pairs.py` up to `done = set()`, so edits above that line change every downstream dataset.

**One prompt everywhere:** the `SYSTEM` string in `pipeline/infer.py` is the system prompt for training data and for every eval system. User turn = `ai_draft`. Decoding: temperature 0.7, top_p 0.9, max 400 tokens, thinking off. Changing any of these for one system invalidates the comparison.

**Evals:** `evals/dev_set.jsonl` (100) + `evals/trick_set.jsonl` (30) = `evals/eval_all.jsonl` (130). `evals/heldout_pairs.jsonl` (120) are held-out real pairs with human references. `pipeline/metrics.py` scores outputs: 13 separate tell metrics (no combined score), `in_band` against a human 10th–90th percentile band (`evals/runs/band_v0.json`), and `faithfulness` hard fails (any new number, name or quote vs the source).

**Every system runner writes the same JSONL** to `evals/runs/hack_<system>.jsonl`: `id, system, output, latency_ms, cost_usd, prompt_tokens, completion_tokens, model`. 130 rows, unique ids, no empty output, no `<think>` text. Prices used go in `hackathon/report/PRICES.md`. `hackathon/eval/score_all.py` joins runs to eval items by `id` and writes `hackathon/report/results.json` + `RESULTS.md`; numbers in the report come only from `results.json`.

## Hard rules

- Nothing under `evals/` is ever training data. Training rows must not share 8+ consecutive words with any eval draft (checked in `make_split.py`).
- Frozen: `evals/dev_set.jsonl`, `trick_set.jsonl`, `baseline_frontier.jsonl`, `pipeline/metrics.py` (bug fixes only, with a test).
- No frontier-model text in training data. No weakening the frontier baseline, no cherry-picking: every system run gets a row.
- No number in docs, messages or reports that is not in a committed file.

## Two-agent hackathon setup

Two people, each with their own Claude Code agent, talk through the repo with `hackathon/bus/bus.sh` (`send`, `recv`, `status`, `board`; see `hackathon/bus/PROTOCOL.md`). Each message is its own file, so agents never edit the same file. `bus.sh` pulls and pushes the current branch, so both agents work on `main`.

| Role | Owns |
|---|---|
| A, Ali (`ROLE_A_ALI.md`) | `hackathon/train/`, `hackathon/data/`, `evals/heldout_pairs.jsonl`, `evals/runs/hack_*.jsonl` |
| B, friend (`ROLE_B_FRIEND.md`) | `hackathon/eval/`, `hackathon/report/`, `hackathon/demo/`, `README.md`, `Makefile`, `.env.example`, `requirements.txt` |

To change the other role's files, send a `CONTRACT:` or `Q:` message instead. Humans are pulled in only via `NEEDS-HUMAN:` for keys, spending, making the repo public, the video, and Submit. `hackathon/CHECKLIST.md` is the definition of done.
