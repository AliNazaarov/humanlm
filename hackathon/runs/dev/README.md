# Dev checks for O3m, O3n, O3p, O3q (2026-11-02, about 13:25 to 13:35 PT)

These are the files behind the dev numbers in the O3m and O3n handoffs
(`hackathon/bus/msgs/20261102T213803Z-ali-to-friend.md`, `20261102T213847Z-ali-to-friend.md`).
They were written to `/private/tmp/` and `/private/tmp/o3n/` and were copied here unchanged on 2026-11-02 to fix
verify pass 1, row E8 (`hackathon/VERIFY/WORKFLOW_PASS1.md`). The `rows:`/`summary:` lines and the `a` field inside the
logs and summaries still show the old /tmp names. The sha256 values in the tables below are those of the files in this folder.

Not training data. These are model outputs on eval items (dev-031..070 of `evals/eval_all.jsonl`, plus three other
eval items in `qcheck/`).

## Setup

- Dev slice: dev-031..dev-070, 40 items. The source was `/private/tmp/featherlm_dev40.jsonl`, which holds exactly the
  `eval_all.jsonl` rows for those ids (checked row by row). It is not copied here because it is eval text.
- Generator: `hackathon/harness/harness.py`, `glm-5p3-flash` on Fireworks, `--loops 3`, T 0.7, top_p 0.9,
  max_tokens 1500, reasoning low. The style round is basic, or lint for O3q. Each variant changes only its prompt file
  `hackathon/train/prompt_<name>.txt`, except O3q, which also uses `--style-round lint`. Each prompt was added in
  commit `fe1f4ef` (13:32).
- Dev judge: `hackathon/eval/judge.py`, model `accounts/fireworks/models/glm-5p3`, reasoning low, both orders, against
  `evals/runs/hack_strong_claude-opus-5-5.jsonl`. It is the only judge used for these choices. No Kimi K3 or Qwen 3.8 Max
  score was used.
- The dev generations are separate samples from the full runs. 0 of the 40 O3m dev outputs and 1 of the 40 O3n dev
  outputs match their full-run rows word for word.
- `gen/O3c_dev40.jsonl` is not a new generation. It is the dev-031..070 rows of the committed
  `evals/runs/hack_O3c_glm_prompt_harness_style.jsonl`, and all 40 outputs are identical.

## Dev judge results (W/L/T vs Claude strong, n=40, from `judge/*.summary.json`)

| Summary file | A file (old /tmp name) | style | overall | facts | judge tokens in/out |
|---|---|---|---|---|---|
| `judge/devjudge_O3c.summary.json` | `featherlm_O3c_dev40.jsonl` | 16/18/6 | 12/18/10 | 0/3/37 | 72274/8269 |
| `judge/devjudge_O3c_low.summary.json` (rerun of the same O3c file) | `O3c_dev40.jsonl` | 16/18/6 | 13/19/8 | 1/2/37 | 72274/8691 |
| `judge/devjudge_O3m_glm_plainclaim.summary.json` | `dev_O3m_glm_plainclaim.jsonl` | 12/14/14 | 12/15/13 | 1/3/36 | 70704/8569 |
| `judge/devjudge_O3n_glm_frame.summary.json` | `dev_O3n_glm_frame.jsonl` | 7/25/8 | 9/24/7 | 2/2/36 | 72706/7761 |
| `judge/devjudge_O3p_glm_positive.summary.json` | `dev_O3p_glm_positive.jsonl` | 8/21/11 | 6/20/14 | 0/1/39 | 72248/8255 |
| `judge/devjudge_O3q_glm_lint.summary.json` | `dev_O3q_glm_lint.jsonl` | 10/18/12 | 9/17/14 | 0/0/40 | 72346/7748 |
| `judge/jtest.summary.json` (3-item smoke test) | `O3c_3.jsonl` | 1/1/1 | 1/2/0 | 0/1/2 | 5464/617 |

Every one of these is net negative on style against Claude strong. The two O3c runs differ by one item overall, so a
difference of 1 is noise at n=40.

Dev-slice gate pass (rows' `gates.pass` in `gen/`): O3c 38/40, O3m 38/40, O3n 39/40, O3p 39/40, O3q 38/40.

## Status of each variant

| Variant | What changed vs O3c | Dev result | Full run | Status |
|---|---|---|---|---|
| O3m_glm_plainclaim | prompt: wider contrast ban, plus slogan, filler and "say what happens" rules, keep contractions | style 12/14/14 | yes (130/120/80) | gates 96.2 / 98.3 / 98.75. **Not a style gain: loses style and facts to Claude strong on both eval judges, worse than O3c** (see "Pass 3" below). Keep the row, do not pitch it |
| O3n_glm_frame | prompt: frame rules (field labels, hashtags, certainty, quotes, one name) | style 7/25/8 | yes (130/120/80) | **FAILED.** eval_all gates 122/130 = 93.8%, below the 95% floor. Heldout 116/120 = 96.7%, real 78/80 = 97.5%. Keep the row, do not pitch it |
| O3p_glm_positive | prompt rewritten as positive rules. The banned-phrase list and the 3 examples are removed | style 8/21/11 | no | dropped at dev |
| O3q_glm_lint | prompt: wider contrast ban and keep contractions, plus `--style-round lint` (located lint feedback, harness.py:240-392) | style 10/18/12 | no | dropped at dev |

## Disclosures

1. **O3n's frame labels come from eval items outside the dev slice.** The O3n rule names `Headline:, Subhead:, Subject:,
   Primary text:, CTA:`. `Headline:` was already in `prompt_v2.txt` (in the "no markdown bold" line). Counts in
   `evals/eval_all.jsonl`:
   "Primary text:" appears in 8 items (dev-080, 082, 083, 084, 086, 087, 088, trick-08), "Subhead:" in 17
   (dev-001..014, trick-09, 12, 17), "CTA:" in 17 (the same 17) and "Headline:" in 25. None of them is in dev-031..070,
   and none appears in `evals/heldout_pairs.jsonl`, `hackathon/data/train.jsonl` or `valid.jsonl`. Only "Subject:"
   occurs in the dev slice (21) and in train (536). No file records where the list came from. The likely source is the
   eval items themselves: dev-080 is an O3c eval_all gate fail, and dev-001..030 were read for the O3l first-30 judging.
   The heldout and real splits contain none of these labels, so they are the only clean checks of O3n.
2. **O3n quick checks on three eval items outside the dev slice.** `qcheck/q3_out*.jsonl` hold outputs named
   `dev_O3n_glm_frame_qcheck`, `qcheckA` and `qcheckB` on dev-023, trick-06 and trick-07. dev-023 and trick-06 are O3c
   eval_all gate fails, and trick-07 holds the quoted testimonial that the O3n quote rule covers. So these items helped
   shape the prompt. All 9 outputs fail the gates. The input file `/private/tmp/o3n/q3.jsonl` (eval text) is not copied.
3. **O3q's lint patterns were found by reading eval-judge reasons.** The harness comment at `harness.py:241-242` says so,
   and it also says no judge score is used. Several patterns match eval items outside the dev slice. "you asked, we"
   matches dev-071 and dev-073, and "it's that simple" matches dev-073. That is 0 dev-slice items for either. Reading
   Kimi K3 or Qwen 3.8 Max reasons to write rules is close to tuning on the eval judges, even though no score was used. O3q
   was dropped and has no row, and `--style-round lint` is off by default. O3m's slogan and filler rules cover the
   same ground as the lint lists (`LINT_SLOGANS`, `LINT_VALUES`). No file says whether the O3m rules came from the same
   reading, so treat O3m's eval_all and eval-judge numbers as possibly optimistic too.
4. **Dev-check spend (estimate, not from a bill).** Generation rows in `gen/` (O3m, O3n, O3p, O3q) plus `qcheck/` used
   897,627 prompt and 78,202 completion tokens. At PRICES.md glm-5p3-flash $0.15/$0.50 per M, that is about $0.17. The
   7 judge summaries used 438,016 prompt and 49,910 completion tokens. At PRICES.md glm-5p3 $1.40/$4.40 per M, that is
   about $0.83, assuming `completion_tokens_total` includes reasoning tokens. The rows record `cost_usd` 0 because no
   prices were passed.
5. Not copied: `/private/tmp/hk/` (12:21 claim-check test on dev-003, made before this window) and the empty
   `s.jsonl`, `sft.jsonl` and `t.jsonl`.

## Pass 3: row status after the eval judges (verify pass 2 fails, 2026-11-02 ~14:05 PT)

Gate and frame-loss numbers below come from `row_checks.json`, written by `python3 hackathon/runs/dev/row_checks.py`
(reads only `evals/runs/hack_*.jsonl` and `evals/eval_all.jsonl`). Judge numbers come from the committed summaries named
in each line (Ruslan's commit `4084c63`, now on origin; this closes the pass 2 E8 fail).

**Gate floor (95% on every split, not pooled).** The README headline pools 247 items (eval 130 + held-out 117), which
can hide a miss on one split.

| Row | eval_all | heldout | real | Floor |
|---|---|---|---|---|
| O3c_glm_prompt_harness_style (entry) | 124/130 = 95.4% | 118/120 = 98.3% | 78/80 = 97.5% | met |
| O3m_glm_plainclaim | 125/130 = 96.2% | 118/120 = 98.3% | 79/80 = 98.75% | met |
| O3n_glm_frame | **122/130 = 93.8%** | 116/120 = 96.7% | 78/80 = 97.5% | **FAILED on eval_all** |

The pooled "95% [92, 97]" for O3n in the headline does not clear the floor. O3n is a failed variant: it keeps its row
(no cherry-picking) and is not judged or pitched.

**O3m vs Claude strong on the eval judges (both orders, eval_all), next to O3c:**

| Judge, file | O3m overall W/L/T | O3m style | O3m facts | O3c overall | O3c style | O3c facts |
|---|---|---|---|---|---|---|
| Kimi K3, `hackathon/report/judge_hack_O3m_glm_plainclaim_vs_hack_strong_claude-opus-5-5.summary.json` (sha256 `806ab0ac…`) | 18/64/48 | 15/54/61 | 5/23/102 | 35/52/43 | 33/46/51 | 9/15/106 |
| Qwen 3.8 Max, `hackathon/report/judge2qwen_hack_O3m_glm_plainclaim_vs_hack_strong_claude-opus-5-5.summary.json` (sha256 `ed246056…`; n=109, 21 incomplete) | 24/50/35 | 31/31/46 | 5/20/83 | 39/43/25 | 44/27/37 | 11/19/78 |

O3m is worse than O3c against Claude on every column of both judges. The Qwen judge, which leaned to O3c on style
(44/27), is even for O3m (31/31). So O3m's +1 gate item (eval_all and real) and its lower reader-tells share
(`hackathon/report/reader_tells.json`, a post-hoc diagnostic built from set-1 reader notes) are not a style result.
They are what the prompt was steered toward, and the judges do not see them. This is the pattern checklist row F10
exists to catch. **O3c stays the entry; the goal "raise style vs Claude strong" is not met by O3m, O3n, O3p or O3q.**

**What O3m drops (eval_all, from `row_checks.json` `frame_loss_eval_all`):**

| | O3m | O3c | O3n | Claude strong |
|---|---|---|---|---|
| drafts with a hashtag (`#\w+`) whose output drops every one | **20/34** | 5/34 | 0/34 | 0/34 |
| same, strict hashtags only (`#` + letter) | **23/32** | 6/32 | 0/32 | 0/32 |
| drafts with a `Subject:` line whose output drops it | 1/36 (dev-039) | 0/36 | 0/36 | 0/36 |
| median output/draft word ratio | 0.766 | 0.864 | 0.889 | 0.88 |

Examples: dev-059 loses its closing question and all five hashtags; dev-039 (an email) loses its subject line. Both
pass all four gates, because the gates check numbers, names, quotes and tells, not post furniture. The likely cause is
O3m's "rebuild each paragraph around its facts" and "delete feeling sentences" rules, which shorten the output.

**Correction (verify pass 3, ruling 2): hashtag loss does NOT explain O3m's facts losses.** An earlier version of this
section called it "a plausible reason". Checked item by item (`row_checks.json` → `facts_loss_vs_hashtag_drop`, which
reads only the FACTS verdicts of the committed judge files and recomputes them with `judge.aggregate`; all four match
their summaries): of O3m's 23 Kimi K3 facts losses, 4 are hashtag-drop items (dev-068, 070, 076, 085); of its 20 Qwen
3.8 Max facts losses, 3 are (dev-052, 058, 085). That is the base rate: 20 of 130 eval items are O3m hashtag drops
(15%). O3c's facts losses on hashtag-drop items: 0/15 Kimi, 0/19 Qwen. The verifier's reading of the judge reasons
(`hackathon/VERIFY/WORKFLOW_PASS3.md`, "Failure examples") found the cause instead: O3m invents qualitative mechanism
sentences that G1 cannot see, because G1 checks only numbers, names, quotes and attributions. Examples quoted there:
dev-005 ("merges without reruns") and dev-001 ("produces fewer errors"). The source is O3m's own rule,
`hackathon/train/prompt_O3m_glm_plainclaim.txt:7`: "Spend the freed words on how the product works, using only the
draft's facts." When the draft has no mechanism, the model writes one. Any later prompt that says "say what happens" or
"explain how it works" should be expected to fail the same way. O3c shows the same blind spot at a lower rate (Kimi
facts 9/15 vs O3m 5/23). This finding was used only to explain a dropped variant; no prompt was changed because of it.

**Variant count for the README limitations line.** Harness variants developed against eval items: O3, O3b, O3c, O3d,
O3e, O3f, O3g, O3h (stopped, no row), O3j, O3k, O3l, O3m, O3n with rows, plus O3p and O3q dropped at dev with no row
(this file). That is 15 variants, O3 to O3q (there is no O3i). Disclosures 1 to 3 above apply to O3m, O3n and O3q.

**Not changed in this pass:** no new run, no prompt or harness change, no eval or judge file touched. Ruslan owns
`README.md`, `hackathon/report/` and the generated headline, so the README text for these fixes went to him as a
`CONTRACT:` on the bus.

## Pass 4: verify pass 3 fails (2026-11-02 ~14:30 PT)

- **Ruling 2 (facts-loss cause):** corrected above. `row_checks.py` now also writes `facts_loss_vs_hashtag_drop`.
- **F11 disclosure and F6 human A/B:** both are `README.md` lines, which Ruslan owns. The exact replacement text went to
  him as a `CONTRACT:` on the bus (`hackathon/bus/msgs/*-ali-to-friend.md`, subject "CONTRACT: README pass-3 fails").
  The human numbers in it come from `hackathon/report/human_votes.json` (O3c vs Claude strong 53/80/31, 164 votes,
  sign test p=0.024) and `hackathon/report/human_ab.jsonl` (165 raw O3c-vs-Claude rows: 53/80/32).
- **O3n gate floor:** closed fail, already disclosed (README pass-2 note and the table above). Not pitched.
- **Goal (style up vs Claude strong, gates >= 95%):** still not met by any O3 variant here. O3c stays the entry. The
  separate R2 (E1 ensemble) and R3 (DeepSeek) runs are handled in their own handoff
  (`hackathon/bus/msgs/20261102T221622Z-ali-to-friend.md`), not in this pass.
- **Not changed:** no new run, no prompt or harness change, no eval, judge or report file touched.
