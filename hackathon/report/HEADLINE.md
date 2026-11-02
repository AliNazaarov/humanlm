Fact-safe human rewrite rate on 250 items (eval 130 + held-out 120), 95% CI; Δ vs `frontier-strong:claude-opus-5-5` by paired bootstrap. Generated from `hackathon/report/results.json`.

| System | Fact-safe rate | Δ vs reference | $ / 1k rewrites | p50 latency |
|---|---|---|---|---|
| `O3b_glm_prompt_harness` | 94% [91, 97] | +23 pp [+18, +28], significant (p=0.000) | $0.55 | 1.6s |
| `F1H_opus_harness` | 94% [90, 96] | +22 pp [+17, +28], significant (p=0.000) | $16.44 | 4.9s |
| `O3_glm_harness` | 93% [89, 96] | +21 pp [+16, +27], significant (p=0.000) | $0.28 | 2.6s |
| `O2_glm_prompt` | 73% [67, 79] | +2 pp [-5, +8], n.s. (p=0.620) | $0.31 | 1.2s |
| `frontier-strong:claude-opus-5-5` | 72% [66, 77] | reference | $8.93 | 3.9s |
| `frontier-live:claude-opus-5-5` | 53% [47, 60] | -18 pp [-24, -13], significant (p=0.000) | $7.21 | 3.7s |
| `F2_gpt61_terra` | 40% [34, 46] | -32 pp [-39, -24], significant (p=0.000) | $0.86 | 2.6s |
| `X0_copy_draft (no rewrite: control)` | 32% [26, 38] | -40 pp [-47, -32], significant (p=0.000) | n/a | 0.0s |
| `O1_glm_base` | 27% [22, 33] | -44 pp [-52, -37], significant (p=0.000) | $0.10 | 1.2s |
| `frontier-persona-preexisting` (130 items) | 12% [7, 19] | -57 pp [-66, -48], significant (p=0.000) | n/a | n/a |

Pairwise judge (both orders; A wins / B wins / ties, two-sided sign test):

- `hack_O3_glm_harness_heldout.jsonl` vs `hack_F1H_opus_heldout.jsonl` (kimi-k3): overall 52/31/37 (p=0.028), style 41/17/62 (p=0.002)
- `hack_O3_glm_harness_heldout.jsonl` vs `hack_strong_claude-opus-5-5_heldout.jsonl` (kimi-k3): overall 42/35/41 (p=0.494), style 28/30/60 (p=0.896)
- `hack_O3_glm_harness.jsonl` vs `hack_F1H_opus.jsonl` (kimi-k3): overall 40/47/43 (p=0.520), style 32/46/52 (p=0.141)
- `hack_O3_glm_harness.jsonl` vs `hack_F2_gpt61_terra.jsonl` (kimi-k3): overall 35/46/49 (p=0.266), style 32/38/60 (p=0.550)
- `hack_O3_glm_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 34/57/39 (p=0.021), style 25/56/49 (p=0.001)
- `hack_O3b_glm_prompt_harness.jsonl` vs `hack_strong_claude-opus-5-5.jsonl` (kimi-k3): overall 35/60/35 (p=0.013), style 26/60/44 (p=0.000)
