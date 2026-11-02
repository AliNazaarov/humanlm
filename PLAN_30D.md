# HumanLM — product definition + 30-day plan (2026-11-01, revised same day after 5 research reports)

Revision note: §3–§6 rewritten to match [WHAT_ELSE.md](WHAT_ELSE.md) (synthesis of research/BENCHMARKS, SIMILAR_PROJECTS, COPY_EVAL, SOLO_PLAYBOOK, USER_VOICE). §7 founder decisions kept as written; §8 lists what the research corrected. [E] = estimate.

## 1. The product (answer to "one tool for everyone, or personal?")
**One simple tool for everyone first. Personal voice second. Model + API underneath from day one.**

- **v1 (everyone):** paste AI-written copy (or your raw notes) → get it back sounding like a skilled human copywriter wrote it. Two versions side by side; you pick one. That pick is your training data.
- **v2 (personal):** "Make it sound like me": upload 10–20 things you wrote → per-user style profile (later a per-user LoRA adapter, once a user has ~50+ pieces [E]).
- **API (same model):** for agents and tools that write copy (cold-email tools, ad tools, agents posting for companies). Priced per rewrite in cents.

Never call it a "humanizer" (that word only shows up as detector-bypass pitches, research/USER_VOICE.md). Say "copy people keep reading".

## 2. What "human" means (our definition, measurable)
Text is "human" when all five hold:
1. **Passes the blind test:** skilled readers (paid copywriters, not crowd, not only Ali) prefer it to the best baseline when asked "which would you send for a client?" Never ask "does this sound human?" (gameable; COPY_EVAL §0.4).
2. **No AI tells:** slop metrics sit inside the human reference band (stock phrases, em-dash and tricolon rate, "not X but Y", hedging, sentence-length sameness). Target the band, not zero.
3. **Specific:** concrete nouns, numbers and examples; nothing generic.
4. **Correct:** zero grammar and spelling errors (hard gate, LanguageTool calibrated on human copy).
5. **Faithful:** keeps every fact and claim and invents nothing (hard gate; also a legal feature under the FTC fake-review rule).
6. **Not thinner:** output length 0.85–1.15× the draft ("paste your draft" mode), or the copy type's cap ("paste your notes" mode). The R2 Specific and R4 Proof pass rates are at least the baseline's. The "both unusable" rate is no higher than the baseline's. The win rate is refit with length and format as covariates (LMArena-style style control); raw and adjusted numbers are both reported. A model that wins raw but not adjusted has not won.

Also tracked: diversity (10 samples per prompt) and copy rate (output ≈ input). AI detector scores are watched only. Never the reward, never the pitch.

## 3. Not a GPT wrapper: the path (revised)
Free Apache-2.0 12B rewriters already exist (jialinyyzz/humanizer, Smaug-Humanizer). Owning *a* model is the starting line; the edge is **founder-copy data + skilled-human judging + the pick loop**.

| Step | What | Cost [E] | When |
|---|---|---|---|
| 0 | Eval v1 (100 → 200 prompts + 30 canaries, frozen holdout). Pair AI sides: half forward (brief pulled from the human original → open model writes from the brief alone), half backward ("rewrite as a typical chatbot"). Day-30 bar scored only on split B (commissioned) and split C (real founder drafts); split A is dev only; split C grows 40 → 80 via concierge work. **Strongest baseline:** best frontier model + senior-copywriter prompt + 5 gold examples of the same copy type + anti-slop filter + best-of-3 picked by the same gates (our model gets the same best-of-3). Also: blader, jialinyyzz, Smaug | ~$20–40 | Week 1 |
| 1 | **Your model v0.1:** LoRA SFT. Default base: Gemma-4-12B base or Qwen3.5-9B-Base (see model/BASE_MODELS.md), chosen by serving path (check the Gemma licence terms). jialinyyzz and Smaug are baselines only until a written lawyer opinion clears training on them. Data: ≥500 modern founder-copy pairs + public-domain/federal ≤60% of the mix | ~$5–20 a run | Week 2 |
| 2 | Anti-slop FTPO/DPO (word-level tells) + inference-time human-rate bans (structural tells) | ~$20–80 | Week 3 |
| 3 | DPO from real user picks (≥300), weekly | ~$10–30/run | Week 4 on |
| 4 | Later: per-user adapters, continued pretraining only if blind tests demand it | $1–3k | Month 2–3 |

Serving, not training, is the recurring cost: Modal + vLLM scale-to-zero or W&B serverless LoRA, ~$50–150/mo at low traffic. Download every adapter.

## 4. The loop (month 1: light, no nightly training)
```
users paste copy → 2 versions → pick/edit (logged with consent) ──┐
                                                                   ▼
nightly: hl-data-curator adds clean pairs → hl-judge (only if something changed):
         gates (grammar, facts, length 0.85–1.15×, copy rate, not-thinner) → slop band → diversity
         → pairwise LLM judge, 2 labs, both orders → failure counts → new cases
         → tomorrow's 20 pairs for Ali → 06:00 SUMMARY (≤15 lines)
weekly:  hl-trainer run if triggered → hl-judge gate → 50-pair human panel
         → hl-critic kill/pivot check → DECISIONS entry
```
North-star metric: **% of outputs used without edits**, counted as "copied without editing in our box" or an explicit "I sent this" (not keystroke watching).

## 5. Solo-founder setup
- **You (never delegate):** taste picks + approving pairs, the pre-registered bar, customer calls and price asks, anything public or sent, money and contracts, shipping a checkpoint, legal calls.
- **Active agents (7):** hl-orchestrator, hl-data-curator, hl-judge (also tells, gate, cases), hl-trainer (weekly), hl-builder (also design for now), hl-gtm (call prep), hl-critic (weekly, legal). hl-researcher weekly scan only. **Paused:** hl-designer, hl-writer-panel as a labeller (LLM judges agree with experts only 43–73%).
- **Humans to hire:** 2–3 paid copywriters (gold rewrites + blind ratings).
- Stack: LanguageTool, MiniCheck, slop-score, open-model AI-ifying; Tinker or Unsloth on RunPod for training; Modal + vLLM or W&B for serving; private HF repo; simple web app + API; Stripe.
- Month-1 cash [E]: compute + API $150–600. **Human spend cap $1,800:** 20 commissioned (~$800) + copywriter trials + two gold panels (D14, D30) at $300–500 each; D5 and D21 panels are Ali-only screens. Tracked in `model/SPEND.md`.

## 6. 30 days (Day 1 = Mon 2026-11-02, Day 30 = Tue 2026-12-01; day-level week 1 in WHAT_ELSE.md §5)
**Pre-register on Day 1:** By Day 30, v-best beats the **strongest prompted baseline** with a **lower 95% Wilson bound above 50%**: ≥200 judgments by 3 paid copywriters only, on splits B (commissioned) and C (real founder drafts), clustered by prompt. Ties and "both unusable" are reported separately and count as non-wins. Ali's ratings are logged as a check, not counted (COPY_EVAL §8.6: "Ali is not a gold rater"). Must also pass the "not thinner" check (§2 point 6) on both raw and style-controlled win rates. Zero invented facts on canaries and split C. Live endpoint. ≥25 founders using it. ≥3 paid. (60/100 or ~114/200 wins just clears 50% before clustering.)

**Week 1: eval + baselines + first humans**
- D1 success bar, eval skeleton, landing page, 15 call requests · D2 gates + baselines run, job post · D3 error analysis on 100 outputs · D4 hire copywriters, filters, 500 pairs · D5 Ali-only 50-pair screen (kappa from copywriter trial ratings) · D6 concierge rewrites, call synthesis · D7 pick the base (Gemma-4-12B / Qwen3.5-9B-Base (see model/BASE_MODELS.md); jialinyyzz + Smaug baselines only), data card by source + licence, kill/pivot check.
- **Targets:** eval v1 (100 + 30) frozen, split A dev-only · strongest baseline + 3 others scored · 7 calls · 2 copywriters · ≥150 modern founder-copy pairs + filtered public-domain/federal pairs (≤60% of mix), reverse-distillation filter on · 20 split-C drafts · 30 waitlist · Ali-vs-pros kappa measured.

**Week 2: your model v0.1 + live tool**
- Week 2 target: ≥500 modern founder-copy pairs, licence-logged, + ≤1,500 public-domain/federal pairs kept ≤60% of the mix (so ≤1.5× the modern count). If modern pairs <300 on D10, train on the general mix and treat founder copy as eval only. Split C to 80. Eval to 200. SFT on the chosen base + one 8B. Endpoint + one-screen tool + pick logging + free tell-checker to the waitlist.
- **Targets:** D14 gold panel: upper Wilson bound ≥50% vs the strongest baseline (splits B + C) · not-thinner passes · fact-gate ≥97% · copy rate <10% · 15 calls · 10 founders using it.

**Week 3: anti-slop pass + first money**
- FTPO/DPO small beta + inference bans; diversity check. Money test: done-for-you rewrite at $99–299 per landing page or launch email (model + Ali's pass, signed data licence), target 3 paid by Day 21; $19/mo self-serve stays a waitlist test only. Test "paste notes" vs "paste draft".
- **Targets:** D21 Ali-only screen above the strongest baseline · diversity not down >10% · 25 active founders · 3 paid done-for-you jobs · ≥300 picks.

**Week 4: loop runs + go public**
- First DPO on real picks. D30 gold panel (3 copywriters only, ≥200 judgments, splits B + C, clustered by prompt). Publish HL-Copy-Bench v0 (Ali publishes). Pick the next copy type from usage.
- **Targets:** pre-registered bar met (raw and style-controlled) · 25+ weekly users · 3 paid (stretch 10) · 30 calls · compute <$600 · human spend ≤$1,800.

**Kill / pivot rules:** (1) Day 14: if the upper Wilson bound is below 50%, stop training → ship on the best baseline, work data + users. (2) Day 21: <5 of 15 founders paste real copy twice a week → change front door (tell-checker / notes) or segment (agencies, cold-email API). (3) Day 30: 0 payments and <3 commitments after 30 calls → stop GPU spend, month 2 = discovery. (4) Compute >$300 before Day 21 → pause. (5) Users mainly beating detectors/stripping watermarks → change intake.

## 7. Decisions from founder answers (2026-11-01)
- **First buyer: founders.** Copy they write themselves: landing pages, launch and cold emails, LinkedIn/X posts. Businesses only, no students.
- **You write the rewrites.** To scale past what you can write: *reverse distillation*. Collect good human copy, have a model write the bland AI version of it, train AI-version → human-original. You only collect and approve; you write or edit ~10 a day.
- **GPUs:** Tenki is CPU-only, so it can host the app and evals, not training. Rent a GPU per training run (one LoRA run ≈ 2–6 hours ≈ $10–50), keep Tenki paused otherwise.

## 8. What the research corrected in §7 (2026-11-01)
- **GPU cost per run is lower than §7 says:** one SFT run ≈ $1–6 (Tinker/Together/RunPod, Oct 2026), not $10–50 (research/SOLO_PLAYBOOK.md). Tenki stays CPU-only for app + evals.
- **Reverse distillation stays, with two changes:** make the AI side with open-weight models (frontier API terms may forbid using outputs to build competing models [K, verify]), and filter pairs hard (Smaug: 3,676 clean pairs beat volume).
- **Reverse-distillation filter (required, 2026-11-01 critic review):** drop any pair where the human original has a number, name, date, claim or proof point that is missing from the AI side. The model must only learn to restyle, never to add. Specifics come from a brief the user fills in (product, audience, facts, numbers, ask), never from the model. (Rivals show the failure: deslop-v4 "made up studies", novel-humanize "invents plot", GoHumanize loses numbers 22% of the time.)
- **"You write the rewrites" stays, plus 2–3 paid copywriters** as the gold raters; Ali alone is one biased rater (market/RISKS.md R4).
- **Lead copy types:** landing pages + launch emails first, cold email second, LinkedIn/X third (research/COPY_EVAL.md, USER_VOICE.md).
