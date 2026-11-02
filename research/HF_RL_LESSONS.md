# What Hugging Face's post-training stories teach HumanLM

Written 2026-11-01 by hl-researcher. All links read on 2026-11-01 unless a date says otherwise.

**Scope.** These are Hugging Face's (HF) public stories and playbooks, applied to one job: a solo founder fine-tunes a small open model to rewrite AI-sounding copy into human copy. The order is SFT on AI-draft → human pairs, then preference training, then maybe GRPO.

**What is already covered elsewhere, so not repeated here:**
- Tools, stars and cost bands: [TECH.md](TECH.md) §B and §D.
- The SFT config (Gemma-4-12B, r=64, α=128), GPU and serving: [model/BASE_MODELS.md](../model/BASE_MODELS.md) §5.
- The FineWeb-Edu classifier recipe: [data/DATA_SOURCES.md](../data/DATA_SOURCES.md) line 117.
- The humanizer recipes (filters, copy penalty, the Smaug 100–200-step GRPO cap): [SIMILAR_PROJECTS.md](SIMILAR_PROJECTS.md) §6.
- The ladder, KL budget and gates: [evals/EVALS_AND_RL_PLAN.md](../evals/EVALS_AND_RL_PLAN.md) §3.

This file adds HF's numbers, its failures and the exact TRL settings.

Tags: **[E]** = my estimate. **[K]** = background knowledge, not checked today. Everything else has a link.

---

## 0. The short version

1. **HF's single best playbook for us is the post-training chapter of "The Smol Training Playbook"** (2025-10-30). Its rules: evals before training, a baby SFT baseline, vibe-test every checkpoint, preference LR about 10× below SFT LR, a β scan, one epoch, then train again on new pairs.
2. **Zephyr's lesson still holds.** DPO without SFT first fails. The ablation scored MT-Bench 4.76 vs 7.00, and the model could not learn the chat template.
3. **TRL changed in 2026.** ORPO and Online DPO now sit under `trl.experimental`. DPO, KTO, GRPO, RLOO, SFT and Distillation are stable. TECH.md's "small-beta ORPO" should become `DPOTrainer` with an `sft` loss term or `apo_zero`.
4. **GRPOTrainer now defaults to `beta=0.0`, so the KL term is off.** Our plan requires a KL anchor, so we must set β ourselves.
5. **No official HF post covers creative writing or style alignment.** I searched and found none. The closest HF material is the RLHF-style chapters, Cosmopedia (making synthetic text diverse) and FineWeb's slop-word check on web crawls.

---

## 1. Zephyr-7B and distilled DPO (2023)

**Story in 3 lines.**
- HF's H4 team took Mistral-7B and ran three steps. First, SFT on UltraChat dialogues written by ChatGPT (dSFT). Then GPT-4 ranked responses (UltraFeedback). Then DPO on those rankings (dDPO).
- No human labels were used, and training took a few hours on 16 A100s.
- It beat Llama2-Chat-70B on MT-Bench and showed DPO works in practice.
- Paper submitted 2023-10-25 ([arXiv 2310.16944](https://arxiv.org/abs/2310.16944), [HTML](https://arxiv.org/html/2310.16944)). Model card: [zephyr-7b-beta](https://huggingface.co/HuggingFaceH4/zephyr-7b-beta).

**Lessons (with numbers).**
- **SFT first is mandatory.** Without SFT, MT-Bench fell to 4.76 and AlpacaEval to 30.76%, against 7.00 and 86.07% with it. "The pure DPO model struggles to learn the chat template" ([HTML](https://arxiv.org/html/2310.16944)).
- **Paper hyperparameters.**
  - dSFT: LR 2e-5, cosine, 10% warmup, batch 512, packing at 2,048 tokens.
  - dDPO: LR 5e-7, linear, 10% warmup, batch 32, β=0.1.
  - Final model: 1 SFT epoch, then 3 DPO epochs.
- **DPO overfit, and that did not hurt.** Training accuracy hit 100% after one DPO epoch, and the chat scores still held. But the paper adds a catch: if SFT ran for more than one epoch, longer DPO caused a regression.
- **The judge was biased, and they said so.** GPT-4 as judge favours models distilled from it and verbose answers.
- **The handbook config differs from the paper.** The QLoRA recipe uses β=**0.01**, LR **5e-6**, 1 epoch, LoRA r=128 α=128 ([config_qlora.yaml](https://github.com/huggingface/alignment-handbook/blob/main/recipes/zephyr-7b-beta/dpo/config_qlora.yaml)). The SFT QLoRA config uses r=16, LR 2e-4, 1 epoch ([sft config](https://github.com/huggingface/alignment-handbook/blob/main/recipes/zephyr-7b-beta/sft/config_qlora.yaml)). So even HF's own β moved from 0.1 to 0.01.

**How HumanLM applies it.**
- **Trainer:** TRL `SFTTrainer`, then `DPOTrainer`. Never skip SFT on a base model like Gemma-4-12B base.
- **Recipe change:** BASE_MODELS §5 says SFT for 2 epochs. If DPO comes after, run **1 SFT epoch**. Only use the 2-epoch checkpoint if the eval proves it better *after* DPO.
- **Hyperparameters to start from, for LoRA DPO:** LR 5e-6, β scan from 0.01, cosine, warmup 0.1, 1 epoch.
- **Data check:** our judge must not be the same model family that wrote the AI drafts, because of the self-preference bias Zephyr admits. Pin the judge model and its version.

---

## 2. The Alignment Handbook (repo, 2023–2025)

**Story in 3 lines.**
- These are HF's open recipes as YAML files, one per run, for SFT, DPO, ORPO, KTO/IPO scans and Constitutional AI ([repo](https://github.com/huggingface/alignment-handbook), 5.7k stars on 2026-11-01).
- The timeline runs from Zephyr code (2023-11-10) to ORPO on Mixtral-8x22B (2024-04-12), SmolLM2 (2024-11-21) and SmolLM3 (2025-07-24).
- Each script supports LoRA/QLoRA as well as DeepSpeed ZeRO-3 full training.

**Lessons.**
- **One YAML file per run.** Every hyperparameter lives in that file, so runs can be reproduced.
- **The SmolLM3 preference config that actually shipped** ([apo.yaml](https://github.com/huggingface/alignment-handbook/blob/main/recipes/smollm3/dpo/apo.yaml)) uses `loss_type: apo_zero`, `beta: 0.05`, LR 1e-6, `cosine_with_min_lr`, 1 epoch, warmup 0.1.
- **There is a `pref_align_scan` recipe.** It compares DPO, KTO and IPO with a β sweep (2024-01-18).

**How HumanLM applies it.**
- Copy the habit, not the code. Keep `model/configs/<run-id>.yaml` with every setting, the dataset hash and the eval it should move. That also meets the GRAPH.md rule "no training run without a stated eval".
- The handbook pins torch 2.6 / flash-attn 2.7.4. It is older than TRL 1.17, so use TRL's own scripts and Unsloth for training. Use the handbook only as a hyperparameter reference.

---

## 3. TRL: the trainers, the 2026 split, and the "how we built it" posts

**Story in 3 lines.**
- TRL is HF's post-training library. v1.0 shipped on 2026-03-31 with a stable core under semantic versioning and an experimental layer ([TRL v1 blog](https://huggingface.co/blog/trl-v1)). The latest release is v1.17.1, from 2026-10-30 ([releases](https://github.com/huggingface/trl/releases)).
- **Stable trainers:** SFT, DPO, KTO, GRPO, RLOO, Reward, Distillation ([docs index](https://huggingface.co/docs/trl/main/en/index)).
- **Experimental trainers:** ORPO, Online DPO, GKD, GOLD, CPO, and others. Import them from `trl.experimental` ([online DPO doc](https://huggingface.co/docs/trl/main/en/online_dpo_trainer)).

### 3a. SFTTrainer ([docs](https://huggingface.co/docs/trl/main/en/sft_trainer))
- **Loss on the completion only.** With a `{"prompt","completion"}` dataset, loss is on the completion by default (`completion_only_loss=None` → completion). BASE_MODELS's draft→rewrite format already fits this.
- **Defaults to watch.**
  - LR 2e-5. The docs advise ≈1e-4 for adapters.
  - `max_length=1024`. It truncates silently, so long landing pages would be cut.
  - `packing=False`.
  - `gradient_checkpointing=True`.
  - `bf16=True`.
- **Base models with a built-in template need `eos_token` set.** Example: `eos_token="<|im_end|>"` for Qwen base. Without it, the model never learns to stop.
- **Metrics:** `mean_token_accuracy` and `entropy`. Entropy falling fast is an early sign of collapse **[E]**.

### 3b. DPOTrainer ([docs](https://huggingface.co/docs/trl/main/en/dpo_trainer))
- **Defaults:** β=0.1, LR 1e-6. The docs suggest ≈1e-5 for adapters. `max_length=1024`. Dropout is off.
- **Useful `loss_type` values for us:**
  - `sigmoid`: plain DPO.
  - `apo_zero`: raises winners and lowers losers. Use it when the chosen text is better than the model's own output.
  - `apo_down`: use it when the model is already better than the chosen text.
  - `sigmoid_norm`: SimPO-style length normalisation.
  - `robust`: tolerates noisy labels. Set `label_smoothing` to the label-flip rate, typically 0.1.
  - `sft`: an NLL term.
  - Loss types can be combined, e.g. `loss_type=["sigmoid","sft"], loss_weights=[...]`.
- **`ld_alpha` (LD-DPO)** down-weights the extra length in verbose responses. This is directly useful against "longer = preferred".
- **`precompute_ref_log_probs=True`** frees memory because the reference model no longer stays loaded.
- **Metrics:** `logps/chosen`, `logps/rejected`, `rewards/margins`, `rewards/accuracies`. The docs say DPO usually works "by suppressing the likelihood of dispreferred completions rather than by increasing the likelihood of preferred ones". So watch `logps/chosen`. If it drops too, the model is moving away from human text as well as from slop.

### 3c. KTOTrainer ([docs](https://huggingface.co/docs/trl/main/en/kto_trainer))
- It needs only thumbs-up/down per output, not pairs.
- **LR:** stay in 5e-7 to 5e-6. With β=0.1, LR should not go above ~1e-6.
- **Batch:** per-step batch ≥4, effective batch 16–128. Small per-step batches give a poor KL estimate.
- **Imbalanced data:** set `desirable_weight`/`undesirable_weight` so that (weight × count) for good:bad lands between 1:1 and 4:3.

### 3d. GRPOTrainer ([docs](https://huggingface.co/docs/trl/main/en/grpo_trainer))
- **Defaults:**
  - `beta=0.0`, so there is no KL term and no reference model. DeepSeek-R1 used 0.001.
  - `num_generations=8`, `epsilon=0.2`, `loss_type="dapo"`, `scale_rewards="group"`, `max_completion_length=512`, LR 1e-6.
- **Reward functions:** `reward_funcs` takes a list of Python functions. Their scores are summed, or weighted with `reward_weights`. A function can return `None` to skip a sample.
- **Metrics to watch:**
  - `frac_reward_zero_std`: the share of groups where every sample scored the same, which means no learning signal.
  - `completions/mean_length` and `clipped_ratio`.
  - `entropy`.
  - `kl`, which is logged only if β>0.

### 3e. Online DPO ([docs](https://huggingface.co/docs/trl/main/en/online_dpo_trainer), experimental)
- The model samples two answers, a judge or reward model picks one, and DPO runs on the fresh pair.
- **Defaults:** LR 5e-7, β=0.1, `max_new_tokens=64`. That cap is far too short for copy, so raise it.
- `missing_eos_penalty` punishes outputs that never stop.

### 3f. "How we built it" posts
- **[The N implementation details of RLHF with PPO](https://huggingface.co/blog/the_n_implementation_details_of_rlhf_with_ppo)** (2023-10-24). Small details decide whether RL works:
  - a pad token separate from EOS;
  - EOS handling in `generate`;
  - normalised rewards;
  - dropout off;
  - PyTorch Adam acts differently from TF Adam early in training.
- **[Putting RL back in RLHF with RLOO](https://huggingface.co/blog/putting_rl_back_in_rlhf_with_rloo)** (2024-06-12).
  - RLOO used about 50–70% less VRAM than PPO and ran 2–3× faster.
  - It "consistently outperforms DPO" on their TL;DR task.
  - The 6.9B model reached a 78.7% preferred rate.
- **[No GPU left behind](https://huggingface.co/blog/vllm-colocate)** (2025-06-03, date from search snippet). vLLM can now run on the same GPU as the trainer, so one rented GPU can do GRPO.
- **[TRL v1](https://huggingface.co/blog/trl-v1)** (2026-03-31). Lessons from the team:
  - design for change;
  - keep abstractions thin;
  - their unified `Judge` abstraction "went largely unused" and is now legacy.
- **[LoRA Without Regret, in TRL](https://huggingface.co/docs/trl/main/en/lora_without_regret)**, reproducing [Thinking Machines, 2025-09-29](https://thinkingmachines.ai/blog/lora/):
  - put LoRA on **all linear layers**;
  - LoRA LR is about **10× the full-fine-tune LR**;
  - keep the **effective batch under 32**;
  - RL needs only rank **1–32**;
  - large SFT sets need rank ~256.
  - Note: HF's own page is inconsistent. The Python example uses LR 2e-4 and the CLI example uses 2e-5 for the same run.

**How HumanLM applies TRL.**
- **Trainers in order:** `SFTTrainer` → `DPOTrainer` (stable) → `KTOTrainer` for app thumbs data → `GRPOTrainer` or `RLOOTrainer`. Avoid ORPO and Online DPO as the main path while they are experimental. They may change between releases.
- **Replace "ORPO with small β" (TECH.md §A.5)** with `DPOTrainer(loss_type=["sigmoid","sft"])` or `apo_zero`. Both keep an anchor on the human text, and both are stable.
- **Set `max_length` from data:** the 99th-percentile token length of prompt + completion, not 1024.
- **Always set GRPO `beta>0`.** Start at 0.01–0.04 **[E]** to honour the KL budget in EVALS_AND_RL_PLAN §3.6.
- **Pin `trl==1.17.x` in `model/configs`.** Defaults have changed between versions before.

---

## 4. Open-R1: reproducing DeepSeek-R1 in the open (2025)

**Story in 3 lines.**
- Eight days after DeepSeek-R1, HF set out to rebuild it openly in three steps: distil R1 traces, rebuild pure RL (R1-Zero), then show SFT → RL ([launch post, 2025-01-28](https://huggingface.co/blog/open-r1)).
- It shipped OpenR1-Math-220k ([update 2, 2025-02-10](https://huggingface.co/blog/open-r1/update-2)), CodeForces-CoTs ([update 3, 2025-03-11](https://huggingface.co/blog/open-r1/update-3)) and Mixture-of-Thoughts (350k traces, 2025-05-26).
- The repo has 26.5k stars and is now "no longer maintained". Its GRPO, SFT and distillation code moved into TRL ([repo](https://github.com/huggingface/open-r1)).

**What went right.**
- **Verify, then filter.** Math-Verify kept the 55% of problems with at least one correct answer, about 220k out of 400k. An LLM judge (Llama-3.3-70B) then rescued 28k false rejects.
- **They released the data and the recipe, not only weights.**
- **They wrote decontamination scripts (n-gram matching).** HF reuses them in later work.

**What went wrong, in their own words.**
- **Packing hurt.** "Packing substantially hurts the model's performance" on reasoning SFT (update 3).
- **The usual LR was wrong.** LR 2e-5 underperformed. 4e-5 gained nearly 10 points on LiveCodeBench.
- **A reward model did not help.** Using a 72B math RM to choose the best of several correct answers "doesn't help" compared with random choice (update 2).
- **A bigger data split was worse.** The `extended` split (131k) did worse than `default` (94k) because it held easier problems.
- **The template broke behaviour.** Without a forced `<think>` prefill, out-of-domain prompts dropped the trained behaviour. This was found by vibe testing.
- **Tokens were mismatched.** The README warns that Qwen base needs EOS `<|im_end|>`, and that the DeepSeek template breaks the format reward.

**How HumanLM applies it.**
- **Our "verifier" is the facts gate.** It plays the role Math-Verify played. Run it on every candidate pair, and log the keep rate as Open-R1 did. If the keep rate is under ~40%, fix generation before training **[E]**.
- **Use an LLM judge only to rescue false rejects, never as the reward.** That matches Open-R1's use and TECH.md §E.
- **Do not assume a reward model picks better winners.** Before building one, test RM-picked chosen vs a random gate-passing chosen on 200 dev prompts. If it doesn't win, skip it. That saves the ≥70%-agreement work in BENCHMARKS.md.
- **SFT settings:** `packing=False` for our small set, and an LR scan rather than a default.
- **Easy pairs dilute.** Drop pairs where the AI draft and the human text are almost the same (Smaug's near-copy filter does this). More rows is not better.

---

## 5. SmolLM2 and SmolLM3 (2025)

**Story in 3 lines.**
- **SmolLM2** (1.7B; [arXiv 2502.02737](https://arxiv.org/abs/2502.02737), 2025-02-04) is a data-centric model. HF trained on ~11T tokens in stages and built new datasets (FineMath, Stack-Edu, SmolTalk) wherever existing data was too small or too poor.
- **SmolLM3** (3B; [blog, 2025-07-08](https://huggingface.co/blog/smollm3)) is a hybrid reasoner. Its pipeline was mid-training → SFT (1.8B tokens) → APO → model merging.
- APO replaced DPO because it gave "a more stable optimization objective" and "higher downstream performance in our internal ablations".

**Lessons.**
- **"Strong vs weak" preference pairs work.**
  - The chosen side came from Qwen3-32B and the rejected side from Qwen3-0.6B, on the same prompts.
  - They made 250k+ pairs this way.
  - APO-zero then added **15–20 points on IFEval** over SFT (playbook, §6 below).
- **Merging repairs damage.** Preference tuning hurt long context (RULER). HF averaged ("souped") the APO checkpoints, then **linearly merged them 0.9/0.1 with a mid-training checkpoint**. That recovered RULER up to 128k (blog).
- **SFT data:** 4 epochs, BFD packing, loss masked on user turns and tool outputs.

**How HumanLM applies it.**
- **Pair recipe = strong vs weak, in our direction.** Chosen = the human rewrite. Rejected = our SFT model's own failed output, or a frontier model's slop draft. Use the "on-policy with grading" variant from the playbook for later rounds.
- **Loss:** add `apo_zero` as a DPO arm. Our chosen side is human copy, which should beat the model's output at first. Once the model's output is beating the human references in blind tests, switch the arm to `apo_down`.
- **Merge as a cheap fix (CPU only, about $0).** If DPO wins on blind taste but loses facts or diversity, linearly merge the DPO and SFT LoRAs. Start at 0.9/0.1 as SmolLM3 did and sweep [0.5, 0.7, 0.9] **[E]**. Use MergeKit, or merge adapters with PEFT before vLLM serving. Gemma-4-12B must be merged before serving anyway (BASE_MODELS §5).

---

## 6. The Smol Training Playbook (2025-10-30): the post-training chapter

**Story in 3 lines.**
- This is a book-length, honest write-up of how HF built SmolLM3, by 12 authors ([Space](https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook); source read from [article.mdx](https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook/blob/main/app/src/content/article.mdx), §"Beyond Base Models—Post-Training in 2025").
- It covers the why/what/how of training, evals, SFT, preference optimisation, RL and on-policy distillation.
- Its tone is "here is what broke". Ablations and debugging used 161,280 GPU-hours, more than half of the 276,480 used for the main run.

**Lessons that matter to us (quoted or close paraphrase).**
- **Should you train at all?** "Do you really need to post-train?" You need domain data, and "Can you measure success?" Our answer is yes only because no open model is tuned on founder copy with a facts gate.
- **Evals first.**
  - Admitted mistake: "We had a tight deadline and rushed ahead with model training before many of the above evals were implemented… In hindsight, this was a mistake."
  - **Pin the judge model and its version.** Prefer open-weight judges.
  - For evals under ~2k items, sample k times and report avg@k.
  - Decontaminate the training data against the evals.
  - Keep anything used during ablations as *validation*, and hold out a real *test* set.
  - Make sure you can replicate published numbers before trusting your eval code.
- **Vibe-test every checkpoint.** A data bug deleted *all system messages*. The evals looked fine. Chatting with the model found it. "Don't underestimate the power of just chatting with your model!"
- **Baby SFT baseline:**
  - full fine-tune LR 1e-5, effective batch 128, 1 epoch;
  - 30–90 min on 8×H100;
  - "this choice of hyperparameters works well as a baseline."
- **The SFT hyperparameters that matter:** LR, batch size and packing.
  - LR scan grid: [1e-6, 3e-6, 1e-5, 3e-5, 1e-4]. 3e-6 to 1e-5 was best for full fine-tunes.
  - Packing speeds training 3–5×. But on small or curated sets it hurt some evals, e.g. IFEval at batch 128. For "limited human-curated data", consider turning packing off.
  - Masking user turns gave only "a few points", mostly on instruction following.
  - Ablate with 1 epoch. More epochs at the end added a few points, and nearly doubled one benchmark.
  - **Balance the data mix by tokens, not by examples.**
- **Skip mid-training for style.** Mid-training is "less useful… if you're trying to elicit shallow capabilities such as style." That agrees with DECISIONS.md: no continued pretraining.
- **Preference optimisation:**
  - Start with DPO as the baseline, then try APO, KTO and ORPO. All of these are a one-line change in `DPOTrainer` (ORPO now lives in `trl.experimental`).
  - **LR ≈ 10× below the SFT LR.** Scan 5×–20× below. Zephyr taught them this, and SmolLM3 confirmed it. Going below 10× hurt the reasoning mode.
  - **β:** they scanned 0.01–0.99, found β=0.1 best, and suggest scanning 0.01–0.5.
  - **Data size:** results held from 2k to 340k pairs. **Even 2k pairs beat the SFT checkpoint.**
  - "Since most preference algorithms overfit after one epoch, partition your data and train iteratively."
- **RL:**
  - Naive GRPO **reward-hacked on length**. The concise mode learned long "Wait, …" chains.
  - The fix was DAPO's overlong penalty. A 2.5–3k-token cap gave the best trade-off.
  - Joint RL over two modes was still "unstable".
  - They skipped RL for the release because APO was already best in class.
- **Cheaper than RL:**
  - Semi-online DPO, which regenerates pairs every 100 steps, matched GRPO in FAIR's table: Math500 58.9 vs 58.1.
  - On-policy distillation beat RL in Qwen3's report at about 1/10 of the GPU-hours (1,800 vs 17,920).

**Two inconsistencies inside HF's own material (useful warnings).**
1. The playbook says "lower values [of β] encourage staying close to the reference model while higher values allow the model to match the preference data more closely". TRL's docs say the opposite, and TRL is correct: "Higher β means less deviation from the reference model" ([DPOConfig](https://huggingface.co/docs/trl/main/en/dpo_trainer)). Don't copy the playbook sentence into our configs or notes.
2. The playbook text says β=0.1 was best, but the shipped SmolLM3 config uses β=0.05 ([apo.yaml](https://github.com/huggingface/alignment-handbook/blob/main/recipes/smollm3/dpo/apo.yaml)). Treat β as something to scan per dataset, never as a known constant.

**How HumanLM applies it.**
- **Vibe set:** 20 fixed founder-copy prompts. Ali reads all outputs from every checkpoint before any number is trusted. This is a check, not a vote (COPY_EVAL keeps Ali out of the gold raters).
- **Avg@k:** our dev set is small, so score 4 samples per prompt (BASE_MODELS already samples 4) and report avg@4 with a CI.
- **The preference LR follows from the SFT LR.** If LoRA SFT runs at 1e-4, scan DPO at 5e-6, 1e-5 and 2e-5 (5–20× below).
- **Iterate in rounds, not epochs.** Split the pairs into 3 parts. Round 1 uses part 1. Then regenerate the rejected side from the new model, and run round 2 on part 2. This is the "semi-online" pattern at almost no extra cost.
- **Length penalty in GRPO, both ways.** Our risk is thin outputs as well as long ones. Reward 0 inside 0.85–1.15× the draft length (PLAN_30D §2.6), with a linear penalty outside, shaped like DAPO's soft cache.

---

## 7. The Ultra-Scale Playbook (2025-02-19)

**Story in 3 lines.**
- This is HF's open book on training across many GPUs: data, tensor, pipeline and context parallelism, and ZeRO. It is based on 4,000+ scaling experiments on up to 512 GPUs ([Space](https://huggingface.co/spaces/nanotron/ultrascale-playbook); [source](https://huggingface.co/spaces/nanotron/ultrascale-playbook/blob/main/ultra_blog.md)).
- It opens with "First Steps: Training on one GPU", which is the only part we need.
- 4.1k likes on 2026-11-01.

**Lessons for one GPU.**
- **Memory rule:** mixed-precision Adam needs about **16 bytes per parameter**. That is BF16 weights and gradients, an FP32 master copy, and two FP32 Adam states.
- **Gradient accumulation** gives a big batch without big memory.
- **Activation recomputation** (gradient checkpointing) trades compute for memory.

**How HumanLM applies it.**
- A full fine-tune of a 12B model needs about 12B × 16 B ≈ **192 GB** before activations. That is over two 80 GB GPUs. So **LoRA is required, not optional**, on one L40S or A100. LoRA keeps the frozen 12B weights in BF16 (≈24 GB) plus small adapter states **[E]**.
- To get an effective batch of 16 (under the LoRA-friendly 32): `per_device_train_batch_size=2`, `gradient_accumulation_steps=8`. This matches BASE_MODELS.
- **DPO with LoRA needs no second model in memory.** TRL uses the base with the adapter turned off as the reference **[K]**. Add `precompute_ref_log_probs=True` if memory is still tight.
- Nothing else in this book applies until we train above ~30B or across nodes.

---

## 8. Courses: smol-course and the Deep RL course

**smol-course** ([repo](https://github.com/huggingface/smol-course), 6.8k stars). v2 is live and built on SmolLM3.
- Units: 1 instruction tuning and chat templates; 2 evaluation; 3 preference alignment (DPO); 4 VLMs; 5 RL (October 2025); 6 synthetic data (November 2025).
- It runs on "most local machines" with minimal GPU needs.
- **For HumanLM:** units 1, 2, 3 and 5 are the founder's 1–2 week learning path. It uses the same TRL trainers we will use. Units 1–3 can run on a Mac with a 135M–360M model to learn the mechanics before renting a GPU **[E]**.

**Deep RL course** ([intro](https://huggingface.co/learn/deep-rl-course/unit0/introduction)). This is classic RL: games and robots, with Stable-Baselines3 and CleanRL. It has no LLM unit.
- **For HumanLM:** skip it. Read only the PPO unit if GRPO clipping needs intuition. Lambert's book (§11) covers the LLM side better.

---

## 9. FineWeb and FineWeb-Edu (2024): the data-quality story

**Story in 3 lines.**
- HF built a 15T-token web dataset from 96 Common Crawl snapshots. Every filter was tested by training small models on the data ([blog Space, created 2024-05-23](https://huggingface.co/spaces/HuggingFaceFW/blogpost-fineweb-v1); [paper, 2024-06-25](https://arxiv.org/abs/2406.17557)).
- FineWeb-Edu then used Llama-3-70B labels, distilled into a small classifier, to keep 1.3T "educational" tokens. It matched C4/Dolma on MMLU with 10× fewer tokens.
- The classifier recipe is already in DATA_SOURCES.md. Below are the *other* lessons.

**Lessons that are new for us.**
- **More deduplication was worse.** Deduplicating across all dumps left 4T tokens and gave "next to no improvement". In the oldest dump, the 10% kept was *worse* than the 90% removed. Deduplicating each dump on its own worked better. Their explanation: data with no duplicates anywhere may be lower quality or out of distribution.
- **One good annotator beat a jury.** They tried Mixtral-8x7B, Mixtral-8x22B, Llama-3-70B and a jury of all three: "using Llama3 alone gave the most reliable results."
- **An additive rubric beat a Likert rubric.** It lets the LLM "reason about each additional point awarded".
- **Thresholds trade one skill for another.** A threshold above 3 helped knowledge benchmarks but "significantly" hurt HellaSwag and PIQA.
- **Measure slop in your "human" data.** They counted "delve", "as a large language model", "it's important to note", "rich tapestry", "intertwined", "certainly!" and "dive into" per crawl. The counts stayed flat until 2023-14, then rose steeply.
- **Honest caveat.** That synthetic text "does not seem to drastically harm" small trainings, and "might actually improve it". So "pre-AI text is better" is not proven by FineWeb. It matches TECH.md's verdict.
- **Results vary by crawl.** Some crawls were much worse than others, and they "could not find any conclusive explanation", after 192 models and 60k+ H100-hours.

**How HumanLM applies it.**
- **Date check plus a slop-word check on the human side.** Run FineWeb's 7-phrase list plus `pipeline/slop_phrases.txt` on every "human" text. For anything dated after 2022-11-30, or with an unknown date, flag any document above the human-band rate. This is cheap insurance against AI text inside our "human" data.
- **Dedup lightly.** Use exact plus near-duplicate dedup *within* a source. Don't run aggressive cross-source MinHash that throws away unique copy. Check on the dev set that dedup doesn't lower the win rate.
- **Annotation:** use one strong open judge with an **additive** rubric for any quality filter, e.g. +1 specific, +1 concrete proof, +1 natural rhythm, and so on **[E]**. Don't use a jury unless it measurably beats one judge on 200 hand-labelled items.
- **Pick the filter threshold with a small test, not by eye.** Train two tiny SFTs (threshold 2 vs 3) for about $5 **[E]** and compare on the dev set.

---

## 10. Cosmopedia (2024-03-20): making synthetic text diverse

This is the closest HF story to our AI-draft generation step ([blog](https://huggingface.co/blog/cosmopedia)).
- **Story:** 25B tokens of synthetic textbooks from Mixtral-8x7B. The goal was under 1% duplicates.
- **Lessons:**
  - Rewording the prompts did not stop duplicates. Prompts needed explicit instructions that the format and content must differ.
  - Early outputs repeated openers. Stories started with "Once upon a time". Telling the model to avoid them helped but did not fix it.
  - Decontamination: find 10-gram overlaps, then drop the sample if `difflib.SequenceMatcher` ratio > 0.5.
- **For HumanLM:**
  - The AI drafts must look like *real* user drafts in their variety. Rotate 3+ draft models (SIMILAR_PROJECTS §6), plus explicit persona/format variants: rushed founder, over-polished ChatGPT, bullet dump, and so on **[E]**.
  - Measure the duplicate rate of drafts (distinct-2 from `pipeline/metrics.py`).
  - Use the 10-gram + 0.5 SequenceMatcher check to keep eval human texts out of training.

---

## 11. Creative writing and style alignment at HF, plus Nathan Lambert's RLHF book

**HF itself.** I found **no official HF blog post on creative-writing or style alignment** (searches on 2026-11-01).
- The writing-style work on the Hub comes from community authors. Examples are the nbeerbower Gutenberg DPO models and N8Programs/Unslopper, already in TECH.md and SIMILAR_PROJECTS.
- A community "Guide to LLM post-training algorithms" by Karina Zadorozhny (2026-01-19) is a member article, not an HF team post ([link](https://huggingface.co/blog/karina-zadorozhny/guide-to-llm-post-training-algorithms)). It adds nothing new for us.
- One related paper, not by HF, is on HF Papers: Chung et al., "Modifying LLM Post-Training for Diverse Creative Writing" ([arXiv 2503.17126](https://arxiv.org/abs/2503.17126), 2025-03-21).
  - It adds a "deviation" weight to DPO/ORPO so that rare good outputs get more weight.
  - An 8B model matched human-written data on diversity, with quality near GPT-4o and R1.
  - **For HumanLM:** if DPO shrinks diversity (TECH.md's Kirk et al. risk), this is the next fix to try. It is not in TRL, so it needs a small custom loss **[K]**.

**[RLHF book](https://rlhfbook.com/) by Nathan Lambert.** Lambert was on HF's H4 team and co-authored Zephyr. The web book was last built 2026-10-30, and the Manning print edition came out July 2026 ([source chapters](https://github.com/natolambert/rlhf-book/tree/main/book/chapters)).
- **Appendix B, "Beyond Just Style."** Preference tuning on general chat data makes models *chattier*. Lambert's own Tulu 3 example shows DPO adding numbered lists and bold headers. "RLHF tends to make models more verbose" because average raters like longer answers. Benchmarks added length correction because "funky RLHF" shows up as length bias.
- **Ch. 14, over-optimisation.**
  - The proxy reward rises while true quality first improves, then falls.
  - Typical exploits: "verbose, confident-sounding responses" and repeated rare tokens.
  - Over-optimisation is different from overfitting. It is gaming the measure, not memorising data.
- **What it means for us.** This is the clearest statement of why HumanLM exists. Generic preference data *produces* the list-heavy, verbose slop we remove. So:
  - (a) **Never mix in generic preference sets** (UltraFeedback, Tulu prefs) "for helpfulness". They pull toward slop.
  - (b) Our rejected side must contain exactly those patterns (lists, bold, hedges, length).
  - (c) Keep length-controlled win rates (PLAN_30D §2.6). The book confirms that this is how the field patched the problem.

---

## 12. The HumanLM post-training recipe v1, borrowed from Hugging Face

**Budget frame.** The hard cap is under $2k. Plan about **$150–350 GPU [E]** for v1. The rest goes to copywriter raters (COPY_EVAL) and pair generation.

**GPU price:** RunPod L40S at $0.79/h Community, or A100 80 GB at $1.19–1.39/h ([RunPod](https://www.runpod.io/pricing), via SOLO_PLAYBOOK).

**Base:** per BASE_MODELS. Gemma-4-12B base (or the humanizer warm start), with Qwen3.5-9B-Base as the second arm. Log every dollar in `model/SPEND.md`.

**Step 0. Evals before training (Smol Playbook; $0–20).**
- Freeze the dev set and a hidden test set. Ablations touch only dev.
- Pin the judge model and version (open-weight if possible). The judge must not be the same family as the draft generators (Zephyr's bias note).
- Score avg@4 per prompt with a CI.
- Prove the harness reproduces one published number, e.g. a known model's slop score on EQ-Bench (BENCHMARKS.md).
- Make a 20-prompt vibe set.

**Step 1. Data checks before any GPU (FineWeb, Cosmopedia, Open-R1; ≈$0 GPU).**
1. Human side: date ≤ 2022-11-30 or commissioned, plus the FineWeb slop-phrase check (flag, don't silently drop).
2. AI side: 3+ draft models with explicit format/persona variation. Distinct-2 above the threshold the judge sets.
3. Facts gate on every pair. Log the keep rate (Open-R1 kept 55%).
4. Light dedup within each source only.
5. Decontaminate against dev/test: 10-gram + SequenceMatcher > 0.5 → drop.
6. Balance genres by **tokens**, not rows.
7. Write the data card (counts by source, licence, drops).

**Step 2. Baby SFT baseline (Zephyr + Smol Playbook + LoRA Without Regret; ≈$15–30 [E]).**
- **Trainer:** `SFTTrainer` (via Unsloth is fine).
- **Data:** prompt/completion format, so loss is on the completion only. Set `eos_token` to match the template.
- **Settings:**
  - `max_length` = p99 of the data.
  - `packing=False`.
  - LoRA on all linear layers, r=64 α=128 (BASE_MODELS). Try r=256 α=16 as one arm if there are ≥10k pairs.
  - Effective batch 16.
  - **1 epoch.**
- **LR scan:** 5e-5, 1e-4, 2e-4. That is the playbook's full-fine-tune sweet spot × ~10 for LoRA.
- **Smoke test first:** 200 pairs, 30 steps.

**Step 3. Vibe test + template audit ($0).**
- Ali reads the 20 vibe prompts × 4 samples.
- Check that outputs stop (EOS), don't echo the instruction, and don't copy the draft (copy-rate).
- Fix data bugs before any preference training. This is HF's deleted-system-prompt lesson.

**Step 4. Offline preference round 1 (Zephyr, pref-tuning scan, SmolLM3; ≈$30–60 [E]).**
- **Trainer:** `DPOTrainer`. Start from the best 1-epoch SFT adapter.
- **Pairs.** 2–3k, which HF showed is enough to move a model.
  - **chosen** = the human rewrite.
  - **rejected** = our SFT model's own output for that draft that failed a gate or lost Ali's pick. This is on-policy with grading.
  - Fill the rest with frontier slop drafts (strong vs weak).
  - Length-match pairs where possible.
- **Arms (1 epoch each):**
  - `sigmoid` (plain DPO baseline);
  - `apo_zero`;
  - `["sigmoid","sft"]` (anchors on the human text);
  - optionally `robust` with `label_smoothing=0.1` if Ali's picks are noisy.
- **β scan:** 0.01, 0.05, 0.1, 0.3.
- **LR:** 5–20× below the SFT LR, e.g. 5e-6 to 2e-5 for LoRA. Warmup 0.1, cosine.
- **Memory:** `precompute_ref_log_probs=True`.
- **Kill a run early if:**
  - `logps/chosen` falls steadily (the model is moving away from human text), or
  - mean output length moves outside 0.85–1.15×, or
  - distinct-2 drops under the SFT model's.
- **Pick the winner** by blind panel plus gates, not by `rewards/accuracies`.

**Step 5. Rounds 2–3, semi-online (Smol Playbook "partition and iterate"; ≈$30–60 [E]).**
- Sample new rejected outputs from the round-1 model on part 2 of the prompts. Re-gate them, get Ali's picks, and train one more epoch.
- Repeat on part 3.
- This gets most of online DPO's benefit while staying on the stable trainer.

**Step 6. Repair by merging if needed (SmolLM3; $0).**
- If the DPO model wins on taste but loses on facts or diversity, linearly merge DPO with SFT at 0.9/0.1, 0.7/0.3 and 0.5/0.5. Re-run the gates.
- Merge before vLLM serving anyway (Gemma-4-12B).

**Step 7. Thumbs data → KTO (only once the app has users; ≈$10–20 [E]).**
- **Trainer:** `KTOTrainer` on accept/reject events from the 2-version picker.
- **Settings:** LR 5e-7 to 5e-6, per-step batch ≥4, desirable:undesirable weighted to 1:1–4:3, β=0.1 to start.

**Step 8. GRPO only if DPO plateaus for 2 rounds (Open-R1, SmolLM3 RL, TRL; ≈$50–150 [E]).**
- **Trainer:** `GRPOTrainer` (or `RLOOTrainer`, which uses less memory).
- **LoRA:** r=16, all linear layers, LR ~1e-5.
- **Settings:**
  - **`beta=0.02` [E], never 0.**
  - `num_generations=8`, `loss_type="dapo"`, `scale_rewards="batch"`.
  - vLLM colocated on one GPU.
- **Reward functions (weighted):**
  - facts gate (fail → group minimum);
  - copy-rate penalty;
  - a two-sided length penalty with a soft band (DAPO shape);
  - the style reward from SIMILAR_PROJECTS §6.
  - No detector.
- **Watch:** `frac_reward_zero_std`, `completions/mean_length`, `entropy`, `kl`.
- **Stop:** at 200 steps, or when the KL budget is used up.

**Step 9. Promote (EVALS_AND_RL_PLAN gates).**
- Score on the hidden test set only once per candidate.
- Report raw and length-controlled win rates.
- Write the run YAML, eval and spend into `model/`.

**Rough GPU total [E]:** 2 + 4 + 5 + 7 + 8 ≈ $135–320. That leaves well over $1.5k of the $2k cap for raters and API pair generation.

---

## 13. Three mistakes Hugging Face admits making

1. **Training before the evals existed.** "We rushed ahead with model training before many of the above evals were implemented (e.g., RULER was not available until a few days before the model release)… In hindsight, this was a mistake." ([Smol Training Playbook](https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook), 2025-10-30).
   - *Our guard:* Step 0 is a hard gate. No GPU spend until the dev set, judge pin and vibe set exist.
2. **A data bug the metrics could not see.** A processing bug deleted every system message from the SFT corpus. The model ignored personas while the evals "looked OK". Only vibe testing caught it (same source). Open-R1 had the same pattern: a missing `<think>` prefill broke out-of-domain behaviour and was also found by vibe testing ([update 3](https://huggingface.co/blog/open-r1/update-3), 2025-03-11).
   - *Our guard:* Step 3 runs on every checkpoint, plus a template/EOS audit script.
3. **RL reward hacking on length.** Naive GRPO turned SmolLM3's concise mode into long "Wait, …" reasoning. Reward rose and completion length rose with it. An overlong penalty was needed (Smol Training Playbook). It is the same family of failure as Lambert's "verbose, confident-sounding responses" (rlhfbook ch. 14).
   - *Our guard:* a two-sided length band in every reward and every promotion gate.

**Also admitted, and worth knowing:**
- FineWeb: more dedup made data worse.
- Open-R1: packing hurt; an RM chose no better than random; the bigger split did worse.
- An Accelerate data-parallel bug kept master weights in BF16 and made the loss unstable (playbook mid-training section).
- TRL v1: the unused `Judge` abstraction.
- Zephyr: the judge favours verbose answers and its own family.

---

## Sources (all accessed 2026-11-01)

- Zephyr paper, 2023-10-25: https://arxiv.org/abs/2310.16944 · https://arxiv.org/html/2310.16944
- Zephyr-7B-β card: https://huggingface.co/HuggingFaceH4/zephyr-7b-beta
- Alignment Handbook: https://github.com/huggingface/alignment-handbook
  - Zephyr DPO QLoRA config: https://github.com/huggingface/alignment-handbook/blob/main/recipes/zephyr-7b-beta/dpo/config_qlora.yaml
  - SmolLM3 APO config: https://github.com/huggingface/alignment-handbook/blob/main/recipes/smollm3/dpo/apo.yaml
- Preference tuning DPO/IPO/KTO, 2024-01-18: https://huggingface.co/blog/pref-tuning
- TRL docs:
  - SFT: https://huggingface.co/docs/trl/main/en/sft_trainer
  - DPO: https://huggingface.co/docs/trl/main/en/dpo_trainer
  - KTO: https://huggingface.co/docs/trl/main/en/kto_trainer
  - GRPO: https://huggingface.co/docs/trl/main/en/grpo_trainer
  - Online DPO: https://huggingface.co/docs/trl/main/en/online_dpo_trainer
  - LoRA Without Regret: https://huggingface.co/docs/trl/main/en/lora_without_regret
  - Index: https://huggingface.co/docs/trl/main/en/index
- TRL releases (v1.17.1, 2026-10-30): https://github.com/huggingface/trl/releases
- TRL v1 blog, 2026-03-31: https://huggingface.co/blog/trl-v1
- N implementation details of RLHF with PPO, 2023-10-24: https://huggingface.co/blog/the_n_implementation_details_of_rlhf_with_ppo
- RLOO, 2024-06-12: https://huggingface.co/blog/putting_rl_back_in_rlhf_with_rloo
- Co-located vLLM, 2025-06-03: https://huggingface.co/blog/vllm-colocate
- Thinking Machines, LoRA Without Regret, 2025-09-29: https://thinkingmachines.ai/blog/lora/
- Open-R1:
  - Launch, 2025-01-28: https://huggingface.co/blog/open-r1
  - Update 2, 2025-02-10: https://huggingface.co/blog/open-r1/update-2
  - Update 3, 2025-03-11: https://huggingface.co/blog/open-r1/update-3
  - Repo: https://github.com/huggingface/open-r1
- SmolLM2 paper, 2025-02-04: https://arxiv.org/abs/2502.02737
- SmolLM3 blog, 2025-07-08: https://huggingface.co/blog/smollm3
- Smol Training Playbook, 2025-10-30: https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook (source: https://huggingface.co/spaces/HuggingFaceTB/smol-training-playbook/blob/main/app/src/content/article.mdx)
- Ultra-Scale Playbook, 2025-02-19: https://huggingface.co/spaces/nanotron/ultrascale-playbook (source: .../blob/main/ultra_blog.md)
- smol-course: https://github.com/huggingface/smol-course
- Deep RL course: https://huggingface.co/learn/deep-rl-course/unit0/introduction
- FineWeb:
  - Blog Space, created 2024-05-23: https://huggingface.co/spaces/HuggingFaceFW/blogpost-fineweb-v1
  - Paper, 2024-06-25: https://arxiv.org/abs/2406.17557
- Cosmopedia, 2024-03-20: https://huggingface.co/blog/cosmopedia
- Chung et al., diverse creative writing, 2025-03-21: https://arxiv.org/abs/2503.17126
- Community guide (Zadorozhny), 2026-01-19: https://huggingface.co/blog/karina-zadorozhny/guide-to-llm-post-training-algorithms
- RLHF book (Lambert), built 2026-10-30: https://rlhfbook.com/ · chapters: https://github.com/natolambert/rlhf-book/tree/main/book/chapters
- On-policy distillation / GOLD Space, created 2025-10-29: https://huggingface.co/spaces/HuggingFaceH4/on-policy-distillation

---

## What to steal

- **Evals, then a baby baseline, then vibe tests, then preference training** (Smol Playbook). It is a simple sequence, and HF admits breaking it.
- **The preference LR comes from the SFT LR:** scan 5–20× below. Scan β in 0.01–0.5. Train 1 epoch. Iterate in rounds on fresh pairs.
- **Strong-vs-weak and on-policy-with-grading pairs** (SmolLM3), with our human text as "strong".
- **`apo_zero` and `["sigmoid","sft"]` as DPO arms.** These are stable TRL code paths that keep the human text from drifting.
- **Merge DPO with SFT to repair lost skills** (SmolLM3's 0.9/0.1). It is free.
- **FineWeb's slop-phrase proxy** as a contamination check on our "human" corpus, and its warning that over-dedup hurts.
- **Open-R1's verify-then-filter** with logged keep rates. An LLM judge only rescues false rejects.
- **HF's habit of writing down what broke.** We should keep `model/FAILURES.md` the same way.

## What it changes for us

- **BASE_MODELS §5:** change SFT from 2 epochs to **1 epoch when DPO follows** (Zephyr finding). Set `max_length` from data, not the default 1024. Add the `eos_token` check. hl-trainer to update.
- **TECH.md §A.5 / roadmap step 3:** replace "small-beta ORPO" with stable `DPOTrainer` arms (`sigmoid`, `apo_zero`, `sigmoid+sft`), because ORPO and Online DPO are experimental in TRL 1.17.
- **EVALS_AND_RL_PLAN §3.5:** GRPOTrainer defaults to `beta=0.0`. Our configs must set β>0 explicitly, or there is no KL anchor at all. Add a two-sided length reward (SmolLM3's length-hacking failure).
- **New Step-0 gate in PLAN_30D:** no GPU spend until the judge pin, avg@k scoring, decontamination script and 20-prompt vibe set exist.
- **Data:** add FineWeb's slop-phrase check to the human-side filter, and test light vs heavy dedup instead of assuming more is better. hl-data-curator to own it.
- **Never add generic preference datasets** (UltraFeedback, Tulu) to "boost helpfulness". Lambert's appendix shows they push toward list-heavy, verbose slop.
- **Budget confirmed:** HF's recipes fit our plan at about $150–350 of GPU [E]. Rater time, not compute, is still the binding cost.
