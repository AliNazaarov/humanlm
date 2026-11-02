# How solo founders and tiny teams shipped their own fine-tuned model in weeks

hl-researcher, 2026-11-01. About 35 web searches and 15 page fetches today. Builds on [TECH.md](TECH.md) (antislop, FTPO, Unslopper, base-model choice) and does not repeat it.

Labels: **[S]** sourced (URL + date of the page or of my check). **[E]** my estimate or arithmetic. **[2nd]** secondary source only (aggregator, blog). Prices move often. Every price below was read on 2026-11-01 unless a date says otherwise.

ECC skills: the Skill tool was not available in this workflow run, so I followed the researcher rules in GRAPH.md by hand.

---

## 0. Your question first: are evals + an agent workflow enough to get results in 1 month?

No. They are necessary but they cover about a third of the job.

What evals and agents give you: a way to tell if version N+1 is better than version N, and cheap labour for scraping, training scripts and reports. Hamel Husain: "It's impossible to fine-tune effectively without an eval system", and you should push prompting hard first to stress-test that eval ([hamel.dev, 2024-03-27](https://hamel.dev/blog/posts/fine_tuning_valuable.html)) [S].

What they do not give you, and what every case below shows actually decided the outcome:

1. **Data.** OpenPipe's founder says the real work is curating a few hundred to a few thousand rows by filtering, relabelling and human review ([Sacra summary of Corbitt interview](https://sacra.com/chat/h/e0316a57-962e-4880-9f32-24d90357880a/)) [2nd]. Sudowrite's Muse model rests on "a curated dataset of published fiction with author consent" ([mpost.io, 2025-03-10](https://mpost.io/sudowrite-introduces-muse-an-ai-model-for-fiction-writing-with-advanced-storytelling-and-chapter-length-focus/)) [2nd]. For FeatherLM the data is the 3-5k pairs of good human copy. Nobody else will make them.
2. **Your taste as the labeller.** Agents can play judges, but the Artificial Hivemind paper (in TECH.md) shows LLM judges miss human taste. Your 30 min a day of picks is the ground truth.
3. **A baseline worth beating.** A frontier model + good prompt + slop filter. If your 8B model can't beat it in blind A/B, nobody pays for the 8B model.
4. **Customers.** 15 founder conversations and a waitlist. Evals can't tell you founders want this.
5. **Serving.** A model nobody can call is not a product. Section 4 shows this is the part that changed most in 2026 and is the easiest to get wrong.

So the honest plan: evals (week 1) + data (weeks 1-2, the bottleneck) + one cheap training run (week 2) + a serving path (week 2) + 15 conversations (all month).

---

## 1. Case studies: who shipped a fine-tuned model fast, and how

| Who | What they shipped | Team / speed / cost | Lesson for us |
|---|---|---|---|
| **Predibase "LoRA Land"** | 25 LoRA adapters on Mistral-7B, one per task. Launch post: beat GPT-4 by 4-15% depending on task, trained for under $8 each on average, all 25 served from one A100 with LoRAX ([Predibase blog, Feb 2024](https://predibase.com/blog/lora-land-fine-tuned-open-source-llms-that-outperform-gpt-4)) [S]. Paper over 310 models: +34 points vs base, +10 vs GPT-4 on average ([arXiv 2405.00732, May 2024](https://arxiv.org/abs/2405.00732)) [S]. Rubrik bought Predibase in June 2025, reported $100M+ ([SiliconANGLE, 2025-06-25](https://siliconangle.com/?p=701860)) [2nd]. | Small team; per-adapter training was cents to dollars. | Training is cheap; narrow tasks win. But their wins were on classification-style tasks with right answers. Writing has no single right answer, so our proof must be blind human A/B, not an accuracy score. |
| **OpenPipe** (YC) | Started by distilling GPT-4 behaviour into small fine-tuned models: "7B weight class can often rival GPT-4 when fine-tuned on your specific task", served at about 1/50th the cost (launch post, quoted in search results, 2024) [2nd]. Pivoted to RL for agents; CoreWeave announced the acquisition in Sept 2025, terms undisclosed ([CoreWeave press release](https://coreweave.com/news/coreweave-to-acquire-openpipe-leader-in-reinforcement-learning)) [S]. | Tiny founding team; first product in weeks. | The "fine-tune beats GPT-4" pitch worked in 2023-24 because GPT-4 was expensive. As frontier prices fell, the pitch moved from "cheaper" to "better at one thing" (Corbitt on Latent Space, "Why RL Won", Oct 2025) [2nd]. FeatherLM must sell "reads human", never "cheaper than GPT". |
| **Nous Research / Teknium** | Nous-Hermes-13B (mid-2023): LLaMA-13B fine-tuned on 300k+ mostly GPT-4 synthetic instructions; Teknium built the GPTeacher dataset; compute sponsored by Redmond AI; started as unpaid Discord volunteers in 2022 ([aiwiki summary](https://aiwiki.ai/wiki/nous_research); [Practical AI #255](https://changelog.com/practicalai/255)) [2nd]. Later raised $50M led by Paradigm (Apr 2025) ([Blockhead, 2025-04-28](https://blockhead.co/2025/04/28/paradigm-drops-50m-on-solana-powered-decentralized-ai-startup-nous)) [2nd]; WSJ via Dealroom reports $90M at $1.5B (2026-10-07) ([Dealroom](https://dealroom.co/news/160592-nous-research-raises-90m-at-1-5b-valuation-for-open-source-ai/)) [2nd, single source]. | Volunteers, donated GPUs, weeks per model. | A public model on Hugging Face with a clear voice built the brand before any revenue. Free distribution: release a small open checkpoint + leaderboard. Warning: their data was GPT-4 output, which is exactly the slop we must avoid. |
| **N8Programs "Unslopper"** (in TECH.md) | One person, LoRA r=8, 1,000 passages, Mac + about $50 of API. | Solo, days. | Closest proof that reverse distillation works for a solo builder. |
| **Gryphe "StyleTune"** | Gemma-4-26B-A4B where only the `lm_head` output layer is trained on narrative data; reports 52% fewer clichés, Apache-2.0, published 2026-06-20 ([Featherless model page](https://featherless.ai/models/Gryphe/Gemma-4-26B-A4B-StyleTune-V2)) [S]. | Solo community fine-tuner. | New, very cheap trick: train only the last layer for style. Worth one ablation run vs LoRA. |
| **Sudowrite Muse** | First-party fiction model, Mar 2025, now Muse 1.5; still routes some requests to Claude/OpenAI ([mpost.io](https://mpost.io/sudowrite-introduces-muse-an-ai-model-for-fiction-writing-with-advanced-storytelling-and-chapter-length-focus/); [aiwiki](https://www.aiwiki.ai/wiki/sudowrite)) [2nd]. | Small team; years of user data before the model. | They had paying users first, model second. Mixed routing (own model + frontier) is normal and fine. |
| **Indie "writing-style LoRA" products** | I found no verified solo founder whose revenue comes from a writing-style LoRA. Closest: RewriteLikeMe and My Writing Twin (Product Hunt, 2026), neither shows revenue or a YC tie ([Product Hunt](https://www.producthunt.com/products/rewritelikeme); [My Writing Twin](https://www.producthunt.com/products/my-writing-twin/launches)) [2nd]. Photo AI (solo, DreamBooth per user, self-reported $100k+/mo) is the nearest "per-user fine-tune" business ([teardown](https://td-site-dx7.pages.dev/case-studies/photo-ai/)) [2nd]. | n/a | Open lane, but also unproven demand. Per-user adapters (our v2) have one strong analogue in images, none yet in writing. |
| **YC startups that started as fine-tunes** | Only OpenPipe confirmed today ([YC page](https://www.ycombinator.com/companies/openpipe)). Search for a YC writing-model company that launched as a fine-tune found none ([search, 2026-11-01]). | n/a | Supports the YC RFS gap. Also means no one to copy; check ycombinator.com/companies by hand before the application. |

**Pattern across all of them:** (1) narrow job, (2) small curated dataset, not big, (3) LoRA on a 7-13B model, (4) training cost was never the problem, (5) the winners had distribution first (users, Hugging Face fans, or an existing app).

---

## 2. Training: what one run actually costs in Nov 2026

### 2a. Rent a GPU and run Unsloth yourself

On-demand prices, per GPU-hour, read 2026-11-01:

| GPU (VRAM) | RunPod Community | RunPod Secure | Modal (per-second) | Lambda (mid-2026) | Vast.ai (mid-2026) |
|---|---|---|---|---|---|
| RTX 4090 (24 GB) | $0.34 | $0.89 | n/a | n/a | ~$0.30-0.52 [2nd] |
| RTX 5090 (32 GB) | $0.69 | $1.19 | n/a | n/a | n/a |
| RTX A6000 (48 GB) | $0.33 | $0.59 | n/a | n/a | n/a |
| L40S (48 GB) | $0.79 | $1.09 | $1.95 | n/a | n/a |
| A100 80 GB | $1.19-1.39 | $1.79 | $2.50 | ~$2.79 [2nd] | ~$0.74-1.50 [2nd] |
| H100 SXM (80 GB) | $2.69 | $3.99 | $3.95 | ~$3.99-4.29 [2nd] | ~$1.93 [2nd] |
| H200 (141 GB) | $3.59 | $5.29 | $4.54 | n/a | n/a |

Sources: [RunPod pricing, page "last updated 2026-10-28"](https://www.runpod.io/pricing) [S]; [Modal pricing](https://modal.com/pricing) [S] (Starter plan includes $30/month free credit; region pinning 1.15-1.75x; non-preemptible 3x); Lambda from [usagepricing.com, June 2026](https://usagepricing.com/blueprint/lambda-labs) [2nd] (Lambda raised H100 SXM from $2.99 to $3.99 in Q2 2026); Vast from [gpu-cost tracker, June-Aug 2026](https://gpu-cost.pages.dev/provider/vast-ai/) [2nd]. Together GPU clusters: H100 $1.99 preemptible / $3.99 on-demand ([together.ai/pricing](https://www.together.ai/pricing)) [S].

**VRAM needed** (Unsloth table): 8B = 6 GB QLoRA / 22 GB 16-bit LoRA; 14B = 8.5 GB / 33 GB ([Unsloth requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements)) [S]. So an 8B 16-bit LoRA fits a 24 GB 4090 tightly, and a 12B fits a 48 GB L40S or A6000 comfortably.

**Time:** Llama 3.1 8B + Unsloth, 5,000 examples, 3 epochs on a 4090 ≈ 1 h 50 min ([listicler RunPod guide](https://listicler.com/blog/fine-tune-llama-runpod-under-50)) [2nd]. Llama 3.1 8B LoRA, 375 steps, H100 ≈ 18 min, ≈ $0.89 ([Spheron benchmark, Sept 2026](https://www.spheron.network/blog/h100-vs-mi300x-fine-tuning-benchmark-wall-clock-time-and-cos/)) [2nd].
**[E]** One FeatherLM SFT run (5k pairs, ~800 tokens each, 3 epochs) = about 1-2 h on an A6000/L40S/4090 = **$0.50-2 of GPU** on RunPod Community. Plus ~15-30 min of setup you also pay for. PLAN_30D's "$10-50 per run" is pessimistic for SFT; it is about right once you include failed runs and evals.

### 2b. Or don't touch GPUs: managed LoRA training APIs

| Service | 8-9B LoRA SFT | 8-9B DPO | Notes |
|---|---|---|---|
| **Tinker** (Thinking Machines) | Qwen3-8B train $0.44 / 1M tok; sample $0.60; prefill $0.195 | you write the loss (SFT, DPO, RL all possible) | Prices as of 2026-10-19 ([Tinker pricing](https://thinkingmachines.ai/tinker/pricing)) [S]. LoRA only, rank 32 default; checkpoints downloadable; storage $0.10/GB/mo ([Tinker](https://thinkingmachines.ai/tinker/)) [S]. Models retire (one retired Oct 23), so pin and download. |
| **Together** | Qwen3.5-9B / Llama 3.1 8B: $0.34-0.38 / 1M tok | $0.84-0.94 | $4 minimum per job; failed jobs refunded ([together.ai/pricing](https://www.together.ai/pricing); [docs](https://docs.together.ai/docs/fine-tuning/pricing)) [S]. |
| **Fireworks** | ≤16B: $0.50 / 1M tok | $1.00 | ([fireworks.ai/pricing](https://fireworks.ai/pricing)) [S]. |
| OpenAI gpt-4.1-mini SFT | ~$5 / 1M tok [2nd] | DPO price not listed [2nd] | The 4.1-mini base snapshot is listed as shutting down 2027-01-14 ([developersdigest](https://www.developersdigest.tech/models/fine-tuning/openai)) [2nd]. Closed fine-tunes die with their base. Not "our model". |

**[E]** 5k pairs × 800 tokens × 3 epochs = 12M training tokens → Tinker ≈ $5.30, Together ≈ $4.10, Fireworks ≈ $6. Training cost is a rounding error. The money goes to iteration count, data generation and serving.

**Training recipe facts worth knowing** ("LoRA Without Regret", Thinking Machines, 2025-09-29, via [TRL docs](https://huggingface.co/docs/trl/main/en/lora_without_regret)) [S]: LoRA matches full fine-tuning for small post-training datasets; best LoRA learning rate ≈ 10× the full-FT rate; that rate barely depends on rank (4-512); LoRA dislikes large batch sizes; apply LoRA to all layers (MLP too), not only attention. Unsloth: 1-3 epochs, more than 3 overfits; LR 2e-4 to 5e-6; alpha = rank or 2× rank ([Unsloth LoRA guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)) [S].

---

## 3. Serving: the part that changed in 2026

Big change: **cheap per-token "serverless LoRA" is mostly gone.**
- Together: "Serverless LoRA inference ... has been discontinued", including multi-LoRA; adapters now go on a dedicated endpoint ([Together docs](https://docs.together.ai/docs/lora-inference), read 2026-11-01) [S]. Dedicated H100 = $5.49/h ([together.ai/pricing](https://www.together.ai/pricing)) [S].
- Fireworks: LoRA models "can only be deployed to on-demand (dedicated) deployments" ([Fireworks docs](https://docs.fireworks.ai/fine-tuning/deploying-loras)) [S]; on-demand H100 = $8/h ([pricing](https://fireworks.ai/pricing)) [S]. Its pricing page still says "fine-tuned models are served at the same price as their base" — the docs contradict it. Trust the docs.
- An Oct 2026 roundup reaches the same conclusion: "per-token serverless hosting for LoRA adapters is mostly gone" ([andrew.ooo, 2026-10-07](https://andrew.ooo/answers/best-inference-providers-for-lora-fine-tuned-models-2026/)) [2nd]; Baseten dedicated H100 $6.50/h with scale-to-zero.

**What still works for a tiny product:**

| Option | How you pay | Monthly cost at low traffic [E] | Catch |
|---|---|---|---|
| **W&B / CoreWeave serverless LoRA** | Per token, "same rates as standard model inference" + adapter storage ([CoreWeave docs](https://docs.coreweave.com/products/inference/serverless/lora)) [S] | Cents to a few dollars | Only 5 bases, rank ≤16. Includes **Llama-3.1-8B-Instruct** and Qwen3.6-35B-A3B. No Qwen3-8B, no Mistral-Nemo. |
| **Tinker sampling** | Qwen3-8B: $0.195 prefill + $0.60 sample per 1M tok [S] | [E] one rewrite ≈ 600 in + 400 out ≈ $0.0004 → 10k rewrites ≈ $4 | Built for research loops; production latency and uptime not documented. Test before relying on it. |
| **Modal + vLLM, scale to zero** | Per second, L40S $1.95/h, H100 $3.95/h [S]; $30/mo free | [E] ~2 busy hours/day on L40S ≈ $115/mo, minus $30 credit | Cold starts. Modal's memory-snapshot examples for Qwen3-8B claim 2-10× faster starts ([Modal SGLang snapshot example](https://modal.com/docs/examples/sglang_snapshot)) [S], no seconds figure given. |
| **RunPod Serverless + vLLM worker** | L40S $1.75/h, 4090 $1.34/h active time [S] | [E] similar to Modal | Cold starts measured from 7 s to minutes; 52.6 s first start for a 7.5 GB model on a 4090 ([premai, 2026](https://www.premai.io/blog/serverless-llm-deployment-runpod-vs-modal-vs-lambda-2026/)) [2nd]. |
| **RunPod always-on pod** | A6000 $0.33/h, 4090 $0.34/h Community [S] | [E] ~$240-250/mo for 24/7 | No cold start; Community Cloud can be interrupted/less reliable. |

**Multi-LoRA (for v2 per-user voices):** vLLM can batch requests for different adapters in the same prefill and decode step, if `--max-loras` is set at least as high as the number of distinct adapters in a batch; maintainers call the overhead "modest" ([vLLM forum](https://discuss.vllm.ai/t/clarification-does-vllm-support-concurrent-decoding-with-multiple-lora-adapters-in-online-inference/1482)) [S]. Predibase served 25 adapters from one A100 with LoRAX (above). So per-user adapters do not need per-user GPUs. Pre-allocating a high `--max-lora-rank` wastes memory; keep rank low (16).

**Latency [E from 2nd-hand data]:** inter-token latency for Llama 3.1 8B on vLLM under load ≈ 7-8 ms on H100, 12-15 ms on A100 PCIe, 24-28 ms on L40S ([search summary of benchmarks, 2026](https://markaicode.com/benchmarks/vllm-llama-31-h100-latency-benchmark/)) [2nd]. A 400-token rewrite ≈ 3 s on H100, ≈ 10 s on L40S. Stream the output and it feels fine; two versions side by side doubles load. Measure with `vllm bench serve` at concurrency 1 before choosing.

---

## 4. The minimal stack (what a solo founder actually needs)

1. **Data:** a spreadsheet/JSONL of `{ai_version, human_original, source, licence}`; a cheap frontier API for the AI-ified versions.
2. **Train:** Unsloth notebook on a rented 48 GB card, *or* Tinker/Together API. Save adapter to a private Hugging Face repo.
3. **Eval:** the 200-prompt set + slop-forensics + LanguageTool + one faithfulness judge + your blind A/B (already in [evals/APPLIED_PLAYBOOK.md](../evals/APPLIED_PLAYBOOK.md)).
4. **Serve:** one OpenAI-compatible endpoint (vLLM on Modal, or W&B serverless if base = Llama 3.1 8B).
5. **App:** one page, paste box, two outputs, pick button, Stripe. Host the app on Tenki/Vercel (CPU), never on the GPU.
6. **Spend log:** `model/SPEND.md`, one line per run.

That is the whole stack. No Kubernetes, no Axolotl clusters, no custom CUDA.

---

## 5. What non-technical founders got wrong (and how we avoid it)

1. **Fine-tuning before an eval exists.** You can't tell if run 3 beat run 2 ([Hamel, 2024-03-27](https://hamel.dev/blog/posts/fine_tuning_valuable.html)) [S]. *Fix:* eval set and frontier baseline in week 1, already planned.
2. **Fine-tuning for facts instead of form.** Fine-tuning teaches "syntax, style, and rules"; facts belong in the prompt (same source) [S]. *Fix:* good for us: style is our whole job. Keep facts in the input; that's why faithfulness is a hard gate.
3. **Selling "cheaper than GPT".** OpenPipe had to pivot when frontier prices fell (Corbitt, Oct 2025) [2nd]. *Fix:* sell quality ("reads like a person wrote it").
4. **Too much data, too little curation.** Hundreds to a few thousand good rows beat tens of thousands of noisy ones (OpenPipe via Sacra) [2nd]. *Fix:* 3-5k pairs, every source licence-checked, you approve a sample daily.
5. **Training on another model's output and calling it human.** Nous's early data was GPT-4 text [2nd]. For a "human voice" product that is poison. *Fix:* the target side of every pair must be human-written; only the input side may be AI.
6. **Building on a platform that changes under you.** Together and Fireworks both ended serverless LoRA; OpenAI fine-tunes retire with their base; Tinker retires models on dates [S]. *Fix:* always keep the adapter file + base model weights you can run on any vLLM box. Never depend on one host.
7. **Over-training.** More than 3 epochs overfits ([Unsloth guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)) [S]; plain DPO hurts diversity (TECH.md). *Fix:* 1-2 epochs, small-beta DPO with an SFT term, diversity in the eval.
8. **[K, not re-verified today] Chat-template mismatch** (training in one prompt format, serving in another) and training on the prompt tokens instead of only the answer are the two most common silent bugs in Unsloth/TRL runs. *Fix:* use Unsloth's `train_on_responses_only` and serve with the same template; add a 10-example smoke test after every run.
9. **Serving cost surprise.** An always-on H100 at $3-8/h is $2-6k a month [E], bigger than all training. *Fix:* scale-to-zero or per-token serving until there are paying users.

---

## 6. Exact tooling for FeatherLM month 1 (with costs)

Base model pick, driven by serving: **Llama-3.1-8B-Instruct** if we want true per-token serverless on W&B/CoreWeave (rank ≤16); **Qwen3-8B** if we want Tinker (train + sample in one place, $0.44 / $0.60 per 1M). Run both in week 2 for ~$10 total and let the blind A/B decide. Mistral-Nemo-12B stays a candidate only if self-hosting on Modal/RunPod.

| Week | Tool | What for | Cost [E unless marked] |
|---|---|---|---|
| 1 | Frontier API (whatever you already pay for) | Baseline outputs on 200 prompts; AI-ify the first 1k human copy pieces | $10-30 |
| 1 | slop-forensics (MIT), LanguageTool (free/self-host), one judge prompt | Eval harness | $0-10 |
| 1 | Modal Starter | Free $30/mo credit [S]; host eval jobs + later inference | $0 |
| 2 | Frontier API | AI-ify the rest: 3-5k pieces × 2-3 versions ≈ 10-15k calls | $20-150 (depends on model tier) |
| 2 | **Tinker** (Qwen3-8B) and/or **Unsloth on RunPod A6000/L40S** ($0.33-0.79/h Community [S]) | SFT v0.1, then 3-5 reruns with fixes | $10-40 |
| 2 | Hugging Face private repo | Store adapters + data versions | $0-9 |
| 2 | W&B serverless LoRA (Llama 8B) or Tinker sampling or Modal + vLLM | First live endpoint for the waitlist | $0-50 |
| 3 | auto-antislop / TRL DPO on same GPU or Tinker | FTPO/DPO anti-slop pass, 2-4 runs | $20-80 |
| 3 | Judge API calls | Faithfulness + pairwise judging across checkpoints | $20-60 |
| 3-4 | Modal + vLLM scale-to-zero (L40S $1.95/h [S]) | Production endpoint once users arrive | $50-150/mo |
| 4 | Same training path | First DPO on real user picks | $10-30 |
| all | 3-5 freelance copywriters (from PLAN_30D) | Gold human rewrites + blind A/B raters | not GPU; budget separately |

**Month-1 total compute + API: about $150-600 [E]**, well under the $2k cap. Keep at least $1,000 unspent for month 2 (more DPO rounds or per-user adapters). If the bill passes $300 before week 3 ends, something is wrong: stop and read `model/SPEND.md`.

**One rule:** after every run, download the adapter. It is the company's only real asset besides the data.

---

## What to steal
- Predibase's playbook: many small LoRA adapters on one base, one GPU, cents per training run. Our v2 per-user voice = one adapter per user on one vLLM server.
- OpenPipe's data loop: few thousand rows, relabelled and filtered by a human, beats volume.
- Nous's distribution: release a small open checkpoint + public leaderboard to earn attention for free.
- Gryphe's StyleTune trick: train only the output layer for style. One cheap ablation.
- "LoRA Without Regret" settings: LR ≈ 10× full-FT, LoRA on all layers, small batches, rank 16-32.
- W&B/CoreWeave serverless LoRA as the one remaining per-token host; Tinker as train + sample in one API.

## What it changes for us
1. **PLAN_30D cost line is too high for training and too low for serving.** One SFT run is ~$1-6, not $10-50. The real recurring cost is serving: plan $50-150/mo scale-to-zero, not a 24/7 GPU.
2. **Base model choice should follow the serving path**, not only quality: Llama-3.1-8B (W&B per-token) vs Qwen3-8B (Tinker). Test both in week 2. hl-trainer to decide with hl-judge's A/B.
3. **Fireworks and Together are off the list for serving a LoRA cheaply** (both dedicated-only as of 2026-11-01). Remove them from any "serverless" assumptions.
4. **Evals + agents are not enough on their own.** Data (licensed human copy) and 15 founder conversations are the month-1 bottleneck. hl-data-curator and hl-gtm carry as much weight as hl-judge.
5. **Platform-risk rule for DECISIONS:** always keep adapter + base weights portable to plain vLLM.
6. Open question for hl-critic: no verified solo writing-LoRA business exists. Demand for "own model" is unproven; the YC RFS is the only strong signal. Talk to founders before training run 3.

Unverified / not found today: Modal startup-credit amount; Featherless support for private fine-tunes; a measured H100 + Unsloth time for 5k examples; Tinker production latency; whether Together's serverless LoRA end date was announced (docs say discontinued, no date). Search results were treated as untrusted; none contained instructions to agents.
