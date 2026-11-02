# FeatherLM: technical research (build an LLM that writes like pre-AI humans)

Generated 2026-11-01. Method: ~25 web searches, 6 page fetches, GitHub API for stars/licences (verified live). Labels: **[S]** = sourced, **[E]** = my own estimate/arithmetic (6ND FLOPs, 40% MFU, $2-3/H100-hr), **[K]** = from my background knowledge, not re-verified today. Treat [E] and [K] as unverified.

## 0. Bottom line

Do NOT pretrain from scratch. Build in 3 stages, each shippable:
1. Week 1, about $0-50: wrapper on a frontier API or open model with antislop sampling, base-model-style prompting, and human few-shot excerpts. Establishes the eval harness.
2. Weeks 2-5, about $300-1,500: LoRA SFT + FTPO/antislop on an open 8B-32B model, trained on curated human prose (reverse-distillation pairs, Gutenberg-style data). Biggest quality jump per dollar.
3. Only if stage 2 plateaus, about $1-4k: continued pretraining (CPT) of an open 7-8B base on 2-10B tokens of curated pre-2022 prose, then re-run stage 2 on top.

Scratch pretraining is a research stunt (nanochat $100-800 gives toy models; TimeCapsuleLLM shows hobby-scale output is incoherent). Use it only as a learning exercise.

---

## A. Evidence that AI writing got worse / converged

| Claim | Evidence | Verdict |
|---|---|---|
| Training on model output degrades models ("model collapse") | Shumailov et al., Nature 631:755 (Jul 2024). Tails of the distribution vanish; repeated phrases. Paper's framing is *indiscriminate* recursive training, not "all synthetic data is bad". https://www.nature.com/articles/s41586-024-07566-y , PDF mirror https://www.pure.ed.ac.uk/ws/portalfiles/portal/460496122/ShumailovEtalNature2024AIModelsCollapseWhen.pdf | Real, but about recursive training, not about why ChatGPT sounds bland today. Supports "keep human data curated". |
| RLHF lowers output diversity | Kirk et al., ICLR 2024, "Understanding the Effects of RLHF on LLM Generalisation and Diversity": RLHF generalises better than SFT but gives less diverse outputs. https://arxiv.org/abs/2310.06452 . Counter-evidence: a 2025 preprint finds preference-tuned models show *more* lexical-pattern diversity in creative writing (found via search, not opened). | Direction well supported; for creative writing it is metric-dependent. |
| Post-training flattens fiction | "Narrative Flattening" (Li, Zhu, Wu, Bao, Evans; EMNLP 2026 main). Compares OLMo 32B Base vs SFT vs DPO vs RLVR against StoryStar, TMAS and New Yorker text. Thematic motion, emotional intensity and stylistic diversity shrink step by step; professional literary fiction is compressed most. https://arxiv.org/abs/2605.27878 | **Strongest controlled evidence for the user's claim**: same weights, only post-training varies. |
| Cross-model homogeneity | "Artificial Hivemind" / Infinity-Chat (Jiang, Choi et al.), NeurIPS 2025 Best Paper. 26K open-ended prompts, 70+ models, 31K human annotations: models repeat themselves AND each other; reward models and LLM judges poorly calibrated to idiosyncratic human taste. https://arxiv.org/abs/2510.22954 , https://blog.neurips.cc/2025/11/26/announcing-the-neurips-2025-best-paper-awards/ | Strong. Also warns: LLM-judge rewards will not capture taste. |
| Creative homogeneity | "We're Different, We're the Same" https://arxiv.org/pdf/2501.19361 | Supports above. |
| Humans also converge when using LLMs | Linguistic-diversity shrinkage https://arxiv.org/pdf/2502.11266 ; DeepMind "How LLMs Distort Our Written Language" https://arxiv.org/pdf/2603.18161 (LLM edits push essays to a region of embedding space with no human precedent, and shift stance). Counterpoint: "Writing in Symbiosis" https://arxiv.org/abs/2512.13697 finds mixed, author-dependent effects. | Mixed on humans; solid on LLM edits. |
| "Delve" and friends | Kobak et al., "Delving into ChatGPT usage in academic writing through excess vocabulary" https://arxiv.org/abs/2406.07016 : PubMed 2010-2024, counterfactual from 2021-22; "delves" about 25x expected, "showcasing"/"underscores" about 9x; at least 13.5% of 2024 abstracts LLM-processed (v5). Language Log notes "delve" was already rising and absolute counts are small https://languagelog.ldc.upenn.edu/nll/?p=64877 . A later paper reports the words dropped after publicity (unverified). | Real signal, but individual words are a moving target. Ban lists must be refreshed; style-level fixes beat word lists. |
| Slop frequency | Antislop paper: some patterns appear over 1,000x more often in LLM text than human text. https://arxiv.org/abs/2510.15061 | Strong. |
| EQ-Bench Creative Writing v3 | Leaderboard with Elo, rubric, repetition, length, and a **slop score** (word list + trigram list over-represented vs human baselines + "Not X, but Y" patterns). https://eqbench.com/creative_writing.html , https://github.com/EQ-bench/creative-writing-bench , https://github.com/sam-paech/slop-score (42 stars, licence unasserted), https://github.com/sam-paech/slop-forensics (373 stars, MIT) | Usable as a free automatic metric. It measures slop, not taste. |
| "Opus 3 had better prose" | Only anecdotes (blog posts, Reddit, an AirOps May 2024 write-up calling Opus a standout for creative writing). Other users say 4.7-era models are better or worse; contested. No controlled study found. | Reputation real, evidence anecdotal. |
| Base vs chat | Narrative Flattening and Kirk et al. support "base > chat" on diversity. Janus-style "raw completion" claims are disputed (commenters say it is not a true base model; Claude character persists). | Base models give the most human distribution but poor controllability. |

**Verdict on "2023-2024 models wrote better":** The *mechanism* is supported (heavier SFT/DPO/RLVR post-training compresses style; cross-model convergence; slop rates). The *time trend* as a clean claim ("2023 > 2025") is NOT proven: no controlled year-over-year study found, newer models also score higher on LLM-judged benchmarks, and fashionable words like "delve" were self-correcting. Reframe the pitch as "less post-training collapse, plus human-grounded style", which is defensible, rather than "older models were better".

Honest caveat for the founder: any base model released after late 2022 (including Qwen3, Llama 3+, Gemma) was pretrained on web data containing ChatGPT text and on deliberate synthetic data [K]. Truly pre-AI bases are Pythia/GPT-J (Pile, 2020), Llama 1/2, OLMo 1 (Dolma 2023) and Mistral 7B v0.1 [K]; they are weaker and old.

---

## B. Anti-slop techniques (ranked by quality per dollar)

1. **Antislop sampler** (sam-paech/antislop-sampler, 359 stars, Apache-2.0, last push 2026-03; https://github.com/sam-paech/antislop-sampler). Backtracks on banned strings/regex, lowers the probability of the match start, resamples. Handles 8,000+ patterns where plain token banning breaks around 2,000. Cost: slower inference. Paper: https://arxiv.org/abs/2510.15061 (Paech, Roush, Goldfeder, Shwartz-Ziv; ICLR 2026 poster). Cost to try: about $0.
2. **FTPO, Final Token Preference Optimization** (same paper; code in sam-paech/auto-antislop, 207 stars, MIT per paper, GitHub shows no licence metadata, https://github.com/sam-paech/auto-antislop , last push 2026-07-29). About 90% slop reduction while holding or improving GSM8K, MMLU and creative writing; plain DPO suppresses less and degrades writing quality and lexical diversity. Pairs come from the sampler's backtracking events. Paper recommends FTPO over the sampler for production. Cost: a LoRA run, tens of dollars [E]. Also antislop-vllm https://github.com/sam-paech/antislop-vllm (34 stars).
3. **Gutenberg DPO / ORPO fine-tunes.** jondurbin/gutenberg-dpo-v0.1 (918 rows, CC-BY-4.0): chosen = human chapter from Project Gutenberg, rejected = chapter written by llama-2-13b-chat / bagel-7b / dolphin-34b from a synthetic prompt. https://huggingface.co/datasets/jondurbin/gutenberg-dpo-v0.1 . nbeerbower's Mistral-Nemo-12B finetunes (gutenberg-12B-v4: 1-3 epochs on a single A100 in Colab; gutades-12B: ORPO on one RTX 3090) https://huggingface.co/nbeerbower/mistral-nemo-gutenberg-12B-v4 , https://huggingface.co/nbeerbower/mistral-nemo-gutades-12B . Cost: under $20. Caveat: rejected samples are weak-model text, so the model learns "not Llama-2", not "not GPT-5"; refresh rejects with a modern model.
4. **Reverse distillation ("Unslopper").** N8Programs/Unslopper-30B-A3B: LoRA r=8 on Qwen3 30B-A3B (MoE), 1,000 Gutenberg passages; GPT-4o-mini rewrote each human passage 10x to amplify AI tics, and the model learns AI-text -> original human text (10,000 API calls). Test on 100 GPT-5.2 stories: Pangram humanness 0.000 -> 0.481, quality 8.60 -> 7.96 (Opus 4.5 judge); untuned control 0.003 / 7.82. MLX on Apple Silicon. https://huggingface.co/N8Programs/Unslopper-GGUF/blob/main/README.md . Cheapest convincing demo found: roughly $50 of API plus a laptop. It is a rewriter (post-processor), not a generator. It also shows the quality-for-humanness tradeoff (-0.64).
5. **Human-vs-AI DPO.** Example: Qwen3.5-9B humanize LoRA, 4,000 pairs, Chinese, https://huggingface.co/XiangJinYu/Qwen3.5-9B-Humanize-DPO-v16 . Note Antislop paper: DPO can hurt diversity and quality; use small beta, mix an SFT loss (ORPO/RPO), and add a diversity metric to eval. DPO/ORPO for diversity: Chung et al. https://arxiv.org/abs/2503.17126 .
6. **Samplers.** Min-p (ICLR 2025 oral, https://arxiv.org/pdf/2407.01082) is shipped in transformers/vLLM, but a re-analysis says its quality/diversity claims are not supported (https://arxiv.org/abs/2506.13681); treat as harmless, not a miracle. XTC "Exclude Top Choices" (Weidmann, Roush, Goldfeder; 11-15% Distinct-2 gains on creative tasks; merged into llama.cpp and text-generation-webui) https://www.alphaxiv.org/abs/2608.22758.md . Weidmann appears to be GitHub user p-e-w [E: inferred from author name], whose repo heretic has 37k stars (AGPL-3.0, "suppress slop") https://github.com/p-e-w/heretic . Kalomaze: experimental-samplers koboldcpp fork, 47 stars, stale since 2024 https://github.com/kalomaze/koboldcpp (not a source of training recipes found today).
7. **Base-model prompting.** Frame the prompt as a document (a magazine page, a book chapter, a blog post with author byline) and let a base model continue. Free, large effect on diversity per Narrative Flattening (Base vs post-trained gap) but weak instruction following.
8. **GRPO with style rewards.** Possible (TRL, Unsloth, open-instruct) but the highest risk: reward = LLM-judge or detector, so Goodhart (section E). Use only after SFT/FTPO, with a KL anchor and a held-out human panel. Cost [E]: about 50-200 H100-hr for an 8B, plus judge API fees ($150-600+).
9. **Mistral-Nemo creative finetunes** (Rocinante, Lyra, magnum): community recipes; Nemo-12B (Apache-2.0 [K]) remains a good small, cheap base for prose.

Ranking by quality jump per dollar: (1) base-style prompting + antislop sampler > (2) SFT on curated human prose > (3) FTPO > (4) reverse-distill rewriter > (5) Gutenberg ORPO > (6) CPT > (7) GRPO > (8) scratch.

---

## C. Vintage / time-locked LLMs

| Project | What | Cost / method | Outcome |
|---|---|---|---|
| **TimeCapsuleLLM** (Hayk Grigorian) https://github.com/haykgrigo3/TimeCapsuleLLM , 2,013 stars, MIT, last push 2026-07-11 | Trained from scratch on London text 1800-1875, 90GB (112GB tokenized) in v2; versions v0 (187MB), v0.5 (435MB), v1 (6.25GB), v2mini (15GB sample, 10K steps), v2 (182K steps). Early versions on nanoGPT. No instruction data. | Student hobby project; no dollar figure published in what I read. Size reported variously (about 700M; 1.2B planned). | v1 first recalled a real 1834 protest; v2mini output badly tokenised; samples still only partly coherent (README). PopSci/Ars coverage: https://www.popsci.com/technology/this-ai-thinks-its-the-1800s/ |
| **History LLMs / Ranke-4B** (Univ. of Zurich, DGoettlich) https://github.com/DGoettlich/history-llms , 1,808 stars | 4B Qwen3-architecture models, from scratch, 80B tokens drawn from a 600B-token historical corpus; cutoffs 1913/1929/1933/1939/1946. For humanities research on discourse without hindsight. | Not published in what I read; [E] 4B x 80B tokens = 1.9e21 FLOPs, about 1,300-2,500 H100-hr, $3-8k raw compute, but corpus building (OCR, dedup) is the real cost. Release status of weights conflicting across aggregators. | https://www.broadstreet.blog/p/history-llms-giving-the-past-a-voice (secondary) |
| Common Pile / Comma v0.1 (EleutherAI, Univ. Toronto etc.) https://arxiv.org/abs/2506.05209 | 8TB of public-domain and openly licensed text from 30 sources; Comma v0.1-1T/2T are 7B models competitive with Llama 1/2 7B. | Compute not found. | A legally clean, mostly pre-2022 pretraining corpus you can reuse today. |

Lesson: vintage-from-scratch works as research and novelty but yields small, brittle models. The affordable version is "modern base + vintage/human-only fine-tuning data", with pre-2022 as a data filter rather than a model constraint. Nobody found a shipped "pre-ChatGPT-only" assistant-quality model.

---

## D. Build options compared

Assumptions [E]: H100 at about $2-3/hr; 40% MFU; FLOPs = 6 x params x tokens (LoRA about 2/3 of that); real jobs 1.5-2x slower than ideal because of data loading, evals, restarts; LLM-judge/API costs separate. MoE counted at active params for compute but needs memory for all.

### Option 1: Wrapper on a frontier API (prompt + sampler)
- Tools: your own prompt + banned-phrase filter + rewrite pass (antislop-style regex, retry); for open models the antislop sampler/antislop-vllm; Unslopper-style rewriter on top.
- Data: 20-100 human excerpts per voice; a ban list from slop-forensics.
- Cost: $0-50 setup; per-1k-words inference pennies. 1B/8B/30B not applicable (API).
- Quality: moderate. Hosted APIs usually don't expose token-level samplers, so you can only filter and regenerate (expensive loop) and rewrite. Good baseline and eval harness. Risk: the base policy is still the post-trained "hivemind".

### Option 2: LoRA / full fine-tune of an open model (SFT + FTPO/DPO/GRPO)
- Tools: Unsloth (78.9k stars, Apache-2.0), TRL (19.6k, Apache-2.0), Axolotl (12.7k, Apache-2.0), torchtune (5.8k, BSD-3, "PyTorch native post-training"), open-instruct (3.9k, Apache-2.0), alignment-handbook (5.7k, Apache-2.0). Candidate bases: Mistral-Nemo-12B, Qwen3 (8B, 30B-A3B), Gemma, Llama, OLMo 3 7B/32B (fully open, Apache-2.0 [K]) – OLMo gives you Base/SFT/DPO checkpoints to ablate, matching the Narrative Flattening setup.
- Data: 5-50M tokens of curated human prose (Gutenberg, Common Pile, Chronicling America-style newspapers, old blogs via Internet Archive, licensed magazines) in prompt -> passage form; 2-10k preference pairs with fresh-AI "rejected".
- GPU cost [E]:
  - 1B: SFT 50M tok x 3 epochs about 1 H100-hr ($3-10); DPO $5-20; GRPO $20-100.
  - 8B: SFT about 5-15 H100-hr ($15-60); DPO/FTPO $20-150; GRPO $150-600.
  - 30B (A3B MoE or 32B dense, QLoRA): SFT $60-400 (multi-GPU or H200); DPO $150-800; GRPO $600-3,000.
- Quality: highest ROI. Evidence: Unslopper (humanness 0 -> 0.48 on a detector with 1k examples), FTPO (about 90% slop reduction w/o benchmark loss), Gutenberg finetunes on a Colab A100. Ceiling: base model's latent style space (post-trained bases are already collapsed) – start from a base/early SFT checkpoint where possible.

### Option 3: Continued pretraining on a curated pre-2022 corpus
- Tools: Axolotl, Megatron-LM (18.3k stars, NOASSERTION licence), nanotron (2.9k, Apache-2.0), OLMo-core (1.8k, Apache-2.0), torchtune, or GPT-NeoX (7.5k, Apache-2.0).
- Data: 2-10B+ clean tokens (Common Pile, Gutenberg, pre-2022 news/blogs/fiction). Dedupe, quality-filter, and drop anything post-Nov-2022 via date + detector (Pangram) filtering.
- GPU cost [E] (6ND, 40% MFU, x1.5 overhead): 1B x 10B tokens about 40-60 H100-hr ($100-200); 8B x 10B about 340 H100-hr ideal, 500-700 real ($1-2k); 30B dense x 10B about 1,250 ideal (2,000 real, $4-6k); 30B-A3B MoE cheaper in FLOPs but needs MoE-capable stack (Megatron).
- Quality: shifts the base's prior toward human prose and can partially "unlearn" synthetic style, but cannot erase it without large token counts (billions). Needs re-instruction-tuning afterwards (Option 2). Forgetting/instability risk; plan LR re-warm and replay of general data. Anchor: RedWhale (Korean) CPT on single H100 about 498 GPU-hr for 9.7B tokens, no convergence yet https://arxiv.org/pdf/2408.11294 .

### Option 4: Pretrain from scratch
- Tools: nanochat (59.3k stars, MIT; "best ChatGPT $100 can buy") https://github.com/karpathy/nanochat ; nanoGPT (64.3k, MIT, stale since 2025-11); modded-nanogpt (6.0k, MIT, 124M in 90s); OLMo-core / Dolma (1.6k, Apache-2.0) for data tooling; nanotron/Megatron for scale.
- Reference costs: nanochat speedrun d20 (about 561M params): about 4 hr on 8xH100 at about $24/hr = about $100 ($15-20 on spot); d32 (1.9B, 38B tokens): about $800, about 33 hr on 8xH100 (README per search summaries; other write-ups list different run lengths). OLMo 3 32B: about 1,024 H100 for 56 days (third-party summary; ~$2.75M at $2/hr), 7B about 234k H100-hr (third-party, unverified) https://arxiv.org/abs/2512.13961 .
- GPU cost [E] at Chinchilla-ish 20 tokens/param: 1B x 20B about 85 H100-hr ($250-400); 8B x 160B about 5,300 ideal (8,000 real, $16-25k); 30B x 600B about 45,000 ideal ($100-150k+). Data limits: a clean pre-2022 corpus is probably 100-300B useful tokens, so 8B+ would repeat data.
- Quality: 1B: fluent but shallow, no knowledge; 8B on 160B tokens: below Llama 3 8B (15T tokens); instruction-following must be built from nothing (you'd still need SFT with some synthetic data, re-introducing slop). TimeCapsuleLLM and nanochat are proof of scale and limits.

### Comparison table

| Option | Cash (8B scale) | Timeline | Quality vs frontier prose | Human-voice ceiling | Main risk |
|---|---|---|---|---|---|
| 1 Wrapper | $0-50 | days | Frontier quality, moderate slop reduction | Low-moderate | Hivemind persists |
| 2 SFT + FTPO/DPO | $200-1,500 | 2-4 wks | Good, below frontier on reasoning, can match on prose | Moderate-high | Collapsed base; DPO hurts diversity |
| 3 CPT then Option 2 | $2-5k | 1-2 months | Same as 2 + better prior | High | Data curation, forgetting |
| 4 Scratch | $15-25k+ (8B), $250-800 toy | 3-6 months | Far below | Highest purity | Everything |

---

## E. AI-text detectors as reward signals

- Detectors exist and are decent on in-distribution text: Pangram (hard negative mining with synthetic mirrors, near-zero FPR claims; independent UChicago BFI study found it met a 0.5% FPR cap) https://arxiv.org/abs/2402.14873 , https://bfi.uchicago.edu/?p=64642 . Pangram human training data about 1M documents (vendor).
- Papers that train against detectors: AuthorMist (GRPO with GPTZero/Winston APIs as rewards, with an anchoring term against unnatural degenerate output) https://arxiv.org/abs/2503.08716 ; StealthRL (GRPO against a multi-detector ensemble, reward balances evasion and semantic preservation) https://arxiv.org/abs/2602.08934 ; DAMAGE (detectors robust to humanizers) https://arxiv.org/abs/2501.03437 . I found no paper that directly measures quality loss for a detector-reward humanizer; the nearest evidence for hacking is general GRPO/reward-hacking surveys (image models: reward climbs while quality degrades).
- Risks: Goodhart (optimising the detector yields odd text that fools it, not good text); detectors drift as they retrain on your outputs (arms race); false positives on non-native/formal human prose; evaluation leakage if you train and judge with the same detector; Artificial Hivemind shows reward models/judges mis-model human taste.
- Safe uses: (a) eval-only metric on held-out prompts (never in the training loop); (b) data filter to remove post-2022 or AI-looking text from the corpus; (c) one component of a multi-signal score (detector + slop score + human panel + diversity such as Distinct-n/self-BLEU); (d) cap its weight and stop early on KL/length drift.
- Watermarking: Kirchenbauer logit-bias (https://github.com/jwkirchenbauer/lm-watermarking, 707 stars, Apache-2.0) and SynthID-Text (https://github.com/google-deepmind/synthid-text, 1,222 stars, Apache-2.0; docs https://ai.google.dev/responsible/docs/safeguards/synthid ). Robustness is weak to paraphrase/translation (one preprint: paraphrase removed KGW/Unigram watermarks in every initially detected case; SynthID 58/59; https://arxiv.org/pdf/2607.16010 , treat as single-source). Watermarks only help if the *other* party embeds them; they are not a "human-ness" reward. For FeatherLM: do not rely on them; consider watermarking your own outputs only if you need provenance.

---

## F. GitHub repos worth stealing from (stars/licence checked via API on 2026-11-01)

| Repo | Stars | Licence | Use |
|---|---|---|---|
| karpathy/nanochat | 59,262 | MIT | Whole pretrain->SFT->RL->chat pipeline on one node; the learning exercise |
| karpathy/nanoGPT | 64,309 | MIT | Minimal GPT trainer (stale since 2025-11) |
| KellerJordan/modded-nanogpt | 6,002 | MIT | Fast training tricks |
| unslothai/unsloth | 78,901 | Apache-2.0 | Fast LoRA/QLoRA SFT, DPO, GRPO on one GPU; notebooks |
| huggingface/trl | 19,648 | Apache-2.0 | SFT/DPO/ORPO/GRPO trainers |
| axolotl-ai-cloud/axolotl | 12,652 | Apache-2.0 | YAML-driven SFT/DPO/CPT, multi-GPU |
| meta-pytorch/torchtune | 5,820 | BSD-3-Clause | PyTorch-native post-training (check maintenance status) |
| allenai/open-instruct | 3,921 | Apache-2.0 | AI2's SFT/DPO/RLVR code (Olmo recipes) |
| allenai/Olmo-core, allenai/OLMo, allenai/dolma | 1,768 / 6,720 / 1,562 | Apache-2.0 | Training stack and data pipeline for CPT/scratch |
| huggingface/alignment-handbook | 5,707 | Apache-2.0 | Reproducible alignment recipes |
| huggingface/nanotron | 2,851 | Apache-2.0 | 3D-parallel pretraining |
| NVIDIA/Megatron-LM | 18,310 | NOASSERTION | Large-scale/MoE pretraining |
| EleutherAI/gpt-neox | 7,471 | Apache-2.0 | Pile-era pretraining stack |
| sam-paech/antislop-sampler | 359 | Apache-2.0 | Banned-phrase backtracking sampler |
| sam-paech/auto-antislop | 207 | MIT per paper (API shows none) | Profiling + FTPO |
| sam-paech/slop-forensics | 373 | MIT | Find slop n-grams per model |
| sam-paech/slop-score, EQ-bench/creative-writing-bench | 42 / 151 | NOASSERTION / none | Metrics |
| p-e-w/heretic | 37,333 | AGPL-3.0 | Training-free slop suppression/abliteration (AGPL: do not embed in closed product) |
| LostRuins/koboldcpp, ggml-org/llama.cpp, oobabooga/textgen | 12,120 / 133,033 / 47,729 | AGPL-3.0 / MIT / AGPL-3.0 | Local inference with XTC, DRY, min-p samplers |
| haykgrigo3/TimeCapsuleLLM | 2,013 | MIT | Time-locked data pipeline example |
| DGoettlich/history-llms | 1,808 | none stated | Time-locked research hub |
| jwkirchenbauer/lm-watermarking; google-deepmind/synthid-text | 707; 1,222 | Apache-2.0 | Watermark references |
| vllm-project/vllm; huggingface/transformers | 96,026; 168,403 | Apache-2.0 | Serving and sampler hooks |
| ContextualAI/HALOs | 911 | Apache-2.0 | DPO/KTO/ORPO losses |
| EleutherAI/lm-evaluation-harness | 14,358 | MIT | General regression evals (check you are not damaging reasoning) |

Datasets: jondurbin/gutenberg-dpo-v0.1 (918 rows, CC-BY-4.0), N8Programs/unslop-good (HF), Common Pile v0.1 (8TB, openly licensed), Project Gutenberg. Pre-2022-era sources to curate [K]: Internet Archive pre-2022 snapshots, Chronicling America, Wikipedia dumps pre-2022, Reddit/StackExchange dumps pre-2022 (licence risk), books under licence.

---

## G. Recommended path and cost

**Path: Option 1 -> Option 2, with Option 3 as a gated upgrade.**

1. Weeks 0-1 ($0-50): Build the eval first. Metrics: slop-score/slop-forensics n-gram rates, Distinct-n and cross-sample similarity (Hivemind-style), Pangram humanness (eval only), plus a blind human A/B panel of 20-50 comparisons against the best frontier model. Baselines: frontier + antislop filter; OLMo/Qwen base prompted as a document.
2. Weeks 1-3 ($100-500): Data: 20-100M tokens of curated human prose with timestamps <= 2022 (Common Pile, Gutenberg, newspapers), turned into (instruction -> passage) pairs; regenerate "rejected" with a current frontier model, 10 rewrites each, Unslopper-style. Train a LoRA SFT on an 8B-12B base (candidate: OLMo 3 7B Base/early SFT, Mistral-Nemo-12B, Qwen3-8B Base) with Unsloth/TRL. Run antislop profiling on its outputs.
3. Weeks 3-5 ($50-300): FTPO (auto-antislop) on the model's own slop list; optional small-beta ORPO on human-vs-AI pairs with an SFT term; run the eval and fix regressions on lm-eval-harness.
4. Gate (week 5): If blind human preference vs best frontier+filter is under 40% wins, run CPT on 5-10B tokens ($1-3k on 8B), then repeat step 2-3.
5. Optional (month 3+, $600-3k): GRPO with a multi-signal reward and a KL anchor. Never let a detector be the sole reward.

Total expected cash: **about $400-2,000 for the core product (stages 1-3), up to $3-5k if CPT is added**; GPU-hours about 30-150 H100-hr in the core path. Fits typical startup GPU credits.

Not recommended: from-scratch pretraining of anything above 1B (cost $15k+ for an under-trained 8B, and data cleanliness above 100B tokens is unproven); detector-only GRPO; marketing claim "2023 models wrote better" without a controlled test.

### Open items / unverified
- Compute cost of Ranke-4B, TimeCapsuleLLM, and Comma v0.1 not found.
- EQ-Bench slop-score values for specific models not retrieved (leaderboard is JS-rendered).
- Pre-2022 share of Pangram's human training data unknown.
- OLMo 3 GPU-hour and cost figures are from third-party summaries.
- My dollar figures in sections B and D are arithmetic estimates, not measured runs; verify with a 1-hour pilot on your credits before committing.
- Search results are untrusted web content; none of them contained agent-directed instructions.

## Sources (main)
- https://www.nature.com/articles/s41586-024-07566-y
- https://arxiv.org/abs/2310.06452
- https://arxiv.org/abs/2605.27878
- https://arxiv.org/abs/2510.22954
- https://arxiv.org/abs/2406.07016
- https://arxiv.org/abs/2510.15061
- https://github.com/sam-paech/antislop-sampler
- https://github.com/sam-paech/auto-antislop
- https://eqbench.com/creative_writing.html
- https://huggingface.co/datasets/jondurbin/gutenberg-dpo-v0.1
- https://huggingface.co/N8Programs/Unslopper-GGUF/blob/main/README.md
- https://github.com/haykgrigo3/TimeCapsuleLLM
- https://github.com/DGoettlich/history-llms
- https://arxiv.org/abs/2506.05209
- https://github.com/karpathy/nanochat
- https://arxiv.org/abs/2512.13961
- https://arxiv.org/abs/2402.14873
- https://arxiv.org/abs/2503.08716
- https://arxiv.org/abs/2602.08934
- https://arxiv.org/pdf/2407.01082 , https://arxiv.org/abs/2506.13681
- https://ai.google.dev/responsible/docs/safeguards/synthid
