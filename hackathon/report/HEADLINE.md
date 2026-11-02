Fact-safe human rewrite rate on 250 items (eval 130 + held-out 120), 95% CI; Δ vs `frontier-strong:claude-opus-5-5` by paired bootstrap. Generated from `hackathon/report/results.json`.

| System | Fact-safe rate (strict) | Δ strict | Fact-safe rate (lenient) | Δ lenient | $ / 1k rewrites | p50 latency |
|---|---|---|---|---|---|---|
| `O3k_glm_calm_claimcheck_bo3` | 99% [97, 100] | +28 pp [+22, +33], significant (p=0.000) | 100% [99, 100] | +15 pp [+11, +20], significant (p=0.000) | $3.15 | 16.7s |
| `O3j_glm_bestof3_judged` | 98% [95, 99] | +26 pp [+21, +32], significant (p=0.000) | 99% [97, 100] | +14 pp [+10, +19], significant (p=0.000) | $2.61 | 12.5s |
| `O3c_glm_prompt_harness_style` | 97% [94, 99] | +25 pp [+20, +31], significant (p=0.000) | 98% [95, 99] | +13 pp [+9, +18], significant (p=0.000) | $0.81 | 3.4s |
| `O3e_glm_harness_cliche` | 96% [93, 98] | +25 pp [+19, +30], significant (p=0.000) | 99% [97, 100] | +14 pp [+10, +19], significant (p=0.000) | $0.81 | 3.0s |
| `O3f_glm_calm` | 96% [92, 98] | +24 pp [+19, +30], significant (p=0.000) | 98% [96, 100] | +14 pp [+9, +18], significant (p=0.000) | $0.93 | 3.5s |
| `O3d_glm_harness_anticopy` | 95% [92, 97] | +24 pp [+18, +30], significant (p=0.000) | 98% [95, 99] | +13 pp [+8, +18], significant (p=0.000) | $0.85 | 2.9s |
| `O3b_glm_prompt_harness` | 94% [91, 97] | +23 pp [+18, +28], significant (p=0.000) | 97% [94, 99] | +12 pp [+7, +17], significant (p=0.000) | $0.54 | 1.7s |
| `F1H_opus_harness` | 94% [90, 96] | +22 pp [+17, +28], significant (p=0.000) | 97% [94, 99] | +12 pp [+8, +17], significant (p=0.000) | $15.83 | 4.8s |
| `O3_glm_harness` | 93% [89, 96] | +21 pp [+16, +27], significant (p=0.000) | 97% [94, 99] | +12 pp [+7, +17], significant (p=0.000) | $0.28 | 2.7s |
| `O3g_glm_calm_retrieval_claimcheck` | 92% [88, 95] | +21 pp [+15, +26], significant (p=0.000) | 97% [94, 99] | +12 pp [+8, +17], significant (p=0.000) | $1.43 | 5.9s |
| `O2_glm_prompt` | 73% [67, 79] | +2 pp [-5, +8], n.s. (p=0.620) | 80% [74, 84] | -5 pp [-10, +0], n.s. (p=0.056) | $0.31 | 1.2s |
| `frontier-strong:claude-opus-5-5` | 72% [66, 77] | reference | 85% [80, 89] | reference | $9.15 | 3.8s |
| `F1h_opus_humanizer` | 60% [54, 66] | -12 pp [-17, -6], significant (p=0.000) | 77% [71, 82] | -8 pp [-12, -3], significant (p=0.002) | $50.26 | 3.7s |
| `frontier-live:claude-opus-5-5` | 53% [47, 60] | -18 pp [-24, -13], significant (p=0.000) | 77% [71, 82] | -8 pp [-12, -3], significant (p=0.002) | $7.21 | 3.7s |
| `O2h_glm_humanizer` | 53% [46, 59] | -19 pp [-26, -12], significant (p=0.000) | 63% [56, 69] | -22 pp [-28, -16], significant (p=0.000) | $1.15 | 1.4s |
| `F2h_gpt61_humanizer` | 51% [45, 58] | -20 pp [-27, -14], significant (p=0.000) | 56% [50, 63] | -28 pp [-35, -22], significant (p=0.000) | $7.74 | 2.5s |
| `F2_gpt61_terra` | 40% [34, 46] | -32 pp [-39, -24], significant (p=0.000) | 44% [38, 51] | -40 pp [-47, -34], significant (p=0.000) | $0.86 | 2.6s |
| `X0_copy_draft (no rewrite: control)` | 32% [26, 38] | -40 pp [-47, -32], significant (p=0.000) | 32% [26, 38] | -53 pp [-60, -46], significant (p=0.000) | n/a | 0.0s |
| `O1_glm_base` | 27% [22, 33] | -44 pp [-52, -37], significant (p=0.000) | 30% [24, 36] | -55 pp [-62, -48], significant (p=0.000) | $0.10 | 1.2s |
| `frontier-persona-preexisting` (130 items) | 12% [7, 19] | -57 pp [-66, -48], significant (p=0.000) | 16% [10, 24] | -66 pp [-74, -58], significant (p=0.000) | n/a | n/a |

Human preference, O3c_glm_prompt_harness_style vs frontier-strong:claude-opus-5-5 (blind A/B; FeatherLM / Claude / tie):

- page: 0 / 4 / 1 (1 voter(s), 5 votes, sign test p=0.125); Ali (founder; knows the project, so treat as a check, not a gold rater)
- Not counted: Ali reports 5 Minerva classmates gave the same answer (preferred the Claude side) in an informal, unlogged session; not counted as data.

Pairwise judge (both orders; A wins / B wins / ties, two-sided sign test):

- `hack_O3c_glm_prompt_harness_style.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (qwen3p8-max): overall 39/43/25 (p=0.741), style 44/27/37 (p=0.057)
- `hack_O3f_glm_calm.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (qwen3p8-max): overall 19/53/31 (p=0.000), style 9/53/41 (p=0.000)
- `hack_O3k_glm_calm_claimcheck_bo3.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (qwen3p8-max): overall 22/56/36 (p=0.000), style 15/55/42 (p=0.000)
- `hack_O3_glm_harness_heldout.jsonl` vs `hack_F1H_opus_heldout.jsonl` (kimi-k3): overall 52/31/37 (p=0.028), style 41/17/62 (p=0.002)
- `hack_O3_glm_harness_heldout.jsonl` vs `hack_strong_claude-opus-5-5_heldout.jsonl` (kimi-k3): overall 42/35/41 (p=0.494), style 28/30/60 (p=0.896)
- `hack_O3_glm_harness.jsonl` vs `hack_F1H_opus.jsonl` (kimi-k3): overall 40/47/43 (p=0.520), style 32/46/52 (p=0.141)
- `hack_O3_glm_harness.jsonl` vs `hack_F2_gpt61_terra.jsonl` (kimi-k3): overall 35/46/49 (p=0.266), style 32/38/60 (p=0.550)
- `hack_O3_glm_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 34/57/39 (p=0.021), style 25/56/49 (p=0.001)
- `hack_O3b_glm_prompt_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 35/60/35 (p=0.013), style 26/60/44 (p=0.000)
- `hack_O3c_glm_prompt_harness_style.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 35/52/43 (p=0.086), style 33/46/51 (p=0.177)
- `hack_O3d_glm_harness_anticopy.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 34/56/40 (p=0.026), style 35/44/51 (p=0.368)
- `hack_O3e_glm_harness_cliche.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 25/65/40 (p=0.000), style 20/54/56 (p=0.000)
- `hack_O3f_glm_calm.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 23/69/38 (p=0.000), style 16/62/52 (p=0.000)
- `hack_O3g_glm_calm_retrieval_claimcheck.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 25/68/37 (p=0.000), style 18/64/48 (p=0.000)
- `hack_O3j_glm_bestof3_judged.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 41/55/34 (p=0.184), style 44/37/49 (p=0.505)
- `hack_O3k_glm_calm_claimcheck_bo3.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 19/72/39 (p=0.000), style 11/68/51 (p=0.000)
