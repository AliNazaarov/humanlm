# FeatherLM founder-copy evals (DEV)

> **RULE: everything in this folder is eval data. It is never training data.**
> No row from `dev_set.jsonl`, `trick_set.jsonl` or `baseline_frontier.jsonl` may go into SFT, DPO, reward-model or RL data, as an input or as a target. The trainer's data loader must refuse any example with more than 8 words of n-gram overlap with these files (COPY_EVAL §8.2). `baseline_frontier.jsonl` is a comparison arm only. If you train on it, you have trained on a Claude-written target, and every win against it means nothing.

Written 2026-11-01. All items are **agent-written** (Claude Opus 5.5) about **invented startups**. So this is the **dev** split only: use it freely to iterate, debug the harness and do error analysis. It does **not** count toward the Day-30 bar. The frozen **gate** split still needs real founder drafts (split C) and commissioned references (split B), per PLAN_30D §3 and COPY_EVAL §8.

## Files

| File | Rows | What |
|---|---|---|
| `dev_set.jsonl` | 100 | Brief + a deliberately AI-sounding draft to rewrite |
| `trick_set.jsonl` | 30 | Edge cases (canary-style) that catch harmful rewrites |
| `baseline_frontier.jsonl` | 130 | One rewrite per item above, the strong prompted baseline |
| `_build/` | | Python source for all three files. Edit a `c*.py` / `t*.py` chunk, then run `python3 _build/build.py` (rebuilds all three files) and `python3 _build/validate.py` (checks) |

### `dev_set.jsonl` fields
- `id`: `dev-001` … `dev-100`
- `split`: `"dev"`; `origin`: `"agent-written"`; `draft_model`: who wrote the AI draft
- `type`: `landing_hero` 14, `landing_section` 9, `launch_email` 12, `cold_email` 16, `linkedin_post` 16, `x_post` 12, `short_ad` 9, `launch_blurb` 5, `product_description` 4, `about_page` 3. That is the COPY_EVAL §8.3 mix scaled to 100, plus product and about pages.
- `brief`: `{product, audience, facts[], numbers[], names[], ask}`. These are the only true facts. `numbers[]` is pulled from `facts[]` automatically.
- `ai_draft`: 45–250 words (median about 100), written to sound like default ChatGPT. It has em-dashes, "not just X, it's Y", tricolons, unlock/elevate/seamless, generic claims, emoji and hashtags in social posts, and some invented puffery.
- `must_keep[]`: facts that must survive. Paraphrase is fine.
- `forbidden[]`: claims the draft invented or inflated (for example "real-time", "#1", "no hidden fees"). The rewrite must not contain them.

### `trick_set.jsonl` fields
Same as above, plus:
- `trick_kind`: `dense_numbers` 4, `quote_verbatim` 3, `claim_not_strengthened` 4 (supplement, telehealth, investing, immigration disclaimers), `puffery_bait` 3, `already_good` 5, `very_short` 3, `list` 3, `non_native` 3, `typos` 2
- `expected_behavior`: what a passing rewrite does
- `draft_is_ai`: false for human drafts (already-good, non-native, typo cases)
- `verbatim[]`: strings that must appear **exactly** (quotes, disclaimers, odd numbers)

### `baseline_frontier.jsonl` fields
`{"id", "system": "claude-opus-persona", "output"}`. Persona: a senior direct-response copywriter. Rules: keep every `must_keep` fact, add nothing, plain and specific human voice, no AI tells, correct grammar, fit the type's length cap.

## Checks run on the baseline (`_build/validate.py`)
- No em or en dashes, no emoji, and no slop words from the list in the script.
- No number appears in the output that is not in the brief or the draft. This is a crude version of faithfulness layer 1 (§8.8).
- Every `verbatim` string is present.
- Length caps: cold email body ≤ 90 words, hero headline ≤ 12 and subhead ≤ 30, section ≤ 80, launch email ≤ 200.

Invented details were also removed by hand, in a second pass over every baseline.

## Caveats (read before using the numbers)
1. **The baseline is short on purpose.** It cuts fluff to the type caps, so its median length is about 0.54× the draft. PLAN_30D §2.6 "not thinner" (0.85–1.15×, paste-draft mode) would flag it. This file is a cut-to-cap arm, not the length-matched "strongest baseline" of PLAN_30D §3 (that one uses 5 gold examples, best-of-3 and an anti-slop filter). When you compare against this arm, report the length-controlled win rate.
2. **The same model wrote the drafts and the baseline.** Its drafts imitate one model family's tells. COPY_EVAL §8.2 wants AI drafts from 4 different models. Add GPT, Gemini and open-model drafts for the same briefs before trusting style metrics.
3. The briefs are invented, so they don't capture real founder messiness. Split C (real drafts) is still the most valuable set.
4. `already_good` items are near copies by design. Use edit distance there, not the A/B win rate.
