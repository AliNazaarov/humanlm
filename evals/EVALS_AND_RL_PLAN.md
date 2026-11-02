# FeatherLM: evals and RL plan

Written 2026-11-01. Applies your own notes on evals, RLHF and loop engineering to the startup: a model that writes like real humans instead of AI slop (continue-pretrain or fine-tune an open model on pre-2023 human writing, then RL toward human-like, high-quality prose across essays/admissions, creative, copywriting and academic).

Source keys (all in the founder's private learning notes unless noted):
`LES` LESSONS.md · `HEV` path-harness-evals.md · `PTR` path-post-training.md · `KRL` path-karpathy-rl.md · `FND` path-foundations.md · `CCL` path-claude-code-loops.md · `RND` `Video Notes/2026-10-28_loops-and-graphs-ROUNDUP.md` · `TCG` `Tastecut/GRAPH.md` · `RWD` `Tastecut/app/engine/reward.py` · `GRP` `hackathon-rl/eval.py` · `PATH` `AI Learning/AI learning path.md`.

Skill framing used: ecc:eval-harness (capability vs regression evals, code/rule/model/human graders, pass@k and pass^k, "code graders first, no flaky graders in release gates") and ecc:mle-workflow (iteration compact, data contract with split and leakage policy, promotion gates that fail closed, error-analysis loop, observation ledger, rollback artifact).

Honest caveat on sources: the per-video notes under `Video Notes/` for the evals/RLHF videos contain only transcripts and frames. The summaries that exist are the `path-*.md` files above, which were written from those videos (with timestamps). I cite those.

---

## 1. The 14 lessons from your notes that matter most here

1. **Judging is easier than specifying. Collect rankings (A vs B), not scores.** You cannot write the reward for "good prose", but a writer can say which of two passages is better. This is the whole reason RLHF exists, and the reason the data engine is writer-ranked pairs. (PTR §2 #1, FND #4, LES principle 10)
2. **Error analysis before any metric.** Read about 100 real outputs, one free-form note each on the first thing wrong, cluster, count. About 80% of problems come from about 20% of failure types. An LLM cannot do the first read for you because it does not know what "human" means to your customer. (HEV §3 #1-5, §5 #1-4, LES principle 2)
3. **One trusted taste-holder labels, not a committee** ("benevolent dictator"). Here: Ali plus one or two paid writers per style, each labelling their own style. Criteria will drift as you read outputs, so the rubric is a living document, re-read the data on a second pass (Shreya's example: "matters" turned up in every essay only on the second pass). (HEV §3 #3, #9; §5 #6)
4. **Judges are binary, single-purpose, and validated with TPR/TNR, never "agreement".** A judge that always says "pass" scores 90% agreement on a 10% error rate. Never 1-5 scales. Run each judge twice to check stability. (HEV §3 #7-8, §6 #2, LES change 5)
5. **LLM judges are gates, never the reward.** Optimise against a learned judge and it breaks within about 10 to 100 steps ("dhdhdhdh" scored perfect; "the the the" became the best joke). (KRL #3, FND #2, LES principle 4)
6. **Silent collapse is the failure mode of this exact startup.** Outputs "look fine" one by one, but ask ten times and you get the same thing. RL punishes diversity. Training on your own synthetic output makes it worse. Slop is partly a diversity problem, so diversity is a first-class eval and the RL objective must protect it. (KRL #4-5)
7. **RL will always optimise the easiest reward. Length is Goodhart's favourite axis.** Cheap signals take over a mix (GPT-4o sycophancy from thumbs-up data). Judges and people prefer longer, "complete-looking" text, so every comparison needs length control. (PTR §5 #1-2, #8, LES principle 3)
8. **Over-optimisation is not overfitting.** Proxy reward keeps rising, even on held-out data, while the true objective falls. Measure it by splitting the preference data in half, training two reward models, optimising on one, and watching the other diverge as KL from the start grows. Stopping at the right time is the skill. Signs: stock phrases, repetition, hedging, degenerate loops. (PTR §5 #4-7)
9. **KL and clipping do different jobs.** The objective is reward minus beta times KL to the reference model (total drift). PPO clipping limits per-batch movement. `pi_old` and `pi_ref` are different models; mixing them up is a common bug. If every sample in a GRPO group gets the same reward the advantage is zero and nothing is learned, so you need outcome diversity. (PTR §2 #3, §4 #5-8)
10. **Use the simple tools first: SFT, then rejection sampling / best-of-N, then DPO, then online RL.** Rejection sampling recipe: temperature 0.7-1.0, 10-30 completions per prompt, keep the top one per prompt, then SFT. Best-of-N is the same without the fine-tune and is the standard baseline. All three optimise the same objective. (PTR §2 #5, §3 #8-9, LES principle 11)
11. **Bradley-Terry reward model: trained on pairs, scores single items.** Loss is -log sigma(r_chosen - r_rejected), about one epoch to avoid overfitting. LLM-as-judge is good for filtering but underperforms a trained reward model on pairwise classification. You already built the small version of this. (PTR §3 #5, #7; `RWD`)
12. **The base model sets the ceiling; the prompt distribution defines what you learn.** You need about 1k-10k prompts per domain before gains show, and human data is still needed for out-of-distribution knowledge work. Prompt mix per style is a design decision, not an afterthought. (PTR §2 #7-8, §3 #1-2, #10)
13. **The maker never grades itself; a separate checker with fresh context, told to assume a defect.** Fresh context per unit of work, state in files, hard stops (3-8 passes), and the loop is only as good as its machine-checkable "done". Hard rules go in hooks/code, not capitals. (RND #3-6, CCL §4 #6, §3 #6, LES principle 12)
14. **Every mistake becomes a permanent change to the environment** (Hashimoto rule): a new eval case, a new check, a new banned pattern. Evals outlive prompts and code by one to three model generations. Keep a headroom check: if the model already passes at 95%+, the metric has no signal. (HEV §1 #1, CCL §1 #3, HEV §6 #2 and "Do this")

Two reusable assets from your own repos:
- `RWD` is a working Bradley-Terry with source weights (human 3.0, panel 1.0), 5-fold held-out accuracy, a minimum-pairs guard (12) and a prior fallback that blends toward the learned model as labels grow (`pairs / 60`). The shape carries over; the features change from video stats to text-level stats plus an LM-embedding head.
- `GRP` is the before/after-on-held-out-split pattern ("this number is your demo slide"). FeatherLM's equivalent is the blind-A/B win rate vs baseline, reported on a frozen prompt set.

---

## 2. Eval design: "human-ness + quality" per writing style

### 2.0 Principles (eval-harness framing)
- **Two eval families.** Capability evals ("can it write an admissions essay a reader believes?") and regression evals ("did the new checkpoint start using em-dashes again?"). Regression suite is pass^3 = 1.00 for release-critical checks; capability evals target pass@3 >= 0.90 on binary rubrics.
- **Grader order: code, then rule, then LLM judge, then human.** Slop-tell metrics are code graders. Binary rubrics are model graders only when a regex cannot decide. Humans decide ties and calibrate everything else.
- **Two bars** (HEV §5 #7). Internal drafts used to generate preference pairs get a lower bar. Anything shipped to a customer gets the high bar plus guardrails.
- **Evals are a living PRD.** The rubric is derived from data, versioned in git, and every cycle can add cases but cannot delete one without a note.

### 2.1 Step 0: error analysis first (Hamel/Shreya method)
1. **Build a prompt set per style** (see 2.2). Generate with the baseline models you will compete against: the raw open base model after continued pretraining, the instruction-tuned open model, and a frontier chat model. Keep model identity hidden from the labeller.
2. **Open coding.** 100 outputs per style, from mixed models. The labeller writes one sentence on the first, most upstream thing that feels non-human or low quality ("opens with a thesis restated twice", "every paragraph ends on a moral", "'tapestry' by line 3", "emotion is named, never shown"). Do not root-cause. Stop at saturation (nothing new in about 20 in a row).
3. **Include human controls.** Mix in real pre-2023 human pieces, blind. Two uses: (a) check the labeller can actually tell, which is the sanity floor for the whole project; (b) human pieces that still read as "AI" to the labeller reveal rubric bugs.
4. **Axial coding.** Cluster the notes with an LLM, refine by hand into actionable categories, add a "none of the above" bucket, pivot-table the counts. Persist as `evals/failure_modes.yaml` (the persisted artifact is the product, not the one-off run; HEV §5 #3).
5. **Second pass.** Re-read the data against the draft taxonomy and back-apply new labels to old outputs (HEV §5 #6). Repeat monthly and after every model release.
6. **Triage each failure mode into one of four moves**: (a) data fix (filter or add to training corpus), (b) decoding fix (sampler, logit bias, repetition penalty), (c) code check (regex/stat), (d) binary judge. Many need a fix, not an eval.
7. **Rank by harm x prevalence**, not by what the agent finds interesting (HEV §6 #4, #8).

Do not let an agent invent failure modes. It may cluster, count, and find more instances of a mode the human already named (HEV §5 #4).

### 2.2 Data contract for the eval set (mle-workflow)
- **Grain:** one row = (prompt_id, style, prompt, model_id, checkpoint, seed, output, decoding config).
- **Prompt sets per style, frozen into three tiers:**
  - `dev` (about 200 per style): used freely for iteration.
  - `gate` (about 150 per style): used only for promotion decisions, re-drawn each quarter, never in any training or reward-model data.
  - `canary` (about 40 per style): real customer-like prompts, human-written ideal references held privately, used to detect training-set contamination and reward hacking.
- **Splits are by prompt and by source document**, not by random row (leakage: the reward model must never see a prompt family from `gate`).
- **Leakage guard:** pre-2023 corpus de-duplication against the eval prompts and references (n-gram overlap and embedding similarity) before training.
- **Snapshot ID** for every eval run: corpus hash, prompt-set hash, code SHA, judge version, rubric version.
- **Data hygiene to settle early (blocking, not evals):** licensing and provenance of the pre-2023 corpus, and an AI-text contamination filter for any web-scraped data dated near the cutoff. This is a corpus decision, flagged here because a contaminated corpus makes every eval below meaningless.

### 2.3 Slop-tell metrics (code graders, run on every output, always logged separately)
Never collapse these into one "slop score" in the logs (HEV §6 "Keep ... checks as separate binary metrics"). A single aggregate is what the optimiser will game. Report each as a rate with a confidence interval against the **human reference distribution** for that style, not against a hard-coded threshold.

| Metric | How to compute | Report as |
|---|---|---|
| Banned-phrase rate | Curated list ("delve", "tapestry", "testament to", "navigate the complexities", "in today's fast-paced world", "it's important to note", "unlock", "landscape of", "a rich tapestry", "not only ... but also") seeded from your error analysis; expand from frequency-ratio mining (words overused vs the pre-2023 corpus) | hits per 1k words; % outputs with >= 1 hit |
| Em-dash rate | count of em-dashes per 1k words | rate vs human style distribution |
| "Not X but Y" / "It's not just X, it's Y" | regex family over contrast-reframes | per 1k words |
| Tricolon / rule-of-three | detect "A, B, and C" lists of parallel short items; adjective triplets | per 1k words and per paragraph |
| Paragraph-ending moral / summary line | last sentence of paragraph matches summary/aphorism patterns (needs small classifier or binary judge) | % paragraphs |
| Opener/closer boilerplate | first and last sentence n-gram repetition across outputs; "In conclusion", "Ultimately" | % outputs |
| Lexical diversity | MATTR / MTLD (not raw type-token ratio, which depends on length), vocabulary rank distribution | vs human reference band |
| Burstiness | sentence-length standard deviation and coefficient of variation; fraction of very short (<= 5 words) and long (>= 35 words) sentences; paragraph-length variance | vs human reference band |
| Repetition | repeated n-grams (3-5) within an output; self-BLEU / distinct-n **across** samples for the same prompt | distinct-n, self-BLEU |
| Cross-sample diversity (collapse detector) | embed 10 samples per prompt at T=1.0; mean pairwise cosine distance; number of unique first-5-word openings | per-prompt and mean; this is the "ask 10 times" test from `KRL` #4 |
| Length | tokens and words | always logged; all comparisons length-matched or length-controlled |
| Template-leak | unfilled "[Your Name]" / "[Company]" / "As an AI" / refusal boilerplate | binary, must be 0 |
| Specificity | density of named entities, numbers, concrete nouns per 100 words | vs human reference band |

Two rules:
- **Target the human distribution, not zero.** Humans use em-dashes and triplets too. The goal is a rate that sits inside the human reference band for that style. A model that drives em-dashes to zero is gaming, and people notice the absence.
- **Style-specific bands.** Admissions essays, ad copy, fiction and academic prose have very different burstiness and sentence length. Compute reference bands per style from the pre-2023 held-out human set.

### 2.4 Binary pass/fail rubrics (model graders, validated)
One failure mode per judge. Each answers PASS or FAIL plus a one-line quote of the evidence; never 1-5. Start with 4-7 judges total across styles (HEV §3 #6). Candidates come from the error analysis; examples to seed it:

Shared (all styles):
- `J1 generic_opener`: opens with a context-setting or restating sentence that adds nothing.
- `J2 told_not_shown`: names an emotion or quality instead of evidencing it.
- `J3 symmetric_structure`: paragraphs or sentences follow the same balanced template.
- `J4 hedge_and_moralise`: hedging, disclaimers, or a closing lesson the writer did not earn.
- `J5 invented_specifics`: concrete detail that is implausible or contradicts the brief (matters for academic and admissions).

Per style:
- Admissions/personal essay: `voice_is_a_specific_teenager_not_a_committee`, `one_concrete_scene_early`.
- Creative: `subtext_present`, `ending_not_tied_with_a_bow`.
- Copywriting: `names_a_specific_buyer_situation`, `no_benefit_stack_cliche`.
- Academic: `claims_are_hedged_where_a_human_would_hedge_and_not_elsewhere`, `citations_not_fabricated` (code check where possible).

Judge hygiene (all from your notes):
- Cheapest grader first: if a regex decides it, it is not a judge.
- Held-out calibration set of at least 50 human-labelled outputs per judge (balanced PASS/FAIL), labelled **blind to the judge's verdict** (labelling after seeing the model's answer biases you; HEV §6 #7).
- Report **TPR and TNR** with confidence intervals, plus a confusion matrix. Promotion to "blocking" requires TPR and TNR above an agreed bar (start: both >= 0.85). Below that, the judge is report-only.
- **Stability:** run each judge twice (and with option order swapped for pairwise); verdict flips above 5% means the rubric text is ambiguous.
- **Different model family** than the generator, fresh context, instruction to assume at least one problem (maker never grades itself).
- **Judge drift check** every release: re-run the calibration set, alarm if TPR/TNR moves.
- Judges **block or route to a human, they do not provide reward** (see 3.5 for the one permitted exception).

### 2.5 Blind human A/B preference tests (the ground truth)
This is the primary metric. Everything else is a diagnostic.
- **Format:** pairwise, blind, randomised position, same prompt, length-matched within a tolerance (or length-controlled analysis). Forced choice plus a one-line reason (reasons feed the error analysis) plus an optional "both bad".
- **Arms to compare:** FeatherLM checkpoint vs (a) frontier chat model with a "write like a human" prompt (the real competitor), (b) the instruction-tuned open base, (c) a pre-2023 human piece (the ceiling), (d) previous FeatherLM checkpoint (regression).
- **Raters:** per style, paid writers/editors who read that kind of text for a living (admissions readers, copy chiefs, fiction editors, academics). One lead labeller per style as benevolent dictator; others for agreement checks. Track inter-rater agreement; if two experts would not grade the same way, the task is not eval-ready (HEV §6 #1).
- **Two questions, asked separately:** "Which is better?" and "Which sounds more like a real person wrote it?" (human-ness and quality can diverge; a clumsy human sentence is human but not good).
- **The "would you have guessed AI?" test** on single items (not pairs) with a human-piece control mixed in, to estimate a false-positive rate on real humans.
- **Statistics:** win rate with a bootstrap CI and Bradley-Terry/Elo ranking across arms; minimum 150 pairs per style per decision; report per-prompt-category slices (e.g. short vs long, formal vs casual).
- **Cost control:** use the panel/LLM-pre-screen only to choose which pairs humans see (e.g. skip pairs where models are near-identical); never replace the human pair label.
- **Labelling UI:** a simple HTML viewer with buttons and a reason box (HEV §6 #5: markdown files make you lazy). Persist every label with rater ID, time and prompt/model hashes.

### 2.6 Detector scores: one signal, never the objective
Run two or three public AI-text detectors plus a small in-house detector (classifier on human-vs-model text).
- **Use them as:** a monitoring dashboard and a red-flag alarm (sudden jump in detectability after a training run), and as one input in the quality report.
- **Do not:** use them as a reward, or as a promotion gate on their own. Reasons: they have high false-positive rates on real human writing (especially non-native and formulaic genres, which includes academic and admissions prose), they shift across vendors, they are cheap to Goodhart (detector evasion is not human-ness: it yields weird, noisy text), and a model optimised against one fails on the others.
- **Always report detector scores next to the human-control baseline** (what fraction of real pre-2023 essays do they flag?). If a detector flags 20% of real humans, a "0% detected" model has simply learned a different style of artefact.
- **Hold-out detector:** keep one detector entirely out of any training or tuning loop so it remains an honest check.

### 2.7 LLM-judge calibration against human labels
1. Humans label a calibration set (blind) for each rubric: PASS/FAIL per judge, and pairwise winner for the pairwise judge.
2. Judge runs on the same set; compute TPR, TNR, Cohen's kappa (as a supplement, never instead of TPR/TNR), and pairwise accuracy.
3. Iterate the rubric text on the **dev** half; report on the **held-out** half.
4. Pairwise LLM judge is allowed only as a pre-screen/filter, and only if its pairwise accuracy against human labels is above an agreed bar (start: 0.75) **after length control**. A trained reward model should beat it (PTR §3 #7); if not, the reward model is under-trained.
5. Re-calibrate on every new generator checkpoint (the failure modes of a better generator are different), and every month (criteria drift).
6. Track judge-vs-human disagreement cases as a first-class queue: these are the best new eval cases.

### 2.8 Eval suite layout and promotion gates (fail closed)

```
FeatherLM/evals/
  failure_modes.yaml          # axial codes + counts, versioned
  prompts/{dev,gate,canary}/  # per style, frozen with hash
  tells/                      # code graders (section 2.3)
  judges/                     # binary rubrics + calibration sets + TPR/TNR reports
  human/                      # A/B pairs, labels, rater stats
  runs/<run_id>/report.md     # observation ledger entry
  baseline.json               # regression baselines per checkpoint
```

Promotion gate for a checkpoint (all must hold on `gate` prompts; any miss blocks):
1. Blind human A/B win rate vs the frontier-chat baseline >= target (set from a pilot; start by requiring significantly above 50% in at least 3 of 4 styles) and vs previous checkpoint not worse.
2. All slop-tell rates inside the human reference band for their style, or no worse than previous checkpoint and trending toward it.
3. Cross-sample diversity (distinct-n, pairwise distance) >= a floor set at the previous best checkpoint, and not lower than the SFT stage by more than a tolerance.
4. Binary judges: pass rates at or above previous checkpoint; no judge's calibrated TPR/TNR below its bar.
5. `canary` set: human-written references still beat or tie in blind comparison at the expected rate (if the model "beats" private human references too often, suspect contamination or judge gaming, not genius).
6. Length distribution matches the reference band (no length drift).
7. Detector scores: no regression vs the human-control baseline on the held-out detector.
8. Rollback artifact named: previous checkpoint, config, data snapshot.

Observation ledger entry per run (from mle-workflow): change, metric movement, slice movement, unexpected errors, decision, tradeoff accepted, lesson captured, regression added, next experiment.

Headroom rule: if the current model passes a judge at 95%+, retire it from the gate and keep it only as a regression test (HEV §6 #2).

---

## 3. The RL loop

### 3.0 Staged plan and why
Follow your own ladder: imitation, then best-of-N, then DPO, and only then online RL (LES principle 11; PTR §2 #4-5). Each stage is gated by the evals in section 2 before the next stage starts.

| Stage | What | Gate to leave the stage |
|---|---|---|
| 0 | Continued pretraining on pre-2023 human text (style-conditioned metadata tags, e.g. genre, register, decade) | Perplexity on held-out human text improves; slop-tell rates of base samples already inside human band |
| 1 | SFT on instruction/prompt-to-human-text pairs (see 3.1) | Beats instruct baseline on blind A/B in dev; diversity retained |
| 2 | Preference data + reward model + best-of-N/rejection sampling | Reward model held-out pairwise accuracy at bar; best-of-N lifts human win rate over SFT |
| 3 | DPO on writer-ranked pairs | Gate (2.8) passes vs stage 2; diversity floor holds |
| 4 | GRPO/online RL with mixed reward, tight KL | Gate (2.8) passes; over-optimisation test (3.6) clean |

### 3.1 SFT: what you can and cannot get from pre-2023 text
- **Gap to plan for:** pre-2023 text is not instruction-following data. Continued pretraining teaches the distribution; you still need (prompt, human text) pairs. Construct them by **back-translation**: take human passages, have a model write the brief that would have produced them (genre, audience, constraints, length), then train prompt to passage. Hold out whole documents for eval.
- **Pitfall from your notes:** chat template and formatting bugs bleed small-team time; train/inference format mismatches (PTR §3 #4). Write one format spec and a round-trip test.
- **Pitfall from your notes:** train only on human text for style; do **not** mix in model-generated text in the SFT target (self-training collapses diversity; KRL #4). Use synthetic data only for prompts/briefs, never for targets.
- **Prompt budget:** about 1k-10k prompts per style before gains show; plan the prompt distribution to match what customers will actually ask (PTR §3 #1-2).
- **Eval set up before training:** the SFT design loop is "set evals first, mix data, measure, curate for gaps, repeat" (PTR §3 #3). Section 2 is built first; the data work follows.

### 3.2 Preference data: human vs model, and writer-ranked
Three pair sources, weighted like `RWD`'s source weights (human > panel):
1. **Human-vs-model pairs (cheap, large, but easy).** Real pre-2023 piece vs model output for the same brief. This teaches "which looks human" but a model can learn artefact detection that does not transfer (it learns the style of the corpus era, not quality). Use with a low weight and never alone.
2. **Model-vs-model pairs ranked by writers (the core).** For each prompt, sample N=4-8 outputs at T=0.8-1.0 from the current policy (and mix in earlier checkpoints for coverage). Writers rank them best to worst (ranking is easier than scoring; FND #4) and give a reason. Convert rankings to pairs. Weight: human 3.0 (as in `RWD`).
3. **Edit pairs (high-signal).** A writer edits a model output to make it sound human. (edited, original) is a pair, and the diff is directly an error-analysis note. This is the closest analogue to your "human edits" in a previous project's plan (LES principle 11).

Rules:
- **Length control in the data:** build pairs so chosen is not systematically longer; where it is, include counter-pairs (shorter chosen) or regress length out (PTR §5 #8).
- **Diversity of prompts** over diversity of samples per prompt; label across all four styles.
- **Hold out** 20% of prompts and raters for reward-model evaluation, and a further `gate` set never used for training anything.
- **Labeller consistency checks:** repeat 10% of pairs blind to measure self-consistency; drop labellers below bar.
- **Log everything with stable IDs** (prompt_id, model_id/checkpoint, sample seed, rater_id, timestamp, rubric_version), joining on IDs not strings (LES principle 7).
- **Cold-start trick:** use the slop-tell metrics only to **choose which pairs to show** (e.g. pair a high-tell output with a low-tell one), not as labels.

### 3.3 Reward model (reuse your Bradley-Terry idea)
- **Two layers, mirroring `RWD`:**
  - *Interpretable layer (ship first):* Bradley-Terry over text features (the slop-tell metrics from 2.3: banned phrase rate, em-dash, tricolon, MATTR, burstiness stats, repetition, specificity, length). Same maths as `RWD` (`P(A over B) = sigmoid(w . (z(A) - z(B)))`, standardised features, L2, source weights, 5-fold held-out accuracy, minimum-pairs guard). Benefit: you can read the weights ("em-dashes get a big negative weight"), which doubles as error analysis and is immune to the adversarial-example problem of neural scorers.
  - *Neural layer:* a small LM with a scalar head trained with `-log sigma(r_chosen - r_rejected)`, about 1 epoch (PTR §3 #5). Initialise from the SFT model or a smaller sibling.
  - *Blend like `RWD`:* trust the learned model more as pairs grow, fall back to a prior (here: distance to the human reference band of tell metrics) when labels are few. Keep the fallback so the system works on day one.
- **Per-style heads or one model with a style token?** Start per style (labels are style-specific; "human" differs between a sonnet and a grant proposal). Share a base.
- **Ensemble** of at least 3 reward models (different seeds/data folds). Use the **mean minus a disagreement penalty** (pessimistic/conservative reward) so the policy is not rewarded where the models disagree. This is the cheapest known mitigation for the estimation error in PTR §5 #7.
- **Reward-model evals:** held-out pairwise accuracy by style and by source; accuracy on the length-confounded slice; accuracy on writer-edit pairs; calibration. Gate: accuracy at an agreed bar and not driven by length.
- **Do not train the reward on detector output.**

### 3.4 DPO first
- Why first: no online sampling machinery, no separate reward in the loop, stable, and uses the writer pairs directly (PTR §2 #5, #4).
- Data: writer-ranked pairs from 3.2, with `pi_ref` = the SFT model. Start with a conservative beta (higher beta = stay closer to reference).
- Watch for: chosen and rejected log-prob both dropping (likelihood displacement), length drift, and diversity loss. Track all three each epoch on the dev set, not just reward margin.
- Iterate **on-policy**: after one DPO round, sample from the new policy, get fresh writer rankings on the new samples, and repeat (new pairs matter more than more epochs).
- Compare against **best-of-N with the reward model** as the baseline DPO must beat (PTR §3 #9). If best-of-N already gets the win rate, you may not need online RL for v1.

### 3.5 GRPO / RL with a mixed reward
Only after DPO plateaus on the gate. Start with a small model or a short run, shaped like the `hackathon-rl` setup (before/after on a held-out split).

Reward design (keep every component logged separately and visible so you can see which is moving; LES principle 3):

```
R = w_h * R_human_RM          # ensemble reward model, conservative (mean - lambda*std)
  + w_t * R_tells             # distance of tell metrics from human band, capped, per-style
  + w_d * R_diversity         # within-group diversity bonus (distinct-n / embedding distance)
  - w_L * length_penalty      # penalise length outside band; makes length unrewarded
  - beta * KL(pi || pi_ref)   # drift control
hard gates (R = 0 / sample dropped): template leak, refusal boilerplate, language mismatch,
                                      copying >N-gram overlap from training corpus (anti-memorisation),
                                      judge-blocking failures from section 2.4
```

- **Reward weights:** human reward model dominates; tell rewards are capped and band-shaped (reward being *inside* the band, not further from it), so there is nothing to gain from driving em-dashes to zero.
- **Group-level diversity term is essential.** GRPO advantage is (r - mean)/std within the group; if every sample scores the same, advantage is zero and nothing is learned (PTR §4 #4-5). A diversity term and a decent sampling temperature keep groups informative, and it directly attacks silent collapse (KRL #4-5).
- **Judges as reward?** No. The one allowed use of an LLM judge in the loop is as a **hard gate** (drop failing samples) with a calibrated TPR/TNR, since gates cannot be gamed by increasing a score. Everything soft goes through the reward model that humans trained.
- **Rewards that cannot be faked:** there is no verifiable reward in prose. The nearest substitutes are (a) held-out human blind A/B (too slow for the loop), (b) the conservative reward-model ensemble, (c) hard gates. Plan for RL to run only for a few hundred updates and then stop (FND #2); do not expect AlphaGo-style open-ended gains.
- **Algorithm choice:** GRPO or RLOO (group baseline, no value model). Remember `pi_old` (generated the batch) vs `pi_ref` (frozen start for KL) are different (PTR §4 #7). Clipping handles per-batch movement; KL handles total drift (PTR §4 #8).

### 3.6 Avoiding reward hacking and over-optimisation
This is the part of your notes (Lecture 9) that decides whether the startup works.

1. **KL control.** Always train against a frozen reference. Track KL to `pi_ref` per step and stop on a **KL budget**, not a step count. Use an adaptive-beta controller to hold a target KL. Treat KL crossing the budget as an automatic stop, like a Ralph max-iterations guard.
2. **Early stopping on held-out true objective, not on training reward.** Every N steps, run the `dev` human-proxy set: (a) blind A/B against the previous checkpoint with a small writer panel (or, for fast iteration, the held-out second reward model), (b) full tell-metric panel, (c) diversity panel. Over-optimisation shows as training reward rising while these peak and decline (PTR §5 #4). Save checkpoints each interval and pick the peak.
3. **Split-RM over-optimisation test (Anthropic method, PTR §5 #5).** Split preference data in half; train RM-A and RM-B. Optimise against RM-A; plot RM-B's score vs KL. When RM-B diverges from RM-A, you have found the safe KL for that data size. Re-run whenever you add data.
4. **Pessimistic ensemble reward** (3.3) and **best-of-N as the fallback** if RL is unstable. If an RL checkpoint does not beat best-of-N, ship best-of-N.
5. **Length is controlled by construction:** length penalty band in the reward, length-matched A/B, and a length-regressed analysis. Watch mean and tail length each step.
6. **Watch the known degenerate signs** (PTR §5 #6): stock phrases, repetition, hedging, and degenerate loops. Automate them as per-step alarms: new top-n-gram frequency spikes, unique-opening collapse, cross-sample cosine collapsing, entropy dropping.
7. **Goodhart on detectors.** Detectors are excluded from reward and from model selection (2.6). One held-out detector stays untouched. If you ever want a "detector-aware" objective, do it only as a *monitor with an alarm* ("detector score moved while A/B did not, investigate").
8. **Goodhart on your own tells.** Tell metrics are reward only as capped, band-shaped terms, and a **canary tell list is kept secret**: a few additional tells (not in the reward) monitored for whack-a-mole. If banned words disappear but new tics rise, the model has learned the metric, not the style.
9. **Goodhart on the reward model.** Refresh it with on-policy pairs each round (new samples are where it is weakest, per the estimation-error point; PTR §5 #7). Hold an unseen set of writers for evaluation.
10. **Judge adversarial examples.** Anything an LLM judge scores is audited by sampling the highest-scoring outputs each round and having a human read them ("read the top 20 of the run"). The "dhdhdhdh" case would have shown up in minutes (KRL #3).
11. **Contamination and memorisation.** Anti-copy gate against the pre-2023 corpus; RL must not rediscover memorised passages. Canary set (2.8 #5) detects it.
12. **Pre-register the stop rule** (intent debt, CCL §4 #7): write the objective, the stop rule and the held-out evals in the spec before the run. The optimiser cannot "win" by loosening the checks; the checks live in files and hooks it cannot edit (LES principle 12).
13. **March of nines.** The first demo will look human on the first sample. Nine-nines for "reads as human to an expert, ten times in a row, across styles" is where the work is (KRL #7). Measure with pass^k on the binary rubrics (all k samples pass), not a single good sample.

---

## 4. Loop-engineering setup: the nightly cycle

Principle mapping (RND, CCL §4-6, `TCG`): graph where steps are known, loop where fuzzy; separate checker with fresh context; state in files; hard stops; one human gate at the least reversible step; structured output at every branch.

### 4.1 The agents (named in the style of your `tc-*` and `rlg-*` graphs, prefix `hl-`)

| Agent | Job | Writes | Notes |
|---|---|---|---|
| `hl-orchestrator` | Runs the nightly graph, enforces budgets and stop rules, writes the run summary | `runs/<id>/SUMMARY.md`, `queue.md` | Never generates or grades |
| `hl-generator` | Samples from the current best checkpoint over the nightly prompt batch (dev + fresh prompts), several seeds, mixed with baseline arms | `runs/<id>/outputs.jsonl` | Maker; no access to judges or labels |
| `hl-tells` | Runs the code graders (2.3) over every output; computes human-band deltas and diversity | `runs/<id>/tells.json` | Deterministic; no LLM |
| `hl-judge` | Runs the calibrated binary judges (2.4), twice each, different model family, fresh context | `runs/<id>/judges.json` | Separate from generator; "assume a defect" |
| `hl-grader-audit` | Re-runs the calibration set, checks TPR/TNR drift, flags disagreements with human labels | `judges/calibration_report.md` | Guards the judges (HEV §3 #8-9) |
| `hl-error-analyst` | Clusters new human notes and failed outputs into the existing taxonomy, counts, finds more instances of named failure modes, proposes (not invents) new categories for the human to accept | `evals/failure_modes.yaml` diff, `runs/<id>/errors.md` | Per HEV §5 #4: human names modes, agent counts and finds instances |
| `hl-case-writer` | Turns confirmed failures into new eval cases: prompt + failing output + pass criterion + which grader; tags capability vs regression | `evals/cases/*.yaml` | Every mistake becomes a permanent case (Hashimoto rule) |
| `hl-pair-builder` | Builds tomorrow's labelling queue: picks pairs for writers (diverse prompts, hard pairs, control items, 10% repeats), builds the HTML viewer batch | `human/queue/<date>/` | Uses tells and RM only to select, not to label |
| `hl-reward-modeler` | Retrains the Bradley-Terry (interpretable + neural) on all labels so far, runs the split-RM over-optimisation test, publishes held-out accuracy | `model/reward/<ver>/report.md` | Reuses `RWD` design; refuses to train under minimum pairs |
| `hl-trainer` | Runs the training stage selected by the orchestrator (SFT refresh, DPO round, or RL run) within a compute and KL budget; writes checkpoints | `model/ckpt/<id>/` | Runs only on trigger conditions (4.3), not every night |
| `hl-gatekeeper` | Applies the promotion gate (2.8) to a candidate checkpoint, fail closed, names rollback artifact | `runs/<id>/GATE.md` | Separate from trainer and generator; never edits |
| `hl-skeptic` | Red-team: tries to find prompts that expose slop, tries to game the metric, reviews top-scoring outputs for adversarial patterns | `runs/<id>/redteam.md` | Reads the "top 20" (3.6 #10) |
| `hl-corpus-scout` | Monitors the training/eval corpus for contamination (AI text, eval leakage), proposes dedup | `data/CORPUS_REPORT.md` | |

Human roles (the single gate, at the least reversible step: promotion/ship):
- **Ali** (benevolent dictator): approves rubric changes, new failure modes, promotions.
- **Writers/editors panel:** label the daily queue (target: a fixed number of pairs per day) and the A/B on candidate checkpoints.

### 4.2 The nightly graph

```
[23:00]  hl-orchestrator reads queue.md + last SUMMARY.md + budget caps
   |
   +-> hl-generator       (samples: current best, previous best, baseline arms; dev + fresh prompts)
   |       |
   |       v
   +-> hl-tells  ||  hl-judge        (parallel; fresh contexts)
   |       |             |
   |       +------+------+
   |              v
   +-> hl-grader-audit    (are the graders still trustworthy tonight?)
   |
   +-> hl-error-analyst   (cluster tonight's failures + the writers' day notes; update counts)
   |
   +-> hl-case-writer     (confirmed failures -> new regression/capability cases)
   |
   +-> hl-skeptic         (try to break the metrics; read top-scored outputs)
   |
   +-> hl-pair-builder    (tomorrow's labelling queue for writers)
   |
   +-> [trigger check]    -> hl-reward-modeler (if enough new pairs) 
                          -> hl-trainer (if trigger conditions met; budget-capped)
                          -> hl-gatekeeper (on any new checkpoint)
   |
[06:00]  hl-orchestrator writes SUMMARY.md: what moved (per tell, per judge, per slice), new failure
         modes proposed, new cases added, labels needed today, gate status, any alarms
```

Ralph-style mechanics for the state (CCL §5-6, RND #5):
- `queue.md` / `evals/cases/*.yaml` hold task items with a `passes: true/false` flag; one item per fresh run; append-only `progress.txt` of learnings (say "append", not "update"); commit every cycle so git history is memory.
- Fresh context per agent run; they read files, not chat history.
- Max-iterations argument required on every loop script; compute and money caps in config.

### 4.3 Retrain triggers (not every night)
- **SFT refresh:** corpus changed materially, or a failure mode is traced to data (filter or add), and gate headroom is gone.
- **DPO round:** at least N new writer-ranked on-policy pairs (start: 1,500 per style pooled, adjust from the split-RM test) and the reward model's held-out accuracy meets bar.
- **RL run:** DPO plateaued on the gate for two rounds and the over-optimisation test shows a safe-KL region; run is KL-budgeted and checkpointed.
- **No retrain:** if the only changes are tell-metric movements with no blind A/B movement, go to decoding/data fixes first.
- Each trigger and its numbers are in config the trainer cannot edit.

### 4.4 Guardrails for the loop itself (hooks, not wishes)
- `hl-trainer` has no write access to `evals/`, `judges/`, `prompts/gate`, or calibration sets (a pre-tool hook blocks it).
- `hl-generator` has no read access to labels or `gate` references.
- Any change to a rubric or a band requires a human-approved commit and a note in the observation ledger.
- Alarm hooks (stop the run and notify): KL over budget, diversity floor breached, length drift, judge TPR/TNR drift, the blind A/B on canary falling, or a tell moving into a "too perfect" region (e.g. em-dash rate below the lowest human decile).
- Cost per cycle and cost per writer-label are logged next to quality (HEV §2 "cost per touch" analogue).

### 4.5 Build order (first two weeks)
1. Freeze `dev/gate/canary` prompts for one style (start with the one you can label best) and set up the writer viewer (HTML with buttons and reasons).
2. Run the 100-output error analysis, produce `failure_modes.yaml` v1 and the first 4-7 tells + judges; validate judges with TPR/TNR on 50 blind labels each.
3. Build the tell panel and the human reference bands from a held-out pre-2023 slice.
4. Stand up the nightly graph with only `hl-generator`, `hl-tells`, `hl-judge`, `hl-error-analyst`, `hl-orchestrator` (read-only, no training). Get the loop reliable first.
5. Collect the first 500 writer-ranked pairs; train the interpretable Bradley-Terry (port `RWD`); report held-out accuracy and read the weights.
6. Only then add DPO. Add GRPO last.

---

## 5. Risks and open decisions

- **Corpus:** licensing and provenance of pre-2023 text, plus contamination near the cutoff. Blocking for training, not for evals.
- **"Human" is plural.** The reference distribution is a mix of eras and registers. Per-style, per-register bands and conditioning tags are needed or the model averages into a new kind of bland (a different slop).
- **Cost of expert labels.** Pair budget drives everything; the interpretable reward model plus selection-by-uncertainty keeps labels cheap. Decide the monthly label budget and writers early.
- **Detector arms race.** Public detectors change; the product claim must rest on blind human A/B, not detector scores.
- **Model-size ceiling.** The base model sets the ceiling (PTR §2 #7); an RL that works well on a 7B may reveal the base is the limit, not the method.
- **Success criterion to pre-register:** state in writing before any training what win rate over which baseline, in how many styles, counts as success, so the result cannot be redefined after the fact.
