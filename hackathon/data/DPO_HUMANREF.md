# DPO pairs toward human references (`dpo_humanref_pairs.jsonl`)

800 preference pairs built from **training data only** (`hackathon/data/train_modern.jsonl`). No eval items, no human A/B votes, no Claude/GPT text.

Each line has these fields:
- `id`: source row (`trm-NNNN` = line index in `train_modern.jsonl`).
- `system`: the shared SYSTEM string.
- `prompt`: the row's AI draft.
- `chosen`: the row's human original.
- `rejected`: our O3c-recipe rewrite of that draft.
- `source`: `train_modern` (all 800; `train.jsonl` was not needed).
- `rejected_reader_tells` / `chosen_reader_tells`: counts from `hackathon/eval/reader_tells.py` `tells()`.

## Rule
1. Shuffle `train_modern.jsonl` row indices with `random.Random(0).shuffle`, then take rows in that order. The first pass took 300 rows; a second pass continued from row 301 of the shuffled order until 570 more were kept.
2. Overlap check: drop any row whose draft or human text shares 8+ consecutive words (lowercased `[a-z0-9']+` tokens) with any `ai_draft` in `evals/eval_all.jsonl` or `evals/real_readmes.jsonl`, or with any `ai_draft`/`human` in `evals/heldout_pairs.jsonl`. **893 rows scanned, 33 dropped, 860 kept.**
3. Rejected = `hackathon/harness/harness.py` with the O3c recipe, exactly as in `hackathon/runs/O3c_glm_prompt_harness_style.json`:
   - provider `fireworks`, `accounts/fireworks/models/glm-5p3-flash`
   - `--loops 3 --prompt-file hackathon/train/prompt_v2.txt --style-round`
   - temperature 0.7, top_p 0.9, max_tokens 1500, reasoning_effort low (prompt sha `99e063324fd0d9b7`)
   - concurrency 8 and 12
4. A pair is kept only if the rejected output is non-empty, passes all gates (`gates.pass`), and differs from the human text. **860 rewrites: 27 failed gates, 0 identical to the human text, 0 empty, so 833 valid pairs.** Because every rejected side passes the gates, DPO learns voice, not fact-keeping.
5. Selection to 800 (reader-tell preference, patterns applied to training text only):
   - Pairs whose rejected side has at least 1 reader tell and whose chosen (human) side has none come first: 98 pairs.
   - The rest follow in shuffled order.
   - Among the 833 valid pairs: 117 rejected sides are tell-positive and 27 chosen sides are tell-positive.
   - **In the 800 selected: 115 rejected sides are tell-positive, and 98 pairs are tell-positive on the rejected side and tell-free on the chosen side.**

Built 2026-11-02 for DPO model O7 (`humanlm-glm-dpo-humanref`, see `hackathon/train/TRAIN_LOG.md`). The same pairs can be reused for SFT A.
