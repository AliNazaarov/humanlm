# How people benchmark "good" and "human-like" writing (2026-11-01)

Author: hl-researcher. Builds on [TECH.md](TECH.md) (which already covers the EQ-Bench slop score at a high level, Antislop/FTPO, Pangram as a reward risk, and Artificial Hivemind as evidence). This file goes into **how each benchmark is built, what it gets wrong, and what we can reuse**.
Every claim has a URL and the date it was checked or published. [E] = my estimate.

## 0. Bottom line (read this if nothing else)

1. **No public benchmark measures what we sell.** No benchmark scores "rewrite this founder copy so it sounds like a skilled human, and keep the facts the same". The closest are WritingBench's Advertising & Marketing domain (LLM-judged), Springboards' marketing Creativity Benchmark (human-judged, data not released) and EQ-Bench (fiction). We have to build our own. That is also a YC asset: "we publish the leaderboard".
2. **LLM judges are weak on taste.** Here is how well judges agree with humans. Surge says the EQ-Bench autograder agreed with expert writers only 43% of the time. The best off-the-shelf judge on LitBench scored 73%. Marketing judges reached Spearman 0.04–0.63 against practitioners. Standard reward models are about 53%, close to chance, on length-matched writing pairs. Judges also favour their own text. Use LLM judges as a cheap filter. Humans are the ground truth.
3. **"Sounds human" and "sells better" are different scores.** In a Dec 2025 study (n=800), AI-written ads beat human ads 59% to 41%. When people *spotted* the AI ad, they liked it 21 points less. So the product has to win on two things at once: (a) not detectable as AI and (b) at least as persuasive. Measure both. Never use one as a stand-in for the other.
4. **Making text human-like costs faithfulness.** The Computational Turing Test paper (Nov 2025) found that tuning for human-likeness lowers semantic fidelity, and the reverse. A faithfulness gate is not optional for a rewriter.
5. **The best cheap human judges are people who use ChatGPT a lot.** A majority vote of 5 frequent LLM users misclassified 1 of 300 articles. They beat commercial detectors, even on humanized text. Recruit those people for our panel.
6. **What to copy: EQ-Bench's machinery and slop-score's lists (MIT). Do not copy their prompts.** Use pairwise judging in both orders, with outputs truncated or length-matched, margin-weighted Glicko/Bradley-Terry, anchor models, and a slop slider. Add LMArena-style length/format control.

---

## 1. Benchmark-by-benchmark

### 1.1 EQ-Bench Creative Writing v3
- **Measures:** short fiction quality. 32 prompts × 3 iterations = 96 pieces, temp 0.7, min_p 0.1. https://github.com/EQ-bench/creative-writing-bench (README read 2026-11-01).
- **Judge setup:** two stages.
  - (1) Each piece gets a rubric score on 22 criteria: Adherence to Instructions, Believable Character Actions, Nuanced Characters, Consistent Voice/Tone, Imagery, Elegant Prose, Emotionally Engaging/Complex, Coherent, Sentences Flow Naturally, Reader Engagement, Overall Impression. Nine are negative (Meandering, Weak Dialogue, Tell-Don't-Show, Unsurprising, Amateurish, Purple Prose, Overwrought, Incongruent Ending Positivity, Unearned Transformations). https://github.com/EQ-bench/creative-writing-bench/blob/main/data/creative_writing_criteria.txt
  - (2) The rubric sets a starting Elo. Then the judge compares the model's outputs with its leaderboard neighbours, pair by pair, on 9 criteria (authenticity, originality, writing quality, coherence, instruction following, world/atmosphere, avoids clichés, avoids flowery verbosity, avoids poetic overload). It marks the margin as `+` to `+++++`, with no draws. Ratings use Glicko-2, modified so the margin counts. DeepSeek-R1 is anchored at 1500 and ministral-3b at 200. https://github.com/EQ-bench/creative-writing-bench/blob/main/data/pairwise_prompt.txt
- **Which judge:** the two sources disagree. The repo README says Claude Sonnet 4.6. The about page, with a news item dated 2026-10-25, says GLM 5.3 for the rubric and Claude Opus 5 for pairwise. https://eqbench.com/about.html (read 2026-11-01). The judge changes over time, so scores across versions are not comparable.
- **Bias controls:** every pair is judged in both orders, and outputs are cut at 4,000 characters to remove length bias. Biases the authors list but do not control: self-bias, positivity bias, slop bias, and "smut bias" (the judge punishes NSFW-tuned models). They also say it is "not objective" and English-only. https://eqbench.com/about.html
- **Known flaws:** Surge's expert writers agreed with the EQ-Bench autograder only **43%** of the time. Surge says the grader rewards dense metaphor even where the writing is incoherent. https://surgehq.ai/blog/hemingway-bench-ai-writing-leaderboard (page dated 2026-02-04 / 2026-10-21). It is fiction only, so it fits marketing copy poorly.
- **Cost:** "around $10" of API fees per model (about page, 2026-11-01). With Opus 5 as the pairwise judge it is probably higher [E].
- **Licence:** the repo has no licence (GitHub API, 2026-11-01: `none`). That means all rights reserved. We can read the method but should not ship its prompts or code inside our product.
- **Reuse:** run it once as a "we didn't break general writing" check, and copy the *method*. Write our own pairwise prompt for copy.

### 1.2 EQ-Bench Longform Creative Writing
- **Measures:** plan → reflect → revise → write 8 chapters of about 1,000 words. Score is 0–100: 8 positive and 6 flaw criteria on a 14-dimension rubric. Forced metaphor is weighted ×1.7 "to offset the judge's difficulty in spotting it". Also shows a degradation sparkline (chapter 8 against chapter 1), repetition, and slop score. Slop and length are displayed but do not count in the score. Since v1.1 there is a penalty for too many ≤5-word one-sentence paragraphs. https://eqbench.com/creative_writing_longform.html (read 2026-11-01)
- **Judge:** Claude Sonnet 4.6 since v1.11 (2026-02-19). Before that Sonnet 4, from v1.1 (2025-08-08).
- **Licence:** no licence. https://github.com/EQ-bench/longform-writing-bench
- **Reuse:** low, because our outputs are short. Steal two ideas. (a) The **short-paragraph penalty**: LinkedIn "broetry" is the same failure. (b) **Up-weight the criteria judges are bad at**, such as forced metaphor.

### 1.3 Slop score (sam-paech/slop-score)
- **Measures:** 60% slop words + 25% "not X, but Y" patterns + 15% slop trigrams. The lists are words and trigrams that appear far more in LLM text than in a human baseline. The "not X but Y" detector has 2 stages: 10 surface regexes, then 35 regexes over POS tags. It also reports MATTR-500 lexical diversity, Flesch-Kincaid grade, sentence and paragraph length, and dialogue rate. Each model is profiled on 150 creative + 150 essay outputs. https://github.com/sam-paech/slop-score (README read 2026-11-01)
- **Judge type:** none. It is deterministic, so it costs nothing and cannot be gamed by a judge.
- **Flaws:** it only catches *lexical* slop. A model can avoid every listed word and still write templated, empty copy. The lists also come from fiction and essays, not marketing.
- **Licence:** the code, slop lists and human profile are **MIT**. The wordfreq port is Apache-2.0 and its data is CC-BY-SA-4.0 (README licence section, 2026-11-01). The repo-level licence field shows NOASSERTION because it is dual-licensed.
- **Reuse: high.** `generate-leaderboard.mjs --force-recalc-human` lets you bring your own human samples. **Point it at our human founder-copy corpus** to get a *copy-specific* human reference band. Then rebuild the slop lists from our own AI-ified copy with slop-forensics (MIT, see TECH.md).

### 1.4 LMArena creative writing category
- **Measures:** crowd votes in blind pairwise chats, filtered to creative-writing prompts. Ratings are Bradley-Terry. The default view is "style controlled": length, header, bold and list counts go into the regression as covariates, and length was the dominant factor. https://lmsys.org/blog/2024-08-28-style-control/ (2024-08-29)
- **Judge type:** anonymous human pairwise votes, cast quickly.
- **Flaws:**
  - Surge argues quick votes reward first-impression polish over coherence and restraint (blog above).
  - "The Leaderboard Illusion" found private variant testing (27 Meta variants before Llama-4) and uneven data access: Google and OpenAI each got about 19–20% of all data, while 83 open models together got 29.7%. https://arxiv.org/abs/2504.20879 (2025-04-29)
  - The top 10 often sit within about 20 Elo of each other (secondary source: https://www.toolcenter.ai/en/articles/lmarena-review-2026 , 2026).
  - Third-party roundups put claude-opus-4-6-thinking at #1 in creative writing, at 1497, as of June 2026. Not verified on the live site. https://officechai.com/learn/these-are-the-best-ai-models-for-creative-writing-june-2026/
- **Cost/licence:** you cannot submit a fine-tune cheaply. Vote data is open: `lmarena-ai/arena-human-preference-140k` (CC-BY-4.0, 2025-08-01), `arena-expert-5k` (2025-11-05), and `leaderboard-dataset` (updated 2026-10-30). https://huggingface.co/lmarena-ai
- **Reuse:** copy the **style-control regression** into our own Bradley-Terry fit. The 140k CC-BY vote set could be filtered for writing prompts to pre-train or calibrate a judge [E: still to check].

### 1.5 Hemingway-bench (Surge AI): new, and closest to "expert human taste"
- **Measures:** holistic writing quality plus 8 sub-dimensions: implicit intent, creativity, writing quality, truthfulness, coherence, instruction following, verbosity, humor. Tasks are real creative, business and everyday requests (business documents, emails to landlords, a commercial script). https://surgehq.ai/blog/hemingway-bench-ai-writing-leaderboard (read 2026-11-01)
- **Judge type:** professional writers (screenwriters, poets, speechwriters, copyeditors), more than 5,000 blind pairwise comparisons.
- **Findings:** Gemini 3 Flash, Gemini 3 Pro and Claude Opus 4.5 came top. Experts penalise overwriting, excess metaphor and tone mismatch, which are exactly the things automated graders reward.
- **Licence/reuse:** prompts and judgments do not appear to be released. Treat it as a reference design and a sanity check of which frontier baseline to beat.

### 1.6 WritingBench (Alibaba X-PLUG)
- **Measures:** 1,000 real-world queries in 6 domains and 100 subdomains. The domains **include Advertising & Marketing** and Finance & Business. Queries average 1,500+ tokens with source materials. Each query gets 5 instance-specific criteria, each scored 1–10. https://github.com/X-PLUG/WritingBench (README read 2026-11-01); paper https://arxiv.org/abs/2503.05244 (v1 2025-03-07, v4 2025-11-27)
- **Judge:** Claude Sonnet 4.5 since 2025-11-27 (earlier Sonnet 4, then 3.7). There is also an open critic model, WritingBench-Critic-Model-Qwen-7B, on Hugging Face.
- **Flaws:** the queries were generated by an LLM and then refined by humans. The criteria are also LLM-generated. Scores are absolute, which is less discriminative than pairwise. Single-judge self-preference applies.
- **Cost [E]:** 1,000 queries × 5 criteria ≈ 5,000 judge calls. About $30–100 with a Sonnet-class judge, or close to $0 with the 7B critic on a rented GPU.
- **Licence:** **Apache-2.0**. **Reuse: high.** Run the Advertising & Marketing + Business subset as our external public number.

### 1.7 LitBench
- **Measures:** creative-writing preference. 2,480 debiased test pairs and 43,827 training pairs from Reddit. https://arxiv.org/abs/2507.00769 (2025-07-01)
- **Labels:** the HF dataset schema shows `chosen_upvotes` and `rejected_upvotes`, so the "human labels" are **Reddit upvotes**, not rater judgments. https://huggingface.co/datasets/SAA-Lab/LitBench-Train (checked 2026-11-01)
- **Key result:** the best off-the-shelf judge (Claude 3.7 Sonnet) agreed with humans 73% of the time. Trained Bradley-Terry and generative reward models reached **78%**.
- **Licence:** none declared on HF, and the data is Reddit-derived, so **do not train on it commercially**. Use it only as a judge-calibration test.
- **Reuse:** medium. It shows a small trained reward model beats prompting a frontier judge. That supports reusing our Tastecut BT reward model.

### 1.8 WritingPreferenceBench (Oct 2025)
- 1,800 human-annotated pairs (1,200 English and 600 Chinese, 8 genres), **matched for grammar, facts and length**, so only subjective quality is left. https://arxiv.org/abs/2510.14616 (v1 2025-10-16, v2 2026-01-28)
- Standard sequence-classifier reward models scored **52.7%** (chance). Zero-shot LLM judges scored 53.9%. Generative reward models that reason first reached 81.8% in English (RM-R1-Qwen2.5-7B). Accuracy swings from 18% to 82% across genres.
- **Implication:** once length and errors are controlled, a plain Bradley-Terry head learns almost nothing about taste. Our reward model should *reason and then score* (a generative reward model), or at least be checked on length-matched pairs.

### 1.9 HelloBench (long text)
- 5 subtasks (open QA, summarisation, chat, completion, heuristic generation). HelloEval is a checklist-style judge that the authors say tracks humans better than ROUGE, BLEU or a plain LLM judge. Most of about 30 models can't write past 4,000 words. https://arxiv.org/abs/2409.16191 (2024-09-24). MIT, last push 2024-11. https://github.com/Quehry/HelloBench
- **Reuse:** low (our outputs are short). Steal the **checklist judging pattern**: binary yes/no checks score more reliably than 1–10 scales.

### 1.10 Diversity: Artificial Hivemind (Infinity-Chat) and NoveltyBench
- **Infinity-Chat:** 26K open-ended queries and 31,250 human ratings, with **25 annotators per example**. Judges and reward models are least calibrated exactly where people's preferences differ. https://arxiv.org/abs/2510.22954 (v2 2026-10-06, NeurIPS 2025 D&B oral). Dataset licence not stated on arXiv.
- **NoveltyBench:** 10 generations per prompt (curated set + WildChat). Responses are grouped into "same idea" groups. Score = number of distinct groups, weighted by quality. 20 models produce "significantly less diversity than human writers", and larger models within a family are often *less* diverse. https://arxiv.org/abs/2504.05228 (2025-04-07)
  - v1.1, current repo: grouping is now done by one `gpt-5.6-luna` call per prompt (ARI 0.90–0.97, against 0.29–0.80 for the old DeBERTa classifier). Quality is scored by `claude-opus-5`, 1–10. v1.0 and v1.1 scores are not comparable. https://github.com/novelty-bench/novelty-bench (MIT, push 2026-09-10)
- **Reuse: high.** Run it NoveltyBench-style on our own prompts: 10 rewrites of the same input, then count distinct groups. This is the collapse alarm for DPO/FTPO.

### 1.11 Turing tests (Jones & Bergen 2025)
- Pre-registered three-party test with 5-minute chats. **GPT-4.5 with a humanlike persona prompt was picked as the human 73% of the time**, more often than the real humans. LLaMa-3.1-405B with the same prompt: 56%. ELIZA: 23%. GPT-4o: 21%. https://arxiv.org/abs/2503.23674 (2025-03-31)
- **Lesson:** most of the "human" signal came from the *persona prompt* (casual, slightly flawed). It is a cheap baseline to beat. Chat is not copy, so the format doesn't carry over.
- **Related warning:** RLHF makes models better at *convincing* time-limited human raters without being more correct. False positives rose 24.1% on QuALITY. https://arxiv.org/abs/2409.12822 (2024-09-19). A rushed human panel can be fooled too. Give raters time and source material.

### 1.12 Human detection studies (better than people think)
- Frequent LLM users as detectors: a majority of 5 got 299 of 300 articles right and beat most commercial detectors, including on paraphrased or humanized text. Their clues were AI vocabulary, formality, originality and clarity. Dataset and code are released. https://arxiv.org/abs/2501.15654 (2025-01-26, ACL 2025)
- "Is Human-Like Text Liked by Humans?": 19 annotators, 16 datasets, 9 languages. Detection accuracy was **87.6%**. The gaps are in **concreteness, cultural nuance and diversity**. Explaining those gaps in the prompt partly closed them in more than half the cases. **Humans don't always prefer human text** when they can't tell the source. https://arxiv.org/abs/2502.11614 (ACL 2026 main; v3 2026-04-29). Data and labels released.
- Computational Turing Test: a BERT detector plus interpretable features plus semantic similarity. 9 open models and 5 calibration methods (fine-tuning, style prompting, retrieval). Text stays detectable. The biggest giveaway is **affective tone and emotion**. **Instruction-tuned models do worse than their base models.** **Human-likeness trades off against semantic fidelity.** https://arxiv.org/abs/2511.04195 (v2 2025-11-25)

### 1.13 Detector benchmarks: RAID and Pangram
- **RAID:** more than 10M documents, 11 LLMs, 11 genres, 4 decoding strategies, 12 adversarial attacks (paraphrase, synonym swap, homoglyph, and others). Public leaderboard. `pip install raid-bench`. **MIT**, pushed 2026-10-21. https://github.com/liamdugan/raid ; paper https://arxiv.org/abs/2405.07940 (2024). Its finding: most detectors break under attacks and decoding changes.
- **Pangram:** a humanizer-robustness paper (19 humanizers, uses RAID's paraphrase and synonym splits). https://arxiv.org/html/2501.03437v1 (2025-01). Independent UChicago work found false negative rates ≤0.02 (already in TECH.md). Vendor-affiliated claims are marked as such.
- **Reuse:** detectors are **monitors, never rewards** (TECH.md §E stands). New: use RAID's *attack list* as a negative control. If our model only beats Pangram the way a synonym-swapper does, we have built a humanizer, not a writer.

### 1.14 Copywriting / marketing benchmarks (thin field)
- **Creativity Benchmark (Springboards.ai):** 678 advertising, marketing and strategy practitioners made 11,012 pairwise comparisons over 100 brands and 3 prompt types. Models sat close together: the top beat the bottom only about 61% of the time. LLM judges (GPT-4o, Claude 4 Sonnet, Gemini 2.0 Flash) reached **Spearman 0.04–0.63** against the humans, which the authors call "unstable". Data release not stated. https://arxiv.org/abs/2509.09702 (v2 2025-10-19)
- **MarketingFM / AutoEval-Main:** rule-based checks plus an LLM judge for ad copy. Reports 89.57% agreement with human reviewers. https://arxiv.org/abs/2506.17863 (2025-06; snippet only, not opened)
- **E-commerce content optimisation:** human ratings plus online A/B tests, diversity, readability and sentiment. https://arxiv.org/abs/2505.23809 (2025-05; snippet only)
- No public benchmark ties copy to real CTR or reply rate.

### 1.15 Human preference: AI vs human ads
- **Meguellati et al., "LLM-Generated Ads", 2025-12-03:**
  - Study 1: 400 people, GPT-3.5. LLM ads 51.1% vs human 48.9%.
  - Study 2: 800 Prolific participants, ads from GPT-5, Sonnet 4 and Llama 4 with Midjourney images. **AI 59.1% vs human 40.9%** (p<0.001). Biggest wins came from authority (63%) and consensus (62.5%) appeals; scarcity was not significant. 58.4% correctly spotted the AI ad (72.5% aged 18–24, 49.2% aged 65+). **Spotting it cut preference by 21.2 points.**
  - Limits: US only, self-reported intent, ads curated by one author. https://arxiv.org/html/2512.03373v1
- **Field evidence:** ads with AI-generated images reached human-level CTR (Exner, Hartmann, Netzer, Zhang). https://www.columbia.edu/~on2110/Papers/AI_in_disguise.pdf (undated PDF; not opened, from search 2026-11-01)
- **Takeaway:** humans don't prefer "human" copy for its own sake. They punish copy they *recognise* as AI. Our value = AI persuasiveness **without** the recognisable tells.

---

## 2. Cross-cutting judge flaws (and the fix for each)

| Flaw | Evidence | Fix we adopt |
|---|---|---|
| Length/verbosity bias | Length-controlled AlpacaEval: a GLM regression on length difference raised Spearman with Arena from 0.94 to 0.98. https://arxiv.org/abs/2404.04475 (2024-04-06). LMArena style control (2024-08-29). | Length-match or truncate pairs (EQ-Bench). Add length and format covariates to the BT fit. Hard gate: output length within ±20% of input [E: threshold]. |
| Position bias | EQ-Bench runs both orders (about page) | Always judge A/B and B/A. Count a pair only if both orders agree. |
| Self-preference | Self-recognition correlates linearly with self-preference (GPT-4, Llama 2). https://arxiv.org/abs/2404.13076 (2024-04-15) | Judge family ≠ generator family ≠ our base family. Rotate 2 judges from different labs. |
| Rewards metaphor and polish | Surge: EQ-Bench grader agreed with experts only 43% | Copy-specific criteria (clear, specific, believable, would send). Up-weight "forced metaphor/hype". |
| Mis-calibrated on contested taste | Infinity-Chat; WritingPreferenceBench (RMs ≈ chance) | Human panel decides. Keep pairs where humans split as their own "contested" slice. Use a generative reward model, not a plain BT head. |
| Crowd raters judge fast | Leaderboard Illusion; RLHF misleads rushed raters | Expert panel (frequent LLM users), no time pressure, source text shown. |

---

## 3. The eval stack FeatherLM should copy

One harness, run on every checkpoint. Gates first, then cheap metrics, then judges, then humans. Owner: hl-judge. Costs are [E].

**Eval set (HL-Copy-200):** 200 inputs: landing hero + sub, launch email, cold email, LinkedIn post, X post, 40 each.
- Each input = AI-sounding draft + facts sheet (names, numbers, claims, CTA) + one *human reference* rewrite.
- Freeze 50 as a never-train holdout. Add 10 new cases a week from failures.

**Layer 0: hard gates (free, every sample).** A sample that fails any gate scores 0.
1. LanguageTool: 0 grammar or spelling errors.
2. Faithfulness: every fact on the facts sheet is kept and nothing is added. Check with an NLI model plus an LLM checklist ("Is $X present? Y/N"; HelloBench-style binary checks).
3. Length ratio inside the band.
4. CTA kept.

The faithfulness gate is required because human-likeness trades off against fidelity (Computational Turing Test).

**Layer 1: deterministic style metrics (free, every sample).**
- slop-score (MIT), re-baselined on *our* human copy corpus with `--force-recalc-human`.
- Slop lists rebuilt from our AI-ified copy with slop-forensics.
- "Not X but Y" regex, em-dash rate, tricolon rate.
- MATTR-500, sentence-length variance, share of ≤5-word one-line paragraphs (the EQ-Bench longform penalty, which is LinkedIn broetry).
- **Pass = inside the human reference band, not "as low as possible".**

**Layer 2: diversity (weekly, about $5).** NoveltyBench-style:
- 10 rewrites of 30 inputs, grouped by an LLM. Report the number of distinct groups.
- Also report embedding similarity to GPT/Claude/Gemini rewrites of the same input (Hivemind check).
- Alarm if either gets worse after DPO/FTPO.

**Layer 3: automatic detectability (eval only, every checkpoint).**
- (a) Pangram score as a monitor.
- (b) Our own "computational Turing test": a small DeBERTa trained on human copy vs AI-ified copy, scored on held-out data. Report AUC; lower is better.
- (c) Negative control: RAID-style synonym or paraphrase attacks on the baseline. We must beat them on Layer 4 quality, not just on detectors.
- **Never used as a training reward.**

**Layer 4: pairwise LLM judge (every checkpoint, about $10–30).**
- Copy EQ-Bench's machinery: pairwise, both orders, margin `+…+++++`, Glicko/BT with style-control covariates (length, bullets, bold, emoji).
- Anchors: input draft = fixed low anchor; best frontier model with a persona prompt and anti-slop filter = the bar.
- Our own copy criteria: clear, specific/concrete, believable (no hype), sounds like a person in this role, would-send/would-click, kept facts.
- Two judges from different labs, neither from our base model's family. Reasoning-first (generative) prompt.
- **Report judge–human agreement every week. If it falls below 70% on the human slice, stop trusting it.**

**Layer 5: blind human panel (weekly, the ground truth).**
- 5 raters who are frequent LLM users and founders or copywriters. They see 50 pairs a week (ours vs the frontier bar), randomised and unhurried.
- Three questions per pair:
  - Q1: Which one did AI write? (detectability)
  - Q2: Which would you send, or which makes you reply or click? (persuasion)
  - Q3: Did either change the facts?
- **Ship rule:** win Q2 at least 55% *and* lower the AI-pick rate on Q1, at majority-of-5.
- Cost [E]: 5 × 1 hr × $25–40 ≈ $150–200/week via Prolific or friends. Our own hl-writer-panel agents pre-screen but never replace this.

**Layer 6: outcome study (once, at month end, about $400–800 [E]).**
- Meguellati-style preference test on Prolific: n≈200 per condition. Human-written founder copy vs frontier AI vs FeatherLM.
- Measure preference, "spotted AI" rate and the detection penalty.
- That is the YC slide: "people can't spot it AND prefer it".

**External sanity numbers (once per milestone):**
- WritingBench Advertising & Marketing + Business subsets (Apache-2.0; can use the 7B critic for near $0).
- EQ-Bench CW v3 (about $10; method only, no licence).
- lm-eval-harness IFEval, so instruction following doesn't regress.

**Public artefact:** publish HL-Copy-Bench: prompts, facts sheets and human references (licensed), plus the blind human leaderboard. Nobody owns "copy that reads human"; Hemingway-bench is closed and Springboards' data is unreleased.

---

## What to steal
- EQ-Bench's pairwise loop: both orders, truncation or length matching, `+` margins, Glicko-2, anchor models, slop slider kept separate from the score.
- slop-score's MIT lists and code, plus its "bring your own human baseline" switch.
- LMArena's style-control regression terms (length plus formatting counts) in our BT fit.
- NoveltyBench's "10 samples → distinct groups" diversity score.
- The Russell et al. rater profile (frequent LLM users, majority-of-5) for our human panel.
- Meguellati's two-number design (preference + detection penalty) for the month-end study.
- WritingPreferenceBench's lesson: length-match pairs, and use a reasoning reward model rather than a plain BT head.
- HelloBench-style yes/no checklists for faithfulness.

## What it changes for us
- **Evals alone are not enough for the 1-month goal.** They tell you if you're winning, not how to win. The month also needs: the human copy corpus and AI-ified pairs (data-curator), a frozen holdout, a 5-person panel booked from week 1, and one rented-GPU LoRA run per week. Evals are the steering wheel, not the engine.
- **Change the PLAN_30D success metric** from "sounds human" to **two numbers**: AI-pick rate down AND send/click preference ≥ the frontier baseline. Add a faithfulness gate. A human-likeness win that drops facts is a fail.
- **The Tastecut BT reward-model reuse is now conditional.** It must reach ≥70% agreement on length-matched human pairs, or we switch to a generative (reason-then-score) judge.
- **Do not anchor on EQ-Bench or LMArena rank** for the pitch. They measure fiction and fast first impressions. Our leaderboard is the pitch.
- **Base checkpoints matter.** The Computational Turing Test found instruction-tuned models less human-like than their base models. That supports starting the LoRA from a base or early-SFT checkpoint (TECH.md §D).

Open / unverified: Jones & Bergen sample size; MarketingFM and e-commerce paper details (snippets only); Exner et al. PDF not opened; live LMArena creative-writing standings not verified; the EQ-Bench judge (Sonnet 4.6 vs GLM 5.3/Opus 5) differs between README and about page.
