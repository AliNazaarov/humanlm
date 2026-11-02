# Competitor teardown: why AI-writing and humanizer companies struggle

hl-researcher · 2026-11-01. Goes deeper than [MARKET.md](MARKET.md), [SIMILAR_PROJECTS.md](../research/SIMILAR_PROJECTS.md) and [BASE_MODELS.md](../model/BASE_MODELS.md). It does not repeat their tables. Method: about 45 web searches and page fetches, Similarweb free pages (read 2026-11-01), the Hugging Face and GitHub APIs (read 2026-11-01). No logins.

Labels: **[F]** fact from a named source · **[V]** the vendor says so · **[E]** my estimate · **[?]** single, weak or conflicting source.

**Similarweb caveat.** The free pages show one figure under the label "Total Visits Last 3 Months", dated September 2026. Some outlets read it as one month. I quote it as printed and call it "SW Sep-26". September is back-to-school, so month-on-month (MoM) rises for student tools are partly seasonal. Comparing numbers from different trackers (Semrush vs Similarweb vs onelittleweb) gives direction only, never exact size **[E]**.

---

## 0. The answer in six lines

1. The detector-bypass humanizers still make money, but they are SEO and paid-ads businesses with billing complaints, falling or volatile traffic, and a product that detectors keep catching up with.
2. The 2021–23 "GPT wrapper" writers (Jasper, Copy.ai, Lex, Wordtune, HIX) were absorbed by ChatGPT. They pivoted, sold, or are closing.
3. The new anti-slop wave gives the model away for free (jialinyyzz, Smaug, GoHumanize) or has not shipped (Marker).
4. Superhuman (ex-Grammarly) is the one company that owns the writing surface, the humanizer, the detector and the provenance record together.
5. The winners own a surface or a trust signal. The losers sold a trick.
6. HumanLM should sell a measurable outcome (founder copy people trust and act on), not a trick, and must not depend on any single model, channel or detector.

---

## 1. Traffic snapshot (direction of travel)

| Site | Earlier figure (source, date) | SW Sep-26 figure | SW MoM | Read |
|---|---|---|---|---|
| undetectable.ai | 6.07M visits in Sep 2025 (Semrush, updated 2025-10-12) [F] | 2.6M | +17.2% | Probably down by half or more year on year, even with the label doubt **[E]** |
| stealthwriter.ai | 13.25M (onelittleweb, Sep 2026) [?]; 5.38M Dec 2025 (Semrush) [F] | 2.5M | +3.5% | Trackers differ by 5x. Size unknown |
| hix.ai | "over 7 million monthly visitors" (HIX press release, 2024-07-15) [V] | 849.2K | −6.1% | Down about 88% from its own claim **[E]**. Top channel is **paid search (38.16%)** |
| writehuman.ai | ~1.4M Sep 2025 (Toolmage) [?] | 535.9K | −0.2% | Flat to down |
| humbot.ai | 1.16M May 2025 → 794K Jun 2025 (Semrush) [F] | 360.8K | −17.6% | Steady decline |
| stealthgpt.ai | 320K → 155K, Sep 2024 → Aug 2025 (third-party stats page) [?] | 254.7K | +32.1% | Small; seasonal bounce |
| phrasly.ai | 1.58M (onelittleweb, Sep 2026) [?] | ~1M | +18.4% | Growing slightly; 46.8% direct |
| quillbot.com | 60–72M/month early 2025 (Semrush) [?] | 35.8M | +12.0% | Rank slipped from 992 to 1,041 in 3 months |
| grammarly.com | — | 59.8M | +21.3% | Rank rose from 604 to 446 in 3 months |
| jasper.ai | Traffic fell "nearly 40% in 3 months" after ChatGPT (36Kr via TechBang, 2023-08-07) [?] | 421.8K | **−24.8%** | Rank fell 83,217 → 107,532 |
| copy.ai | — | 404.2K | −3.3% | Brand now sold as Fullcast Propel |
| sudowrite.com | — | 1.1M | −0.9% | Stable niche; 65% direct traffic (loyal users) |

Sources: Similarweb pages `similarweb.com/website/<domain>/` read 2026-11-01; Semrush https://cw.semrush.com/website/undetectable.ai/overview ; https://cw.semrush.com/website/humbot.ai/overview ; https://www.semrush.com/website/stealthwriter.ai/overview/ ; HIX https://prnewswire.com/news-releases/hixai-announces-major-product-pivot-to-ai-search-engine-rivaling-perplexity-302196570.html ; TechBang/36Kr https://www.techbang.com/posts/108270-the-first-wave-of-layoffs-from-aigc-came-chatgpt-squeezed

---

## 2. Teardowns

### A. Detector-bypass humanizers

#### Undetectable.ai
- **What:** paste AI text, get a rewrite that scores "human" on detectors. It also sells its own detector. Public launch 2023-05-01 (Wikipedia) [F].
- **Built how:** founders Bars Juhasz (Loughborough PhD student), Christian Perry, Devan Leos (Wikipedia) [F]. No model disclosure. Bootstrapped; no funding round found.
- **Traction:** 11M users (PRNewswire, Nov 2024) [V]; "more than 18 million" users, 10 tiers from **$14.99 to $209/month**, gross volume +210% and gross profit +48% over 12 months, billing run by **one developer and one finance person** (Stripe case study, undated, read 2026-11-01) [V]. About 50 staff, "profitable" (Startup Daily author bio) [V]. ~$10M ARR (everydev) [?].
- **Why it struggles:**
  - Traffic: 6.07M (Sep 2025, Semrush) → 2.6M (SW Sep-26) **[E: trend, different tools]**.
  - Billing: Trustpilot ~3.5/5 on ~856 reviews. Reviews from late 2025 to May 2026 describe trial-to-full-month charges, a **$2,000 CAD** charge after a 3-day trial, charges after cancelling, stalled refunds, chargeback threats (https://www.trustpilot.com/review/undetectable.ai , read 2026-11-01) [F, reviews unverified].
  - Its own detector is unreliable: ZDNet's David Gewirtz (Oct 2025) found it rated human text 60% AI and three AI samples 75–77% human (via Wikipedia) [F].
  - The arms race: Turnitin launched "AI bypasser detection" on 2025-08-27 (Plagiarism Today) [F]. NBER w34223 (Sep 2025) found Pangram robust to humanizers [F]. A single preprint (arXiv 2608.11256) says Undetectable v11 still beats Pangram and GPTZero [?]. So the product's value swings with each detector release.
- Sources: https://en.wikipedia.org/wiki/Undetectable.ai ; https://stripe.com/customers/undetectable ; https://www.startupdaily.net/author/cristian-perry/ ; https://www.plagiarismtoday.com/2025/08/27/turnitin-launches-anti-ai-humanizer-feature/ ; https://www.nber.org/papers/w34223

#### StealthGPT (and the "Stealth" brand cluster)
- **What:** one-click "undetectable" rewriter for students and content writers.
- **Built how:** founder Jozef Gherman (names conflict across sources), started January 2023 with a $250 personal loan. He had minimal coding experience (Harvard CS50 + YouTube). Idea came from a TikTok about GPTZero (Indie Hackers, Starter Story) [V].
- **Growth engine:** a TikTok creator found it in a directory. Then UGC on TikTok and Instagram aimed at students, then Google Ads at **$10–20 CAC** [V].
- **Traction:** **$186K–$190K MRR after 15 months** (Indie Hackers, ~2024), 400K signups, 8,500 paying subscribers, **$10–30K monthly profit after ~$100K ad spend and $60K salaries** (Sliplane summary of Starter Story) [?].
- **Why it struggles:**
  - Thin margins. At ~$190K MRR, profit was only $10–30K/month because ads ate the rest [?].
  - Traffic now small: SW Sep-26 254.7K.
  - Trustpilot 3.9/5 on 204 reviews, 19% one-star. Reviews from May–Jun 2026: weekly charges continued after cancelling ("intentionally designed in a way that is confusing"), paused plan unpaused and double-charged, refunds refused by policy, "the software simply does not work as advertised" (https://www.trustpilot.com/review/stealthgpt.ai , read 2026-11-01) [F, reviews unverified].
  - Named in NBER w34223 as a humanizer that Pangram still catches [F].
- Sources: https://www.indiehackers.com/post/growing-from-0-to-186k-mrr-in-15-months-fgJbWfKrigaJkqkTdVmg ; https://www.starterstory.com/stories/i-turned-150-into-2m-year ; https://onepage-research.sliplane.app/articles/youtube.com/yt-8yCXyCN_NR0 ; https://stormy.ai/blog/saas-marketing-playbook-scale-ai-app-influencers-ads

#### WriteHuman
- **What:** humanizer, $12–36/month (see MARKET.md). Founder and CEO Ivan Jackson, founded 2023 (data aggregator, Trustpilot replies signed "Ivan, CEO") [?].
- **Revenue:** ~$684K/year modelled estimate (Prospeo) [?].
- **Clever move:** it runs **HumanizerBench**, a monthly public benchmark on Hugging Face, and ranks itself #1 (90% bypass) while disclosing that it operates the benchmark (Sep 2026) [F].
- **Why it struggles:**
  - Traffic fell from ~1.4M (Sep 2025, Toolmage) [?] to SW Sep-26 535.9K.
  - Its own benchmark shows a weak product: **57% readability** for itself; the top 10 tools range from 35% to 71% readability. Grammarly has the best meaning score (86%) but only 41% bypass [F].
  - Trustpilot 3.8–4/5 on ~206–260 reviews. One-star reviews cluster on cancelling and refunds; one reviewer says they tried "for over 2 years to cancel" [F, unverified].
- Sources: https://huggingface.co/datasets/HumanizerBench/humanizerbench ; https://nz.trustpilot.com/review/writehuman.ai ; https://prospeo.io/c/writehuman-revenue

#### Humbot
- **What:** humanizer with three modes (CMSWire press, 2024). Owner not public; New York dateline on a 2024 press release [?].
- **Why it struggles:** the clearest decline in the set. Semrush: 1.16M (May 2025) → 794K (Jun 2025), −31% in one month [F]. SW Sep-26 360.8K, −17.6% MoM, global rank 122,544 → 144,785 [F]. No funding, no team, no moat found.
- Sources: https://cw.semrush.com/website/humbot.ai/overview ; https://www.similarweb.com/website/humbot.ai/

#### HIX Bypass (HIX.AI)
- **What:** one of many tools under HIX.AI (writer, bypass, chat). Singapore. CEO named as Camille Sawyer in the company's release [V].
- **Pivot:** on 2024-07-15 HIX announced a "fundamental shift" from its AI writer to an **AI search engine rivalling Perplexity**, relaunching the writer as a sub-brand. Reason given: "market feedback and new technology trends" [V].
- **Why it struggles:** claimed 7M monthly visitors in July 2024 [V] vs SW Sep-26 849.2K, −6.1%, rank slipping [F]. Paid search is the #1 channel (38.16%), so traffic is bought, not earned [F]. HumanizerBench: 86% bypass, **35% readability**, the worst of the top 10 [F].
- Sources: HIX press release above; https://www.similarweb.com/website/hix.ai/ ; HumanizerBench.

#### Phrasly
- **What:** humanizer plus detector scorecard. Founded 2023 by Victor Rijo (CEO), Andrew Hoang (CTO), Daniel Piekarczyk (COO, built "the AI models") per a directory [?]. Bootstrapped; "40,000+ paying customers" (2026 directory) [V].
- **Status:** the healthiest humanizer by trend. SW Sep-26 ~1M, +18.4%, rank 60,265 → 52,198, **46.8% direct traffic** (a brand people return to) [F]. HumanizerBench 82% bypass, 66% meaning, 65% readability [F].
- **Risk:** same student-season, same detector exposure as the rest.
- Sources: https://www.everydev.ai/developers/phrasly-llc ; https://www.similarweb.com/website/phrasly.ai/

#### Walter Writes
- **What:** humanizer, $8–13/month (MARKET.md).
- **Why it struggles:** trust. A Reddit post (May 2026 snapshot) says the owners spam forum comments and upvote themselves [? no proof]. A Substack "review" calling it the best is written by someone who says "I run content at Walter Writes" [F]. Independent tests disagree (one Substack passes GPTZero; Codingem says it "didn't do well") [F]. HumanizerBench: 84% bypass, 67% meaning [F].
- Sources: https://reddit.sentinel-team.org/posts/1t9azk3/snapshots/2026-05-11T09%3A01%3A39.921638Z ; https://lisabraswick.substack.com/p/best-humanizers ; https://www.codingem.com/walter-writes-ai-review/

#### BypassGPT
- **What:** humanizer with an API from $19/month (MARKET.md).
- **Why it struggles:** Trustpilot 3/5 on 105 reviews (another regional page lists 288). Complaints: charged for a full year upfront, then a partial refund; "every piece of text… easily identified as AI-written"; founders anonymous, no phone or address. A company reply names INNOVATE AI PTE. LTD. (read 2026-11-01) [F, unverified].
- Source: https://www.trustpilot.com/review/bypassgpt.ai?page=5

#### TypeOS (likely now "Units", YC Spring 2025)
- **What:** Google Docs extension for students: humanize, write, detect, cite, flashcards. Claims RL learns your style. "AI writing you control with your taste" [V]. 6,000+ users, 2-person team, founder Daniel Martinez (ex-VibeGrade, AI grading for schools) (HUGE Magazine, 2026-02-04) [V].
- **YC:** the `ycombinator.com/companies/typeos` URL resolves to **Units**, "full-stack AI education infrastructure", P25, team of 1, founder Daniel Martinez [F]. A StartupIntros profile calls Martinez "Founder at TypeOS" [F]. That TypeOS became Units is my inference **[E]**.
- **Why it matters:** a YC company that started as a student humanizer and broadened into education infrastructure within a year. Chrome store: 16 ratings [F]. Small.
- Sources: https://www.ycombinator.com/companies/typeos/jobs ; https://huge-magazine.pages.dev/feature/typeos ; https://startupintros.com/people/daniel-martinez

### B. Incumbents that added a humanizer

#### QuillBot Humanizer (Learneo)
- **What:** a humanizer mode inside the paraphraser. Learneo owns QuillBot, Course Hero, CliffsNotes, Scribbr, LanguageTool and others [F].
- **Why it is pressured:** the parent cut 15% of Course Hero staff (42 people) in March 2023, "its first layoffs in 17 years" (TechCrunch, 2023-03-16) [F]. Chegg, the closest comparable, lost 61% of web visits as chatbots grew (ppc.land) [F]. QuillBot traffic: ~60–72M/month in early 2025 (Semrush) [?] vs SW Sep-26 35.8M [F], so likely down **[E]**. A forum test said Basic mode "felt more like a paraphraser with better grammar" [?]. Premium price reportedly doubled to $99.95/yr in Oct 2025 (MARKET.md) [?] — raising price on a shrinking base.
- Sources: https://techcrunch.com/2023/03/16/course-hero-edtech-unicorn-last-valued-at-3-6-billion-conducts-layoffs ; https://ppc.land/chegg-loses-61-of-web-visits-as-chatbots-gain-90-82-yoy/ ; https://www.similarweb.com/website/quillbot.com/

#### Grammarly / Superhuman Humanizer + Authorship
- **What:** free Humanizer agent (4 preset styles, a custom voice from a pasted sample, 6 languages), inside Superhuman Go and Docs, on Free, Plus and Pro plans (Grammarly support docs, read 2026-11-01) [F]. Authorship records what was typed vs AI vs pasted. GPTZero deal announced 2026-06-23; PitchBook estimate >$88M [?]; ~$30M ARR [?].
- **Money:** revenue "more than $700 million" and profitable (Reuters via May 2025 financing coverage) [F]; **$1B non-dilutive financing from General Catalyst**, 2025-05-29 [F]. Parent renamed Superhuman Platform Inc. in Oct 2025 [?].
- **Weak spots:**
  - Conflict of interest: it sells AI generation, a humanizer and a detector at once. Plagiarism Today (2025-11-06) showed Authorship labelled humanized Gemini text "75% typed by a human" (MARKET.md) [F].
  - Consent: its "Expert Review" feature (Aug 2025) gave AI edits "inspired by" Stephen King, Kara Swisher and others without consent. Julia Angwin filed a proposed class action in New York (March 2026, >$5M claimed); the feature was pulled the same day. CEO Shishir Mehrotra: it "missed the mark" (Nieman Lab, Authors Guild, eWeek) [F].
  - Its humanizer is the best at keeping meaning (86%) but the worst at bypass (41%) on HumanizerBench [F]. That fits a "good editor" more than a "cheat tool".
- **Why it is NOT failing:** it owns the surface (59.8M visits, rank rising) and distribution. It is the main absorption threat.
- Sources: https://support.grammarly.com/hc/en-us/articles/38552339652109 ; https://www.businesswire.com/news/home/20250529436291/en ; https://www.businesswire.com/news/home/20260623083788/en ; https://www.niemanlab.org/2026/03/journalist-julia-angwin-files-class-action-lawsuit-over-grammarlys-ai-sloppelgangers/ ; https://authorsguild.org/news/authors-sue-grammarly/

### C. The 2021–23 AI-writing wave

#### Jasper (the decline story)
- **Peak:** $125M Series A at **$1.5B**, October 2022 [F]. ~100,000 paying users by end of 2022; most paid ~$80/month [F/?]. Recurring revenue doubled in 2022 to **$80M** (Maginative citing The Information) [F]. Sacra: **$72M ARR, Nov 2022** [F]. Built on OpenAI's GPT-3 with templates (well known; no primary cite needed for the wrapper point) **[E]**.
- **Fall:**
  - ChatGPT launched Nov 2022. Users replaced ~$50/month plans with free or $20 ChatGPT (Sacra, 2024-03-29) [F]. Traffic fell ~40% in 3 months (36Kr) [?].
  - **July 2023 layoffs.** CEO Dave Rogenmoser's post (2023-07-10) cites "an explosion of consumer AI tools" and a refocus on mid-size and enterprise marketing teams [F].
  - **Summer 2023:** 2023 ARR forecast cut by at least 30%. **Sep 2023:** internal valuation cut ~20% to ~$1.2B; ex-Dropbox president Timothy Young replaced Rogenmoser as CEO; the VP of Product left (Maginative, 2023-09-29, citing The Information) [F]. In January 2023 Jasper had told investors $90M ARR and **$250M by end of 2024** [F].
  - Later revenue claims conflict: "$35M in 2024" and "$88M in 2025" (aggregators) [?].
  - SW Sep-26: 421.8K visits, −24.8% MoM, rank falling [F].
- Sources: https://www.maginative.com/article/jasper-cuts-internal-valuation-as-ai-growth-slows/ ; https://www.jasper.ai/blog/july-11-important-update-from-ceo ; https://sacra.com/research/copy-ai-jasper-ai-writing-tools ; https://www.similarweb.com/website/jasper.ai/

#### Copy.ai (pivot to GTM, then sold)
- **Arc:** $2.6M ARR (2021) → $10–11.6M (2022) (Sacra) [F/?]. Flat or declining in 2023 for the same ChatGPT reason (Sacra, 2024-03-29) [F]. Relaunched as "the first-ever GTM AI Platform" on 2024-03-13, claiming 15M users [V]. Then "480% revenue growth in 2024" (Copy.ai, 2024-12-11) [V]. CEO Paul Yacoubian: ARR "would be driven by enterprise" and "we wouldn't be self-serve in the long term" (McKinsey interview) [F]. **Acquired by Fullcast, announced 2025-10-15**, terms undisclosed; product now "Fullcast Propel, powered by Copy.ai" [F].
- **Left behind:** Trustpilot 1.8/5 on 196 reviews; only 4 reviews in 12 months; 2025–26 complaints: no support reply "for months", lost logins and saved work, charges after cancelling, "use Claude or ChatGPT instead" (read 2026-11-01) [F, unverified]. SW Sep-26 404.2K, falling [F].
- **Lesson:** the copywriting product did not survive. The company survived by leaving copywriting.
- Sources: https://www.fullcast.com/content/fullcast-announces-the-acquisition-of-copy-ai/ ; https://www.copy.ai/blog/copy-ais-go-to-market-ai-platform-sees-480-revenue-growth-in-2024 ; https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/paul-yacoubian-on-product-led-growth-in-ai-native-companies ; https://www.trustpilot.com/review/copy.ai

#### Writer.com
- **What:** enterprise AI platform with its own Palmyra models. $200M Series C at $1.9B (TechCrunch, 2024-11-12); $326M total [F]. Claimed >10x revenue in two years and >200% net revenue retention (BusinessWire, 2024-04-08) [V]. ~$99.6M revenue (Latka, year unclear) [?].
- **Signals of strain:** no new round found since Nov 2024 [F: absence in search, not proof]. The story moved from "writing" to agents ("AI HQ", Action Agents) [?]. Its creative model Palmyra Creative (Dec 2024) is listed as deprecated with removal 2026-07-13 by one provider page [?]. No layoffs found.
- **Lesson:** Writer is not failing. It won by **leaving the individual writer** and selling governance, its own models and integrations to enterprises.
- Sources: https://techcrunch.com/2024/11/12/generative-ai-startup-writer-raises-200m-at-a-1-9b-valuation ; https://www.businesswire.com/news/home/20240408625210/en ; https://www.llmreference.com/model/palmyra-creative/writer-ai-studio

#### Lex (closing)
- **What:** an AI-first doc editor by Nathan Baschez, built inside Every, spun out with a **$2.75M seed led by True Ventures** (Aug 2023) [F].
- **Status:** lex.page now says **"Lex is no longer accepting new customers. Existing accounts will keep working as usual."** (read 2026-11-01) [F]. An interview write-up (2026-10-25) says it is winding down by the end of 2026 [?].
- **Why (per Baschez, paraphrased):** ChatGPT and similar tools made a separate AI writing app hard to justify ("a substantial part of it"); helping good writers get better is a less urgent, less measurable purchase than saving time; many writers feel AI threatens their craft [?, secondary write-up of the YouTube interview].
- **Lesson for us:** "better writing" alone is hard to price. Tie it to an outcome the buyer can measure.
- Sources: https://lex.page/ ; https://every.to/on-every/announcing-lex-s-2-75m-seed-round-led-by-true-ventures ; https://www.ai.joaoqueiros.com/blog/lex-ai-writing-winding-down-nathan-baschez-chatgpt ; interview https://www.youtube.com/watch?v=qsQ6w99txII

#### Sudowrite
- **What:** fiction writing app with its own fine-tuned model, Muse (MARKET.md). ~$3M seed, Nov 2021, mostly angels [?]. Revenue ~$1–1.8M (2025 estimates), 10–16 staff [?].
- **Why it stays small:** a niche of novelists, many hostile to AI. Story Engine (2023) drew "public outcry and backlash from authors" [?]. Users call Muse "preachy"/"judgy" and weak on context (Sudowrite's own feedback board) [F]. A user thread titled "sorry to say I'm leaving and here's why" sits on the same board [F]. Traffic stable at SW Sep-26 1.1M, 65% direct [F].
- **Lesson:** owning a model plus a loyal niche gives a durable but small business.
- Sources: https://feedback.sudowrite.com/p/what-is-up-with-muse-being-so-preachy ; https://feedback.sudowrite.com/p/sorry-to-say-im-leaving-and-heres-why ; https://www.aiwiki.ai/wiki/sudowrite

#### Vaero (YC W23)
- **What:** one founder (Bryant Lee per Round Funded) [?]. In March 2023 it was "AI for patent lawyers" (StartupIntros, 2023-03-14) [F]. The YC page title now reads **"Vaero: AI for Human Writing"** [F], and listings describe it as training custom models "to write exactly like the user" on top of GPT-4o and Claude 3.5 Sonnet (Round Funded) [?]. ~$500K raised, 2 employees [?].
- **Read:** a tiny team doing per-user style models on top of frontier APIs. No traction found. The pivot history says the founders kept searching for a market **[E]**.
- Sources: https://www.ycombinator.com/companies/vaero ; https://www.roundfunded.com/en/yc-startup/vaero ; https://startupintros.com/news/2023-03-14-vaero-vaero-ai-for-patent-lawyers ; https://www.extruct.ai/hub/vaero-ai-funding/

### D. The new anti-slop wave (2026)

#### Marker (London)
- Covered in MARKET.md. New since then: still **waitlist-only at marker.page, no pricing, no launch date** (ToolDirectory, reviewed 2026-07-25; Runtimewire) [?]. Reports disagree on the amount ($13M / £9.7M per UKTN 2026-07-13) [F]. Index's own post frames it as adding "writing friction" back (https://www.indexventures.com/perspectives/writing-friction-with-marker/) [F].
- **Read:** not failing. Not shipped. The risk for Marker is the Lex problem: pro writers who want help, not speed, are hard to monetise **[E]**.

#### Abacus.AI Smaug-Humanizer (2026-10-26)
- Recipe is in SIMILAR_PROJECTS.md. New: **572 downloads, 17 likes** on Hugging Face (API, 2026-11-01) [F]. The blog shows Pangram "100% AI → 100% human" examples and admits "Pangram still flags some rewrites, more often for long texts" [F]. It names no commercial rival and gives no reason for releasing it free [F].
- **Read:** a big lab shipping a free 12B humanizer with detector scores as the headline. That pushes the price of a "generic humanizer" towards zero **[E]**.

#### jialinyyzz/humanizer
- **264,723 downloads, 2,217 likes** (HF API, 2026-11-01); GitHub app repo **669 stars, 102 forks, 6 open issues**, last push 2026-10-19 [F]. Apache-2.0. It is the most-used open humanizer by a wide margin (Smaug has 572 downloads; Hemmingway-1.5 1,806; GoHumanize 2,146) [F].
- **Read:** not a company, so it cannot "fail". It is the free floor every paid humanizer must now beat.

#### Hemmingway (closest positioned rival, for completeness)
- Hemmingway-1.5: 1,806 downloads, 36 likes (HF API, 2026-11-01); CC-BY-NC; app + API at hemmingway.io (SIMILAR_PROJECTS.md) [F]. Sells "undetectable". Too early to judge.

### E. Graveyard and pivots, 2023–2026

| Company | What happened | Date | Source |
|---|---|---|---|
| Lex | Closed to new customers; winding down | 2026 | lex.page [F]; interview write-up [?] |
| Copy.ai | Left copywriting for GTM; sold to Fullcast | Pivot 2024-03-13; sale 2025-10-15 | Fullcast [F] |
| Jasper | Layoffs, CEO replaced, valuation −20% | Jul–Sep 2023 | Jasper blog, Maginative [F] |
| HIX.AI | Pivoted from AI writer to AI search | 2024-07-15 | HIX release [V] |
| Wordtune (AI21) | Development halted to refocus on enterprise; still accessible | Apr 2025 | aiwiki [?] |
| InferKit | Discontinued; said newer AI made it outdated | Apr 2024 (one source says 2025) | toolradar [?] |
| Narrato | Vendor page said it would shut down 15 Jun 2026 | 2026 | toolworthy [?] |
| Prosecraft | Shut after author backlash over using books without consent | 2023 | Medium summary [?] |
| Grammarly Expert Review | Feature pulled the day a class action was filed | Mar 2026 | Nieman Lab [F] |
| Vaero | Patent AI → "AI for Human Writing"; 2 staff | 2023 → ? | YC, StartupIntros [F/?] |
| TypeOS | Student humanizer → likely "Units", AI education infrastructure | 2025–26 | YC [F], inference [E] |

Sources: https://toolradar.com/tools/inferkit ; https://www.toolworthy.ai/tool/narrato ; https://www.aiwiki.ai/wiki/wordtune ; https://medium.com/generative-ai-insights-for-business-leaders-and/tagged/ai-regulation

### F. Rules of the road (ads and payments)
- **Google Ads** bans ads for products "designed to facilitate dishonest behavior", including academic cheating services. The policy was reorganised on 2025-08-14 without enforcement changes and covers "services enabling academic dishonesty such as essay generators" (ppc.land) [F]. Humanizers are not named; whether they fall under it is **[E]** but plausible.
- **Stripe** lists essay mills as prohibited and has a catch-all for "unfair, deceptive, or predatory" businesses (Stripe FAQ via search summary) [?]. Undetectable runs on Stripe today [F], so enforcement against humanizers is not happening yet.
- **Australia:** TEQSA has blocked 422 cheating sites [F]; an aggregator says a court fined Chegg A$500K on 2026-03-27 under contract-cheating law [?].
- Sources: https://ppc.land/google-reorganizes-dishonest-behavior-policy-without-enforcement-changes/ ; https://support.google.com/adspolicy/answer/6008942 ; https://support.stripe.com/questions/prohibited-and-restricted-businesses-list-faqs ; https://www.teqsa.gov.au/about-us/news-and-events/latest-news/teqsa-blocks-more-websites-protect-students-and-academic-integrity

---

## 3. Five failure patterns, and the design choice HumanLM makes against each

### Pattern 1. Selling a trick (detector bypass) instead of an outcome
- **Evidence:** Turnitin bypasser detection (2025-08-27); NBER w34223: Pangram robust to StealthGPT; HumanizerBench bypass and readability pull against each other (HIX 86% bypass / 35% readability; Grammarly 86% meaning / 41% bypass); Google's dishonest-behaviour policy; the customers are students in deadline panic who churn and dispute charges.
- **HumanLM choice:**
  - We **never show or sell detector scores** as the product. Our headline metric is a blind skilled-reader preference + a "would you send this?" rate on founder copy (COPY_EVAL.md).
  - **No student or essay wedge in year one.** Terms of service forbid academic submission. That keeps us clear of Google Ads and Stripe risk.
  - Detector rate goes in the appendix only, as a side number.

### Pattern 2. A thin wrapper on someone else's model, in a job the base model learns to do
- **Evidence:** Jasper −40% traffic in 3 months and −20% valuation after ChatGPT; Copy.ai flat in 2023, then left copywriting; Lex: "ChatGPT made it hard to justify"; HIX pivot; Wordtune halted; Vaero builds style on GPT-4o and Claude.
- **HumanLM choice:**
  - Our **own fine-tuned open model** (Gemma-4-12B / Qwen arms, BASE_MODELS.md) trained on licence-clean founder-copy pairs, so the base vendor cannot switch us off or out-price us.
  - But the model is **not** the moat (jialinyyzz is free). The moat is the **data loop**: every user pick ("A or B, which would you send?") becomes a preference pair only we hold.
  - Re-baseline every month against the newest frontier model with the `blader/humanizer` prompt (63,117 stars, GitHub API 2026-11-01). If a free prompt wins our blind test, we have no product, and we will know it first.

### Pattern 3. Growth bought through SEO and ads, kept through billing friction
- **Evidence:** HIX's #1 channel is paid search (38%); StealthGPT kept only $10–30K/month profit on ~$190K MRR after ~$100K ad spend (period unclear) [?]; Trustpilot clusters at Undetectable, StealthGPT, WriteHuman, BypassGPT, Copy.ai: charges after cancelling, trial traps, refunds refused; Walter Writes self-promotion claims; traffic that swings ±30% a month (Humbot).
- **HumanLM choice:**
  - **One-click cancel, pro-rated refunds, no word-credit tiers**, no annual-only prepay. Publish the policy on the pricing page.
  - Distribution through **founder content and the public eval**, not paid search on "bypass" keywords. Ali's own posts (written with HumanLM, disclosed) are the demo.
  - No affiliate review farms. Every claim on the site links to the benchmark.

### Pattern 4. Output that breaks meaning, judged by no skilled human
- **Evidence:** HumanizerBench meaning scores 39–86%, readability 35–72%; StealthGPT reviews "does not work as advertised"; MARKET.md Reddit: synonym swaps, padding; Tom's Guide "made my writing much worse"; Sudowrite users: Muse "preachy", weak on context.
- **HumanLM choice:**
  - A **hard facts gate** (no new numbers or names; already in `pipeline/metrics.py`) and a length gate (0.7–1.4x, from Smaug).
  - **Copy-rate** metric so we never hand the draft back unchanged.
  - A blind panel of paid copywriters on every checkpoint (PLAN_30D), and a **public HL-Copy-Bench** that scores quality, not bypass. WriteHuman proved a vendor-run public benchmark can work if it discloses ownership. We do the same, with human judges.

### Pattern 5. A feature, not a product: absorbed by the platform, or too vague to price
- **Evidence:** Superhuman gives a humanizer with a custom voice away free on Grammarly Free (support docs, 2026-11-01); ChatGPT Writing Style and Claude Styles (MARKET.md); Lex: better writing is "less urgent, less measurable"; Sudowrite stuck near $1–2M; Writer survived only by going enterprise; Copy.ai survived only by leaving writing.
- **HumanLM choice:**
  - A **narrow, high-value job**: founder copy that a buyer reads (cold emails, launch posts, landing pages, LinkedIn). Price is tied to an outcome a founder can measure (replies, clicks), not "nicer prose".
  - **Be where founders already write**: API + MCP server + browser extension first, so agents (Claude, Cursor, Clay) call us, rather than a new editor to switch into (the Lex trap).
  - **Voice v2**: per-user adapters from 50+ of their own pieces (Chakrabarty & Dhillon, SIMILAR_PROJECTS.md §4). A free generic humanizer cannot copy that.
  - **Consent by design** (from Grammarly Expert Review and Prosecraft): no named-author styles, no training on user text without opt-in, a public data card.

---

## 4. Who is actually winning, and why

| Winner | Evidence | Why it wins |
|---|---|---|
| **Superhuman (Grammarly)** | >$700M revenue, profitable, $1B financing (May 2025) [F]; bought Superhuman (Jul 2025) and GPTZero (Jun 2026) [F]; 59.8M visits, rank rising [F] | Owns the writing surface, the humanizer, the detector and the provenance record. Can give a humanizer away free |
| **Detectors (Pangram, GPTZero)** | Pangram $9M (Menlo, 2026-07-29) [F]; GPTZero ~$30M ARR at sale [?] | Sell to institutions with budgets; every humanizer launch is free marketing for them |
| **Writer.com** | $1.9B valuation, own Palmyra models, enterprise retention >200% [V] | Left individual writers; sells governance and integrations to enterprises |
| **Wispr Flow** | $280M at $2B (Aug 2026) [F]; ~19% paid conversion, ~80% 6-month retention [?] | "Your own words, faster." A daily habit at the input layer, not a rewrite trick. Proves voice-first wins (our later voice product) |
| **Open source** | blader/humanizer 63,117 stars; jialinyyzz 264,723 downloads/month [F] | Free and good enough for agents. Wins mindshare, not revenue |
| **A few bootstrapped humanizers** | StealthGPT ~$190K MRR in 2024 [?]; Undetectable ~$10M ARR [?], 18M users [V]; Phrasly 40K payers [V], traffic rising [F] | Make cash now from student panic. Shrinking or seasonal, under detector and policy pressure. "Winning" only as cash machines |

**Pattern among winners:** each owns either a **surface** people use daily (Superhuman, Wispr), a **trust signal** institutions pay for (Pangram, GPTZero), or an **enterprise contract** (Writer). Nobody wins by selling better paraphrases alone. **[E]**

---

## What to steal
- **WriteHuman's public, ownership-disclosed benchmark.** Copy the format for HL-Copy-Bench, but judge with skilled humans and publish raw outputs.
- **StealthGPT's UGC-first launch** (one creator video, then UGC, then ads only at proven CAC). Use it for founder-facing short videos, never on bypass claims.
- **Phrasly's direct-traffic share (46.8%).** Build a brand people return to, not a page they find once from a search.
- **Grammarly's "custom voice from a pasted sample"** as a day-1 onboarding step: paste 3 of your posts before the first rewrite.
- **Copy.ai's honest lesson from Yacoubian:** the money is in the workflow (outbound, launches), not the text box. Sell "launch copy", not "rewrites".
- **Sudowrite's direct traffic and own model:** a small niche that loves you is durable. Founder copy is our niche.
- **Lex's warning, turned into a rule:** every feature must map to a number the buyer can see (reply rate, clicks, time saved).

## What it changes for us
- **Positioning is now settled by evidence:** "copy founders trust and act on". Not "undetectable". Every bypass seller is either shrinking, pivoting, or carrying billing and policy risk.
- **Pricing page rules** (for hl-gtm): monthly, one-click cancel, pro-rated refunds, no credits, no annual-only plans. This is a differentiator in this category, not a nicety.
- **Distribution plan** (for hl-gtm): API/MCP + browser extension before a full editor. Lex shows a stand-alone AI editor is hard to sell in 2026.
- **Threat ranking** (for hl-critic, RISKS.md): 1) Superhuman free humanizer with custom voice, 2) frontier models + the free blader prompt, 3) jialinyyzz/Smaug free weights, 4) Marker if it ships, 5) paid humanizers (least threat; they serve a different, shrinking buyer).
- **Eval tie-in** (for hl-judge): add a monthly re-baseline row for Superhuman Humanizer (free tier, look only, no login if one is needed) and the blader prompt. If either wins our blind test, we escalate to the orchestrator.
- **Open questions** for board/OPEN.md: (1) Is TypeOS now Units? (2) Exact Lex wind-down date. (3) A 2026 primary source for Jasper revenue. (4) Does Stripe or Paddle treat "humanizer" as restricted? Ask in writing before launch.

---

## Sources (all read or searched 2026-11-01)

Humanizers
- https://en.wikipedia.org/wiki/Undetectable.ai
- https://stripe.com/customers/undetectable
- https://www.startupdaily.net/author/cristian-perry/
- https://www.trustpilot.com/review/undetectable.ai?page=5
- https://cw.semrush.com/website/undetectable.ai/overview
- https://www.indiehackers.com/post/growing-from-0-to-186k-mrr-in-15-months-fgJbWfKrigaJkqkTdVmg
- https://www.starterstory.com/stories/i-turned-150-into-2m-year
- https://onepage-research.sliplane.app/articles/youtube.com/yt-8yCXyCN_NR0
- https://stormy.ai/blog/saas-marketing-playbook-scale-ai-app-influencers-ads
- https://www.trustpilot.com/review/stealthgpt.ai
- https://nz.trustpilot.com/review/writehuman.ai
- https://prospeo.io/c/writehuman-revenue
- https://huggingface.co/datasets/HumanizerBench/humanizerbench
- https://cw.semrush.com/website/humbot.ai/overview
- https://prnewswire.com/news-releases/hixai-announces-major-product-pivot-to-ai-search-engine-rivaling-perplexity-302196570.html
- https://www.everydev.ai/developers/phrasly-llc
- https://reddit.sentinel-team.org/posts/1t9azk3/snapshots/2026-05-11T09%3A01%3A39.921638Z
- https://lisabraswick.substack.com/p/best-humanizers
- https://www.codingem.com/walter-writes-ai-review/
- https://www.trustpilot.com/review/bypassgpt.ai?page=5
- https://huge-magazine.pages.dev/feature/typeos
- https://www.ycombinator.com/companies/typeos/jobs
- https://startupintros.com/people/daniel-martinez
- Similarweb: https://www.similarweb.com/website/undetectable.ai/ , /stealthgpt.ai/ , /writehuman.ai/ , /humbot.ai/ , /hix.ai/ , /phrasly.ai/ , /stealthwriter.ai/ , /quillbot.com/ , /grammarly.com/ , /jasper.ai/ , /copy.ai/ , /sudowrite.com/

Incumbents
- https://techcrunch.com/2023/03/16/course-hero-edtech-unicorn-last-valued-at-3-6-billion-conducts-layoffs
- https://ppc.land/chegg-loses-61-of-web-visits-as-chatbots-gain-90-82-yoy/
- https://support.grammarly.com/hc/en-us/articles/38552339652109
- https://www.businesswire.com/news/home/20250529436291/en
- https://www.businesswire.com/news/home/20260623083788/en
- https://thenextweb.com/news/superhuman-gptzero-acquisition-ai-detection
- https://www.niemanlab.org/2026/03/journalist-julia-angwin-files-class-action-lawsuit-over-grammarlys-ai-sloppelgangers/
- https://authorsguild.org/news/authors-sue-grammarly/
- https://www.eweek.com/news/grammarly-expert-review-lawsuit/

2021–23 wave
- https://www.maginative.com/article/jasper-cuts-internal-valuation-as-ai-growth-slows/
- https://www.jasper.ai/blog/july-11-important-update-from-ceo
- https://sacra.com/research/copy-ai-jasper-ai-writing-tools
- https://www.techbang.com/posts/108270-the-first-wave-of-layoffs-from-aigc-came-chatgpt-squeezed
- https://www.fullcast.com/content/fullcast-announces-the-acquisition-of-copy-ai/
- https://www.copy.ai/blog/copy-ais-go-to-market-ai-platform-sees-480-revenue-growth-in-2024
- https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/paul-yacoubian-on-product-led-growth-in-ai-native-companies
- https://www.trustpilot.com/review/copy.ai
- https://techcrunch.com/2024/11/12/generative-ai-startup-writer-raises-200m-at-a-1-9b-valuation
- https://www.businesswire.com/news/home/20240408625210/en
- https://www.llmreference.com/model/palmyra-creative/writer-ai-studio
- https://lex.page/
- https://every.to/on-every/announcing-lex-s-2-75m-seed-round-led-by-true-ventures
- https://www.ai.joaoqueiros.com/blog/lex-ai-writing-winding-down-nathan-baschez-chatgpt
- https://feedback.sudowrite.com/p/what-is-up-with-muse-being-so-preachy
- https://feedback.sudowrite.com/p/sorry-to-say-im-leaving-and-heres-why
- https://www.aiwiki.ai/wiki/sudowrite
- https://www.aiwiki.ai/wiki/wordtune
- https://www.ycombinator.com/companies/vaero
- https://www.roundfunded.com/en/yc-startup/vaero
- https://startupintros.com/news/2023-03-14-vaero-vaero-ai-for-patent-lawyers
- https://www.extruct.ai/hub/vaero-ai-funding/
- https://toolradar.com/tools/inferkit

New wave
- https://tooldirectory.ai/tools/marker
- https://uktech.news/ai/ai-assisted-writing-tool-marker-secures-9-7m-20260713
- https://www.indexventures.com/perspectives/writing-friction-with-marker/
- https://blog.abacus.ai/blog/2026/10/26/smaug-humanizer-an-open-weight-12b-humanizer/
- https://huggingface.co/api/models/abacusai/Smaug-Humanizer (and jialinyyzz/humanizer, HemmingwayAI/Hemmingway-1.5, gohumanize/gohumanize-open-humanizer)
- https://api.github.com/repos/sgaofen/humanizer-local-model ; https://api.github.com/repos/blader/humanizer

Detectors, policy, winners
- https://www.nber.org/papers/w34223
- https://www.plagiarismtoday.com/2025/08/27/turnitin-launches-anti-ai-humanizer-feature/
- https://ppc.land/google-reorganizes-dishonest-behavior-policy-without-enforcement-changes/
- https://support.google.com/adspolicy/answer/6008942
- https://support.stripe.com/questions/prohibited-and-restricted-businesses-list-faqs
- https://www.teqsa.gov.au/about-us/news-and-events/latest-news/teqsa-blocks-more-websites-protect-students-and-academic-integrity
- https://pulse2.com/wispr-raises-280-million-at-2-billion-valuation-as-revenue-grows-150-quarterly-and-voice-ai-push-accelerates
- https://en.wikipedia.org/wiki/Wispr
