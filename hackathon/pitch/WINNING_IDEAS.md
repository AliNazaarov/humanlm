# FeatherLM: winning ideas (research, 2026-11-02)

The problem we're solving: FeatherLM wins on fact safety (94% fact-safe vs 72% for Opus 5.5, at 1/16 the cost). Both the human panel (6 people) and Kimi K3 still prefer Claude's style. Our rewrites use too many dramatic fragments and repeated words, and they end on punchy one-line closers. Claude writes calm, complete sentences.

What the harness already has (checked in `harness/harness.py`, `harness/gates.py`):
- kNN few-shot (`--retrieve`, TF-IDF over the AI draft)
- an LLM claim check (`--claim-check`)
- best-of-N with an absolute 1-10 GLM score (`--best-of`)
- a `calm` style round
- G3 tells: stock phrases, em dash, not-X-but-Y, emoji, exclamation marks

`band_v0.json` also measures `sent_len_mean`, `sent_len_std`, `one_line_para_share`, `para_opener_repeat`, `tricolon_rate` and `question_share`, but **no gate uses them yet**. The ideas below build on what exists rather than repeating it.

Fireworks API facts checked in the docs ([chat completions reference](https://docs.fireworks.ai/api-reference/post-chatcompletions)):
- `logit_bias` is supported (token ID mapped to a value from -100 to 100, added to the logits).
- `n` goes up to 128.
- Also available: `min_p`, `top_k`, `typical_p`, `frequency_penalty`/`presence_penalty`, `repetition_penalty`, `logprobs`/`top_logprobs`, `response_format` (`json_object`/`json_schema`), `return_token_ids`, `prompt_cache_key`, `echo`.
- Warning: `repetition_penalty` "applies to both prompt and output". It would push the model away from copying numbers and names exactly, so **do not use it**. G2 (nothing lost) would suffer.

---

## Ranked: 6 best ideas for us (about 4 hours left)

### 1. A rhythm gate (G5) built on metrics we already compute, plus fragment and closer detectors
- **What it is:** A deterministic style gate aimed at the exact gap the humans and Kimi named. It fails the output when any of these is outside the human band:
  - fragment rate (sentences under 4 words, or with no finite verb)
  - share of short sentences (6 words or fewer)
  - `one_line_para_share`
  - `para_opener_repeat` / anaphora (the same first 2 words in 2 or more sentences)
  - `sent_len_mean` below the human 10th percentile
  - `tricolon_rate`
  - a "punchy closer" (last paragraph is one sentence of 6 words or fewer)

  The gate's plain-English problems go straight into the existing revise loop. It follows the same "measure, then fix" approach as EQ-Bench's slop score (60% slop words, 25% not-X-but-Y, 15% slop trigrams) and the Wikipedia AI-writing checklist (rule of three, negative parallelisms, puffery).
- **Sources:**
  - [sam-paech/slop-score](https://github.com/sam-paech/slop-score) (MIT; its 10 surface regexes and 35 POS regexes for not-X-but-Y can be reused)
  - [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
  - [slop-forensics](https://github.com/sam-paech/slop-forensics)
- **Evidence from practitioners in 2026 (X, read only):** The anti-slop skills ranked highest on X are aimed at exactly our problem.
  - **stop-slop** (hardikpandya, ranked #1 by @juampitech) lists "dramatic fragmentation" and "staccato fragmentation" as clichés. It scores Directness, Rhythm ("varied or metronomic?"), Trust, Authenticity and Density from 1 to 10 each, and says to revise below 35/50.
  - **humanizer** (blader, built on the Wikipedia guide) has "one-line closers and dramatic fragments" as pattern #2 of its five strongest tells, plus repeated sentence openings (#7) and forced triads (#6). Its fix is to cut closers that repeat or explain, and to merge fragments into a specific claim.

  Both lists can be used as revise-prompt wording and as a pitch citation ("the community's top two anti-slop tools name our exact failure mode; we turned it into a measured gate").
  - [stop-slop](https://github.com/hardikpandya/stop-slop)
  - [humanizer](https://github.com/blader/humanizer)
  - [@juampitech ranking](https://x.com/juampitech/status/2090834948332655011)
  - [10 anti-slop skills list](https://x.com/Defi_Warhol/status/2115811776705241150)
- **Expected effect:** This is the most direct fix. The judges described the gap in rhythm terms, and this gate makes rhythm a hard constraint. It also gives the pitch a chart: fragment rate and mean sentence length for FeatherLM vs Opus vs real human copy, before and after. Expect most of the "dramatic fragments / one-line closer" complaints to go away. Pairwise preference should move toward parity, but not all the way.
- **Steps:**
  1. In `gates.py`, add a fragment counter: split on `m.sentences()`, then count sentences with fewer than 4 words, or with none of a small finite-verb list (is/are/was/has/have/will/can/-ed/-s). Also add `closer_punchy`.
  2. Set the bounds from `band_v0.json`: upper bound for fragment and one-line paragraph share, lower bound for `sent_len_mean`. Run the human corpus through it once and use its 90th percentile.
  3. Add G5 to `pass`, with problems such as "Join these fragments into full sentences: '...'" and "Your last line is a punchy one-liner. Fold it into the previous sentence."
  4. Re-run the eval. Report the fact-safe rate with and without G5 (it must stay 90% or higher).
- **Time:** 30-45 min. **Risk:** Low. It may cost a few points of pass rate (more loops). Keep `--loops 3`.

### 2. Pairwise, position-swapped selection in best-of-N (replace the absolute 1-10 score)
- **What it is:** For each item, generate N candidates that pass the gates (`n=4` in one request). Pick the winner in a pairwise knockout with both orders (A/B, then B/A). Inconsistent verdicts count as a tie, and ties are broken by the smallest distance to the human rhythm band from idea 1. Absolute 1-10 scores bunch up at 6-8 and barely separate candidates. Pairwise comparison is how the eval judge and the humans actually decide.

  Edit-based reward work found that selecting by a writing-quality reward produced text experts preferred 66% of the time, and 72.2% of the time when the reward gap was more than 1 point. Selection gains are real but need a discriminating selector.
- **Sources:**
  - [AI-Slop to AI-Polish? (Chakrabarty, Laban, Wu, COLM 2025)](https://arxiv.org/abs/2504.07532), with code in salesforce/creativity_eval
  - [Zheng et al. 2023, Judging LLM-as-a-judge](https://arxiv.org/abs/2306.05685) (swap positions; call it a tie if the verdict flips)
- **Expected effect:** Medium to large, and it stacks with idea 1. The selector must **not** be Kimi K3, because Kimi is the eval judge and using it would look like tuning to the test. Keep GLM-5.3 (already the default `--select-judge-model`) or another open model, and say so on the slide.
- **Steps:**
  1. In `rewrite()`, replace `judge_score` with `pair_pick(a_text, b_text)`. The prompt is "Which reads more like a calm, skilled human copywriter? Answer 1 or 2", with `temperature=0` and a 1-token answer.
  2. Run both orders.
  3. Run a knockout over the eligible candidates.
  4. Log the picks in `selection`.
- **Time:** 30-40 min. **Risk:** Low. Cost goes up about 2(N-1) small calls per item, so recompute the "1/16 cost" claim with the judge cost included (the harness already tracks `judge_cost_usd`).

### 3. A span-level "calm editor" pass (edit only the bad spans, not the whole text)
- **What it is:** After the gates pass, the model returns JSON `{"edits":[{"span": "...", "replacement": "..."}]}` covering only the spans flagged by G5/G3. Typical fixes: merge fragments, cut the punchy closer, vary repeated openers. Python applies the edits by exact string replacement. This is the LAMP/WQRM approach: a model trained on expert edit traces "identifies problematic spans, suggests edits, and combines them". Because untouched text stays byte-identical, numbers and names can't drift. That protects our fact-safe lead better than the current full-text `calm` style round.
- **Sources:**
  - [AI-Slop to AI-Polish? (LAMP corpus, 1,282 AI/expert-edit pairs)](https://arxiv.org/abs/2504.07532)
  - [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- **Expected effect:** Medium. It fixes the specific flagged sentences with almost no risk to G1/G2. Pitch line: "we edit like a human editor, with surgical changes and no rewrite drift."
- **Steps:**
  1. Add `--style-round span`.
  2. Build the prompt from the G5 problem list and require `response_format={"type":"json_object"}`.
  3. Apply edits whose `span` occurs exactly once, and skip the rest.
  4. Re-run `gates.check` and the claim check. Keep the result only if everything still passes, as the existing style round already does.
- **Time:** 45-60 min. **Risk:** Medium. Malformed JSON or spans that don't match exactly can occur; fall back to the unedited text.

### 4. Register-matched exemplars and a "style card" (change *which* human examples we retrieve)
- **What it is:** `retrieve()` currently picks training pairs by TF-IDF similarity on the AI draft, i.e. by content. A 2025 EMNLP study found that choosing few-shot examples by content similarity **reduced** style-imitation scores, and that gains flatten between 2 and 10 shots. Adding a human-written snippet still noticeably raised perceived human-likeness. The fix:
  1. Retrieve by *register*: same genre/length band, and human originals whose `sent_len_mean` and `one_line_para_share` match the calm target. Pick 2-3, no more.
  2. Prepend a measured style card, e.g. "Human copy in this genre averages about 17 words per sentence, has no fragments and no one-line closing paragraph", with the numbers taken from the band.
- **Sources:**
  - [Catch Me If You Can? Not Yet (arXiv 2509.14543, EMNLP Findings 2025)](https://arxiv.org/abs/2509.14543)
  - [How Well Do LLMs Imitate Human Writing Style? (arXiv 2509.24930)](https://arxiv.org/abs/2509.24930) (few-shot gives up to 23.5x higher style match than zero-shot)
- **Expected effect:** Small to medium on its own. It reduces how many loops idea 1 needs, which lowers cost and latency.
- **Steps:**
  1. Precompute the rhythm metrics for each training human original once.
  2. Pick k=3 by a weighted score: 0.5 × same genre + 0.5 × (1 − normalized rhythm distance to the band median).
  3. Add the style card to the system prompt.
- **Time:** 25-35 min. **Risk:** Low. Run an A/B test with `--limit 30` before switching.

### 5. `logit_bias` against tell tokens (em dash, exclamation mark, and a few slop words)
- **What it is:** Fireworks supports OpenAI-style `logit_bias`, so we can push banned single tokens to -100: the em dash variants (`—`, ` —`), `!`, and the most over-represented single-token slop words from slop-score's list that our outputs actually contain. The Antislop paper notes that plain token banning stops working at around 2,000 entries, which is why it uses backtracking. A list of 10 to 30 tokens is safe.
- **Sources:**
  - [Fireworks chat completions: logit_bias](https://docs.fireworks.ai/api-reference/post-chatcompletions)
  - [Antislop (Paech et al., arXiv 2510.15061)](https://arxiv.org/abs/2510.15061)
  - [auto-antislop (MIT)](https://github.com/sam-paech/auto-antislop)
- **Expected effect:** Small on the fragment problem, but it removes whole G3 failure classes before any revise loop runs. That saves loops and cost, so the claim becomes "0 em dashes by construction".
- **Steps:**
  1. Get the token IDs: send a probe prompt with `return_token_ids: true` (or load the GLM tokenizer from Hugging Face) and read the IDs for each banned string, including leading-space variants.
  2. Add `"logit_bias": {id: -100, ...}` in `decoding()` for the Fireworks provider only.
  3. Check outputs for broken punctuation (for example, sentences that spliced around the em dash).
- **Time:** 20-30 min. **Risk:** Low to medium. A token can be shared with legitimate text; never ban tokens that are part of numbers or names. **Repo rule:** CLAUDE.md says the shared decoding (temperature 0.7, top_p 0.9, max 400) must not change for one system. Treat `logit_bias` as part of FeatherLM's *harness*, add it as an explicit run flag, and list it under that system's settings in the report. Do not change it quietly.

### 6. Antislop-style backtracking on the API (stretch goal)
- **What it is:** An API version of the Antislop sampler. Stream the output and regex-match the banned pattern (a punchy closer, "Not X. Y.", or a fragment run). When it matches, cut the text at the start of the match. Then continue from that prefix (assistant prefill, or the completions endpoint with a raw prompt) with `logit_bias` set against the first token of the banned continuation. This is how the paper suppresses more than 8,000 patterns without hurting quality, and it supports regex bans for sentence-level structure.
- **Sources:**
  - [Antislop paper](https://arxiv.org/abs/2510.15061)
  - [auto-antislop](https://github.com/sam-paech/auto-antislop)
  - [KoboldCpp phrase-ban origin](https://github.com/LostRuins/koboldcpp)
- **Expected effect:** Potentially the largest, and a strong technical-depth story ("we brought backtracking decoding to a serverless API"). But ideas 1-3 get most of the gain with far less risk.
- **Steps:**
  1. Use `stream=True` and accumulate the text.
  2. Run the regexes from idea 1 on each sentence boundary.
  3. When one matches, abort the stream and resend the prefix as an assistant prefill with the ban bias.
  4. Cap at 3 backtracks.
- **Time:** 90+ min. **Risk:** High (prefill behaviour on GLM via chat, latency). Only do it if 1-4 are done.

**Recommended order today:** 1, then 2, then 4, then 5. Do 3 if time allows. Do 6 only if everything else is finished. Re-run the full eval once after 1+2+4+5 and once after 3.

---

## Extra topic: claim-level faithfulness checks under 2 s per item

What exists today: `claim_check` makes one GLM call that lists claims added versus the draft. It is one-directional, and errors return an empty list, which silently counts as "clean". That is a silent failure, and judges who read the code will spot it.

- **Two-way atomic check in one JSON call (recommended, about 30 min):**
  1. Cache the draft's atomic claims once per item, FActScore-style decomposition into short, independent facts.
  2. Make one call with `response_format: json_schema`, `temperature=0`, reasoning off/low, about 250 max tokens, and `prompt_cache_key=item_id`. It returns:
     - `draft_claims_missing` (nothing lost; this catches paraphrased losses that the number/name regex misses)
     - `rewrite_claims_unsupported` (nothing invented)

  On GLM-5.3 Flash serverless with a short marketing text, this should land around 1-2 s.
  - [FActScore (Min et al. 2023)](https://arxiv.org/abs/2305.14251)
  - Known weakness: decomposition choices change scores ([EmergentMind summary](https://www.emergentmind.com/topics/factscore))
- **MiniCheck-style sentence grounding:** MiniCheck checks each output sentence against the grounding document. It reached GPT-4-level accuracy on LLM-AggreFact at about 400x lower cost with a 770M Flan-T5. Bespoke-MiniCheck-7B is the current open SOTA, but it needs a commercial-use licence from Bespoke. For us, copy the *protocol* (one sentence vs the whole draft, supported/unsupported) in a single batched prompt.
  - [MiniCheck paper](https://arxiv.org/abs/2404.10774)
  - [Bespoke-MiniCheck-7B](https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B)
  - [LLM-AggreFact leaderboard](https://llm-aggrefact.github.io)
- **Non-LLM second opinion:** AlignScore-base (125M RoBERTa) runs on CPU in well under 1 s for 100-word texts. Run it in both directions: draft→rewrite catches distortion and loss, rewrite→draft catches additions. It is an independent check from a different model family, which strengthens the "fact-safe" claim. Its download is about 0.5 GB, so ask before installing.
  - [AlignScore (ACL 2023)](https://arxiv.org/abs/2305.16739)
- **Fix the silent failure:** On an exception, return `None` ("unchecked") and count it as a **fail** in the fact-safe rate, or retry once. Report the number of items left unchecked.

---

## How to make "human-likeness" credible quickly (eval design)

1. **Pairwise judging with position swap.** Run every pair in A/B and B/A order. If the verdict flips, count it as a tie, and report the flip rate as judge noise ([Zheng et al. 2023](https://arxiv.org/abs/2306.05685); [Judging the Judges, position bias](https://arxiv.org/abs/2406.07791)).
2. **Two judges from different families, neither one the selector.** Kimi K3, plus one more (e.g. DeepSeek V4.x on Fireworks). Report the agreement between them. Do not use GLM as an eval judge, because it is our generator and selector (self-enhancement bias).
3. **Raw and style-/length-controlled win rates.** Fit a logistic regression of win on (system + length difference + fragment-rate difference), the same way LMSYS adds style covariates to a Bradley-Terry model. Show both numbers. Present it honestly: "after controlling for length, the remaining gap is X; G5 targets exactly the covariate that explains it."
   - [LMSYS style control](https://lmsys.org/blog/2024-08-28-style-control)
   - [Length-controlled AlpacaEval](https://arxiv.org/abs/2404.04475) (Spearman correlation with Arena went from 0.94 to 0.98)
4. **Small human study done properly:**
   - blind, randomized order
   - include a third arm, **the real human original**, as an anchor
   - report the exact binomial/sign test p-value and Wilson 95% CIs (e.g. n=6 raters × 20 pairs)
   - report per-rater results
   - with 6 people, call it "directional"
5. **Bootstrap CIs over items** for the fact-safe rate (94% vs 72%), with 1,000 resamples. Show error bars on the hero chart.
6. **Blend the checklist with human preference.** This is Fireworks' own lesson: a correct checklist can still be "misaligned with human expectations", so show both the gates and the preference results ([Fireworks: "Your AI benchmark is lying to you"](https://www.plushcap.com/content/fireworks-ai/blog/fireworks-ai-your-ai-benchmark-is-lying-to-you-heres-how-we-caught-it)).
7. **Freeze and hash:** a held-out split, config hashes (`cfg_hash` already exists) and a public commit of the exact prompts.

---

## What 1st-place-style submissions did (presentation and eval design)

I could not find a verified public list of 1st-place winners from a Fireworks-run hackathon with their charts. On X, Fireworks posts about hosting hackathons (the RSI RL Environments hackathon with HUD and YC in June 2026, and MongoDB hackathons) but doesn't name winners. The patterns below come from what Fireworks publishes and promotes, from a 2026 index of AI-lab hackathon winners, and from documented winners of comparable events.

0. **Data from 585 winners (HacksRadar: 93 AI-lab hackathons, 31,980 projects since 2025, winners tagged by an LLM):**
   - The commonest "core trick" among winners is **generate, then run a deterministic checker that verifies and corrects**. Examples: "a deterministic beam tracer checks power, polarization and laser safety before export" (BEAMTEAM); "runs dimension and motion checks to verify and correct each result" (Morf); "stores every extracted fact with a verbatim quote" (NurseMate).
   - Our gates (G1-G5) plus the claim check are this pattern, so lead the technical slide with it.
   - Caution: "productivity" projects are *under*-represented among winners (23.6% of winners vs 29.1% of submissions). A copy-rewriter needs a visceral demo moment, not a feature tour.
   - Sources: [HacksRadar insights](https://hacksradar.thepushh.com/insights); [thread by @the_pushh](https://x.com/the_pushh/status/2117113776839475552)

1. **Lead with "open model within X points of first, at Y% cheaper", against a named frontier model.** This is Fireworks' own headline format. The Specialized Intelligence Index says "16 benchmarks with an open model within 5 percentage points of first" and labels each result with points behind and percent cheaper (e.g. "GLM 5.3 ... −3 Elo, 77% cheaper"). Make our hero chart the same shape: fact-safe rate vs $/1k rewrites, with Opus 5.5 labelled. ([Fireworks Specialized Intelligence Index](https://fireworks.ai/specialized-intelligence-index/))
2. **One-line claims of parity plus a cost multiple.** Recent Fireworks customer stories are headlined "frontier-level model ... at ~98% lower inference cost" (Paper Instruments) and "Opus 5-level decks at a fraction of the cost" (Gen-1 Slides). Our line: "Opus-level human copy, 94% vs 72% fact-safe, at 1/16 the cost". ([Fireworks blog index](https://fireworks.ai/blog))
3. **A live demo of the model doing the task, not slides.** The 1st place in the fine-tuning track at the Mistral hackathon (on Fireworks) showed a fine-tuned Mistral-7B actually playing Doom. Our version: paste a real AI-written landing page, watch the gates fire live (red G1 "invented number" turns green), and show a side-by-side with Opus where Opus invents a stat. ([Fireworks: LLM plays Doom](https://fireworks.ai/blog/llm-play-doom-fine-tune-mistral); [summary](https://www.plushcap.com/content/fireworks-ai/blog/fireworks-ai-doomed-to-code-how-we-teamed-up-with-fireworks-ai-at-mistralai-hackathon-to-conquer-the-shores-of-hell))
4. **A narrow domain, a named user, and honest limits.** OpenAI's Open Model Hackathon gave Most Useful Fine-Tune to a narrow domain tool (Dental Assessment GPT). Write-ups of those winners stress clear problem framing, visible behaviour, a named audience and stating what you don't do. For us, that means putting "Claude still writes prettier; we never lie" on a slide, which turns the weakness into a credibility point. ([What AI hackathon winners have in common](https://dev.to/jsb-securedme/what-ai-hackathon-winners-actually-have-in-common-1kla); [Devpost gallery](https://openai.devpost.com))
5. **A clear architecture diagram and a working end-to-end pipeline on cheap, fast models.** A team that placed in three hackathons (1st at the MongoDB GenAI Hackathon, 2nd at E2B x Fireworks with ProoferX) credits a clear data-flow diagram, fast and cheap models for iteration, and structured outputs for reliability. For us: one diagram of draft → generate → G1-G5 gates → claim check → pairwise select. ([Fireworks: triple hackathon winner](https://fireworks.ai/blog/triple-hackathon-winner-prooferx))

A related benchmark pattern judges will recognise: Together AI reported that open judges fine-tuned with DPO on 5,400 preference pairs beat GPT-5.2 by 10.3 points on math evaluation, at about 15x lower cost. Their framing is a specific delta, a specific cost multiple and a small, stated data budget. ([summary](https://www.plushcap.com/content/together-ai/blog/together-ai-fine-tuning-open-llm-judges-to-outperform-gpt-52))

---

## One-slide framing for the style gap

Plot a Pareto chart: x = fact-safe rate, y = human preference win rate (vs Opus). Show 3 points for FeatherLM (baseline, + G5 rhythm gate, + pairwise select) moving up toward Opus while staying far right of it on x. Caption, as a template (fill it only with numbers from `results.json`, per the CLAUDE.md rule): "Opus writes prettier, but only 72% of its rewrites pass all four fact and length gates, vs 94% for ours. We closed [X] of the style gap and kept fact safety at [Y]%." Note: 72% fact-safe is not the same as "invents facts in 28%", because some of those failures are dropped facts or length. Say what the gates actually measure.
