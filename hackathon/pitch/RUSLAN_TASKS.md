# Ruslan's side: three tasks to push FeatherLM past Claude on judged quality (written 13:30 PT, 2026-11-02)

Clock: times below are PT; the bus stamps UTC (PT = UTC-8 today). New-system freeze **15:00 PT = 23:00Z**. Dev stop rule **14:30 PT = 22:30Z**.

## Where we stand (all numbers from `hackathon/report/RESULTS.md`)
- Fact-safe rate: O3c 97% vs Claude Opus 5.5 strong 71%. Won.
- Judged quality, O3c vs Claude: Kimi K3 style 33/46 (n.s.), Qwen 3.8 Max style 44/27 (p=0.057, ours). Humans 13/23/7, lean Claude, n.s.
- Two readings of the judge table that decide what to build:
  1. **Selection works, "calm" does not.** The only row that leads Kimi on style is O3j (best-of-3 picked by a GLM judge): 44/37. Every calm round loses badly (O3f 16/62, O3k 11/68). So: more candidates + a better picker, never a calmer prompt.
  2. **We lose "overall" on the Facts sub-verdict, not only style.** O3j facts 4/25, O3d 5/22, O3c 9/15. G1/G2 pass, so the judge is seeing dropped claims and thinness (criterion (c) "Coverage" in `hackathon/eval/JUDGE_PROMPT.md`), which the regex gates never check. Fixing coverage flips "overall" even where style stays level.

Rules for all three: no Claude/GPT text as training data or few-shot; the picker/labeller is GLM-5.3 (never Kimi K3 or Qwen, the eval judges); every run gets a row and a manifest; dev check on `dev-031..dev-070` with the GLM-5.3 dev judge before any full run; abandon at 14:30 PT if the dev style verdict vs O3c is not ahead (wins > losses). Ruslan writes only under `hackathon/train/ruslan/`, `evals/runs/hack_R*_*.jsonl`, `hackathon/runs/R*.json`, and his own `hackathon/eval`, `hackathon/report`, `README.md`.

Shared setup (once, 5 min):
```bash
mkdir -p hackathon/train/ruslan hackathon/runs/logs
# 40-item dev slice (ids dev-031..dev-070), used by every dev check below
python3 - <<'EOF'
import json
rows=[l for l in open("evals/eval_all.jsonl") if 31<=int(json.loads(l)["id"].split("-")[1])<=70 and json.loads(l)["id"].startswith("dev-")]
open("hackathon/train/ruslan/dev_031_070.jsonl","w").writelines(rows); print(len(rows))
EOF
# dev judge = GLM-5.3 (not an eval judge). Usage for any candidate run R:
#   python3 hackathon/eval/judge.py evals/runs/hack_R.jsonl evals/runs/hack_O3c_glm_prompt_harness_style.jsonl \
#     --eval hackathon/train/ruslan/dev_031_070.jsonl --model accounts/fireworks/models/glm-5p3 \
#     --allow-partial --out hackathon/train/ruslan/devjudge_R_vs_O3c.jsonl
```

---

## TASK R1 (start first, it runs longest): human-reference DPO from base GLM-5.3 Flash
**Row:** `R1_glm_dpo_humanref` (+ `R1h_glm_dpo_humanref_harness` if time). **Owner:** Ruslan's agent, Ruslan's Fireworks account.

**Why it can beat Claude:** today's judges ask "which reads like a skilled human wrote it" and the held-out judge asks "closer to the human original". SFT only raises the likelihood of human text; DPO with chosen = the real human original and rejected = GLM's *own* rewrite of the same AI draft teaches the contrast the judge scores: "this is what the human did instead of what you do". No frontier text anywhere, licence-clean (Common Pile + CC), and it is a clean third row for the chart: SFT alone (O4, Ali) / DPO alone from base (R1) / SFT+RLAIF-DPO (O6, Ali). Not a duplicate of O6: different signal (human originals, not GLM preferences), different start (base), 5x the pairs.

**Steps**
1. Rejected candidates (10 min, ~$0.10 est.): take the first 400 `tr-*` rows of `hackathon/data/train.jsonl` (user turn = AI draft, assistant turn = human original). Generate GLM's own rewrite with the plain O2 setting so the rejected side is the model's natural output:
   ```bash
   python3 - <<'EOF'
   import json; rows=[json.loads(l) for l in open("hackathon/data/train.jsonl")][:400]
   with open("hackathon/train/ruslan/r1_prompts.jsonl","w") as o:
       for i,r in enumerate(rows):
           m=r["messages"]; o.write(json.dumps({"id":f"tr-r1-{i:04d}","ai_draft":m[1]["content"],"human":m[2]["content"]})+"\n")
   EOF
   python3 hackathon/harness/harness.py hackathon/train/ruslan/r1_prompts.jsonl hackathon/train/ruslan/r1_rejected.jsonl \
     --provider fireworks --model accounts/fireworks/models/glm-5p3-flash --system-name R1_rejected \
     --loops 0 --prompt-file hackathon/train/prompt_v2.txt --concurrency 8
   ```
   (If harness.py needs a `facts` field on each item, add `"facts": []`.)
2. Build pairs in the exact format `hackathon/train/dpo_serverless.py:build_pairs` writes (`{"chosen":{"messages":[system,user,assistant]},"rejected":{...}}`, system = `harness.SYSTEM`). Keep a pair only if the human original passes `gates.check(draft, human)` G2+G4 (numbers kept, length 0.7-1.3) so DPO never prefers a fact-dropping text, and drop pairs where rejected == chosen. Expect ~300 left. Write `hackathon/train/ruslan/r1_dpo_pairs.jsonl`.
3. Train (serverless DPO, same cookbook loop as `dpo_serverless.py`, but **from the base model, reference = base**; copy the script to `hackathon/train/ruslan/dpo_humanref.py` and remove the SFT-resume branch): base `accounts/fireworks/models/glm-5p3-flash`, tokenizer `zai-org/GLM-5.3-Flash`, LoRA rank 16, beta 0.1, LR 1e-5, **1 epoch, batch 4** (≈75 steps), max_seq_len 4096, DCP save every 25 steps, `--output-model-id humanlm-glm-dpo-humanref`. Run through your Windows runner as for SFT model B. Log to `hackathon/train/ruslan/R1_LOG.md`.
   - **Time budget:** measure s/step at step 5. If projected finish is after 14:40 PT, stop and restart with 200 pairs (≈50 steps). Keep the session open after training (the sampler hang in TRAIN_LOG was tied to a deleted session).
4. Sample 250 rows (`evals/eval_all.jsonl` and `evals/heldout_pairs.jsonl`) with `--provider fwsampler --model <acct>/<run>/step-<last>` into `evals/runs/hack_R1_glm_dpo_humanref.jsonl` / `_heldout.jsonl`, `--loops 0` (pure model row). If fwsampler still hangs after 5 min, send `BLOCKED:` to ali with the snapshot path: Ali's side is sampling O4 now and will post the exact command that worked.
5. Dev check: judge the 40 dev rows vs O3c with the GLM dev judge (command above). Continue to the full 250 only if style wins > losses. If time remains, `R1h` = same model with `--loops 3 --prompt-file hackathon/train/prompt_v2.txt --style-round` (the O3c harness on top).
6. Manifest `hackathon/runs/R1_glm_dpo_humanref.json` (base, pairs file + count, beta, LR, epochs, batch, run id, step, git commit); add the training row to `hackathon/train/TRAIN_LOG.md` via a `CONTRACT:` to ali (Ali owns that file) or put it in `R1_LOG.md` and link it.

**Cost (estimate, not from a bill):** rejected generation under $0.20; DPO ≈ 75 steps × ~6k tokens ≈ 0.5M tokens × $8.89/M ≈ $4-8; sampling under $0.30. **Time:** pairs 15 min, train 40-60 min, sample 10 min → start by 13:50, lands ~14:50. **Stop rule:** not started training by 14:05, or projected finish after 14:45, or dev style not ahead of O3c by 14:30 → abandon, report as "trained, not evaluated" like model B.

---

## TASK R2 (cheapest, most certain): cross-run ensemble with a GLM pairwise knockout and a coverage gate
**Row:** `R2_ensemble_select`. **Owner:** Ruslan's agent (eval side; no harness change, reads committed run files only).

**Why it can beat Claude:** best-of-3 from one pipeline already moved Kimi style to 44/37 (O3j). We have 8+ gate-passing runs per item (O3c, O3j, O3l, O3e, O3d, O3b, O3f, O3k, plus O4/O5/O6/R1/R3 as they land) made with different prompts and rounds, so the candidate pool is far more diverse than any single best-of-N. A per-item knockout by a non-eval judge (GLM-5.3, both orders, "which reads like a skilled human and keeps everything", tie → keep incumbent) picks the best of all our work. The new part that targets the Facts loss: **eligibility = gates.check pass AND a two-way GLM claim check with no `draft_claims_missing`** (the one-way check in `harness.claim_check` only catches added claims; the judge punishes dropped ones, see WINNING_IDEAS "two-way atomic check"). Also prefer, on ties, the longer candidate within G4, since criterion (c) punishes thinness.

**Steps**
1. `hackathon/train/ruslan/ensemble_select.py`: inputs = list of run files (main + `_heldout` variants), output `evals/runs/hack_R2_ensemble_select.jsonl` (+ `_heldout`, + `_real` if the real-split files exist for ≥3 candidates). Per item: load every candidate output; eligibility as above (reuse `gates.check` from `hackathon/harness/gates.py`; write the two-way claim check as one GLM-5.3 call with `response_format json_object` returning `draft_claims_missing` and `rewrite_claims_unsupported`, temperature 0); knockout with `harness.pair_pick`-style prompting (copy the prompt, both orders, agreement required, else incumbent stays; incumbent order = O3c first, then by fact-safe rate). Record `selection: {source_run, eligible, picks}` per row.
2. Cost accounting (honest): `cost_usd` per row = sum of the constituent candidates' `cost_usd` for that item + judge cost; latency = max candidate latency + judge latency. The row will cost roughly the sum of the runs it draws on; still under Claude's $9.11/1k (RESULTS.md) if you cap the pool at 5 runs. Write this rule in the manifest.
3. Dev check on `dev-031..070` first with a 5-run pool (O3c, O3j, O3l, O3e, O3d) vs O3c with the GLM dev judge. Proceed to full 250 only if style and overall wins > losses.
4. Full run; then both eval judges (Kimi, Qwen) vs `hack_strong_claude-opus-5-5` through the normal `judge.py` path, both orders, on **all 250** (and the real 80 if available), so the n is large enough to turn a lean into significance honestly.
5. Manifest `hackathon/runs/R2_ensemble_select.json`: pool (run names + commits), selector model, prompt sha, eligibility rules, cost rule. Add the row to `score_all.py` like any other.

**Cost (estimate):** ~250 items × ≤4 knockout rounds × 2 orders + 250 × 5 claim checks ≈ 3,000 GLM-5.3 calls ≈ $2-4. **Time:** script 25 min, dev 10 min, full 15 min, judges 15 min → done by ~14:45. **Stop rule:** dev style not ahead of O3c by 14:30 → drop; the script still stays as the pitch's "pick/edit loop" demo.

---

## TASK R3 (cheap, feeds R2): a second open model family as candidate generator, same O3c harness
**Row:** `R3_<model>_prompt_harness_style`. **Owner:** Ruslan's agent, Ruslan's Fireworks key.

**Why it can beat Claude:** every candidate in every row comes from GLM-5.3 Flash, so best-of-N and R2 can only choose among GLM's habits (the fragments and closers the humans named). A different family with the identical harness (prompt_v2, 3 loops, style round, same gates) adds genuinely different prose to R2's pool and is a clean "harness transfers across open models" slide. Kimi K3 and Qwen are off limits (eval judges). Candidates on Fireworks, in order: `accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b` (already named in `hackathon/train/run_matrix.sh`), then a DeepSeek V4.1 Flash id if the account lists one, then a gpt-oss id. Verify the id with a 3-item smoke run (`--limit 3`) before anything else.

**Steps**
1. Smoke: `python3 hackathon/harness/harness.py hackathon/train/ruslan/dev_031_070.jsonl /tmp/r3_smoke.jsonl --provider fireworks --model <id> --system-name R3_smoke --loops 3 --prompt-file hackathon/train/prompt_v2.txt --style-round --limit 3 --in-price <p> --out-price <p>` (prices from the Fireworks pricing page, logged to `hackathon/report/PRICES.md`).
2. Dev run on the 40-item slice to `evals/runs/hack_R3_<model>_prompt_harness_style_dev.jsonl`; dev judge vs O3c. Also check the gate pass rate with `pipeline/metrics.py score` / `score_all` on the slice; abandon the model if fact-safe on the slice is below O3c's dev rate (RESULTS.md dev split: O3c 96%) by more than 5 pp.
3. Full 250 (eval_all + heldout) and the real 80 if time; `hackathon/runs/R3_<model>_prompt_harness_style.json` manifest; hand the paths to R2's pool.

**Cost (estimate):** under $1 at open-model prices. **Time:** 10 min smoke+dev, 10 min full → done by 14:15. **Stop rule:** no working model id by 13:55, or dev style behind O3c at 14:30 → drop.

---

## What Ali's side owes Ruslan (sent on the bus too)
- The exact `fwsampler` command/path that worked for O4 sampling, as soon as it works (R1 step 4).
- `hackathon/train/TRAIN_LOG.md` row for R1 (Ali owns the file; Ruslan sends a `CONTRACT:` with the row text).
- No harness change is required for R1-R3: R2 imports `gates.check` and copies the pairwise prompt; R3 and R1h use existing flags (`--loops --prompt-file --style-round --provider fwsampler`). If `harness.py` cannot read an item without `facts`, Ali adds a default of `[]` (one-line change).
- Ali's `beat-claude-style` workflow should drop its own routing/ensemble variant if it has one: R2 covers it and will include Ali's O4/O5/O6 rows the moment they are committed under `evals/runs/hack_O4*|O5*|O6*.jsonl`.

## Entry decision at 15:00
Pick the entry row by the pre-registered order: fact-safe rate first (must stay ≥ O3c's), then Kimi+Qwen style and overall vs Claude on the same items, then cost. Candidates: O3c (current), R2, best of O5/O6/R1h. Whatever wins, the chart shows every row.
