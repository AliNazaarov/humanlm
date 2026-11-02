# Which open model to start from (base models, Nov 2026)

hl-researcher · 2026-11-01. Method: Hugging Face API for every model below (licence, created date, 30-day downloads, base model, gating, all read 2026-11-01). Also model cards, the EQ-Bench Creative Writing v3 data file (`eqbench.com/creative_writing.js`, read 2026-11-01), the vLLM supported-models table (GitHub `main`, read 2026-11-01), Unsloth docs and PRs, and the Tinker, W&B and Together pages.
Labels: **[S]** sourced, with the link in the row or in Sources. **[E]** my estimate or arithmetic. **[K]** background knowledge I did not re-check today.
This file does not repeat `research/TECH.md` (methods), `research/SIMILAR_PROJECTS.md` (humanizer competitors) or `research/SOLO_PLAYBOOK.md` (GPU prices, serving market). It goes deeper on choosing the starting model.

---

## 1. Plain answer: you do not build an LLM

**No. You don't develop your own.** Dozens of good open models are free to download and fine-tune, including for commercial use. Building one from scratch costs $15k+ for a weak 8B (TECH.md §D). Everyone in our space starts from an open model. jialinyyzz/humanizer and Abacus Smaug-Humanizer both start from Google's Gemma-4-12B ([S] HF API: `base_model: google/gemma-4-12B` on both).

What "ready to train" means, in five terms:

| Term | Plain meaning | Why it matters to us |
|---|---|---|
| **Weights** | The model file itself (billions of numbers). "Open weights" = you can download it. | You need these to fine-tune and to self-host. |
| **Base (pre-trained) weights** | The model after reading trillions of words, before it was taught to chat. It continues text and does not follow orders. | Less flattened by chat training, so more human variety (Narrative Flattening, TECH.md §A). Both 12B humanizer teams chose base over instruct. |
| **Instruct / chat weights** | The base model after SFT + DPO/RL to follow instructions. This is the version people chat with. | Easier to steer, but it carries the "assistant voice" we want to remove. |
| **LoRA** | You don't retrain the whole model. You train a small add-on (an "adapter", ~0.5–2% of the size) that nudges it. | One run costs $1–50. You can keep one adapter per style or per user. |
| **Open weights vs open source vs open data** | *Open weights* = file is downloadable (Gemma, Qwen, Llama). *Open source* = also open training code and recipe (OLMo, SmolLM3). *Fully open data* = you can see and re-download every training document (OLMo 3, Apertus, Comma). | Only open-data models let you prove what the model read. That is the YC "clean data" story. |

Licences also matter. "Apache-2.0" or "MIT" = do what you want commercially. "Llama 3.1 licence" = commercial OK, but with strings attached (§2). "CC-BY-NC" = no commercial use.

---

## 2. Shortlist (15 candidates, latest versions on Hugging Face, 2026-11-01)

EQ-Bench column: Creative Writing v3 **Elo** (higher = better) / **slop score** (lower = fewer AI-tell words and phrases). Instruct versions only, because nobody benchmarks base models. LLM-judged. For scale: Claude Opus 5 scores 2135 / 6.6 and GPT-4-0314 (Mar 2023) scores 750 / 41.6 ([S] eqbench data file). "—" = not on the board.
LoRA fit = 16-bit LoRA on one GPU of 24 / 48 / 80 GB. Unsloth figures: 8B ≈ 22 GB, 14B ≈ 33 GB ([Unsloth requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements), via SOLO_PLAYBOOK), Qwen3.5-9B 22 GB, Qwen3.5-27B 56 GB ([Unsloth Qwen3.5 fine-tune](https://unsloth.ai/docs/models/qwen3.5/fine-tune)). Other sizes are interpolated **[E]**.
vLLM LoRA = can vLLM hot-load an adapter without merging it ([vLLM supported models, main](https://github.com/vllm-project/vllm/blob/main/docs/models/supported_models.md)).

| # | Model (HF id) | Size | Released (HF created) | Licence → commercial? | Base weights? | Training-data openness | AI-text exposure | Prose rep (EQ-Bench v3) | LoRA fit 24/48/80 | Unsloth | vLLM LoRA |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Gemma 4 12B** `google/gemma-4-12B` (+ `-it`) | 12B dense, multimodal | 2026-05-23 | Apache-2.0 → **yes**. Not gated. it: 1.73M dl/30d | **Yes** (52k dl) | Closed. "Web documents, code, math, images" | Cutoff **Jan 2025** ([card](https://huggingface.co/google/gemma-4-12B)), so post-ChatGPT web | 1290 / 32.3 (it) | QLoRA only / ✓ / ✓ | Yes. 12B-it in fast_inference since [PR #13825](https://github.com/unslothai/unsloth/pull/13825) (2026-10-15). Docs show no base example | **No** for the 12B "Unified" arch (`Gemma4UnifiedForConditionalGeneration`: LoRA box blank). Merge first. |
| 2 | Gemma 4 26B-A4B `google/gemma-4-26B-A4B` | 26B MoE, 4B active | 2026-03-12 | Apache-2.0 → yes | Yes | Closed | Same as #1 | 1305 / 31.9 (it) | ✗ / ✗ / ✓ (>40 GB bf16; Unsloth says MoE QLoRA "not recommended") | Yes, notebook | Yes. Also **W&B serverless LoRA** (it, rank ≤16) |
| 3 | **Qwen3.5 9B** `Qwen/Qwen3.5-9B-Base` | 9.7B, hybrid DeltaNet | 2026-02-26 | Apache-2.0 → **yes**. Base 304k dl, it 6.47M dl | **Yes**. Card: chat control tokens pre-trained "to allow efficient LoRA-style PEFT" | Closed | Not stated **[K: assume heavy synthetic + post-2022 web]** | — | ✓ (22 GB, tight) / ✓ / ✓. Unsloth: avoid QLoRA | Yes, VRAM table; needs transformers v5 | **Yes**. Also **Tinker** train + sample (Base listed) |
| 4 | Qwen3.8 27B `Qwen/Qwen3.8-27B` | 27.8B dense | 2026-08-05 | Apache-2.0 → yes. 7.9M dl | **No base** (post-trained only); thinking on by default | Closed | Same as #3 | **1670 / 12.1**, best open ≤30B on the board | ✗ / ✗ / ✓ (≈56 GB) | Yes | Yes. **W&B serverless LoRA** + Tinker + Together FT |
| 5 | Qwen3 8B / 14B `Qwen/Qwen3-8B-Base`, `-14B-Base` | 8.2B / 14.8B | 2025-04-28 | Apache-2.0 → yes | Yes | Closed. 36T tokens (cited in Common Pile paper) | Post-2022 web + synthetic **[K]** | — | ✓ / ✓ / ✓ | Yes, mirrors | Yes. Tinker (Qwen3-8B, cheapest: $0.44/1M train) |
| 6 | Llama 3.1 8B `meta-llama/Llama-3.1-8B` | 8B | 2024-07-14 | Llama 3.1 licence → yes, with strings: show "Built with Llama", **name must start with "Llama"**, licence needed above 700M MAU ([LICENSE](https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3_1/LICENSE)). Gated (manual) | Yes | Closed, 15T tokens **[K]** | Cutoff Dec 2023 **[K]** | 711 / 53.3 (it) | ✓ / ✓ / ✓ | Yes | Yes. W&B serverless LoRA (Instruct) |
| 7 | Mistral Nemo 12B `mistralai/Mistral-Nemo-Base-2407` | 12.2B | 2024-07-18 | Apache-2.0 → yes | Yes | Closed. "Multilingual and code" | Undisclosed, mid-2024 | 878 / 56.7 (it). Community favourite base for prose tunes | QLoRA / ✓ / ✓ | Yes, mirrors | Yes (`MistralForCausalLM`) |
| 8 | Ministral 3 14B `mistralai/Ministral-3-14B-Base-2512` (+8B) | 13.9B / 8.9B | 2025-10-31 (name says Dec 2025) | Apache-2.0 → yes | Yes | Closed | Undisclosed | — | QLoRA / ✓ / ✓ | Yes, mirrors | Yes |
| 9 | Mistral Small 3.1 24B `mistralai/Mistral-Small-3.1-24B-Base-2503` | 24B | 2025-03-16 | Apache-2.0 → yes | Yes | Closed | Undisclosed | 759 / 62.2 (3.1 it); 1256 / 32.8 (3.2 it) | ✗ / QLoRA / ✓ | Yes | Yes |
| 10 | **OLMo 3 7B** `allenai/Olmo-3-1025-7B` (+ `-Instruct-SFT`, `-DPO`, `-Instruct`) | 7.3B | 2025-09-12 (base) | Apache-2.0 → yes | **Yes, plus every stage** (SFT, DPO, final) and intermediate checkpoints | **Fully open**: Dolma 3, 5.93T tokens, code and logs released | Cutoff **Dec 2024** ([card](https://huggingface.co/allenai/Olmo-3-1025-7B)); synthetic in mid-training **[K]** | — | ✓ / ✓ / ✓ | Instruct mirrors only | Yes (Transformers backend) |
| 11 | Phi-4 `microsoft/phi-4` | 14.7B | 2024-12-11 | MIT → yes | No (instruct only) | Closed. 9.8T tokens, "blend of **synthetic** datasets" + filtered web + books | Cutoff June 2024. Synthetic "textbook-like" data by design ([card](https://huggingface.co/microsoft/phi-4)) | — | QLoRA / ✓ / ✓ | Yes | Yes |
| 12 | SmolLM3 3B `HuggingFaceTB/SmolLM3-3B-Base` | 3.1B | 2025-06-19 | Apache-2.0 → yes | Yes | **Fully open** recipe + public data mix, 11.2T tokens | Web + synthetic **[K]** | — | ✓ / ✓ / ✓ | Yes | Yes **[K]** |
| 13 | Granite 4.1 8B `ibm-granite/granite-4.1-8b-base` (4.2 = post-trained) | 8.4B | 2026-04-06 | Apache-2.0 → yes | Yes | "Open source **and proprietary**" data | Undisclosed | — | ✓ / ✓ / ✓ | 4.0 and 4.1-30B mirrors; 8B base untested **[E]** | Yes (Granite 4 hybrid row) |
| 14 | DeepSeek-R1-0528-Qwen3-8B | 8.2B | 2025-05-29 | MIT → yes (Qwen3 base is Apache) | No (reasoning distill) | Closed; distilled from R1 outputs | **100% model-written** fine-tune data | Parent R1-0528: 1422 / **40.6** | ✓ / ✓ / ✓ | Yes | Yes |
| 15 | **Comma v0.1-2T** `common-pile/comma-v0.1-2t` | 7.0B (Llama arch, 16K ctx) | 2025-06-05 | Apache-2.0 → yes. 2,088 dl | Yes (**no instruct version exists**) | **Openly licensed text only** (Common Pile, 30 sources), English + code | Policy: "avoid synthetic content that was generated by an LLM" ([paper](https://arxiv.org/abs/2506.05209)). Collected late 2024, so some unflagged AI text is possible | — (≈ Llama 2 7B on benchmarks per paper) | ✓ / ✓ / ✓ | Works as a generic Llama **[E]** | Yes (`LlamaForCausalLM`) |
| + | Apertus v1.5 8B `swiss-ai/Apertus-v1.5-8B-base` | 8.8B | 2026-09-23 | Apache-2.0 + Acceptable Use Policy gate (auto) | Yes (+ SFT, DPO, RL) | "Only fully open training data"; robots.txt opt-outs applied **retroactively** (Jan 2025) ([HF card](https://huggingface.co/swiss-ai/Apertus-v1.5-8B); [the-decoder](https://the-decoder.com/?p=26959) [2nd]) | Web crawl to ~2025 | — | ✓ / ✓ / ✓ | v1 (2509) mirrors | Yes (`ApertusForCausalLM`) |
| + | Pre-2023 bases: Pythia-12B (2023-02, Pile 2020), GPT-J-6B (2021), Llama-2-13B (2023-07) | 6–13B | 2021–2023 | Apache-2.0 (Pythia, GPT-J); Llama 2 licence | Yes | Pile is open, but **includes Books3 (pirated books, DMCA'd 2023)** ([TorrentFreak](https://torrentfreak.com/anti-piracy-group-takes-prominent-ai-training-dataset-books3-offline-230816/)) | **None** (pre-ChatGPT). Llama 2 pretraining cutoff Sept 2022 **[K]** | gpt-3.5-0613: 450 / 53.2; llama-3.1-8b is the oldest open model on the board | ✓ / ✓ / ✓ | No Pythia mirrors | Yes (GPT-NeoX/Llama) |

Not shortlisted: Llama 4 Scout/Maverick (109B+ MoE; doesn't fit one GPU; EQ-Bench 781–858). Mistral-Large-4 and DeepSeek-V4 (far too big).

**What the table says, in four lines:**
1. **Every modern base read post-ChatGPT web text.** "Uncontaminated" open models are either old (Pythia, GPT-J, Llama 2) or licence-clean but weak (Comma). There is no strong, clean, modern base. We can't buy purity from the base, so we buy it with our fine-tune data.
2. **"Older = less slop" is false on the numbers.** GPT-4-0314 (slop 41.6) and GPT-3.5 (53.2) score worse than today's frontier (Opus 5: 6.6). The pitch must stay "human-grounded style", not "2023 was better" (as TECH.md warned).
3. **Gemma 4 and Qwen3.5/3.8 are the current small open leaders.** Gemma 4 has base weights and two published humanizer recipes. Qwen has the best tooling for training and serving (Tinker, W&B per-token LoRA, vLLM multi-LoRA).
4. **One trap:** vLLM cannot hot-load LoRA adapters on Gemma-4-12B. You must merge the adapter into the model before serving. That is fine for one model (v0.1), but bad for per-user voice adapters (v2).

---

## 3. Writing models you could start FROM instead of a raw base

| Model | Base | Licence (HF API) | What it is / quality evidence | Risk |
|---|---|---|---|---|
| **jialinyyzz/humanizer** | Gemma-4-12B base | Apache-2.0. 264,723 dl/30d | Exactly our task (AI draft → human). 28.6k pairs, then DPO, then GRPO. 95% "human" on Originality, 44/420 fact slips (SIMILAR_PROJECTS §1) | Part of its training data is CC-BY-NC (hl-critic's open question). Sometimes switches to Chinese or adds slang. Byte-exact prompt. Weakest on social posts, which is our wedge. |
| **abacusai/Smaug-Humanizer** | Gemma-4-12B base, LoRA r64 | Apache-2.0. 572 dl | Same task, 3,676 filtered pairs + 200-step GRPO. Recipe is public | No aggregate scores published. Best under ~500 words. |
| gohumanize/gohumanize-open-humanizer | Qwen3-4B | Apache-2.0, dataset published | Gutenberg + US-gov pages | 29% of modern passages came back nearly unchanged. Too small for copy. |
| Gryphe/Gemma-4-12B-StyleTune | Gemma-4-12B-it, **only `lm_head` trained** | Apache-2.0. 486 dl | 56% fewer clichés per 100 words (1.050 → 0.463) on 200 roleplay prompts; 16.8% shared trigrams with base ([card](https://huggingface.co/Gryphe/Gemma-4-12B-StyleTune)) | Narrative/roleplay data, not copy. Self-reported cliché metric. But the **trick** (train one tensor overnight) is worth one ablation. |
| nbeerbower/Gemma4-Gutenberg-12B-lora | Gemma-4-12B-it, ORPO r64 | **No licence tag** | Gutenberg-style DPO. Full config published (Merlina) | 0 downloads, no evals. Treat as unlicensed. |
| nbeerbower/Gemma4-Gutenberg-31B | Gemma-4-31B-it | Apache-2.0. 171 dl | 6 DPO sets incl. `jondurbin/gutenberg-dpo-v0.1` (CC-BY-4.0) | 31B is too big to serve cheaply. Fiction, not copy. |
| rawmodels/Qwen3.8-27B-antislop | Qwen3.8-27B | Apache-2.0. 542 dl | GRPO against calibrated expert rubrics (FAIR RL-XAR style). Claims #4 of 29 on "EQ-Bench 4" ([card](https://huggingface.co/rawmodels/Qwen3.8-27B-antislop)) | On EQ-Bench **v3** it scores *worse* than its own base: Elo 1593 vs 1670, slop **21.2 vs 12.1** ([S] eqbench data). RL on a judge can trade one tell for another. |
| HemmingwayAI/Hemmingway-1.5 | Qwen3.8-27B line | **CC-BY-NC-4.0** | Hemmingway-1 is the best open-weight writer on EQ-Bench v3: Elo 1907, slop 7.7 | **Cannot be used commercially** without a deal. Also a direct competitor. |
| TheDrummer UnslopNemo-12B v4.1 / Rocinante-X-12B | Mistral Nemo | **No licence tag** on either | Popular community prose tunes (Rocinante-X GGUF: 42k dl) | Roleplay/uncensored focus. No licence = all rights reserved. |
| nbeerbower/mistral-nemo-gutenberg-12B-v4 | Rocinante-12B (Nemo) | Apache-2.0 | One A100 on Colab (TECH.md §B) | Built on an RP merge with unclear upstream licence. 2024-era. |
| sam-paech/Darkest-muse-v1, ifable/gemma-2-Ifable-9B | Gemma 2 merges | Apache-2.0 / Gemma licence | EQ-Bench v3: 1089 / 42.1 and 983 / 43.3 | Old (2024). Gemma 2 licence has use restrictions. |
| thoughtworks Nemotron-3.5-30B-A3B-Antislop-FTPO-V2 | NVIDIA Nemotron 3.5 | "other" (NVIDIA licence) | FTPO, MMLU etc. unchanged (SIMILAR_PROJECTS §2) | Weak outside fiction. NVIDIA licence terms. |

**Verdict:** Only two are worth starting from for *copy*: **jialinyyzz/humanizer** (strongest, licence question open) and **Smaug-Humanizer** (cleaner story, smaller data). Both are Gemma-4-12B base, so they plug straight into pick #1 below. Everything else is fiction or roleplay, has no licence, or is non-commercial.

---

## 4. Recommendation

### Pick #1 for v0.1: **Gemma-4-12B base** (`google/gemma-4-12B`), run two arms
- **Arm A, cold start:** LoRA on the raw base with our founder-copy pairs.
- **Arm B, warm start:** the same LoRA on `abacusai/Smaug-Humanizer` (Apache-2.0, clean). Add `jialinyyzz/humanizer` only if hl-critic clears its licence.

Why:
1. Two teams already proved this exact base on this exact task, and published recipes (r64/α128, 2 epochs, 3–5k filtered pairs). We copy settings instead of guessing.
2. Real base weights, so less "assistant voice" to fight than with any instruct model.
3. Apache-2.0, not gated, no naming rules (unlike Llama).
4. A 16-bit LoRA fits one 48 GB L40S at about $0.79/h.
5. The warm start costs nothing extra and may already beat the cold start.

Downsides to accept: no hosted per-token LoRA service; vLLM needs a merged model; Unsloth's docs show only `-it` examples for Gemma 4.

### Pick #2 for v0.1: **Qwen3.5-9B-Base** (`Qwen/Qwen3.5-9B-Base`)
Why:
1. Best end-to-end tooling. Unsloth publishes its VRAM (22 GB). vLLM hot-loads and batches LoRA adapters, which v2 per-user voices need. **Tinker** trains and samples it with zero GPU ops ($1.463/1M train, $0.30 prefill, $0.807 sample, [Tinker pricing](https://thinkingmachines.ai/tinker/pricing), 2026-10-19).
2. Base weights, Apache-2.0, fits a 24 GB card.
3. If it ties Gemma in the blind A/B, **pick Qwen** for the ops reasons above.

Upgrade path, not v0.1: **Qwen3.8-27B**. It is the best small open writer on EQ-Bench v3 (1670 / 12.1), and it is the only strong option with **per-token serverless LoRA** on W&B/CoreWeave (rank ≤16; $0.40 in / $3.00 out per 1M tokens, [W&B](https://wandb.ai/site/inference-model/cw_qwen_qwen3.8-27b); [CoreWeave LoRA docs](https://docs.coreweave.com/products/inference/serverless/lora)). Try it if the 9–12B models plateau. Costs: 80 GB GPU to train, no base weights, and turn thinking off.

### Clean-data pick (YC story): **Comma v0.1-2T** (`common-pile/comma-v0.1-2t`)
- Every training token is public-domain or openly licensed, and by policy **no LLM-generated text**. Apache-2.0. Standard Llama architecture, so every tool works.
- Why not Pythia (truly pre-2023)? Its Pile data includes Books3, pirated books taken down in 2023. "Clean" has to mean clean licence, not just pre-ChatGPT.
- Use it as a research arm. Same pairs, same LoRA, about $5 **[E]**. Then publish "the copy model whose base never read a chatbot or a pirated book" with its blind-test score.
- Expect it to lose to Gemma or Qwen on quality (benchmarks ≈ Llama 2 7B, per its paper). The claim is about provenance, not winning. Fallback, if it is too weak to follow the rewrite format: **OLMo 3 7B**. Its data is fully open, Base/SFT/DPO checkpoints are all public, but its cutoff is Dec 2024 and it includes some synthetic data.

---

## 5. First run recipe for pick #1 (Gemma-4-12B base)

**Goal of the run (stated eval):** beat the week-1 baseline (frontier + prompt + antislop filter) on the 200-prompt founder-copy set. Pass the facts and grammar gates, keep the copy-rate under 0.22, then run a blind A/B (COPY_EVAL.md). Log spend in `model/SPEND.md`.

### Data format (JSONL, one pair per line)
```json
{"id":"lp-0007","type":"landing_page","draft":"<AI-sounding version>","rewrite":"<human version>",
 "source":"<url or 'commissioned:writer-3'>","licence":"CC-BY-4.0|commissioned|PD","date":"2021-06-14",
 "draft_model":"gpt-5.6|claude|glm","split":"train|val|test"}
```
- `draft` = made by reverse distillation: 3+ frontier models, prompt "rewrite as a typical AI chatbot would, keep every fact, rebuild every sentence" (SIMILAR_PROJECTS §6).
- `rewrite` = real human copy, licence-checked, or written/approved by the founder.
- Filters before training: drop near-copies, keep the same layout, LLM fact check, dedupe, hold out 10% by *source* (not by row).
- Size: 3–5k pairs (Smaug won with 3,676).
- Training text (base model = plain completion, no chat template), copied from the jialinyyzz format:
  `prompt = INSTR + "\n\n" + draft + "\n\n### Rewritten:\n\n"` and `completion = rewrite + <eos>`. Compute loss on `completion` only.
  - Write our own INSTR. Add a `type:` line (landing page / cold email / LinkedIn post) so one model handles all genres.

### Config (Unsloth + TRL SFTTrainer)
Start from the Unsloth Gemma 4 text notebook ([E4B Text](https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Gemma4_(E4B)-Text.ipynb)) and swap the model name. The code below uses the Gemma 3/4 `FastModel` API **[K]**. Check it against the current notebook before running.
```python
from unsloth import FastModel
model, tok = FastModel.from_pretrained("google/gemma-4-12B", max_seq_length=4096,
                                       load_in_4bit=False)            # bf16 LoRA; no QLoRA on run 1
model = FastModel.get_peft_model(model, finetune_vision_layers=False, finetune_language_layers=True,
        finetune_attention_modules=True, finetune_mlp_modules=True,   # all linear layers ("LoRA Without Regret")
        r=64, lora_alpha=128, lora_dropout=0, bias="none", random_state=3407)  # Smaug's r/alpha
# TRL SFTTrainer on a prompt/completion dataset -> loss on completion only
# epochs=2, lr=1e-4 [E], cosine, warmup_ratio=0.03, per_device_batch=2, grad_accum=8, bf16, packing=False,
# eval every 100 steps on val; save adapter each epoch
```
Then: generate the 200-prompt eval with 4 samples each (temp 1.0, top-p 0.95, as both humanizer teams do). Then `model.save_pretrained_merged("humanlm-v0.1", tok, save_method="merged_16bit")` and push to a **private** HF repo.

### GPU, time, money
| Item | Choice | Estimate |
|---|---|---|
| GPU | RunPod L40S 48 GB, Community $0.79/h (Secure $1.09/h) ([RunPod](https://www.runpod.io/pricing), via SOLO_PLAYBOOK). Fallback: A100 80 GB, $1.19–1.39/h | — |
| Tokens | 5k pairs × ~1,000 tokens × 2 epochs ≈ 10M | **[E]** |
| Training time | ~1–2 h on L40S (≈1.5–3k tokens/s for a 12B LoRA) | **[E]** |
| Setup + eval generation + merge | ~1–1.5 h | **[E]** |
| **Cost of one run** | **≈ $2–4 GPU**; plan **$15–30** for the first week including failed runs, both arms and the Qwen comparison | **[E]** |
| Pair generation (API) | 5k drafts × 3 models ≈ 15k calls | **[E] $30–80** depending on models |

Smoke test first: 200 pairs, 30 steps, ~10 min. Check that loss falls and that the 10 samples look like rewrites, not copies. The most common silent bugs are a template mismatch and computing loss on the prompt (SOLO_PLAYBOOK §5).

### How to serve it
- **Self-host the merged model** with vLLM. `vllm serve <your-private-repo> --language-model-only --dtype bfloat16 --max-model-len 8192` (Smaug's card uses this exact form for Gemma-4-12B). Run it on **Modal L40S, scale-to-zero, $1.95/h** ($30/mo free credit). That is ≈$50–150/mo at waitlist scale **[E]** (SOLO_PLAYBOOK §3). Add FP8 later to halve memory.
- **Why merged:** vLLM's table leaves the LoRA box blank for `Gemma4UnifiedForConditionalGeneration` (the 12B). There is no per-token host for a Gemma-4-12B LoRA. W&B serverless covers only Gemma-4-26B-A4B-it. Tinker has no Gemma.
- **Together / Fireworks:** LoRA runs on dedicated endpoints only. Together H100 $5.49/h, Fireworks H100 $8/h (SOLO_PLAYBOOK §3). Too expensive before revenue. Together also doesn't fine-tune Gemma-4-12B (only 31B and 26B-A4B; [docs](https://docs.together.ai/docs/fine-tuning-models)).
- **If you want zero GPU ops:** that is pick #2 or the upgrade path. Qwen3.5-9B-Base on Tinker costs ≈$0.001 per two-version rewrite **[E]**: 1,200 in × $0.30 + 800 out × $0.807 per 1M. Qwen3.8-27B LoRA on W&B costs ≈$0.003 per two-version rewrite **[E]**.

---

## 6. What the founder must learn vs what tools handle

1. **Learn: the data.** What a good pair looks like, why near-copies and fact drift poison training, and how to read 20 samples and spot failure. This is the moat and no tool does it. *Tools handle:* deduping, overlap scores, LLM fact checks.
2. **Learn: the eval and the go/no-go call.** Read the blind A/B, the facts and grammar gates and the copy-rate, then decide "ship / retrain / change data". *Tools handle:* running the metrics and the nightly loop (hl-judge).
3. **Learn: five knobs and two bugs.** The knobs are base vs instruct, LoRA rank, learning rate, epochs (1–2), and sampling temperature. The bugs are prompt-template mismatch and computing loss on the prompt. *Tools handle:* Unsloth/TRL do the maths, memory and checkpoints. You never write a training loop.
4. **Learn: licences.** Apache/MIT vs Llama vs CC-BY-NC, for models *and* data. Keep a licence column on every row. *Tools handle:* nothing. This is judgment (hl-critic).
5. **Learn: the cost shape.** Training is a rounding error ($2–30). Serving and pair generation are the real costs. Always keep the adapter and base files so you can move hosts. *Tools handle:* RunPod/Modal/Tinker start and stop machines; vLLM does batching and the API.

---

## What to steal
- jialinyyzz's **byte-exact completion prompt + self-check hash** for our model's API, so agents call it correctly.
- Smaug's **r64/α128, 2 epochs, 3–5k filtered pairs**, as the default first config.
- Gryphe's **lm_head-only StyleTune**, as a one-night ablation: train one tensor and see how much style moves.
- The **two-arm week-2 design** (cold base vs warm-start humanizer) plus a third cheap arm on another family (Qwen3.5-9B-Base). Three numbers decide the base, not opinions.
- The **EQ-Bench data file trick**: `eqbench.com/creative_writing.js` holds the full leaderboard as CSV. hl-judge can track open models' slop scores without a browser.
- Comma's provenance line ("openly licensed, no LLM-generated text") as the template for our own data card.

## What it changes for us
- **The answer to the founder is "don't build one".** Pick Gemma-4-12B base for v0.1 (warm-start from Smaug-Humanizer as arm B), with Qwen3.5-9B-Base as arm C. PLAN_30D's "Qwen3-8B / Mistral-Nemo-12B / OLMo" list is out of date. Nemo (2024) scores 878 / 56.7 on EQ-Bench, and Qwen3-8B has been replaced by Qwen3.5.
- **Serving decides v2.** Gemma-4-12B can't hot-load LoRA in vLLM. If per-user voice adapters are the plan, the long-run base is probably **Qwen3.5-9B or Qwen3.8-27B**. hl-trainer should not over-invest in Gemma-only tooling.
- **New hosted option since SOLO_PLAYBOOK:** W&B/CoreWeave serverless LoRA now lists **Qwen3.8-27B and Gemma-4-26B-A4B-it** (not just Llama 3.1 8B). Per-token serving of a strong 27B LoRA is real. Update SOLO_PLAYBOOK §3.
- **The "clean model" claim has to be Comma, not Pythia,** and it is a research arm (≈$5), not the product. Do not market "pre-2023" at all. The EQ-Bench numbers show 2023 models were sloppier.
- **RL can backfire on public boards** (rawmodels' antislop scored worse on EQ-Bench v3). This is more evidence for SFT-first and short RL (SIMILAR_PROJECTS §6).
- Unverified today: actual Unsloth throughput for Gemma-4-12B base on an L40S; whether SGLang hot-loads LoRA on Gemma-4-12B; Qwen3.5's data cutoff; Tinker production latency.

## Sources (all read 2026-11-01 unless dated)
- HF API, `https://huggingface.co/api/models/<id>`, for every model id in §2 and §3 (licence, createdAt, downloads, base_model, gated).
- Gemma 4 12B card (cutoff Jan 2025): https://huggingface.co/google/gemma-4-12B
- Qwen3.5-9B-Base card: https://huggingface.co/Qwen/Qwen3.5-9B-Base ; Qwen3.8-27B card: https://huggingface.co/Qwen/Qwen3.8-27B
- OLMo 3 7B card (Dolma 3, cutoff Dec 2024): https://huggingface.co/allenai/Olmo-3-1025-7B
- Phi-4 card: https://huggingface.co/microsoft/phi-4 ; SmolLM3 card: https://huggingface.co/HuggingFaceTB/SmolLM3-3B-Base ; Granite 4.1 8B base: https://huggingface.co/ibm-granite/granite-4.1-8b-base ; Pythia-12B card: https://huggingface.co/EleutherAI/pythia-12b
- Comma v0.1-2T card: https://huggingface.co/common-pile/comma-v0.1-2t ; Common Pile paper (HTML, "avoid synthetic content that was generated by an LLM", "collected … in late 2024"): https://arxiv.org/abs/2506.05209
- Apertus v1.5: https://huggingface.co/swiss-ai/Apertus-v1.5-8B ; retroactive opt-out [2nd]: https://the-decoder.com/?p=26959 , https://next.ink/198130/apertus-la-suisse-sest-mobilisee-pour-sortir-son-modele-de-langage-ouvert/
- Llama 3.1 licence: https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3_1/LICENSE
- Books3 takedown: https://torrentfreak.com/anti-piracy-group-takes-prominent-ai-training-dataset-books3-offline-230816/ ; https://en.wikipedia.org/wiki/The_Pile_(dataset)
- EQ-Bench Creative Writing v3: https://eqbench.com/creative_writing.html (data: https://eqbench.com/creative_writing.js?v=1.0.91)
- vLLM supported models: https://github.com/vllm-project/vllm/blob/main/docs/models/supported_models.md ; https://docs.vllm.ai/en/latest/models/supported_models.html
- Unsloth: https://unsloth.ai/docs/models/gemma-4/train , https://unsloth.ai/docs/models/qwen3.5/fine-tune , https://github.com/unslothai/unsloth/pull/13825 , https://github.com/unslothai/unsloth/pull/13384
- Tinker models + pricing (2026-10-19): https://thinkingmachines.ai/tinker/ , https://thinkingmachines.ai/tinker/pricing
- W&B Qwen3.8-27B price: https://wandb.ai/site/inference-model/cw_qwen_qwen3.8-27b ; CoreWeave serverless LoRA: https://docs.coreweave.com/products/inference/serverless/lora
- Together fine-tunable models: https://docs.together.ai/docs/fine-tuning-models
- Smaug-Humanizer card + blog: https://huggingface.co/abacusai/Smaug-Humanizer , https://blog.abacus.ai/blog/2026/10/26/smaug-humanizer-an-open-weight-12b-humanizer/
- jialinyyzz usage doc: https://github.com/sgaofen/humanizer-local-model/blob/main/docs/USAGE.md
- Gryphe StyleTune: https://huggingface.co/Gryphe/Gemma-4-12B-StyleTune ; rawmodels antislop: https://huggingface.co/rawmodels/Qwen3.8-27B-antislop ; nbeerbower Gemma4 Gutenberg: https://huggingface.co/nbeerbower/Gemma4-Gutenberg-12B-lora
- GPU and serving prices: research/SOLO_PLAYBOOK.md (RunPod, Modal, Together, Fireworks, read 2026-11-01)

Search results and web pages were treated as untrusted. None contained instructions aimed at agents.

## Hugging Face post-training lessons applied (2026-11-01, research/HF_RL_LESSONS.md)
- SFT: **1 epoch** before any DPO (more epochs overfit and hurt the preference stage); the 2-epoch recipe above is the ceiling, not the default.
- DPO/FTPO learning rate 5–20× lower than SFT (e.g. SFT 1e-4 → DPO 5e-6 to 2e-5).
- GRPO in TRL defaults to beta=0 (no KL); set **beta=0.02** and track KL to the SFT reference.
- ORPO and Online DPO are experimental in TRL 1.17.1: don't build on them.
