# Final number check (pitch, deck, overview, Q&A)

Checked 2026-11-02 14:50 PT after `git pull` (results.json as committed then). Rule: every number said or shown comes from a committed file; this table names the file and key. `RJ` = `hackathon/report/results.json`. Rates are `blocks.<split>.systems[label].summary.pass` (rate, lo, hi); deltas are `vs_reference.pass` (diff, lo, hi, p); cost and p50 are `systems[label].cost_per_1k_usd` and `latency_ms.p50`.

Main row: `O3c_glm_prompt_harness_style` (FeatherLM). RESULTS.md marks no other main row.

## Fact-safe rate and cost

| Number | Value | Source |
|---|---|---|
| Items, all | 247 (130 main + 117 held-out) | RJ `blocks.all.n_items`; RESULTS.md headers |
| O3c, all | 96.8% [93.7, 98.6] (239/247) | RJ `blocks.all` O3c |
| Claude strong, all | 71.3% [65.2, 76.8] (176/247) | RJ `blocks.all` `frontier-strong:claude-opus-5-5` |
| O3c vs Claude strong, all | +26 pp [+20, +31], p<0.001 | RJ `blocks.all` O3c `vs_reference.pass` (0.255) |
| E1 ensemble, all | 99.2% [97.1, 99.9] (245/247) | RJ `blocks.all` E1_ensemble |
| R3 DeepSeek + harness, all | 94.7% [91.2, 97.2] | RJ `blocks.all` R3_deepseek_harness |
| F1H Claude + our harness, all | 93.5% [89.7, 96.3] | RJ `blocks.all` F1H_opus_harness |
| Claude same prompt, all | 52.6% [46.2, 59.0] | RJ `blocks.all` frontier-live |
| GPT-6.1 Terra, all | 39.7% [33.5, 46.1] | RJ `blocks.all` F2_gpt61_terra |
| SFT B (O4m), no harness | 32.8% [27.0, 39.0] | RJ `blocks.all` O4m_glm_sft_modern |
| Copy-the-draft control | 31.6% [25.8, 37.8] | RJ `blocks.all` X0 |
| GLM base (O1) | 26.7% [21.3, 32.7] | RJ `blocks.all` O1_glm_base |
| Claude strong G1 / G2, all | 88% / 88% | RESULTS.md all-items table |
| Real READMEs (80): O3c / Claude strong | 97.5% / 76.2%, Δ +21 pp [+13, +31] | RJ `blocks.real` |
| Held-out clean (96): O3c / Claude strong | 99.0% / 71.9% | RJ `blocks.heldout_clean` |
| $ per 1k: O3c / Claude strong / F1H / E1 / F2 / O1 | 0.81 / 9.11 / 15.85 / 15.12 / 0.85 / 0.10 | RJ `systems[].cost_per_1k_usd` |
| p50: O3c / Claude strong / F1H / E1 / R3 | 3.4 / 3.7 / 4.8 / 9.9 / 3.4 s | RJ `systems[].latency_ms.p50` |
| R3 cost | none in RJ (n/a): never quote | RJ `systems` R3 |
| "~11x cheaper" than Claude strong | 9.1107 / 0.8061 = 11.3 | RJ cost fields |
| **Closing "~20x"** (accountability) | F1H 15.8502 / O3c 0.8061 = 19.7, rounded 20 | RJ cost fields; deck computes it live (`ratio`) |

## Style (where we do not win)

| Number | Value | Source |
|---|---|---|
| Human A/B votes (frozen 15:15 PT) | 209 votes, 45 readers | `hackathon/report/human_votes.json` `pooled` / `sources.page` |
| Ours / Claude / both fine | 64 / 89 / 56; win rate 0.42 [0.34, 0.50] | same |
| Sign test | p=0.052 (0.0520), not significant at 0.05 | same, `sign_test_p` |
| Without fast/position clickers | 48 / 73 (34 readers), p=0.029 | same, `sensitivity_no_position_clickers` |
| Kimi K3, O3c vs Claude, overall | 35/52/43, p=0.086 | `judge_hack_O3c_..._vs_hack_strong_claude-opus-5-5.summary.json`; RESULTS.md pairwise table |
| Kimi K3 style | 33/46/51, p=0.177 | same |
| Qwen 3.8 Max overall | 39/43/25, p=0.741 (107 complete) | `judge2qwen_hack_O3c_...summary.json`; RESULTS.md |
| Qwen 3.8 Max style | 44/27/37, p=0.057 | same |
| E1 vs Claude: Kimi / Qwen overall | 30/51/49 (p=0.026, sign test computed) / 39/39/34 | `judge_hack_E1_ensemble_...summary.json`, `..._qwen.summary.json` |
| O3t (Ali-taste prompt): Kimi / Qwen overall | 34/63/33 (p=0.004) / 35/40/30 | `judge_hack_O3t_...summary.json`, `..._qwen.summary.json` |
| Reader tells, main split: any tell O3c / Claude | 37.7% / 10.0% | `reader_tells.json` `blocks.eval` `any_share` |
| Fragment runs per 100 outputs O3c / Claude | 28.5 / 4.6 | same, `per_100_outputs.fragment_run` |
| Reader tells, held-out: O3c / Claude | 7.5% / 0.8% | `reader_tells.json` `blocks.heldout` |

Sign-test p values for E1 and O3t were computed from the win/loss counts in the summary files (two-sided, ties dropped), the same test RESULTS.md uses.

## Audit (its own 250-item run, primary row O3)

| Number | Value | Source |
|---|---|---|
| Lenient pass O3c / Claude strong | 98% [95, 99] / 85% [81, 89] | `hackathon/audit/AUDIT.md` section E |
| Official→lenient lead (O3 vs Claude) | 21 → 11 pp | AUDIT.md section D |
| Any draft sentence deleted: Claude strong / O3 / O3c | 51% / 17% / 42% | AUDIT.md section C; `audit.json any_sent_deleted` |
| Near-copies O3 / frontier / base | 10% / 1-2% / 7% | AUDIT.md section F (C1) |

## Training (TRAIN_LOG.md)

| Fact | Source |
|---|---|
| SFT A (O4, v1), B (O4m), C trained on Fireworks Serverless Training API, LoRA r16 on GLM-5.3 Flash, 5,000 rows | `hackathon/train/TRAIN_LOG.md` sections "SFT v1", "SFT model B", "SFT C" |
| Serving a LoRA needs an on-demand deployment (4x NVIDIA B300, about $60/h); serverless LoRA not enabled on the account | TRAIN_LOG "SFT model B" and "O4m evaluation deployment" |
| Only SFT B evaluated (brief approved deployment): 32.8% strict, base 26.7% | TRAIN_LOG; RJ |
| SFT C: trained, eval deployment created 14:36 PT; no row in RJ at check time | TRAIN_LOG "SFT C" |
| DPO toward human refs on Fireworks (O7): stopped at step 1 (sampler hang) | TRAIN_LOG "DPO toward human references" |
| Local L2 DPO (Qwen3-4B, MLX): 70 of 143 pairs, not evaluated in time | TRAIN_LOG "L2" |
| Nemotron: no row in RJ, so the NVIDIA track is not claimed | RJ `systems` (no Nemotron label) |

## Discrepancies found

- Earlier briefs said "164 votes, p=0.024" and "195 votes, p=0.020"; the frozen `human_votes.json` (15:15 PT) says 209 votes, p=0.052. The pitch uses the frozen file.
- The audit (AUDIT.md) is on its own 250-item run; score_all.py uses 247 items. The deck labels the audit slide as the audit's run; headline rates come only from RJ.
