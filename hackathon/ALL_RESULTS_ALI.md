# FeatherLM: all results in one place (Ali's side, generated 2026-11-02 ~15:00 PT)

Source of truth for the submission remains `hackathon/report/RESULTS.md` (Ruslan's score_all). This file lists every run manifest and judge summary so nothing is missed.

## Every system run (gate pass rate = fact-safe human rewrite rate on that split)

| Run (manifest) | Rows | Pass rate | Model |
|---|---|---|---|
| `E1_ensemble` | 130 | 99.2% | `glm-5p3` |
| `E1_ensemble_heldout` | 120 | 99.2% | `glm-5p3` |
| `E1_ensemble_real` | 80 | 98.8% | `glm-5p3` |
| `E2_ensemble_glm_deepseek` | 130 | 100.0% | `glm-5p3` |
| `E2_ensemble_glm_deepseek_heldout` | 120 | 99.2% | `glm-5p3` |
| `E2_ensemble_glm_deepseek_real` | 80 | 98.8% | `glm-5p3` |
| `F1H_opus_harness` | 130 | 92.3% | `claude-opus-5-5` |
| `F1H_opus_harness_real` | 80 | 97.5% | `claude-opus-5-5` |
| `F1h_opus_humanizer` | 130 | 53.8% | `claude-opus-5-5` |
| `F2_gpt61_terra` | 130 | 13.8% | `gpt-6.1-terra` |
| `F2_gpt61_terra_heldout` | 120 | 61.7% | `gpt-6.1-terra` |
| `F2h_gpt61_humanizer` | 130 | 36.2% | `gpt-6.1-terra` |
| `F2h_gpt61_humanizer_heldout` | 120 | 67.5% | `gpt-6.1-terra` |
| `O1_glm_base` | 130 | 10.0% | `glm-5p3-flash` |
| `O1_glm_base_heldout` | 120 | 38.3% | `glm-5p3-flash` |
| `O2_glm_prompt` | 130 | 49.2% | `glm-5p3-flash` |
| `O2_glm_prompt_heldout` | 120 | 76.7% | `glm-5p3-flash` |
| `O2h_glm_humanizer` | 130 | 41.5% | `glm-5p3-flash` |
| `O2h_glm_humanizer_heldout` | 120 | 65.0% | `glm-5p3-flash` |
| `O3_glm_harness` | 130 | 89.2% | `glm-5p3-flash` |
| `O3_glm_harness_heldout` | 120 | 95.8% | `glm-5p3-flash` |
| `O3_glm_harness_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O3b_glm_prompt_harness` | 130 | 89.2% | `glm-5p3-flash` |
| `O3b_glm_prompt_harness_heldout` | 120 | 98.3% | `glm-5p3-flash` |
| `O3b_glm_prompt_harness_real` | 80 | 97.5% | `glm-5p3-flash` |
| `O3c_glm_prompt_harness_style` | 130 | 95.4% | `glm-5p3-flash` |
| `O3c_glm_prompt_harness_style_heldout` | 120 | 98.3% | `glm-5p3-flash` |
| `O3c_glm_prompt_harness_style_real` | 80 | 97.5% | `glm-5p3-flash` |
| `O3d_glm_harness_anticopy` | 130 | 93.8% | `glm-5p3-flash` |
| `O3d_glm_harness_anticopy_heldout` | 120 | 96.7% | `glm-5p3-flash` |
| `O3e_glm_harness_cliche` | 130 | 96.2% | `glm-5p3-flash` |
| `O3e_glm_harness_cliche_heldout` | 120 | 96.7% | `glm-5p3-flash` |
| `O3f_glm_calm` | 130 | 96.2% | `glm-5p3-flash` |
| `O3f_glm_calm_heldout` | 120 | 95.0% | `glm-5p3-flash` |
| `O3f_glm_calm_real` | 80 | 97.5% | `glm-5p3-flash` |
| `O3g_glm_calm_retrieval_claimcheck` | 130 | 93.1% | `glm-5p3-flash` |
| `O3g_glm_calm_retrieval_claimcheck_heldout` | 120 | 91.7% | `glm-5p3-flash` |
| `O3j_glm_bestof3_judged` | 130 | 98.5% | `glm-5p3-flash` |
| `O3j_glm_bestof3_judged_heldout` | 120 | 97.5% | `glm-5p3-flash` |
| `O3j_glm_bestof3_judged_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O3k_glm_calm_claimcheck_bo3` | 130 | 99.2% | `glm-5p3-flash` |
| `O3k_glm_calm_claimcheck_bo3_heldout` | 120 | 99.2% | `glm-5p3-flash` |
| `O3k_glm_calm_claimcheck_bo3_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O3l_glm_style_claimcheck_bo3` | 130 | 98.5% | `glm-5p3-flash` |
| `O3l_glm_style_claimcheck_bo3_heldout` | 120 | 98.3% | `glm-5p3-flash` |
| `O3l_glm_style_claimcheck_bo3_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O3m_glm_plainclaim` | 130 | 96.2% | `glm-5p3-flash` |
| `O3m_glm_plainclaim_heldout` | 120 | 98.3% | `glm-5p3-flash` |
| `O3m_glm_plainclaim_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O3n_glm_frame` | 130 | 93.8% | `glm-5p3-flash` |
| `O3n_glm_frame_heldout` | 120 | 96.7% | `glm-5p3-flash` |
| `O3n_glm_frame_real` | 80 | 97.5% | `glm-5p3-flash` |
| `O3t_glm_ali_taste` | 130 | 96.2% | `glm-5p3-flash` |
| `O3t_glm_ali_taste_heldout` | 120 | 98.3% | `glm-5p3-flash` |
| `O3t_glm_ali_taste_real` | 80 | 98.8% | `glm-5p3-flash` |
| `O4m_glm_sft_modern` | 130 | 17.7% | `humanlm-o4m` |
| `O4m_glm_sft_modern_heldout` | 120 | 49.2% | `humanlm-o4m` |
| `R3_deepseek_harness` | 130 | 96.2% | `deepseek-v4p1-flash` |
| `R3_deepseek_harness_heldout` | 120 | 93.3% | `deepseek-v4p1-flash` |
| `R3_deepseek_harness_real` | 80 | 95.0% | `deepseek-v4p1-flash` |
| `R3t_deepseek_ali_taste` | 130 | 95.4% | `deepseek-v4p1-flash` |
| `R3t_deepseek_ali_taste_heldout` | 120 | 93.3% | `deepseek-v4p1-flash` |
| `R3t_deepseek_ali_taste_real` | 80 | 97.5% | `deepseek-v4p1-flash` |
| `WF_Pairwise_both_orders_knockout_selector_with_fact_aware_eligibility_replace_the_1_10_judge_score_` | 30 | 96.7% | `glm-5p3-flash` |
| `pref_cand1` | 120 | 97.5% | `glm-5p3-flash` |
| `pref_cand2` | 120 | 99.2% | `glm-5p3-flash` |

## Judges vs Claude Opus 5.5 (strong prompt): wins / losses / ties for OUR system

| Pair | Judge | Overall | Style | Facts |
|---|---|---|---|---|
| `E1_ensemble_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (26, 43, 61) | (10, 14, 106) |
| `E1_ensemble_vs_hack_strong_claude-opus-5-5_qwen` | qwen3p8-max |  | (42, 37, 30) | (10, 11, 88) |
| `O3_glm_harness_heldout_vs_hack_strong_claude-opus-5-5_heldout_heldout` | kimi-k3 |  | (28, 30, 60) | (13, 12, 93) |
| `O3_glm_harness_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (25, 56, 49) | (13, 8, 109) |
| `O3b_glm_prompt_harness_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (26, 60, 44) | (15, 5, 110) |
| `O3c_glm_prompt_harness_style_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (33, 46, 51) | (9, 15, 106) |
| `O3d_glm_harness_anticopy_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (35, 44, 51) | (5, 22, 103) |
| `O3e_glm_harness_cliche_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (20, 54, 56) | (6, 15, 109) |
| `O3f_glm_calm_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (16, 62, 52) | (7, 7, 116) |
| `O3g_glm_calm_retrieval_claimcheck_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (18, 64, 48) | (11, 8, 111) |
| `O3j_glm_bestof3_judged_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (44, 37, 49) | (4, 25, 101) |
| `O3k_glm_calm_claimcheck_bo3_first30_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (4, 11, 15) | (2, 2, 26) |
| `O3k_glm_calm_claimcheck_bo3_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (11, 68, 51) | (9, 6, 115) |
| `O3l_glm_style_claimcheck_bo3_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (30, 51, 48) | (10, 10, 109) |
| `O3m_glm_plainclaim_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (15, 54, 61) | (5, 23, 102) |
| `O3t_glm_ali_taste_vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (29, 54, 47) | (10, 16, 104) |
| `O3t_glm_ali_taste_vs_hack_strong_claude-opus-5-5_qwen` | qwen3p8-max |  | (37, 28, 40) | (14, 19, 72) |
| `WF_Pairwise_both_orders_knockout_selector_with_fact_aware_eligibility_replace_the_1_10_judge_score__vs_hack_strong_claude-opus-5-5` | kimi-k3 |  | (4, 18, 8) | (2, 2, 26) |

## Human A/B

See `hackathon/report/human_votes.json` (latest at writing: 164 votes O3c vs Claude strong, 53 ours / 80 Claude / 31 same, sign test p=0.024: humans prefer Claude's prose).

## Reading

- Facts: every harness row beats Claude strong on the fact-safe benchmark (Claude 71% on 247 items, 76% on 80 untouched real READMEs; ours 93-99%).
- Harness transfers: DeepSeek V4.1 Flash + the same harness (R3) reaches 93-96%.
- Style: Qwen 3.8 Max prefers ours, Kimi K3 prefers Claude, humans prefer Claude (significant). Prompt-level style fixes did not close the gap; weight-level training (Fireworks SFT A/B/C, local L1/L2) is trained but serving limits are documented in `hackathon/train/TRAIN_LOG.md`.
- Cost: harness rows $0.3-3 per 1k rewrites vs Claude strong ~$9 and Claude+harness ~$16.
