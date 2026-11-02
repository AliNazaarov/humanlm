# HumanLM overnight report (2026-11-01)

**Short version:** The full pipeline works end to end on free compute: data, pairs, training, eval. Model v0 is trained. It moves every AI tell toward the human range, but it's a tiny 0.6B model and it picked up a news-article habit from the data. That tells us what to fix before the first real GPU run (~$2–6).

## What exists now
- **Corpus:** ~290k licence-clean human passages (Common Pile: news, Gutenberg, CC-licensed web, food writing, Public Domain Review). Stored on Tenki `hl-data` (paused).
- **Training pairs (AI draft → human original):** 1,925+ and growing at about 550/hour (the Mac plus 2 cloud boxes). Fact filter is on: a pair is dropped if a number or name is lost or added. About 75–80% of pairs pass.
- **Model v0:** LoRA on Qwen3-0.6B, CPU only, 600 pairs, 64 min. Held-out loss 1.34. Adapter is at `hl-train:/data/train/lora_v0`.
- **Eval:** 130 prompts (100 dev + 30 trick) scored on 13 tell metrics against the human range from our pairs. Files are in `evals/runs/`.

## Results (130 eval prompts, lower is better for the tells)
| System | Words | Stock phrases | Em-dashes | Emoji | One-line paras | In human range | Fact fails |
|---|---|---|---|---|---|---|---|
| AI draft (input) | 89 | 1.31 | 1.61 | 3.86 | 59% | 54% | — |
| Qwen3-0.6B, untrained | 88 | 1.22 | 1.51 | 4.04 | 59% | 56% | 12 |
| **HumanLM v0** | 79 | **0.94** | **1.20** | **1.22** | **7%** | **68%** | **9** |
| Frontier model + strong prompt | 53 | 0.02 | 0.00 | 0.00 | 57% | 70% | **42** |

## What this means
1. **The training signal works.** v0 cut emoji by 70%, stock phrases by 28%, em-dashes by 25%, and got close to the frontier on "in human range". It got there from 600 pairs on a 0.6B model.
2. **The frontier baseline is clean but unfaithful and thin.** It drops or changes facts in 42 of 130 rewrites and cuts length by 40%. That's the opening: "removes the tells **and** keeps every fact".
3. **v0's main flaw is data mix, not method.** News makes up most of the pairs, so v0 writes like a reporter. Six outputs invent quotes like "says the CEO", which the fact gate doesn't catch yet. Fixes:
   - Cap news at 25% of the mix.
   - Add an invented-quote/attribution check to `keep()` and to `metrics.py`.
   - Add the modern founder-copy pairs from your rewrites.
4. **Not proven yet:** that people prefer v0's output. Metrics are a screen only. The blind writer A/B is still the test.

## What broke overnight and what I fixed
- **Two cloud generator boxes died of memory pressure, losing about 230 pairs.** Fixed with 6 GB swap, a single model slot and a smaller context, plus a safe sync that never shrinks a file.
- **The new cloud generators sat idle for an hour.** The watchdog's "already running?" check matched its own command line. Fixed with a start script on each box.
- **Training was slow and ran out of memory.** Qwen3.5 is very slow on CPU in transformers, so v0 trains Qwen3-0.6B in fp32 instead.
- **First inference loaded the adapter onto the wrong base model.** The env var was missing. Rerun and fixed.

## Running now
- The Mac and 2 cloud boxes (`hl-gen4`, `hl-gen5`) keep generating pairs. The watchdog is `~/models/hl/overnight.sh`.
- `hl-data` and `hl-train` are paused.

## Next steps (your call)
1. **First GPU run, about $2–6:** LoRA on Qwen3.5-9B-Base or Gemma-4-12B with ~3k filtered pairs (news ≤25%) plus the attribution filter. Needs your OK to rent a GPU (RunPod or Tinker).
2. **Write 20 founder-copy rewrites yourself:** landing page, launch email, LinkedIn. These become split C and the first modern pairs.
3. **Book the copywriter trial** for blind ratings (PLAN_30D week 1).

## Update: data fix → v1 (same model, same 600 steps, only the data changed)
**What changed:** new fact rule (an added quote or "says/said/according to" = hard fail), applied to both the scorer and the pair filter. That removed 1,834 of 5,326 pairs (34%, mostly news). v1 mix: 2,814 pairs, news capped at 25%. Generators now run on CC-licensed modern web text.

| System | Words | Stock phrases | Em-dashes | Emoji | Fact fails (strict) | Invented quotes | In human range |
|---|---|---|---|---|---|---|---|
| Untrained 0.6B | 88 | 1.22 | 1.51 | 4.04 | 15 | 3 | 56% |
| v0 | 79 | 0.94 | 1.20 | 1.22 | 13 | 7 | 68% |
| **v1** | 75 | **0.92** | **0.89** | **0.34** | **6** | **3** | **71%** |
| Frontier + strong prompt | 53 | 0.02 | 0.00 | 0.00 | 53 | 13 | 70% |

- **The data fix worked.** Fact fails dropped from 13 to 6, invented quotes from 7 to 3 (the untrained model's level), and v1 now edges past the frontier on "in human range". Under the strict rule the frontier fails 53 of 130.
- **v1 is still too timid.** It keeps lines like "seamlessly integrates" and "not just automation". A 0.6B model trained on 600 steps mostly edits lightly. Removing all the slop needs the bigger base model (GPU) and modern copy data.
- **Fixed in the trainer:** a pair whose prompt fills the 512-token window now gets skipped instead of producing a NaN loss.
