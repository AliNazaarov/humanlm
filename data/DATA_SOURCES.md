# HumanLM data sources: pre-generative-AI human text

Researched 2026-11-01. Status tags: [V] verified on the source page this session, [S] from a secondary write-up, [?] not verified or from memory. Not legal advice; get a lawyer to sign off before any commercial training run.

Practical cutoffs: ChatGPT is Nov 2022, but GPT-3 API text (Jasper, Copy.ai, article spinners) was in the wild from mid-2020 and 2021. For web-scraped text use a hard cutoff of mid-2021. For curated sources with trustworthy timestamps (books, Wikipedia revision dumps, Stack Exchange dumps, Enron, Blog Corpus) Nov 2022 is fine.

## 1. Corpora table

### 1a. Large, licence-clean or licence-aware corpora

| Corpus | Size | Date range | Licence | Commercial? | Notes / link |
|---|---|---|---|---|---|
| Common Pile v0.1 (EleutherAI) | 8 TB raw, 30 sources [V]. Comma training mix 463.6B raw tokens main stage + 176.2B cooldown [V] | Mixed. Includes post-2022 material (peS2o, StackExchange, Wikimedia, CCCC), so filter by date | Public domain + Open Definition 2.1 licences only; per-source licence in metadata | Yes, but BY and BY-SA subsets carry attribution/share-alike duties | [paper](https://arxiv.org/abs/2506.05209), [Comma mix](https://huggingface.co/datasets/common-pile/comma_v0.1_training_dataset), [blog](https://blog.eleuther.ai/common-pile/). Useful prose subsets: project_gutenberg, pre_1929_books, news, public_domain_review, library_of_congress, uk_hansard, usgpo, doab, pressbooks, wikimedia, stackexchange, peS2o |
| Common Corpus (Pleias) | 2.267T tokens total [V]: OpenCulture 967B, OpenGovernment 579B, OpenSource 283B, OpenScience 281B, OpenWeb 88.5B, Semantic 68B | More than half predates 2000 [V]. Per-doc `date` field | Public domain, CC0, CC-BY, CC-BY-SA, MIT, Licence ouverte; filterable to PD only | Yes (filter by licence field) | [HF](https://huggingface.co/datasets/PleIAs/common_corpus), [launch post](https://huggingface.co/blog/Pclanglais/two-trillion-tokens-open). Mostly English + French. Best source of large PD book and newspaper text |
| Institutional Books 1.0 (Harvard / IDI) | 983,004 public-domain volumes, 242B tokens (OpenAI tokenizer; 248-311B depending on tokenizer) [S] | Google Books scans, mostly 19th to early 20th c. | Public domain per HathiTrust, but dataset terms reported as non-commercial [S, unconfirmed] | Probably NO until terms are read | [paper](https://arxiv.org/abs/2506.08300), [HF](https://huggingface.co/datasets/institutional/institutional-books-1.0). Gated; read terms on the card. OCR noise is heavy |
| Project Gutenberg | ~75k books [?]; Common Pile `project_gutenberg` | Pre-1929 mostly (US PD) | Texts PD in US; "Project Gutenberg" name is a trademark | Yes if you strip PG licence boilerplate and trademark. No scraping of the site; use bulk mirrors | [Permissions](https://gutenberg.org/policy/permission.html), [terms](https://gutenberg.org/policy/terms_of_use.html) |
| PG-19 (DeepMind) | 28,602 train books (+50 val, +100 test), 11.5 GB text [V], roughly 2B words [?] | Books published before 1919 | Apache-2.0 on the dataset [V]; underlying PD | Yes | [HF](https://huggingface.co/datasets/deepmind/pg19) |
| Wikipedia dumps | ~15.8B tokens in Comma mix [V] (English) | Pick a pre-Nov-2022 dump | CC BY-SA 3.0 / GFDL [V] | Yes with attribution; whether model weights must be BY-SA is unresolved [S] | [HF wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia). Encyclopaedic voice, low value for style |
| Stack Exchange dumps | 23.9B tokens in Comma mix [V] | To 2024; filter to <2022 | CC BY-SA; 2024 dump moved behind login with a no-LLM-training clause, contested [S] | Use the Internet Archive pre-2024 dump or Common Pile copy; attribution needed | [DevClass](https://devclass.com/2024/07/30/stack-exchange-restricts-access-to-dump-of-user-contributed-data-as-critics-complain-license-permits-reuse-for-any-purpose). Q&A voice, not literary |
| peS2o | ~40M papers [V]; 43.3B tokens in Comma mix [V] | Various versions; latest has recent cut-off | ODC-BY [V] | Yes | [HF](https://huggingface.co/datasets/allenai/peS2o). Academic register; sample lightly |
| arXiv | 6.0B tokens papers in Comma mix [V] | 1991 to present | Only papers with permissive licence in Common Pile | Yes (subset only) | Academic register |
| US government docs | Common Pile `usgpo` (1M-10M docs, ~59 GB), `regulations`, `library_of_congress` (cc-by-4.0) [V], `caselaw_access_project` [V] | Varied | US federal works are public domain; LoC subset CC-BY | Yes | Dry legal register; Hansard, speeches are the useful part |
| Dolma | ~3T tokens, v1.7 4.5 TB gz [V] | Crawl to ~2023 | ODC-BY on compilation [V] | Compilation licence only; underlying web and book text is not cleared | [HF](https://huggingface.co/datasets/allenai/dolma). Treat like web crawl, see below |
| RedPajama-V2 | 100B+ docs from 84 CC snapshots, 30B with quality signals, 20B deduped [S]; "30T tokens" | 84 snapshots; years [?] | Apache-2.0 on code; underlying web text uncleared | Same as Dolma | [HF](https://huggingface.co/datasets/togethercomputer/RedPajama-Data-V2). Its 50+ per-doc quality signals are handy for building filters |
| FineWeb / FineWeb-Edu | FineWeb 15T tokens, 96 snapshots, CC-MAIN-2013-20 onward [S/V]; FineWeb-Edu 1.3T (threshold 3), 5.4T (threshold 2) [S] | Keep only snapshots up to ~2021 | ODC-BY on compilation [V] | Same web-crawl copyright exposure | [paper](https://arxiv.org/pdf/2406.17557), [HF](https://huggingface.co/datasets/HuggingFaceFW/fineweb). Educational classifier is the wrong target for style but the recipe is the template |
| DCLM-baseline | 4T tokens-class [?] | CC to 2022-23 | CC-BY-4.0 compilation [V] | Same | [HF](https://huggingface.co/datasets/mlfoundations/dclm-baseline-1.0) |
| The Pile | 825 GB [?] | to 2020 | "other" [V] | Mixed. Books3 (196,640 pirated books) was taken down by DMCA in Aug 2023 [V] | [TorrentFreak](https://torrentfreak.com/anti-piracy-group-takes-prominent-ai-training-dataset-books3-offline-230816/). Do not use Books3 or anything derived from it. Plenty of lawsuits cite it. Prefer Common Pile |

### 1b. Style-rich sources by genre

| Source | Size | Date | Licence | Commercial? | Link / note |
|---|---|---|---|---|---|
| PERSUADE 2.0 (student argumentative essays) | ~26k essays, grades 6-12, 15 prompts [S] | 2010s | Non-commercial Creative Commons (PERSUADE 1.0 repo says CC BY-NC-SA 4.0) [S] | NO | [GitHub](https://github.com/scrosseye/PERSUADE_corpus), [Zenodo](https://zenodo.org/records/8221504). Good for eval and a student-writing probe, not for a commercial training mix |
| ASAP essays (Kaggle) | ~13k essays, 8 prompts [?] | 2012 | Kaggle competition rules | Check; likely no | Probe only |
| ICNALE | Asian learners' English essays [?] | 2010s | Research only [?] | NO | Learner English; low value |
| Blog Authorship Corpus | 681,288 posts, 19,320 bloggers, >140M words [V] | Collected Aug 2004 | "Non-commercial research" per project page [V]; HF says unknown | NO as stated | [page](https://u.cs.biu.ac.il/~koppel/BlogCorpus.htm). Excellent informal voice, but licence blocks commercial use. Ask the authors (Koppel, BIU) for a commercial licence |
| Reddit WritingPrompts (Fan et al. 2018) | 272,600 train stories, ~955 MB [V] | 2018 | HF copies say MIT; underlying content is Reddit user text under Reddit terms [S] | Grey. Research only until cleared | [HF](https://huggingface.co/datasets/euclaise/writingprompts) |
| Reddit Pushshift dumps | Billions of comments/submissions [?] | 2005 to 2023 | Reddit cut Pushshift off in 2023 [S]; Reddit says any business training on public posts needs an agreement [S] | Treat as NO without a Reddit deal | [Pebblous summary](https://blog.pebblous.ai/blog/reddit-rss-public-api-shutdown/en/) |
| AO3 (Archive of Our Own) | 12.6M fics scraped in April 2025 [S] | to 2025 | Authors own works; AO3 asked Common Crawl to stop in Dec 2022 [S]; strong community opposition | NO. Consent problem even if technically fair use | [Gizmodo](https://gizmodo.com/ai-chatbot-fanfiction-fanfic-archive-of-our-own-1850524393). Skip |
| Gutenberg fiction | see above | pre-1929 | PD | Yes | Real narrative craft but archaic diction; use for structure and dialogue, not as the only "voice" |
| Enron emails | >1.6M emails originally; cleaned subsets smaller [S] | 1998-2002 | Released by FERC in 2003, widely treated as public domain; no current licence statement [S] | Probably yes but redactions and PII; strip PII | [EDRM](https://edrm.net/2025/08/still-on-dial-up-why-its-time-to-retire-the-enron-email-corpus/). Corporate email voice |
| Speeches / Hansard | Common Pile `uk_hansard`; US Congressional Record in `usgpo` | Varied | OGL / US PD | Yes | Spoken-register oratory |
| News | Common Pile `news` (100k-1M docs, ~0.55 GB) [V] | Varied | Openly licensed outlets only | Yes | Small. Mainstream news archives (NYT etc.) are in active litigation; avoid |
| Copywriting / ads | No clean open corpus found [gap] | | | | Must be commissioned or licensed. Old PD ads exist in Library of Congress / Internet Archive scans but OCR is noisy |
| College / admissions essays | No clean public dataset found [gap]; "college essays that worked" books are copyrighted | | | | See section 6 |

### 1c. Human-vs-AI paired and preference data

| Dataset | Size | Licence | Use |
|---|---|---|---|
| HC3 (Hello-SimpleAI) | 10K-100K rows, human vs ChatGPT answers [V] | CC BY-SA 4.0 unless a source is stricter [V] | [HF](https://huggingface.co/datasets/Hello-SimpleAI/HC3). Detector training, small |
| RAID | >10M docs, 11 LLMs, 11 genres, 4 decoding strategies, 12 attacks [V] | MIT [V] | [HF](https://huggingface.co/datasets/liamdugan/raid). Best for robust detector eval; the human side is from existing corpora (check their terms) |
| MAGE (DeepfakeTextDetect) | 100K-1M rows, 27 LLMs [V] | Apache-2.0 [V] | [HF](https://huggingface.co/datasets/yaful/MAGE) |
| M4 / M4GT | 8 LLMs, 6 domains, 9 languages; English subset 78,766 docs [S] | Check repo [?] | Multilingual detection |
| DetectRL | 4 high-risk domains, GPT-3.5, Claude, PaLM-2, LLaMA-2 [S] | Check repo [?] | Real-world detection with attacks |
| Ghostbuster data | Essays, news, creative writing, human vs ChatGPT [?] | Check repo [?] | Domain match with your goal (essays, creative) |
| gutenberg-dpo-v0.1 (jondurbin) | <1K pairs, chosen = original Gutenberg chapter, rejected = Llama-2/bagel/dolphin chapter [V] | CC BY-4.0 [V] | [HF](https://huggingface.co/datasets/jondurbin/gutenberg-dpo-v0.1). Exactly your preference-pair shape. Replicate at scale with your own PD chapters and modern generators |
| Human rewrite pairs | No big public set found [gap] | | Build it: AI draft vs paid-writer rewrite (section 6) |

Caveat for all of 1c: the AI side is output of OpenAI/Meta/Mistral models. Check each generator's terms before training a competing model on its outputs. For preference pairs you only need the human side as "chosen"; generate the "rejected" side with models whose terms allow it.

## 2. Recommended starter corpus mix

Goal: a clean, defensible base for continued pretraining / SFT to get human prose style, around 30B tokens after filtering. Token counts are my estimates after quality filtering and English-only selection; actual yield needs a pilot.

| # | Component | Target tokens | Why | Risk |
|---|---|---|---|---|
| 1 | Common Corpus OpenCulture English, PD books + newspapers, 1850-1960, top 40% by prose classifier | 8B | Biggest clean source of edited human prose | OCR noise, archaic style; blend with modern text |
| 2 | Common Pile `project_gutenberg` + `pre_1929_books` + PG-19 (dedup against each other) | 4B | Clean fiction/non-fiction craft | Archaic diction |
| 3 | Wikipedia (dump from before Nov 2022) | 3B | Factual register, clean | CC BY-SA attribution; share-alike question for weights |
| 4 | Stack Exchange (Internet Archive pre-2024 dump, posts <2022, score >=3) | 4B | Modern conversational explanations | CC BY-SA; 2024 terms dispute |
| 5 | Common Pile `cccc` / CC-licensed web, snapshots up to 2021 only, quality-filtered | 5B | Modern informal web prose under open licences | CC-BY attribution; check no mis-licensed pages |
| 6 | Common Pile news, public_domain_review, uk_hansard, LoC, usgpo speeches, doab/pressbooks long-form | 2B | Journalism, oratory, edited long-form | Small |
| 7 | peS2o + arXiv, sample lightly | 2B | Argumentation and precision | Academic register can bleed into outputs |
| 8 | Enron (PII-scrubbed) + sample of Hansard dialogue | 0.3B | Email register | Redactions, PII |
| 9 | Licensed / commissioned fresh text (section 6): admissions-style essays, ads, blog posts, creative | 0.05-0.2B at first | The only way to get modern 1990-2022 voices you can legally use. Highest-value tokens | Cost and consent paperwork |
| 10 | Research-only probes, never in the commercial mix: PERSUADE, WritingPrompts, Blog Authorship Corpus, HC3/RAID/MAGE | 0.5B | Eval and detector work | NC / ToS |
| | Total commercial-safe mix | ~28-30B | | |

Skip: Books3 and anything derived from it, AO3 scrapes, Pushshift/Reddit dumps, Institutional Books until its terms are confirmed commercial, anything from news archives in litigation, and the pirated-book shadow libraries at issue in Bartz.

Honest gap: clean data is thin for modern (1980-2022) literary and persuasive prose. Public domain gives you 1850-1929 writing; open licences give you forums, Wikipedia and academia. The style you probably want (essays, ads, blogs, creative) mostly lives in copyrighted text, so licensing or commissioning is the main lever, not scraping.

## 3. Legal state of play (as of 2026-11-01)

Most of this comes from search write-ups; verify on dockets before relying on it.

- **Bartz v. Anthropic.** In June 2025 Judge Alsup held training on lawfully acquired books was fair use but copying pirated books into a central library was not [S]. Anthropic settled for $1.5B, roughly $3,100 per work gross. A search result reports final approval on 20 July 2026, claim rate 91.3%, release covers past conduct up to 25 Aug 2025 only and does not cover outputs or future conduct [S]. Sources: [Authors Alliance](https://www.authorsalliance.org/2026/07/21/bartz-v-anthropic-settlement-receives-final-approval/), [Pearl Cohen](https://pearlcohen.com/federal-court-approves-1-5-billion-anthropic-copyright-settlement-largest-in-history). Lesson: how you acquire the data matters as much as what you do with it. Pirated sources create statutory-damages exposure.
- **Kadrey v. Meta (June 2025).** Chhabria granted Meta summary judgment on fair use because plaintiffs offered no evidence of market harm, but said market dilution (a model flooding the market with competing works) will often decide factor four for plaintiffs. Narrow ruling, only those plaintiffs. [Authors Alliance](https://www.authorsalliance.org/2025/06/26/meta-wins-on-fair-use-for-now-but-court-leaves-door-open-for-market-dilution/). This matters directly for you: a model built to write like humans is a market substitute for human writers, the exact scenario Chhabria flagged.
- **Thomson Reuters v. Ross.** Third Circuit affirmed that Ross's training use was not fair use (reported 30 Sep 2026), first appellate ruling on AI training; limited because Ross was a non-generative competing legal-search tool [S]. [Nieman Lab](https://www.niemanlab.org/2026/09/federal-appeals-court-upholds-thomson-reuters-landmark-ai-copyright-win/).
- **NYT v. OpenAI/Microsoft (S.D.N.Y., Judge Stein).** Core claims survived dismissal in March 2025; summary judgment cross-motions pending in autumn 2026, no trial date [S, schedule sources conflict]. [Axios](https://axios.com/2026/09/08/nyt-openai-microsoft-copyright-lawsuit).
- **EU AI Act.** GPAI providers must publish a training-content summary (Article 53(1)(d)) using the Commission template published 24 July 2025 and have a copyright policy (incl. honouring text-and-data-mining opt-outs). Obligations applied from 2 Aug 2025; Commission enforcement powers from 2 Aug 2026; models placed on the market earlier have until 2 Aug 2027 [S]. If you sell in the EU, your documented data provenance doubles as compliance. [Mayer Brown](https://www.mayerbrown.com/de/insights/publications/2025/08/eu-ai-act-news-rules-on-general-purpose-ai-start-applying-guidelines-and-template-for-summary-of-training-data-finalized).

### What a solo founder can safely train on commercially (my reading, not legal advice)
1. Public domain (US pre-1929 and US federal works): safest. Keep per-document provenance.
2. CC0 / CC-BY / ODC-BY / MIT / Apache sources via Common Pile and Common Corpus, using their licence metadata. Keep an attribution file. Treat BY-SA (Wikipedia, Stack Exchange) as usable but flag the weights question.
3. Text you license or commission with a written assignment/licence that explicitly allows model training. Safest source of modern voice.
4. Everything else (general web, Reddit, news, books of unknown origin): US fair use is being argued both ways, and a human-writing product is the weakest fair-use fact pattern (market dilution). Not a good bet for a company with no litigation budget.

### Licensing routes
- Pay writers directly for assignment or a training licence (cheapest, cleanest; section 6).
- Approach small rightsholders: Blog Authorship Corpus authors, Baker/other university corpus owners, magazine back-catalogues, defunct blog networks, local newspaper archives.
- Marketplaces and brokers: Microsoft Publisher Content Marketplace (Feb 2026, usage-based) [S], Amazon reportedly building one [S], Human Native (London, brokers licences) [S]. About 91 public AI licensing deals by June 2026 [S]. [Media and the Machine](https://mediaandthemachine.substack.com/p/ai-content-licensing-deals-june-2026). I found no per-word price benchmarks; get quotes.

## 4. Filtering: pre-2022 timestamps are not enough

Why timestamps fail:
- Crawl date is not authoring date. Pages crawled in 2021 can have been edited later, and 2020-2022 web already holds GPT-3 text (marketing sites, spun articles, product reviews).
- Fix: hard cutoff mid-2021 for web; for curated sources use revision/dump date; verify with `last-modified`, URL date patterns, and in-text year mentions; drop docs mentioning post-cutoff events (ChatGPT, GPT-4, LLM, "as an AI language model").

Recommended pipeline:
1. Provenance first: store source, licence, date, URL, hash per doc. Needed for EU summary and takedowns.
2. Language ID, boilerplate removal (trafilatura/resiliparse), PII scrub.
3. Dedup: exact + MinHash (FineWeb uses 5-gram MinHash at 75% similarity within snapshot [S]); also dedup across sources (Gutenberg appears in PG-19, Common Pile, Common Corpus).
4. Heuristic filters: repetition, line-length, symbol ratios (use RedPajama-V2's 50+ signals [S]).
5. Decontaminate against your eval sets.
6. Learned quality classifier, FineWeb-Edu style [S]: LLM labels ~460k docs 0-5 on a rubric, train a small embedding model (Snowflake-Arctic-Embed-M) plus regression head, keep score >=3 (F1 82% on the held-out 50k). FineWeb-Edu's rubric is "educational"; for you write a different rubric.

Building a "human-quality prose" classifier:
- Rubric (0-5): specific detail, a distinct voice, varied sentence rhythm, concrete over abstract, no filler or hedging, no SEO/listicle structure, no template phrases.
- Positives: Gutenberg-class fiction/essays, edited magazine and newspaper prose, commissioned writer text, top-voted Stack Exchange answers. Negatives: SEO spam, boilerplate marketing, forum fragments, machine-translated text, and (as hard negatives) modern LLM output you generate yourself.
- Add stylometric features: sentence-length variance (burstiness), type-token ratio, perplexity under a small LM and its variance, punctuation mix, contraction rate. Train gradient boosting on features + embedding head and compare.
- Validate with blind human ratings of 500 docs (Spearman vs classifier) and check that pre-2020 true-human text scores above LLM text; use HC3/RAID/MAGE human sides and gutenberg-dpo pairs as sanity checks. A good prose classifier should also separate human from AI better than chance without being a detector.
- Watch for classifier bias: it will favour formal, standard-English, higher-register text and drop dialect and slang. Keep a quota of informal registers (Blog Corpus-style, forums) so the model does not only write like a textbook.

## 5. Fresh human data going forward

- **Pay rates (all from blogs/aggregators, treat as rough) [S]:** Mercor reportedly averages $95-110/hr with specialists far higher; Outlier/Scale about $15-50/hr (sources conflict); Surge pays by credential; rates have been falling and volatile; a March 2026 Mercor breach was reported. Creative-writing hourly rates were not found. [Business Insider via mirror](https://kompas.wasmer.app/https_www_businessinsider_com/mercor-cuts-contractors-meta-project-less-money-musen-nova-ai-2025-11).
- **Solo-founder options:** (a) Pay per piece directly: for example $30-100 per 600-word essay or ad with an assignment/licence clause (my estimate, test the market), (b) run a pilot of 100-200 writers through Upwork/Contra/a Substack or Reddit call, (c) use a vendor only for volume. A vendor holds the contractor paperwork and PII burden, you hold the data rights, so confirm assignment of rights to you in their MSA.
- **What to collect:** human first drafts on prompts; human rewrites of AI drafts (gives preference pairs); ranked pairs; style labels; and explicit permission for training use and for derivative models.
- **Contract basics:** work-for-hire or exclusive assignment (or a non-exclusive perpetual licence for training), warranty of originality (no AI use, attested), right to include in a commercial model, deletion/withdrawal policy, payment, and PII handling. Collect "no-AI-used" attestations; add a spot-check detector pass (imperfect).
- **Admissions-essay angle:** FERPA covers matriculated students' education records, not applicants, per one university summary [S], but it is not the main risk. Real risks: (1) copyright stays with the student, so you need a written licence; (2) essays carry highly sensitive PII (health, family, immigration, trauma), so scrub and gate; (3) minors under 18 need parental consent, and COPPA/state laws apply under 13; (4) if essays come from a school, counselor or service, their contract and FERPA/ethics policies apply; (5) institutions can have access controls on applicant data (2019 Stanford exposure shows the sensitivity) [S]; (6) the Common App and many universities have integrity rules, so publishing or training on essays can embarrass the student. Safe path: students submit their own essays voluntarily through an opt-in form with a clear licence, optional anonymisation, easy withdrawal, and payment. Do not buy scraped essay collections or "essays that worked" books.

## 6. Open questions to resolve before building

1. Institutional Books 1.0 terms: confirm if commercial use is allowed (read the HF card while logged in).
2. Contact Koppel (BIU) about commercial rights to the Blog Authorship Corpus.
3. Ask a lawyer about the BY-SA share-alike effect on weights for Wikipedia and Stack Exchange; if unsure, keep BY-SA to under 20% of the mix or drop it.
4. Test the FineWeb-Edu recipe on 20k docs with your own rubric before a large run.
5. Obtain per-word quotes for commissioned writing and licensing (none found online).

## Key links

- Common Pile: https://arxiv.org/abs/2506.05209, https://blog.eleuther.ai/common-pile/, https://huggingface.co/common-pile
- Common Corpus: https://huggingface.co/datasets/PleIAs/common_corpus
- Institutional Books: https://arxiv.org/abs/2506.08300
- FineWeb paper: https://arxiv.org/pdf/2406.17557
- Dolma: https://huggingface.co/datasets/allenai/dolma
- Bartz final approval: https://www.authorsalliance.org/2026/07/21/bartz-v-anthropic-settlement-receives-final-approval/
- Kadrey v. Meta analysis: https://www.authorsalliance.org/2025/06/26/meta-wins-on-fair-use-for-now-but-court-leaves-door-open-for-market-dilution/
- Thomson Reuters v. Ross (3d Cir.): https://www.niemanlab.org/2026/09/federal-appeals-court-upholds-thomson-reuters-landmark-ai-copyright-win/
- NYT v. OpenAI status: https://axios.com/2026/09/08/nyt-openai-microsoft-copyright-lawsuit
- EU template: https://www.mayerbrown.com/de/insights/publications/2025/08/eu-ai-act-news-rules-on-general-purpose-ai-start-applying-guidelines-and-template-for-summary-of-training-data-finalized
- Books3 takedown: https://torrentfreak.com/anti-piracy-group-takes-prominent-ai-training-dataset-books3-offline-230816/
