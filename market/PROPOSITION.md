# FeatherLM: the market proposition

Date: 2026-11-02. Labels: **[F]** fact from a named source, **[V]** vendor claim, **[E]** our estimate (assumption stated), **[?]** single or conflicting source. Every FeatherLM number comes from `hackathon/report/results.json` (via `README.md`) or from a committed run file. Financials come from `market/fin_model.py`; change an assumption there, rerun it, and `market/fin_model.json` updates. Earlier research: `market/MARKET.md`, `market/COMPETITORS_DEEP.md`, `research/YC_RFS.md`.

---

## 1. The proposition in one breath

**FeatherLM turns AI-drafted copy into copy that reads like a skilled person wrote it, and it proves it didn't change a single fact.** One API and one paste box serve anyone who publishes words: founders, marketers, agencies, sales teams, shops, creators, and the AI agents that now write for all of them. It runs on an open model on Fireworks for **about a tenth of the cost of a frontier model**.

- **For the buyer:** copy people trust and act on, without the "this was written by ChatGPT" penalty, and without the legal risk of a rewrite that quietly invents a claim.
- **For a platform:** a drop-in rewrite step with a fact-check receipt, at $0.80 per 1,000 rewrites in compute.

---

## 2. Why now

1. **YC asked for exactly this.** YC's Winter 2027 Request for Startups, "LLMs That Write Well" (Jared Friedman), says current models have "actually gotten worse at writing" as labs optimise for code and agents. It calls this structural and asks for a startup that cares about a model people like reading (`research/YC_RFS.md`, https://www.ycombinator.com/rfs) [F].
2. **AI already writes half of the web.** About 50% of new English-language web articles are primarily AI-generated, flat since early 2025 (Graphite, 65k URLs; Axios update through March 2026, 55.4k URLs) [F]. Readers still prefer human work: 86% of top-ranking Google pages are human-written (Graphite) [F].
3. **Sounding like AI costs money.** 57% of US consumers trust brand messaging less because of low-effort AI content (Gartner, Sept 2026, n=1,006). 32% would trust a brand less if its content were AI-generated, against 15% who would trust it more (YouGov, 7 countries, n=9,869). 53% are less likely to buy from brands that use AI on social (Clutch, n=601) (all in `MARKET.md` §5.4) [F].
4. **Everyone drafts with AI and then edits by hand.** 93% of marketers use AI for content (Ahrefs 2026), and 91% edit AI copy specifically to sound human (Typeform) (`MARKET.md` §5.4) [secondary]. That hand-edit is the job we automate.
5. **The usual fix breaks facts.** "Make it sound human" prompts and humanizer tools change claims. In published marketing copy, a changed number or an invented customer is a truth-in-advertising problem, so a rewrite that changes a fact is worse than no rewrite.

---

## 3. Proof: what we measured (Fireworks hackathon benchmark)

Fact-safe human rewrite rate on 247 items (130 eval + 117 held-out human passages). A rewrite passes only if it invents nothing (no new number, name, quote or attribution), loses nothing, has no AI tells, and isn't gutted. 95% CIs; Δ is against Claude Opus 5.5 with a strong prompt, by paired bootstrap (README, from `results.json`).

| System | Fact-safe rate | Δ vs Claude strong | $ / 1k rewrites | p50 latency |
|---|---|---|---|---|
| **FeatherLM (`O3c`: GLM-5.3 Flash on Fireworks + verify-and-revise harness)** | **97% [94, 99]** | **+26 pp [+20, +31], p<0.001** | **$0.81** | **3.4 s** |
| Claude Opus 5.5, strong prompt (the frontier baseline) | 71% [65, 77] | reference | $9.11 | 3.7 s |
| Claude Opus 5.5 inside *our* harness | 94% [90, 96] | +22 pp | $15.85 | 4.8 s |
| Claude Opus 5.5, "humanizer" prompt | 60% [53, 66] | −12 pp | $50.22 | 3.7 s |
| GPT-6.1, "humanizer" prompt | 51% [45, 57] | −20 pp | $7.73 | 2.5 s |
| GPT-6.1 Terra | 40% [34, 46] | −32 pp | $0.85 | 2.6 s |
| No rewrite at all (control) | 32% [26, 38] | −40 pp | n/a | n/a |

**What this means for a buyer:**
- Out of 100 rewrites, Claude with a good prompt gets about 29 wrong (a fact broken, a tell left in, or text gutted). FeatherLM gets about 3 wrong.
- The usual "humanize it" prompt is *worse* than a plain strong prompt (60% and 51%), which is why humanizer tools have a trust problem.
- Our harness on an open model matches the same harness on Claude (97% vs 94%) at **about a twentieth of the cost** ($0.81 vs $15.85). The value is the system we built, not the frontier model underneath.
- Compute is **11.4× cheaper** than Claude strong and **19.9× cheaper** than Claude in our harness (`fin_model.json`, from measured tokens: about 4,346 input and 290 output per rewrite).

**What we don't claim (judges will check):**
- Readers don't prefer our prose yet. In the blind human A/B against Claude strong, readers picked Claude more often: 54 FeatherLM, 82 Claude, 46 ties (39 voters, 182 votes, sign test p=0.020; mostly public-page visitors). The independent judge (Kimi K3) also leans to Claude on style.
- No system passes as human. In the spot-the-human test, the judges picked the real human original over every system's rewrite almost every time, Claude's included.
- **Our edge today is trust plus cost: same-or-better fact safety, no tells, about a tenth of the price. Style preference is the next milestone (section 9), not today's claim.**

---

## 4. Who it's for: everyone who publishes words

The beachhead stays **founders** (`board/DECISIONS.md`): they write launch emails, landing pages and LinkedIn posts themselves, feel the AI-slop penalty directly, and can pay $19/month without a procurement process. The same engine serves every segment below with no new model.

| Segment | What they rewrite | Why fact-safety matters to them | How they buy |
|---|---|---|---|
| **Founders (beachhead)** | Landing pages, launch and cold emails, investor updates, LinkedIn/X posts | Claims about traction, customers and prices must stay exact | Solo plan, $19/mo |
| **Marketers and content teams** | Blogs, newsletters, ads, product pages | Brand and legal review; 91% already hand-edit AI copy [secondary] | Team plan |
| **Agencies and freelance copywriters** | Client copy at volume | One invented claim can lose a client | Team plan, API |
| **Sales and recruiting** | Cold outreach, follow-ups, job posts | Generic AI outreach gets ignored; names and numbers must be right | Team plan, CRM integration (future) |
| **E-commerce and SMBs** (36.2M US small businesses, SBA Feb 2026 [F]) | Product descriptions, store pages, emails | Specs and prices can't drift | Solo plan, plugins (future) |
| **Creators and personal brands** | Posts, captions, scripts | Voice is the product | Solo plan |
| **AI agents and writing platforms** | Every piece of copy an agent drafts and posts | Agents publish without a human check, so the check has to be built in | **API, per rewrite** |

Out of scope by decision: student essays, and any marketing as "detector evasion" (`CONTEXT.md`, `board/DECISIONS.md`).

---

## 5. Competitors

| Player | What it is | Price | Checks facts after rewriting? | Where it falls short |
|---|---|---|---|---|
| **FeatherLM** | Rewrite plus verify-and-revise; open model on Fireworks | $19/mo solo, $79/mo team, $4 per 1k API rewrites (proposed) | **Yes: numbers, names, quotes, attributions; revises until it passes** | Readers still prefer Claude's prose; early product |
| ChatGPT / Claude ("make it sound human") | General chat models | $0–20/mo; API ~$9 per 1k rewrites (our measurement for Claude strong) | No | 71% fact-safe even with a strong prompt; 53% for Claude with a live-style prompt; "humanizer" prompts are worse |
| Grammarly / Superhuman Humanizer | Free humanizer inside the writing surface; also owns GPTZero (2026-06-23) and Authorship | Free tier; paid plans | Not disclosed | The same company sells the detector and the fix; critics call Authorship laundering (`MARKET.md` §2.2) |
| Jasper (YC W18) | Marketing content platform, enterprise-focused | Pro ~$59–69/mo [?] | Not disclosed | Generates copy; doesn't fix the slop it makes. Consumer and SMB base reported shrinking (Feb 2025) [V]; revenue estimates ~$88M (2025) [?] |
| Copy.ai | GTM and marketing workflows | ~$29–49/mo [?] | Not disclosed | Workflow tool; output quality is the frontier model's |
| Writer | Enterprise brand-voice platform; $200M at $1.9B (Nov 2024) [F] | Enterprise | Brand rules, not per-claim verification [E] | Long sales cycles; enterprise only |
| Humanizers (StealthWriter, Undetectable, WriteHuman, Phrasly, Walter Writes) | Paraphrasers sold on beating detectors | ~$5–36/mo | No | Top tools keep only 66–67% of meaning on HumanizerBench; billing complaints; detectors keep catching up (`COMPETITORS_DEEP.md`). Undetectable ~$10M ARR [?] |
| QuillBot (Learneo) | Paraphraser with a humanizer mode | ~$99.95/yr [?] | No | Synonym swaps |
| Marker | "Anti-slop" AI word processor; $13M seed (Index, July 2026) [F] | Not public | Not disclosed | Not shipped broadly; an editor, not an API |
| Open anti-slop fine-tunes (Hugging Face) | Free models | Free | No | No verifier, no product, no support |

**Our position:** we're the only option on this list that **measures and guarantees fact preservation** and sells it **as an API at open-model cost**. Jasper, Copy.ai, agents and CMSs are potential *customers* of the API, not only competitors.

---

## 6. Market size

**Top-down (third-party, wide ranges):**
- Copywriting services: roughly **$25B in 2024**, growing to about $42B by 2030 (Credence; Coherent via blog) [?]. This is the human spend that AI drafting plus our rewrite step partly replaces.
- AI writing-assistant software: **$1.1–2.3B in 2024**, reaching $1.9–10B by 2030 across four analyst reports (`MARKET.md` §7) [?].
- Content marketing: $80B to over $500B depending on definition [?]. Too loose to use, except to say the copy itself is a very large spend.

**Bottom-up [E]:**

| Layer | Definition | Estimate | Basis |
|---|---|---|---|
| TAM | Paid AI writing software plus the copywriting spend it touches | **$25B+** | Copywriting services ~$25B [?] + AI writing software $1–2B [?] |
| SAM | Paid "make AI copy read human" tools plus rewrite APIs for agents and platforms | **$0.5–1B** [E] | Humanizer-type tools $50–300M ARR (`MARKET.md` §7) + English-market SMB and creator subscriptions + API demand from agents (≈50% of new web articles are AI-written [F]) |
| SOM (year 3, base case) | FeatherLM exit ARR | **$9.6M** | `fin_model.py` base scenario |

Cross-check: 36.2M US small businesses [F] × 1% paying $19/month [E] ≈ $83M ARR from US SMBs alone, before agencies, teams, the API or other countries.

---

## 7. Business model and financials

All from `market/fin_model.py`. Measured inputs: tokens per rewrite, Fireworks prices. Everything else is a labelled assumption.

**Pricing (proposed):** Free (20 rewrites/mo) → Solo **$19/mo** (the $19 entry from `board/DECISIONS.md`) → Team **$79/mo** → API **$4 per 1,000 rewrites**. For comparison, a buyer's own Claude compute alone costs about $9.11 per 1,000 (strong prompt) or $15.85 (our harness). We undercut both, *and* we're more fact-safe.

**Unit cost:** $0.80 per 1,000 rewrites measured. We plan on **$1.59** (2× buffer for longer real drafts [E]). Prompt caching on the repeated system and harness text could bring it to about **$0.38** [E, cached input $0.03/1M in `PRICES.md`].

**Unit economics [E]:**

| Plan | Price | Rewrites/mo (avg) | Variable cost/mo | Gross margin | LTV | CAC | LTV/CAC | Payback |
|---|---|---|---|---|---|---|---|---|
| Solo | $19 | 200 | $0.98 | 95% | $300 | $40 | 7.5 | 2.2 mo |
| Team | $79 | 1,500 | $5.16 | 94% | $2,461 | $300 | 8.2 | 4.1 mo |
| API | $4 / 1k | n/a | $1.59 / 1k | 60% (≈90% with caching [E]) | n/a | n/a | n/a | n/a |

Assumes 6%/mo churn for Solo and 3%/mo for Team, and a 3.5% payment fee. CAC is our assumption; one humanizer reports $10–20 CAC on Google Ads (`COMPETITORS_DEEP.md`) [V].

**Three-year scenarios (year-end run-rate) [E]:**

| Scenario | Year 1 ARR | Year 2 ARR | Year 3 ARR | Year-3 gross margin | Year-3 run-rate operating result |
|---|---|---|---|---|---|
| Conservative | $0.14M | $0.92M | $2.96M | 77% | −$0.72M |
| **Base** | **$0.52M** | **$2.96M** | **$9.64M** | **77%** | **+$4.40M** |
| Upside | $1.79M | $11.76M | $40.14M | 73% | +$26.47M |

Base case at year 3: 15,000 Solo, 1,500 Team, 100M API rewrites per month. Fixed costs are assumed at $0.25M, $1.2M and $3M for years 1–3. Gross margin is held below the plan margins by the API share and the free tier. Caching would lift it.

---

## 8. Scalability in production

- **No GPUs to run.** Inference is Fireworks serverless, billed per token. Cost scales linearly with use: **1M rewrites ≈ $800 of compute** measured (≈ $1,600 with our buffer).
- **Latency is chat-speed.** p50 3.2–3.5 s and p95 about 7.5 s on the 130-item eval and 120-item held-out runs (committed run files), with the full verify-and-revise loop included. One run on 80 real drafts had a 74 s tail (cause not investigated).
- **Limits grow with spend.** Fireworks serverless limits are per-minute tokens per account and model, and rise with spending tier (Fireworks docs) [F]. Past that, move to dedicated deployments. At an assumed $8/hour per H100 [?], a dedicated GPU (~$5,840/month) costs the same as about **3.7M rewrites/month** on serverless, so that's roughly where dedicated starts to pay.
- **Personal voice per customer, without a model per customer.** Fireworks serves LoRA fine-tunes on serverless at the base model's per-token rate, with no extra fee, and its multi-LoRA serving runs hundreds of adapters on one base (Fireworks pricing page; multi-LoRA blog, Sept 2024) [F]. "Sounds like you" for every customer is a product feature, not an infrastructure problem.
- **Model-agnostic.** The harness (gates G1–G4 plus revise) wraps any model. When a better open model ships on Fireworks, we swap it in and re-run the same 247-item benchmark before switching. We aren't tied to one lab.
- **Built-in verifiability.** Every rewrite comes with a machine-checkable pass/fail per gate. Agents can log that receipt and skip human review when it passes.

---

## 8b. Scaling up: more data, more compute, funding

Everything here comes from `SCALE` in `market/fin_model.py`. Measured inputs: our SFT run (5,000 rows, 1,856,167 training tokens, $8.89 per 1M tokens on the Fireworks serverless GLM-5.3 Flash training rate, `hackathon/train/TRAIN_LOG.md`) and today's Fireworks inference prices. Everything else is [E].

**Why more data should help.** Today our edge is fact safety, and readers prefer Claude's prose. External evidence says data is how that gap closes: in a blind study, expert readers rejected prompted AI writing (style odds ratio 0.16), but **preferred AI fine-tuned on an author's own works** (style OR 8.16, quality OR 1.87). The median fine-tuning cost was $81 per author (Chakrabarty, Ginsburg, Dhillon, arXiv 2510.13939, preprint) [F]. A related result: reward models trained on expert edits of AI drafts beat frontier LLM judges at rating writing quality, and experts preferred their best-of-N pick 66% of the time (WQRM, COLM 2025, in `research/COPY_EVAL.md`) [F]. Our one evaluated SFT run on reverse-distilled pairs alone did *not* beat the harness (`O4m`: 33% fact-safe). So the plan keeps the harness gates as hard constraints and adds **expert edit pairs and reader preference data**, the signals those studies say matter.

**What the data and training cost (per stage) [E]:**

| Stage | SFT pairs | Expert edit pairs | Preference pairs | SFT compute | DPO compute | Expert data | Human evals / yr | Total |
|---|---|---|---|---|---|---|---|---|
| Today's data, full sweep | 5,000 | 0 | 66 | $990 | $52 | $0 | $14,400 | **$15k** |
| Seed (months 0–12) | 50,000 | 5,000 | 20,000 | $9,901 | $15,841 | $50,000 | $14,400 | **$90k** |
| Series A (months 12–36) | 500,000 | 25,000 | 500,000 | $99,008 | $396,032 | $250,000 | $14,400 | **$759k** |

Assumes 3 epochs × 20 runs per stage (sweeps, not one lucky run), DPO at 2× the SFT per-token cost, expert copywriters at $60/hour doing 6 edit pairs an hour (freelance range $50–85/hour, Payscale/guides) [?], and 24 blind copywriter panels a year at $600 (`market/RISKS.md` R15). Our actual hackathon training spend was about $26 for two SFT runs (TRAIN_LOG estimates). The SFT pairs stay cheap because they're reverse-distilled from licence-clean Common Pile text. Preference pairs come mostly from the product: each time a user picks one of two versions, that's a free label.

**Training is cheap, so data quality is the real cost.** Even the Series A stage costs well under $1M, small next to payroll. What money buys is expert edits and blind panels, plus the user picks that only a live product produces.

**Inference gets cheaper as the model improves [E].** A style-tuned model that passes the gates on the first try needs fewer revise loops. At an assumed 1,800 input and 300 output tokens per rewrite (against 4,346 and 290 today), cost falls from $0.80 to **$0.42 per 1,000**, or **$0.25** with prompt caching. Fireworks serves the LoRA at the base model's per-token rate, so there's no serving premium for our own model [F].

**Funded five-year case [E]:** $3M seed now, a $12M Series A in year 3. Users stay longer because the product improves (churn 4%/mo Solo, 2%/mo Team, so LTV rises to $451 and $3,752), and the API price falls as volume grows ($4 → $2.50 per 1,000).

| Year | Exit ARR | In-year revenue | Rewrites / month | Gross margin | Fixed cost | Raised | Cash at year end |
|---|---|---|---|---|---|---|---|
| 1 | $1.03M | $0.52M | 10.6M | 79% | $1.5M | $3M | $1.91M |
| 2 | $7.52M | $4.28M | 83.9M | 88% | $4.0M | n/a | $1.65M |
| 3 | $23.7M | $15.6M | 314M | 90% | $9.0M | $12M | $18.7M |
| 4 | $58.8M | $41.3M | 833M | 91% | $16.0M | n/a | $40.3M |
| 5 | $100.4M | $79.6M | 1.56B | 90% | $25.0M | n/a | $87.1M |

Year-5 mix: 160,000 Solo, 20,000 Team, 1.5B API rewrites a month (about 50M a day, a small share of the copy that agents now draft). Gross margin *rises* with scale (79% → 90%) because the fine-tuned model is cheaper to run than today's multi-loop harness. Cash never goes negative: the seed lasts until the Series A, and the business is operating-profitable from year 3. Every one of these customer counts is an assumption, not a forecast we can defend with data today; the point is the shape. **Cost per rewrite falls, margin rises, and data, not GPUs, is the main investment.**

**What scale needs operationally:** 1.56B rewrites a month at $0.42 per 1,000 is about $656k of compute a month. That's past the ~3.7M-rewrites-a-month point where dedicated deployments beat serverless, so at that volume we'd run dedicated Fireworks deployments with multi-LoRA (per-customer voices on one base), plus batch inference (−50%, `PRICES.md`) for non-urgent jobs.

**Quality milestones the money is for (targets, not results):**
1. Seed: win or tie Claude in a blind copywriter panel (≥200 judgments, lower Wilson bound above 50%), with the fact-safe rate held at ≥95%.
2. Seed: a personal-voice LoRA per paying team, measured by the same gates.
3. Series A: a public copy benchmark with paid human judges, and an API used by agent platforms.

---

## 9. Moat and roadmap

1. **The benchmark and the gates.** We define and publish "fact-safe human rewrite" with a 247-item benchmark and a code-level verifier. Whoever owns the measurement shapes how the category is judged.
2. **Data that's licence-clean.** Training pairs are reverse-distilled from Common Pile human text (no frontier-model text, no pirated books), so customers and platforms can adopt it without licence risk.
3. **Style is the next milestone.** Readers prefer Claude's prose today (p=0.020). The plan is preference data from blind reader picks, then style fine-tunes as LoRA adapters on the same base, with the gates kept as hard constraints so style gains can't cost facts.
4. **Distribution through the API.** Agents, CMSs and marketing tools embed the rewrite step, so we ride their distribution.

---

## 10. Risks (stated before a judge raises them)

| Risk | Answer |
|---|---|
| Readers prefer Claude's prose | True today (54/82/46, p=0.020). We sell fact safety and cost now and treat style as the roadmap. We won't claim "more human than Claude." |
| Frontier labs improve writing | YC calls the regression structural. Our harness wraps any model, so a better base raises our score too |
| Incumbents bundle it for free (Grammarly, ChatGPT) | None of them measure or guarantee fact preservation; we sell the receipt and the API price |
| Gates measure our own definition | That's why we also report an independent judge (Kimi K3, a different model family) and a blind human test, including the results that go against us |
| Assumptions in the model | Every one is labelled in `fin_model.py`; conservative case shown |
| Real customer drafts differ from eval drafts | 2× cost buffer; the 80-item real split was never used for tuning |

---

## 11. The pitch in 30 seconds

> AI writes half the web now, and readers can tell. When you ask a frontier model to make copy sound human, it quietly breaks facts: Claude Opus 5.5 gets it right 71% of the time on our benchmark. FeatherLM gets it right 97% of the time, at about a tenth of the cost, on an open model running on Fireworks. Every rewrite comes with proof that no number, name or quote changed. Founders first, then every team and every agent that publishes copy. That's the startup YC asked for in "LLMs That Write Well", and we built the part the labs won't: writing you can trust.

---

## Sources

- FeatherLM results: `README.md`, `hackathon/report/results.json`, `hackathon/report/RESULTS.md`; run files `evals/runs/hack_O3c_glm_prompt_harness_style*.jsonl`; prices `hackathon/report/PRICES.md`; model `market/fin_model.py` → `market/fin_model.json`
- YC RFS "LLMs That Write Well": https://www.ycombinator.com/rfs (notes in `research/YC_RFS.md`)
- Graphite / Axios on AI-written web articles: https://axios.com/2026/05/15/human-vs-ai-written-articles ; https://www.techradar.com/ai-platforms-assistants/the-internet-is-now-mostly-written-by-machines-study-finds ; https://www.eweek.com/news/ai-writes-half-internet/
- Consumer trust (Gartner, YouGov, Clutch) and marketer AI use (Ahrefs, Typeform): `market/MARKET.md` §5.4
- SBA Office of Advocacy, FAQ 2026 (36,207,130 small businesses): https://advocacy.sba.gov/2026/02/03/advocacy-releases-frequently-asked-questions-about-small-businesses-2026/
- Copywriting services market: https://www.credenceresearch.com/report/copywriting-services-market ; https://bloggingwizard.com/copywriting-statistics/
- AI writing-assistant market estimates: `market/MARKET.md` §7
- Jasper pricing and revenue estimates: https://costbench.com/compare/jasper-vs-copy-ai/ ; https://miracuves.com/blog/jasper-revenue-model/ ; https://www.webull.com/news/12853278535779328
- Copy.ai pricing changes: https://costbench.com/changelog/copy-ai-plan-removed-2026-05/
- Writer Series C: https://techcrunch.com/2024/11/12/generative-ai-startup-writer-raises-200m-at-a-1-9b-valuation
- Humanizers, Grammarly/GPTZero, Marker, QuillBot: `market/MARKET.md` §2 and §4, `market/COMPETITORS_DEEP.md`
- Fine-tuning evidence: Chakrabarty, Ginsburg, Dhillon, "Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers" (preprint): https://arxiv.org/abs/2510.13939 ; WQRM and related work: `research/COPY_EVAL.md`
- Our training runs and costs: `hackathon/train/TRAIN_LOG.md`; Fireworks fine-tuning tiers (third-party): https://www.morphllm.com/fireworks-ai-pricing
- Copywriter rates: https://www.payscale.com/research/US/Job=Freelance_Copywriter/Hourly_Rate ; https://joingerald.com/learn/work--income/freelance-copywriter-rates-2026
- Fireworks rate limits: https://docs.fireworks.ai/serverless/rate-limits ; LoRA pricing: https://app.fireworks.ai/pricing ; multi-LoRA: https://fireworks.ai/blog/multi-lora ; H100 hourly reports: https://www.morphllm.com/fireworks-ai-pricing
