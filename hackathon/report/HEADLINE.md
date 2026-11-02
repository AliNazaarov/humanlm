Fact-safe human rewrite rate on 250 items (eval 130 + held-out 120), 95% CI; Δ vs `frontier-strong:claude-opus-5-5` by paired bootstrap. Generated from `hackathon/report/results.json`.

| System | Fact-safe rate (strict) | Δ strict | Fact-safe rate (lenient) | Δ lenient | $ / 1k rewrites | p50 latency |
|---|---|---|---|---|---|---|
| `O3c_glm_prompt_harness_style` | 97% [94, 99] | +25 pp [+20, +31], significant (p=0.000) | 98% [95, 99] | +13 pp [+9, +18], significant (p=0.000) | $0.81 | 3.3s |
| `O3b_glm_prompt_harness` | 94% [91, 97] | +23 pp [+18, +28], significant (p=0.000) | 97% [94, 99] | +12 pp [+7, +17], significant (p=0.000) | $0.55 | 1.6s |
| `F1H_opus_harness` | 94% [90, 96] | +22 pp [+17, +28], significant (p=0.000) | 97% [94, 99] | +12 pp [+8, +17], significant (p=0.000) | $15.83 | 4.8s |
| `O3_glm_harness` | 93% [89, 96] | +21 pp [+16, +27], significant (p=0.000) | 97% [94, 99] | +12 pp [+7, +17], significant (p=0.000) | $0.28 | 2.6s |
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

Pairwise judge (both orders; A wins / B wins / ties, two-sided sign test):

- `hack_O3_glm_harness_heldout.jsonl` vs `hack_F1H_opus_heldout.jsonl` (kimi-k3): overall 52/31/37 (p=0.028), style 41/17/62 (p=0.002)
- `hack_O3_glm_harness_heldout.jsonl` vs `hack_strong_claude-opus-5-5_heldout.jsonl` (kimi-k3): overall 42/35/41 (p=0.494), style 28/30/60 (p=0.896)
- `hack_O3_glm_harness.jsonl` vs `hack_F1H_opus.jsonl` (kimi-k3): overall 40/47/43 (p=0.520), style 32/46/52 (p=0.141)
- `hack_O3_glm_harness.jsonl` vs `hack_F2_gpt61_terra.jsonl` (kimi-k3): overall 35/46/49 (p=0.266), style 32/38/60 (p=0.550)
- `hack_O3_glm_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 34/57/39 (p=0.021), style 25/56/49 (p=0.001)
- `hack_O3b_glm_prompt_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 35/60/35 (p=0.013), style 26/60/44 (p=0.000)
- `hack_O3c_glm_prompt_harness_style.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 35/52/43 (p=0.086), style 33/46/51 (p=0.177)
