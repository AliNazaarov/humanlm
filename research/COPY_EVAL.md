# HumanLM: copywriting evidence + founder-copy eval set v1

Written 2026-11-01 by hl-researcher. All sources accessed 2026-11-01. Labels: **[S]** sourced (URL given), **[E]** my estimate, **[K]** background knowledge not re-checked today, **[V]** vendor data (has a reason to look good).
Builds on `research/TECH.md`, `evals/APPLIED_PLAYBOOK.md` and `data/DATA_SOURCES.md`. Those cover slop metrics, FTPO, Unslopper, detectors and the general data law. This file covers copy only. It does not repeat them.

---

## 0. Bottom line (read this if nothing else)

1. **Better copy moves money, but the effect is small and is measured on real outcomes.** Meta's RL-trained ad writer lifted CTR 6.7% across ~35,000 advertisers. Alibaba's AI product descriptions lifted sales ~2%. Nobody found a 2x effect from prose alone.
2. **Pure AI copy vs human copy is a split decision.** In small ad tests humans win on cost, not clearly on clicks. Human + AI teams beat human-only on text quality. "AI draft, then a skilled-human pass" is the pattern the evidence backs. That is exactly HumanLM's job.
3. **Experts and lay readers judge differently.** Expert readers strongly reject *prompted* AI text. They *prefer* a *fine-tuned* model's text. Lower cliché density explains the flip. This is the best single piece of evidence for our "own fine-tuned model" plan. It also means the gold raters must be professional copywriters, not crowd workers.
4. **"Does this sound human?" is a broken question.** People use wrong shortcuts (contractions, "I", family topics). A model can game them. Ask raters "which would you send / which converts?" instead.
5. **Cold email: no independent study of AI vs human reply rates exists.** Vendor averages sit near 3.4%. The best controlled analogue (phishing) shows AI = human experts (54% vs 54% clicks) when both do research first. Facts about the prospect matter more than prose. A rewriter must never invent them.
6. **Inventing a testimonial or claim is now illegal in the US** (FTC rule, Oct 2024). The faithfulness gate is a legal feature, not a nice-to-have.
7. **No licence-clean corpus of modern founder copy exists.** Build it from: public-domain ads (to 1930), US federal plain-language pages, a few openly licensed company texts, the founder's own writing, and commissioned copy.

---

## 1. Does AI copy perform? Field evidence

| Study | Design | Result | Strength | Source |
|---|---|---|---|---|
| **AdLlama** (Jiang et al., Meta, arXiv Jul 2025, rev. Dec 2025) | 7B Llama 2 Chat trained with "RL with performance feedback". Reward model built from pairs of ads *in the same campaign*, labelled by which got the higher CTR. 10-week A/B, ~35,000 advertisers, ~640,000 ad variations | **+6.7% advertiser-level CTR** vs an SFT model trained to imitate curated ads (p=0.0296). Advertisers also made 18.5% more variations | Strong (huge field test), but internal to Meta, not replicated | [S] https://arxiv.org/abs/2507.21983 , https://arxiv.org/html/2507.21983v1 |
| **Generative AI and Firm Productivity** (Fang et al., arXiv Oct 2025, v3 Feb 2026; CESifo 2026) | Randomised field tests on a big cross-border e-commerce platform. Inputs held fixed | AI product descriptions: **~+2% sales, ~+1.3% conversion**. Biggest gains for sparse or badly translated listings and small sellers. Chatbot: +16.3% sales | Strong design. The exact % comes via an aggregator summary; check the PDF | [S] https://arxiv.org/abs/2510.12049 , https://business.columbia.edu/insights/digital-future/ai-supercharging-online-retail , https://www.emergentmind.com/papers/2510.12049 |
| **Collaborating with AI Agents** (Ju & Aral, MIT, arXiv Mar 2025, v4 Oct 2026) | ~2,300 people randomised to human-human or human-AI teams, ~11,000 ads, field test on X with ~5M impressions | Human-AI teams wrote **higher-quality text**; text quality raised CTR and view time. Human-human teams made better images, which lowered CPC. Net ad performance about equal | Strong, preregistered-style RCT; isolates teams, not "pure AI" | [S] https://arxiv.org/abs/2503.18238 |
| **The hybrid formula** (Hunt & Kerr, Journal of Brand Strategy 14(1), May 2025) | Meta ad A/B tests in 6 verticals (SaaS, dental, restaurants, real estate, podcasts, sports). GPT-4, a custom GPT and Meta's AI vs human copywriters | Humans won **9/12 on cost per result** but only **5/12 on CTR**. Authors recommend AI draft + human edit | Weak (small, agency-run) | [S] https://ideas.repec.org/a/aza/jbs000/y2025v14i1p30-42.html |
| Search Engine Journal test | One Google RSA per writer, Copy.ai vs humans | CTR 3.65% AI vs 4.98% human, but on 26 and 65 clicks | Anecdote; not significant | [S] https://www.searchenginejournal.com/humans-vs-machines-ad-copy-content-test-data-study/509942/ |
| **Spear phishing with LLMs** (Heiding, Lermen, Kao, Schneier, Vishwanath; arXiv Nov 2024; Expert Systems with Applications 2026) | 101 people, 4 arms | Click rate: control 12%, **human experts 54%, fully automated AI 54%**, AI + human 56%. AI research profiles accurate 88% of the time | Small but controlled. Best analogue for cold email | [S] https://arxiv.org/abs/2412.00586 , https://www.schneier.com/academic/archives/2026/02/evaluating-large-language-models-ability-to-automate-spear-phishing.html |
| **Conversational persuasiveness of GPT-4** (Salvi et al., Nature Human Behaviour 2025) | 900 US people debating | With personal data, GPT-4 beat humans (+81.7% odds of higher agreement; ~64% of non-tied debates). Without personal data, no significant edge | Strong; debates, not copy | [S] https://www.psypost.org/scientists-demonstrate-that-ais-superhuman-persuasiveness-is-already-a-reality/ , https://www.scimex.org/newsfeed/could-chatgpt-be-more-persuasive-than-people |

**What this says, plainly.**
- Copy quality is real money, but single-digit percent. Our pitch should be "reads like your best copywriter, at agent speed", not "doubles your conversions". [E]
- In every strong study, the win comes from **specific inputs** (personal data, prospect research, richer product facts), not from fancier words. The rewriter can only keep and sharpen the facts it is given. It must not make new ones.
- The strongest ad model (AdLlama) was trained on **real outcome pairs from the same campaign**. That is the long-run reward we want: API customers' own A/B results, with consent. It is out of reach in month 1.

### 1b. AI disclosure and trust
- Disclosing AI in ads lowered trust in the ad and the brand (Koning & Voorveld, Journal of Interactive Advertising 2025, N=304) [S, via search summary] https://pure.uva.nl/ws/files/292049880/Disclaimer.pdf
- An 8-study "AI disclosure penalty" for creative writing; perceived authenticity is the driver (Raj, Berg, Seamans; listed as J. Exp. Psych. 2026) [S, summary only] https://citations.prolific.com/paper/the-artificial-intelligence-disclosure-penalty-humans-persistently-devalue-ai-generated-creative-wri
- Some studies find no harm or mixed effects. Evidence leans toward a penalty. [S, same search]
- Meaning for us: founders want copy that does not *read* as AI because readers discount it. Fine to say. Do not sell "hide that you used AI".

---

## 2. LinkedIn: AI vs human posts

| Source | What | Number | Caveat |
|---|---|---|---|
| Originality.ai 2024 | 8,795 long posts (100+ words) | ~54% "likely AI"; likely-AI posts got **45% less engagement** [V] | Detector-labelled, not true authorship. Vendor sells the detector |
| Originality.ai 2025 | 3,368 long posts, 99 influential profiles, Jan-Nov 2025 | 53.7% likely AI. Engagement **mixed by topic**: AI ahead in Tech/AI and Finance (~7%) and Leadership (+75%); humans ahead in Marketing & Branding (+73%), Healthcare, Wellness [V] | Same caveats; small per-topic samples |
| Pangram, Jul 2026 | Five platforms, posts >250 words, Apr-Jun 2026 | **41% of LinkedIn long posts** fully AI; LinkedIn = ~1/3 of sample but 62% of flagged text [V] | No engagement data. CEO calls it a lower bound |

Sources [S]: https://originality.ai/blog/linkedin-ai-study-engagement , https://originality.ai/blog/ai-content-published-linkedin , https://ppc.land/over-half-of-linkedin-posts-are-now-likely-ai-but-authenticity-still-wins/ , https://www.fastcompany.com/91571983/linkedin-is-the-most-ai-saturated-platform , https://the-decoder.com/linkedin-is-the-undisputed-king-of-long-form-ai-slop-according-to-a-study-spanning-five-platforms/

**Read:** the market is real (roughly 4-5 in 10 long LinkedIn posts read as AI). The engagement claim is **not** settled. Do not put "AI posts get 45% less reach" in marketing. Use "about half of long LinkedIn posts now read as AI" with the source, if anything.

---

## 3. Cold email: what is actually known

- **No independent, peer-reviewed study of AI-written vs human-written cold email reply rates was found.** Everything public is vendor data. [S, search 2026-11-01]
- Instantly 2026 benchmark (2025 data): average reply **3.43%**, top quartile 5.5%+, top decile 10.7%+; 58% of replies come from step 1; best sequences reported to keep emails **under 80 words** [V, via secondary summaries; primary page did not render]. https://instantly.ai/cold-email-benchmark-report-2026 , https://prospeo.io/s/cold-email-reply-rate
- Belkins (16.5M emails): personalised 7% vs generic 3% reply [V, unverified against original]. Unify (25M sends): AI personalisation +57% replies *when fed real account data* [V]. https://www.smartlead.ai/benchmarks/how-much-to-personalize-cold-email , https://thedigitalbloom.com/learn/cold-outbound-reply-rate-benchmarks/
- Mailshake's report is self-reported by 508 practitioners [V]. https://assets.mailshake.com/wp-content/uploads/2025/04/16091740/Cold-Email-Report-2025-Mailshake.pdf
- Controlled analogue: phishing study above. AI with research = human experts.

**Read:** reply rate is driven by list, offer and real personal relevance. Prose is a smaller lever. For our eval: cold-email prompts must include 1-2 true prospect facts. The model passes only if it uses them correctly, adds no new "personal" facts, and stays short. We should never claim a reply-rate lift until a user runs a real A/B.

---

## 4. How expert copywriters judge copy

Frameworks that recur across classic and modern practice. I mapped each to something we can check.

| Framework | Core idea | Source | Becomes rubric item |
|---|---|---|---|
| MECLABS conversion heuristic `C = 4m + 3v + 2(i-f) - 2a` | Motivation, **value-prop clarity**, incentive vs friction, anxiety. A thinking tool, not a real equation | [S] https://searchengineland.com/want-higher-conversions-get-clear-about-your-value-propositions-15369 , https://digitaleditions.napco.com/article/The+Mix/2888406/440511/article.html | R1 Clear in 5 seconds; R5 one clear ask; R4 proof lowers anxiety |
| 4 U's (Masterson, popularised by Bob Bly) | Useful, Urgent, Unique, **Ultra-specific** | [S] https://www.bly.com/Pages/DMNCOL1e[1].htm | R2 Specific |
| LAMP taxonomy (Chakrabarty, Laban, Wu; 8 MFA writers) | AI writing problems: awkward word choice (28%), poor sentence structure (20%), redundant exposition (18%), cliché (17%), purple prose, lack of specificity, tense issues | [S] https://arxiv.org/abs/2409.14509 | R6 Voice/craft; error-analysis codes |
| AdParaphrase v1/v2 (CyberAgent, ACL Findings 2025) | 16,460 ad paraphrase pairs, 10 raters each. Preferred ads were more fluent, a bit longer, **more nouns** (concrete), used brackets. Human preference tracked real ad performance | [S] https://arxiv.org/abs/2505.20826 , https://arxiv.org/abs/2502.04674 | Supports R2; method template for our pairs. Japanese only |
| Reader-first, one reader, one ask [K] | Classic direct-response craft (Ogilvy, Schwartz, Caples) | [K] not re-verified | R3 Reader-first; R5 |
| Plain language (US federal) [K] | Short sentences, active voice, "you" | [K] plainlanguage.gov | R1; also a data source (section 6) |

Two research results that change *who* judges:
- **Experts vs lay readers.** Chakrabarty, Ginsburg, Dhillon (arXiv Oct 2025): with prompting only, MFA experts strongly rejected AI text for quality (OR=0.13) and style (OR=0.16); lay readers were mixed. After fine-tuning on an author's works, experts *preferred* the AI (quality OR=1.87, style OR=8.16). Mediation: fine-tuning removed tells like **cliché density**. [S] https://arxiv.org/abs/2510.13939
- **Lay "is it human?" judgments are flawed.** Jakesch, Hancock, Naaman (PNAS 2023, 6 experiments, 4,600 people): people could not tell AI from human self-descriptions, and used wrong cues (first person, contractions, family topics). AI can be tuned to look "more human than human". [S] https://pmc.ncbi.nlm.nih.gov/articles/PMC10089155
  - So: never ask raters "is this human?". Never reward contraction rate or "I" count. Ask "which would you ship?" and "which reads like a skilled copywriter?"

## 5. Can a model learn copy taste? Reward-model evidence

| Work | Finding | Use for us | Source |
|---|---|---|---|
| WQRM (Chakrabarty, Laban, Wu; COLM 2025) | Reward models trained on 1,282 expert-edited AI paragraphs (LAMP) hit **74%** on a 4,729-judgment writing-quality benchmark; frontier LLMs (GPT-4o, o1) barely beat random. Best-of-N with WQRM: experts preferred its pick **66%** (72% when the reward gap > 1) | **Edit pairs** (AI draft → expert edit) are the right training signal. That is exactly what the founder's ~10 daily edits produce | [S] https://arxiv.org/abs/2504.07532 |
| LitBench (Fein et al.; EACL 2026) | 43,827 Reddit preference pairs. Trained Bradley-Terry RM **78%** vs best zero-shot judge (Claude 3.7 Sonnet) **73%**. Chain-of-thought distillation *hurt* | Train our own small BT reward model once we have 1-2k copy pairs [E]; don't trust a prompted LLM judge for taste | [S] https://arxiv.org/abs/2507.00769 |
| PersuasionBench / "transsuasion" (Singh et al., Adobe; ICLR 2025) | 1.57M natural-experiment pairs: same account, similar tweet, posted within 45 days, different engagement. Small models trained on them got more persuasive | Template for *outcome* pairs later (users' own post analytics, with consent). Do not scrape | [S] https://arxiv.org/abs/2410.02653 |
| AdLlama (above) | Same-campaign CTR pairs as reward | Long-run reward for the API | [S] https://arxiv.org/abs/2507.21983 |

## 6. Licence-clean sources of good human copy

The gap from `data/DATA_SOURCES.md` line 44 is still open: there is no clean open corpus of modern copy. Ranked by use for the founder-copy eval and reverse distillation:

| # | Source | Licence status | Fit for founder copy | Notes / source |
|---|---|---|---|---|
| 1 | **Founder's own writing** (emails, posts, pitch notes, pre-2023 if possible) | His to use | High (voice + B2B) | Strip third-party names. Best for the "voice" split later |
| 2 | **Commissioned copy** from 3-5 freelance copywriters: brief → human copy, with written assignment of rights | Clean if the contract assigns rights | Highest | Plan already has this. Budget est. $30-100 per piece [E, from DATA_SOURCES] |
| 3 | **Consented copy from founders/companies** (landing pages, launch emails) via a simple licence form | Clean with signed permission | High | Offer free rewrites in exchange. Keep the form on file |
| 4 | **US public-domain ads, published 1930 or earlier** | Works published in 1930 entered US public domain on 1 Jan 2026 [S] https://web.law.duke.edu/cspd/ , https://blog.archive.org/2026/01/01/welcome-to-the-public-domain-in-2026/ | Medium: great headlines and long-form direct response (Caples era), old diction | Duke Ad*Access (1911-1955) is **not** a PD collection: most items are post-1923 and Duke claims no rights; commercial use needs the rights holder [S] https://repository.duke.edu/dc/adaccess/about , https://dlib.org/dlib/february00/pritcher/02pritcher.html . Use only items you can date to 1930 or earlier. OCR noise |
| 5 | **US federal government text** (agency plain-language pages, SBA guides, PSAs written by federal staff) | Not copyrightable under 17 U.S.C. §105 [S] https://www.law.cornell.edu/uscode/text/17/105 . 2024 amendment carves out some military-academy faculty works; contractor work is **not** covered [S] https://uscode.house.gov/ | Medium: clear, plain, reader-first; not salesy | Good for "clarity" references and LanguageTool calibration |
| 6 | **Openly licensed company writing** (e.g. GitLab Handbook, reported CC BY-SA 4.0) | Licence not confirmed from GitLab itself [S, weak] https://gitlab.com/gitlab-org/gitlab-docs/-/issues/95 . Share-alike: whether model weights count as an adaptation is unsettled [K] | Medium (internal B2B voice, not ad copy) | Eval references OK with attribution. Avoid in training until a lawyer says yes |
| 7 | HF tagline sets, e.g. Hanno-Labs/saas-taglines-rated (listed CC-BY-4.0) | Listed only; provenance of the taglines (scraped company sites?) unknown [S] https://huggingface.co/datasets/Hanno-Labs/saas-taglines-rated/discussions | Medium | A licence on a dataset of scraped copy does not clear the original companies' copyright [K]. Eval inspiration only |
| 8 | Live landing pages, YC company sites, Product Hunt, LinkedIn, X | Copyrighted; LinkedIn/X require login and ban scraping in terms [K] | Highest fit, **not usable** for training | May *read* them to write our own briefs. Never copy text in |

## 7. Faithfulness and grammar tooling

- **MiniCheck** (Tang, Laban, Durrett; EMNLP 2024): 770M Flan-T5 checker matches GPT-4 on grounded fact-checking at ~400x lower cost; benchmark LLM-AggreFact. Runs on CPU, so it fits Tenki. Claim decomposition did not reliably help. [S] https://arxiv.org/abs/2404.10774 , leaderboard https://llm-aggrefact.github.io
- **FTC fake reviews and testimonials rule:** final 14 Aug 2024, effective 21 Oct 2024; covers AI-generated fake testimonials; civil penalties up to $51,744 per violation (2024 figure, inflation-adjusted yearly). [S] https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials
- **LanguageTool:** self-hostable HTTP server; reported licence LGPL-2.1 (confirm on the repo) [S, weak] https://railway.com/deploy/languagetool . Docker image `erikvl87/languagetool` serves on port 8010 [S]. Python wrapper `language_tool_python` can point at your own server and sends "picky" per request [S] https://language-tool-python.readthedocs.io/en/latest/references/examples.html . Disabling rules is done per request, not by server flags (old forum thread; test it) [S] https://forum.languagetool.org/t/how-to-disable-built-in-language-check-rules-when-running-an-http-server/2083 . Official API docs: https://languagetool.org/http-api [K]

---

## 8. Founder-copy eval set v1 spec

### 8.1 What the task is
Input: an **AI-sounding draft** + a short **brief** (product, audience, facts that are true, the ask). Output: one rewrite.
A pass means: a skilled copywriter would ship it, it adds no facts, drops no required facts, has zero grammar errors, and fits the format.

### 8.2 Where the 200 prompts come from
| Origin | Count | How the reference answer is made |
|---|---|---|
| A. Reverse-distilled from licence-clean human copy (section 6 rows 1, 4, 5, 6) | 80 | The human original is the reference. The AI draft is made by **4 different models** (e.g. GPT, Claude, Gemini, an open model), 20 each, so we don't learn one model's tells |
| B. Commissioned: copywriter gets brief + AI draft, writes the fix | 80 | Their rewrite is the reference. Pay for 2 references on 20 of them to measure agreement |
| C. Real founder drafts (consented, from waitlist or Ali's network) | 40 | No reference at first. Judged only by pairwise A/B and gates. Becomes the most valuable split |

None of these 200 may appear in training. Hash and store them; the trainer's data loader refuses any match (n-gram overlap > 8 words).

### 8.3 The 200 by type
| Type | Count | Length cap (hard) | Brief must include |
|---|---|---|---|
| Landing page hero (headline + subhead + CTA) | 30 | headline ≤ 12 words, subhead ≤ 30 [E] | product, buyer, 1 outcome, CTA |
| Landing page section (feature/benefit block, FAQ, pricing blurb) | 20 | ≤ 80 words | 2-3 facts, 1 number |
| Launch / announcement email | 25 | ≤ 200 words | what shipped, who for, date, link |
| Cold email, first touch | 35 | ≤ 90 words [E, vendor data says < 80 works best] | 1-2 true prospect facts, offer, soft ask |
| LinkedIn post | 35 | 80-250 words | story or lesson, 1-3 facts |
| X post or 3-5 post thread | 25 | 280 chars per post | 1 claim, 1 proof |
| Short ad (Meta primary text + headline; Google RSA lines) | 20 | platform limits [K: RSA headline 30 chars, description 90] | offer, audience, proof |
| Launch blurb (Product Hunt tagline/first comment, Show HN) | 10 | tagline ≤ 60 chars [K] | what it is, for whom |
| **Total** | **200** | | |

Plus 30 **canaries** (separate, never in training, run every time):
- 10 **already-good human copy** as input. A good model changes little. Fail if meaning or voice is lost (edit distance > 40% [E] or expert says "worse").
- 10 **puffery bait**: brief has weak facts and the draft invents "trusted by 10,000 teams". Pass only if the invention is removed, not polished.
- 10 **dense-number briefs** (prices, dates, %): every number must survive exactly.

Splits: `dev` 80 (free use), `gate` 100 (scores only, run per checkpoint), `canary` 30. Each split has the same type mix.

### 8.4 Each prompt record (`evals/copy_v1/*.jsonl`)
```
id, type, origin (A|B|C), source_licence, draft_model,
brief: {product, audience, facts[], numbers[], names[], ask},
required_facts[]  (must appear, paraphrase OK),
forbidden[]       (claims that would be invented, e.g. "SOC 2", user counts),
ai_draft, reference (nullable), length_cap, notes
```

### 8.5 Rubric (binary, one judge per item, per the playbook's "no aggregate score" rule)
| ID | Question (yes/no) | Grounded in |
|---|---|---|
| R1 Clear | Can a stranger say what it is, for whom, and what to do next after 5 seconds? | MECLABS clarity |
| R2 Specific | Does it use the brief's concrete nouns/numbers instead of generic benefit words ("streamline", "unlock", "seamless")? | 4 U's; LAMP "lack of specificity"; AdParaphrase nouns |
| R3 Reader-first | Is the reader's problem or gain the subject, not the company? | classic craft [K] |
| R4 Proof placed | Is each proof point from the brief present and near the claim it backs? | MECLABS anxiety |
| R5 One ask | Exactly one call to action, matching the brief's ask? | MECLABS friction |
| R6 Craft | Free of the LAMP faults: cliché, redundant exposition, purple prose, awkward phrasing, clumsy structure? | LAMP |
| R7 Format | Fits the type's length cap and platform norms? | section 8.3 |
| Ship | "Would you ship this unchanged for a paying client?" (expert rater only) | the north-star question |

Plus code metrics, reported, never gated alone: slop-phrase rate and em-dash / tricolon / "not X but Y" rates vs the human band **per type** (from TECH.md); Distinct-n across 5 samples (collapse check).

Not in the rubric on purpose: "sounds human", contraction rate, first-person rate (Jakesch: gameable). Detector scores: monitor only.

### 8.6 Gold: blind pairwise A/B
- Arms: HumanLM checkpoint vs (a) best frontier model with a strong "rewrite like a senior copywriter" prompt + 3 human examples, (b) the human reference where one exists.
- Raters: 2-3 paid working copywriters (B2B/SaaS), not crowd workers (Chakrabarty 2025: experts and lay readers disagree). Ali is not a gold rater.
- Question: "Which would you send for a client?" + one-line reason + "both unusable" option. Position randomised, lengths within ±15%.
- Report win rate with Wilson 95% CI **per type**. 100 `gate` prompts × 1 comparison gives roughly ±10 points CI [E]; that is enough to see a big gap, not a small one.
- Agreement: 20 pairs double-rated. If two copywriters agree < 65% [E], fix the rubric before trusting results.

### 8.7 Grammar gate (LanguageTool)
1. Run LanguageTool locally (Docker, CPU, on Tenki when awake; never a public API with user text).
2. Count only categories GRAMMAR, TYPOS, plus PUNCTUATION and CONFUSED_WORDS. Ignore STYLE, REDUNDANCY, TYPOGRAPHY and CASING (headlines are title case; copy uses fragments on purpose) [E: category names per LanguageTool docs, confirm].
3. **Calibrate on human references:** run on all reference copy. Any rule that fires on > 5% of human references gets disabled [E]. Commit the disabled list.
4. Whitelist per prompt: product names, `names[]` from the brief, URLs.
5. Gate: zero remaining matches. Also fail on any spelling change to a brand or person name.
6. Log every disabled rule and every miss a human finds; the gate is reviewed monthly.

### 8.8 Faithfulness check (three layers, cheap first)
1. **Code diff (free):** extract numbers, money, %, dates, URLs, emails, proper nouns, superlatives ("#1", "only", "fastest"), and certifications from output. Each must be in the brief or the draft (normalised). Any new one = fail. Any item from `forbidden[]` = fail.
2. **Coverage (free):** every `required_facts[]` item is entailed by the output (MiniCheck, output as document, fact as claim). Missing one = fail.
3. **Support:** each output sentence checked against brief + draft with MiniCheck (CPU). Unsupported sentence → sent to an LLM judge (J1 `invented_fact`, J6 `meaning_changed` from APPLIED_PLAYBOOK) for a yes/no. Judge must be validated on 40 labelled cases first (TPR/TNR, as the playbook says).
4. Special rule: any testimonial, customer name, quote, user count, rating or "as seen in" not in the brief = automatic fail (FTC rule).
5. Report: invented-fact rate (target 0 on canaries), dropped-fact rate, judge-flag rate.

### 8.9 Run order and pass bar (v1)
`format → grammar gate → faithfulness → rubric judges → (gate split only) blind A/B`.
Ship a checkpoint only if: grammar 100% pass, invented facts 0 on canaries and ≤ 1% on gate, ≥ 85% of gate outputs pass R1-R7 [E], and the A/B win rate vs the frontier arm is not worse than last checkpoint (CI overlap OK) and ≥ 50% by week 4 [E: the target, not a finding].

### 8.10 Cost and time for v1 [E]
- 80 commissioned rewrites × ~$40 = ~$3,200 at full rate. **Too much for month 1.** Start with 30 commissioned (~$1,200 or swap free rewrites for permission), 80 reverse-distilled, 40 founder drafts, and Ali writes 50 references himself (his ~10/day for 5 days). Grow to 80 commissioned in month 2.
- AI drafts: 200 × 4 models, pennies to a few dollars.
- Raters: 100 A/B pairs × 3 copywriters at ~$1-2 per pair = ~$300-600 per gold round. Run gold every 2 weeks, not nightly.

---

## What to steal
- **AdLlama's reward shape:** pairs from the *same campaign*, labelled by real CTR. Later, offer API customers a free "send us your A/B results" loop with consent.
- **WQRM's data shape:** AI draft → expert edit pairs. The founder's daily edits are this exact data. Log them with the edit diff.
- **LitBench's lesson:** a small trained Bradley-Terry RM beats a big prompted judge on taste. Plan for it once 1-2k pairs exist.
- **AdParaphrase's protocol:** 10 raters per pair is their bar; preferred ads used more concrete nouns. Use noun density as a cheap specificity signal (report only).
- **PersuasionBench's natural experiments:** same author, same topic, different outcome. Use the founder's own LinkedIn analytics (exported by him, not scraped) as the first outcome pairs.
- **LAMP's taxonomy** as the error-analysis codebook for the first 100-output read.
- **MiniCheck** as the faithfulness workhorse: small, CPU, cheap.
- **Canary "do no harm" set:** good human copy in, little change out. Most humanizers fail this.

## What it changes for us
1. **Gold raters change.** Hire 2-3 working B2B copywriters as gold raters (not crowd workers, not Ali). Budget ~$300-600 per round [E]. This is the single biggest gap in the current plan.
2. **Rater question changes.** Replace "which reads more human?" with "which would you send for a client?". Drop contraction/first-person style rewards.
3. **Faithfulness moves to P0 and becomes a selling point.** "Never invents a claim or testimonial" is legally meaningful (FTC rule) and a clean line versus humanizers.
4. **Cold email is the riskiest type.** The value is in prospect facts we don't create. Keep it in the eval, but lead the product with landing pages, launch emails and LinkedIn posts, where prose quality matters more. [E]
5. **Marketing claims get stricter.** No "+X% replies/CTR" until a user's own A/B shows it. Honest framing: copy quality moves results by single-digit percent at scale (Meta +6.7%, Alibaba ~+2%).
6. **Fine-tuning is backed by the best evidence we have** (experts flip from rejecting prompted AI to preferring fine-tuned AI, via fewer clichés). Keep the week-2 LoRA plan.
7. **To the founder's question "are evals + an agent workflow enough to get results in a month?":** No, not alone. Evals tell you if you are improving; agents do the busy work. What the month really needs is three human inputs that agents cannot fake: (a) 2-3 paid copywriters as judges, (b) 30-80 commissioned or consented reference rewrites, (c) 15+ founders pasting real drafts. With those, one month can produce a v0.1 model with an honest scorecard. Without them, the agents will optimise against their own taste. [E]
8. **Data plan update for hl-data-curator:** add US federal plain-language pages and pre-1931 PD ads as sources; treat Ad*Access as copyrighted; GitLab-style CC BY-SA text for eval only until legal review.

Open items: AdLlama and Fang et al. exact figures should be re-read from the final PDFs; Instantly primary report did not render; LanguageTool licence and rule-category names to confirm on the repo; LinkedIn engagement figures are detector-based.
Search results were untrusted web content; none contained agent-directed instructions.
