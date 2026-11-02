# What else do I need? (beyond evals + loops + agents)

Written 2026-11-01 by the HumanLM graph (synthesis of research/BENCHMARKS.md, SIMILAR_PROJECTS.md, COPY_EVAL.md, SOLO_PLAYBOOK.md, USER_VOICE.md, TECH.md, market/MARKET.md, data/DATA_SOURCES.md, evals/EVALS_AND_RL_PLAN.md, market/RISKS.md).
Labels: **[S]** sourced (link + date), **[E]** our estimate, **[K]** background knowledge, not re-checked today. Every [S] claim links to the research file that holds the full citation.

---

## 1. Straight answer

**No. Evals + loop engineering + an agent workflow are necessary, but they are about a third of the job.**

- **Evals measure progress. They do not create it.** They tell you whether version 2 beat version 1. They cannot make the training data, supply taste, find customers or serve the model ([Hamel Husain, hamel.dev, 2024-03-27](https://hamel.dev/blog/posts/fine_tuning_valuable.html): you can't fine-tune well without evals, and you should push prompting hard first) [S].
- **Agents are cheap labour, not judgment.** LLM judges agree with expert writers only 43% (Surge, Hemingway-bench) to 73% (best judge on LitBench) of the time. Standard reward models are at 52.7%, near chance, on length-matched writing pairs (WritingPreferenceBench, Oct 2025) [S, research/BENCHMARKS.md]. So agents cannot be the ones who decide "this reads like a skilled human".
- **The model recipe is already free.** `jialinyyzz/humanizer` (12B, Apache-2.0, 2026-09-11, 264,723 downloads/month) and `abacusai/Smaug-Humanizer` (12B, Apache-2.0, 2026-10-26) already do "AI draft → human text" with reverse distillation ([HF](https://huggingface.co/jialinyyzz/humanizer), [HF](https://huggingface.co/abacusai/Smaug-Humanizer)) [S, research/SIMILAR_PROJECTS.md]. "We trained our own model" is the starting line, not the edge.
- **Training is cheap; the scarce things are human.** One SFT run costs about $1–6 (Together/Tinker/RunPod prices, Oct 2026) [S, research/SOLO_PLAYBOOK.md]. What decides the month is: (1) ≥500 licence-clean *modern* founder-copy pairs (plus a capped public-domain/federal mix), (2) skilled human judges, (3) a baseline you can actually beat, (4) founders who use it, (5) a way to serve the model.
- **The opposite risk is real too:** building a 13-agent nightly graph while `app/` and `model/` are empty (market/RISKS.md R5). In month 1 the agent workflow should take ~20% of your time, not 80% [E].

**What "results in 1 month" can realistically mean (pre-register this, Day 1):**
By Day 30, v-best beats the **strongest prompted baseline** with a **lower 95% Wilson bound above 50%**: ≥200 judgments by 3 paid copywriters only, on splits B (commissioned) and C (real founder drafts), clustered by prompt. Ties and "both unusable" are reported separately and count as non-wins. Ali's ratings are logged as a check, not counted (COPY_EVAL §8.6: "Ali is not a gold rater"). Must also pass the "not thinner" check (§2 point 6 of PLAN_30D) on both raw and style-controlled win rates. Zero invented facts on canaries and split C. Live endpoint. ≥25 founders using it. ≥3 paid. Sample sizes: 60/100 or ~114/200 wins just clears 50% before clustering; clustering widens it, so plan for more [E]. Recipes exist, so the model part is likely [E]. Demand is the unproven part: nobody in 800 Reddit items named a price (research/USER_VOICE.md §5) [S].

---

## 2. The full list beyond evals + agents

Who: **You** = the founder. `hl-*` = the agent. Time = calendar time in month 1 [E].

### 2a. Skills to learn (you)
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| Error analysis: read 100 outputs, write notes, name 5–7 failure modes | It is the one eval skill that can't be delegated; it sets every rubric | Hamel's 50-min video (§3), then do it on Day 3 | You; hl-judge counts instances | 3 h once, then 20 min/day |
| Run one LoRA fine-tune yourself, end to end | So you can supervise hl-trainer and spot the two silent bugs (chat-template mismatch, training on prompt tokens) [K, SOLO_PLAYBOOK §5] | One Unsloth notebook on a rented $0.33–0.79/h GPU [S, SOLO_PLAYBOOK] | You, with hl-trainer pairing | 1 evening, ~$2 |
| Read a model card, data card and licence | Licence mistakes kill the moat (jialinyyzz has CC-BY-NC data inside) | Read the jialinyyzz and Smaug cards line by line | You; hl-critic rules | 1 h |
| Customer interviews that don't lie | Founders will be polite; you need past behaviour and money | *The Mom Test* (Rob Fitzpatrick) [K]; ask "last time you fixed copy, what did you pay?" | You only | 2 h reading + calls |
| Calibrate your own taste | You are one rater; you need to know when you disagree with pros (RISKS R4) | Rate the same 50 pairs as the copywriters; compute agreement (Cohen's kappa ≥0.6) | You; hl-judge computes | 1 h in week 1 |

### 2b. Data (the real bottleneck)
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| ≥500 modern founder-copy pairs + ≤60% public-domain/federal mix (AI version → human original) | Every winning recipe says clean pairs beat RL; Smaug used 3,676: "cleaner pairs helped more than anything we did later" [S, SIMILAR_PROJECTS] | Human side from: your writing, commissioned copy with rights assigned, permissioned founder copy (trade free rewrites for a signed licence), US ads ≤1930, US federal text [S, COPY_EVAL §6]. AI side, made with open models: **half forward** (pull a brief out of the human original, then write the copy from that brief alone, like a real founder's chatbot draft), **half backward** ("rewrite as a typical chatbot, keep every fact"). D7 data card counts pairs by source and licence | hl-data-curator builds + filters; you approve 20 random pairs/day | Weeks 1–2 |
| Hard filters on pairs | GoHumanize returned 29% of texts near-unchanged and lost a number in 22% [S, SIMILAR_PROJECTS] | Drop near-copies (5-gram overlap), require same layout, fact check, dedupe. **Reverse-distillation filter (required):** drop any pair where the human original has a number, name, date, claim or proof point missing from the AI side. The model learns to restyle, never to add. Specifics come from a brief the user fills in (product, audience, facts, numbers, ask), never from the model | hl-data-curator (scripts) | 1 day to build |
| 20 commissioned + 50 own gold rewrites | Gold references and the blind panel need real skilled-human copy | 20 × ~$40 ≈ $800 [E, COPY_EVAL §8.10] (inside the $1,800 human cap); you write 10/day | You + 2–3 copywriters | Weeks 1–2 |
| Frozen holdout: 50 cases + 30 canaries | Without a locked test set, every "win" is self-deception | 10 good-human (must barely change), 10 invented-claim drafts (must remove), 10 number-heavy (every number survives) [S, COPY_EVAL §8] | hl-judge owns; hl-trainer can't read it | Day 1–2 |
| LinkedIn/X post data, on purpose | Social posts are jialinyyzz's weakest genre (3/16 flagged) and your wedge [S, SIMILAR_PROJECTS] | Your own posts + permissioned founder posts; never scrape LinkedIn/X (login + ToS) | hl-data-curator; you ask founders | Weeks 2–3 |
| Data card + provenance log | Lets you prove licence-cleanliness to YC, buyers and a lawyer | Copy jialinyyzz's data-card format | hl-data-curator | 2 h |
| Pick + edit logging in the tool (with consent) | This is the long-term moat: preference data nobody else has | One table: input, 2 outputs, pick, edit diff, model version | hl-builder | Week 2 |

### 2c. Infra
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| Eval harness (gates + metrics) | The measuring stick | LanguageTool (self-host), MiniCheck fact check on CPU, slop-score re-baselined on human copy (MIT), copy-rate, NoveltyBench-style diversity [S, BENCHMARKS/COPY_EVAL] | hl-builder writes, hl-judge runs | Days 1–3 |
| Blind A/B rating page | Humans are the ground truth; make rating fast | One HTML page: 2 outputs, "which would you send for a client?", reason box [S, COPY_EVAL: never ask "sounds human?"] | hl-builder | 1 day |
| Training path | One run per week | Tinker (Qwen3-8B, ~$5/run) or Unsloth on RunPod (~$1–2/run) [S, SOLO_PLAYBOOK, prices 2026-10] | hl-trainer | Week 2 |
| Serving path | A model nobody can call isn't a product; serverless LoRA ended at Together and Fireworks [S, SOLO_PLAYBOOK] | Modal + vLLM scale-to-zero ($30/mo free credit; L40S $1.95/h) or W&B/CoreWeave serverless LoRA (Llama-3.1-8B, rank ≤16) [S] | hl-builder + hl-trainer | Week 2 |
| Weights you own | Hosts retire models (Tinker dates, OpenAI base shutdown 2027-01-14) [S] | Download every adapter; private HF repo; must run on plain vLLM | hl-trainer | ongoing |
| Spend log | Budget creep | `model/SPEND.md`; stop if compute >$300 before Day 21 | hl-orchestrator | 10 min |

### 2d. Distribution
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| Landing page + waitlist | Somewhere to send people from calls | One page, one promise: "copy people keep reading" — never the word "humanizer" [S, USER_VOICE §9] | hl-builder (+designer guidance); you approve words | Days 1–3 |
| Free "check my writing for tells" tool | Brings honest users (people falsely flagged too) + clean data [S, USER_VOICE §10] | Runs the slop/tell checks only, no model needed | hl-builder | Week 2 |
| Direct outreach to 30 founders | First users come from you, not ads | Your network, founder communities; agents draft lists, **you** send | You; hl-gtm preps lists + scripts | All month, 30 min/day |
| Public HL-Copy-Bench (100 prompts, human-judged leaderboard) | Nobody publishes a founder-copy benchmark judged by skilled readers; it is also the YC pitch [S, BENCHMARKS/SIMILAR_PROJECTS] | Publish prompts, judging method, win rates of frontier models + yours | hl-judge builds; you publish | Week 4 |
| Lead message | Pain is trust, not detectors: "I automatically disregard any business that has a website that is screaming AI generated" ([r/Entrepreneur, 2026-09-25](https://www.reddit.com/r/Entrepreneur/comments/1wq0lxd/how_does_a_serious_company_get_taken_seriously_in/pbzzmvb/), 77 upvotes) [S, USER_VOICE] | Lead with landing pages + launch emails; cold email second (prospect facts matter more than prose [S, COPY_EVAL §3]); LinkedIn third | hl-gtm drafts; you decide | Week 1 |

### 2e. Design
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| One screen: paste → 2 versions → pick | Picks are the training data; zero-edit rate is the north star | Copy the Wispr calm (design/WISPR_TEARDOWN.md); no settings in v1 | hl-builder using hl-designer's notes | Week 2 |
| Test "paste your notes" vs "paste your AI draft" | Every workflow that works starts from raw input [S, USER_VOICE §8] | Two tabs; count which gets used | hl-builder; you read results | Week 3 |
| An observable "used without edits" event | A hotkey can't see "sent" without watching keystrokes (RISKS R2) | Count "copied without editing in our box" + explicit "I sent this" button | hl-builder | Week 2 |

### 2f. Legal (cheap now, expensive later)
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| Ruling on continuing to train jialinyyzz weights | Weights Apache-2.0, but its training data includes CC-BY-NC text and GPT/Claude rewrites (board/OPEN.md). Until a written lawyer opinion clears it, jialinyyzz and Smaug are **baselines only** | hl-critic writes the question; 1 h with a lawyer before you sell | hl-critic → you decide | Week 1 |
| Provider terms for making the "AI side" of pairs | Frontier API terms restrict using outputs to build competing models [K, verify] | Generate the AI side with open-weight models (Qwen/Llama/Gemma) to sidestep it; check each licence | hl-critic checks; hl-data-curator switches | Week 1 |
| Watermark policy | Rewriting Claude output may look like watermark stripping; Reddit says rollout to older models Nov 3 (unconfirmed) [S, USER_VOICE §6] | Policy: accept the user's own drafts and notes; never market around detection or watermarks | hl-critic drafts; you sign | Week 1 |
| Copywriter contracts | Commissioned copy is only clean if rights are assigned | One-page work-for-hire + training-use clause [K] | You sign; hl-critic drafts | Day 4 |
| Privacy + training-consent line | You train on user picks | One checkbox + plain privacy page | hl-builder + hl-critic | Week 2 |
| "Never invents a claim" | FTC fake-review rule, fines up to $51,744 per violation (effective 2024-10-21) [S, COPY_EVAL] | Faithfulness hard gate; say it on the landing page | hl-judge gate; hl-gtm copy | Week 1 |

### 2g. Customer discovery
| What | Why | Cheapest way | Who | Time |
|---|---|---|---|---|
| 15 calls by Day 14, 30 by Day 30 | Demand for "our own writing model" is unproven; no solo writing-LoRA business found [S, SOLO_PLAYBOOK §13] | 20-min calls; ask for the last real draft and what they paid to fix copy | You only; hl-gtm preps and summarises | 30 min/day |
| Concierge rewrites | Proves value before the model is good, and every rewrite is gold data | Rewrite 10 founders' real copy (model + your pass), with a signed data licence | You | Week 1–2 |
| Money test | Free rivals exist (jialinyyzz local app, Hemingway) and nobody in the research named a price [S, USER_VOICE §5] | Done-for-you rewrite at $99–299 per landing page or launch email (model + your pass, signed data licence). Target 3 paid by Day 21. $19/mo self-serve is a waitlist test only | You; hl-gtm designs | Weeks 2–3 |
| Expert rater pool | Experts and lay readers judge copy differently [S, COPY_EVAL, arXiv 2510.13939] | Laid-off copywriters (r/copywriting is full of them) [S, USER_VOICE §14]; prefer heavy ChatGPT users [S, BENCHMARKS] | You hire; hl-gtm drafts the job post, **you** post it | Day 2–4 |

**Month-1 cash [E]:** compute + API $150–600 (of the $2k GPU budget) + **human spend cap $1,800**: 20 commissioned × $40 ($800) + copywriter paid trials + two gold panels (D14, D30) at $300–500 each. The D5 and D21 panels are Ali-only screens. Tracked in `model/SPEND.md`. (The old plan's 4 panels + 30 commissioned came to ~$2.4–3.6k, above its own estimate.) Humans cost more than GPUs. That is normal, and it is where the money should go.

---

## 3. Five things to learn about AI this month (one resource each)

| # | Learn | Single best resource | Why this one | When |
|---|---|---|---|---|
| 1 | How models are made: pretraining → SFT → preference training/RL, and why post-training flattens style | [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI), Andrej Karpathy (2025-02-05, 3h31) — in your Video Notes and AI learning path | Your whole thesis (post-training flattens voice) sits in its last hour. Watch the post-training + RL chapters first | Week 1 |
| 2 | Evals by error analysis: read outputs, name failures, binary judges, validate the judge against your labels | [AI Evaluations Clearly Explained in 50 Minutes](https://www.youtube.com/watch?v=uiza7wp1KrE), Hamel Husain with Peter Yang (2025-09-28, 52 min) — in Video Notes | A real worked example you can copy on Day 3. Optional follow-up: [Can Claude Build Your Evals?](https://www.youtube.com/watch?v=5ykulgyB8kk) (2026-10-13), which is exactly your agent setup | Week 1 |
| 3 | LoRA fine-tuning settings (rank, learning rate, epochs, train on answers only) | [Unsloth LoRA hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) (cited in SOLO_PLAYBOOK, 2026-10) — **not in your notes yet** | It is the tool hl-trainer will use; pair with TRL's "LoRA Without Regret" settings (LR ~10× full-FT, all layers, 1–3 epochs) [S, SOLO_PLAYBOOK] | Week 2 |
| 4 | Preference training (DPO) and over-optimisation (reward hacking, KL anchor, stop early) | [Post-Training and RLHF Overview, Lecture 1](https://www.youtube.com/watch?v=o6l6tJQgUg4), Nathan Lambert (2026-04-14, 46 min) — in Video Notes | Explains why a judge reward is a proxy and why pairwise beats scores. Smaug saw quality fall after training longer [S]; that is this lecture in practice. Lecture 9 (23 min) is the follow-up | Week 3 |
| 5 | Data curation: what a clean pair is and how to document it | The [jialinyyzz/humanizer model + data card](https://huggingface.co/jialinyyzz/humanizer) (2026-09-11) — not a video, read it like a textbook | It is the exact recipe for your product: sources, licence tiers, cutoff, drop counts, copy penalty. Then read the [Smaug card](https://huggingface.co/abacusai/Smaug-Humanizer) for the filtering lesson | Week 1 |

Skip for now: GRPO/policy-gradient maths (Lambert Lecture 3), agent-harness videos, continued pretraining. None changes a month-1 decision.

---

## 4. Making the agent workflow better

### 4a. Agents: keep, merge, pause, add (month 1)
| Agent | Month 1 | Change |
|---|---|---|
| hl-orchestrator | Keep | Runs the nightly loop; writes a ≤15-line morning SUMMARY; enforces caps |
| hl-data-curator | **Keep, top priority** | Also owns pair-building, filters (near-copy, layout, fact, dedupe) and the data card. Absorbs `hl-pair-builder` and `hl-corpus-scout` from EVALS_AND_RL_PLAN §4.1 |
| hl-judge | **Keep, top priority** | Also owns the code graders (tells, copy rate, diversity), error-analysis counts, case-writing and the promotion gate. Absorbs `hl-tells`, `hl-error-analyst`, `hl-case-writer`, `hl-gatekeeper` |
| hl-trainer | Keep | Weekly only, on a trigger. Hook blocks it from writing `evals/` |
| hl-builder | Keep | Also does month-1 design from hl-designer's notes |
| hl-gtm | Keep | Adds call prep + call-note synthesis + price-test design. Never sends anything |
| hl-critic | Keep, weekly | Owns legal questions (licence, provider terms, watermark, contracts) and the kill/pivot check |
| hl-researcher | **Cut to 1 run/week** | Research is done for now; 5 reports landed today. Weekly scan for new rival models only |
| hl-designer | **Pause** | Fold into hl-builder until there are users to design for |
| hl-writer-panel | **Pause as a labeller** | LLM "writers" agree with experts 43–73% [S]; their labels would poison preference data. Reuse only as a pre-screen that removes obviously bad outputs before humans rate |
| Do not add | `hl-generator`, `hl-reward-modeler`, `hl-skeptic`, `hl-grader-audit` | Not until there's a checkpoint and ≥500 human-rated pairs (EVALS_AND_RL_PLAN §4.5 step 5) |

Net: 10 agents → 7 active (orchestrator, data-curator, judge, trainer, builder, gtm, critic) + researcher weekly. Deterministic checks are **scripts**, not agents; they're cheaper and can't drift.

### 4b. The month-1 nightly loop (light; no nightly training)
```
23:00 hl-orchestrator   reads queue.md, last SUMMARY, caps (tokens, $)
  ├─ hl-data-curator    next 200 human pieces → AI-ify (open models) → filter → +N clean pairs
  ├─ hl-judge           ONLY if a checkpoint/prompt changed: gates (grammar, facts, length,
  │                     copy rate) → slop band → diversity → pairwise LLM judge (2 labs, both orders)
  │                     → counts per failure mode → new cases from confirmed failures
  └─ hl-judge           builds tomorrow's 20-pair human queue (hard pairs + 2 repeats + 2 controls)
06:00 hl-orchestrator   SUMMARY.md (≤15 lines) + push: pairs added, gate status, what moved, your 20 pairs
WEEKLY (Sun)            hl-trainer run if trigger met → hl-judge gate → human panel (50 pairs)
                        → hl-critic kill/pivot check → hl-researcher scan → DECISIONS entry
```
Rules: fresh context per agent, state in files, max-iteration + $ caps in config the agents can't edit, the maker never judges, a hook blocks hl-trainer from `evals/` and the holdout (EVALS_AND_RL_PLAN §4.4).

### 4c. What you must never delegate
1. **Taste picks and approving gold pairs.** Your 20 pairs a day and the 20-pair data sample are the ground truth.
2. **The pre-registered success bar and rubric changes.** Written before training, never changed after seeing results.
3. **Customer conversations and price asks.** Agents prep and summarise; you talk.
4. **Anything public or sent:** posts, emails, job posts, the leaderboard release (also a standing rule: agents never log in, post, like or follow).
5. **Money and contracts:** paying copywriters, GPU spend above the cap, signing licences.
6. **Ship/promote a checkpoint** to users — the one human gate at the least reversible step.
7. **Legal calls** (licence, watermark policy, provider terms) — hl-critic frames them, you decide, a lawyer checks before revenue.

---

## 5. Revised 30-day plan

Day 1 = Mon 2026-11-02. Day 30 = Tue 2026-12-01. Daily founder routine all month: 20 pairs labelled (15 min), 10 rewrites written (45 min, weeks 1–2), 1–2 founder calls or outreach (30–60 min), read SUMMARY (5 min).

### Week 1 — eval, baselines, first humans (day by day)
| Day | You | Agents |
|---|---|---|
| **D1 Mon 11-02** | Write the pre-registered success bar (§1). Watch Hamel 50-min. Message 15 founders for calls. | hl-judge: eval v1 skeleton (100 prompts: 30 landing, 25 launch email, 25 cold email, 20 LinkedIn/X) + 30 canaries, frozen. hl-builder: landing page + waitlist draft. hl-critic: licence, provider-terms, watermark questions. |
| **D2 Tue 11-03** | Approve landing copy; it goes live. Post copywriter job ad (you post). 1 call. | hl-builder: gates (LanguageTool, MiniCheck, length, copy rate) + slop-score re-baselined on human copy. hl-trainer: rent GPU ~2 h, run jialinyyzz + Smaug on the 100 prompts. Strongest baseline on API: best frontier model + senior-copywriter prompt + 5 gold examples of the same copy type + anti-slop filter + best-of-3 picked by the same gates (our model gets the same best-of-3). Plus blader. |
| **D3 Wed 11-04** | **Error analysis:** read 100 baseline outputs, write notes, name 5–7 failure modes. 1 call. | hl-judge: counts per failure mode, first binary judges, A/B rating page. hl-data-curator: first 300 human pieces (your writing first; ≤1930 ads and federal text capped) + AI side from open models, half forward (brief → copy), half backward. Split A = dev only. |
| **D4 Thu 11-05** | Hire 2–3 copywriters (paid trial: 10 rewrites + 30 ratings each). Sign contracts. Write 10 rewrites. 2 calls. | hl-critic: rulings posted. hl-data-curator: filters built; 500 clean pairs. hl-gtm: call script + notes template. |
| **D5 Fri 11-06** | Ali-only screen: rate 50 blind pairs (best open model vs strongest baseline). 2 calls. | hl-judge: screen results; kappa you-vs-pros from the copywriters' paid-trial ratings; judge-vs-human agreement. |
| **D6 Sat 11-07** | Concierge: rewrite 3 founders' real copy (signed data licence). Write 10 rewrites. Watch Karpathy post-training chapters. | hl-gtm: synthesise calls so far (pain, words, last price paid). hl-data-curator: pairs with the reverse-distillation filter on; count modern vs public-domain. |
| **D7 Sun 11-08** | Weekly review. Pick the base: Gemma-4-12B base or Qwen3-8B / Llama-3.1-8B, by serving path (check the Gemma licence terms). jialinyyzz and Smaug stay baselines only until a written lawyer opinion clears training on them. Write DECISIONS. | hl-critic: kill/pivot check #1. hl-data-curator: data card counts pairs by source + licence. hl-orchestrator: week summary. |

**Week 1 targets:** eval v1 (100 + 30 canaries) frozen, split A dev-only · strongest baseline + 3 others scored · 7 founder calls · 2 copywriters hired · ≥150 modern founder-copy pairs + filtered public-domain/federal pairs (≤60% of mix), data card by source + licence · 20 split-C founder drafts collected · 30 waitlist sign-ups · kappa you-vs-pros measured.

### Week 2 — your model v0.1 + the live tool
- Pairs: ≥500 modern founder-copy pairs, licence-logged, + ≤1,500 public-domain/federal pairs, kept ≤60% of the mix. **If modern pairs <300 on D10, train on the general mix and use founder copy as eval only.** Split C grows from 40 to 80 drafts via concierge work. hl-trainer: SFT on the chosen base (LoRA, 1–2 epochs, answers only) + one serving-friendly 8B for ~$10 total.
- Structural tells (em dashes, bullets, headers, emoji) handled at inference with human-rate bans, not in training [S, SIMILAR_PROJECTS §6.8].
- hl-builder: endpoint (Modal+vLLM or W&B serverless) + one-screen tool (paste → 2 versions → pick) + pick/edit logging + free tell-checker. Ship to the waitlist.
- **Targets:** D14 gold panel: upper Wilson bound ≥50% vs the strongest baseline on splits B + C · passes "not thinner" · fact-gate pass ≥97% · copy rate <10% · 15 calls total · 10 founders using the tool.

### Week 3 — anti-slop pass + first money
- FTPO/DPO, small beta, on v0.1 outputs (word-level tells only) + your picks. Diversity check (10 samples/prompt).
- Money test: done-for-you rewrite $99–299 per landing page or launch email (model + your pass, signed data licence); 3 paid by Day 21. $19/mo self-serve = waitlist test only.
- Test "paste your notes" vs "paste your draft".
- **Targets:** D21 Ali-only screen trending above the strongest baseline · diversity not down >10% vs v0.1 · 25 active founders · 3 paid done-for-you jobs · ≥300 real picks logged.

### Week 4 — the loop runs + go public
- First DPO on real user picks (if ≥300). Month-end gold panel (D30): 3 copywriters only, ≥200 judgments on splits B + C, clustered by prompt; your ratings logged as a check (Prolific study moves to month 2 to save $400–800 [E]).
- Publish HL-Copy-Bench v0 (100 public prompts, method, frontier models + yours). You publish it.
- Decide next copy type from what users paste most.
- **Targets:** pre-registered bar met (lower Wilson bound >50%, raw and style-controlled, zero invented facts) · 25+ weekly users · 3 paid (stretch 10) · human spend ≤$1,800 · 30 calls total · compute spend <$600.

### Kill / pivot rules (checked every Sunday by hl-critic, decided by you)
1. **Model kill (Day 14):** if the upper 95% Wilson bound of v0.1's win rate vs the strongest baseline is below 50% (D14 gold panel, splits B + C), **stop training.** Ship the tool on the best baseline, spend weeks 3–4 on data and users, retry training in month 2 with more pairs.
2. **Wedge pivot (Day 21):** if fewer than 5 of 15 founders paste real copy twice in a week, switch the front door to the free tell-checker or "paste your notes", or switch segment to agencies / cold-email tools via API.
3. **Business pivot (Day 30):** 0 payments and <3 written commitments after 30 calls → stop GPU spend; month 2 is discovery only.
4. **Spend stop (any day):** compute >$300 before Day 21, or any run without a stated eval it should move → pause and review `model/SPEND.md`.
5. **Ethics stop (any day):** if users mainly paste text to beat detectors or strip watermarks, change the intake, not the pitch.

---

## 6. Rejected critic points (2026-11-01 review, market/RISKS.md R8–R15)

All 8 critic fixes were accepted in substance. These parts were rejected or corrected:
1. **Fix 1, "116/200 just clears 50%".** Corrected: ~114/200 is the edge (Wilson lower bound ≈50.1%); 116/200 gives ≈51%. Both are before clustering by prompt, which widens the interval, so treat them as minimums.
2. **Fix 2, length 0.85–1.15× the draft.** Narrowed: applies to "paste your draft" mode only. "Paste your notes" mode has no draft to match, so it uses the copy type's length cap.
3. **Fix 5, "≤1,500 public-domain pairs, kept below 60% of the mix".** Rejected as written: with 500 modern pairs, 1,500 public-domain pairs is 75% of the mix. The 60% cap wins: public-domain/federal ≤1.5× the modern count (≤750 at 500 modern; 1,500 only if modern reaches 1,000).
4. **Fix 7, best-of-3 for the baseline only.** Corrected: our model gets the same best-of-3 through the same gates, or the comparison is unfair in the baseline's favour and hides real wins.
5. **Fix 8, "$1,800 cap" alongside 30 commissioned pieces.** Rejected as inconsistent: 30 × $40 ($1,200) + two panels ($600–1,200) is $1,800–2,400. Commissioned cut to 20 ($800) and panels capped at $500 each so the cap holds.
6. **Fix 8, D5 panel becomes Ali-only.** Accepted, but the week-1 kappa (Ali vs pros) now comes from the copywriters' paid-trial ratings (30 each), so calibration is not lost.
