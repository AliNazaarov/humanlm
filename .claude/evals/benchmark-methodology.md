## EVAL: benchmark-methodology
Created: 2026-11-02 12:30 PT
Question: is the FeatherLM benchmark a fair, reproducible test of "fact-safe human rewrite" vs a frontier baseline?

### Capability Evals (validity)
- [ ] C1 Train/eval separation: 0 training or validation rows share 8+ consecutive words with any eval draft
- [ ] C2 Same items for every system: each leaderboard system covers all items of every split it ran (persona disclosed as 130 only)
- [ ] C3 No silent drops: refusals and failed calls are scored as fails, and counted in the table
- [ ] C4 Baseline not weakened: F1 uses the strong prompt; decoding differences are recorded per row and disclosed
- [ ] C5 Gaming check: the harness optimises the same gates we score, so an independent signal exists (judge from a family not under test; blind human test)
- [ ] C6 Judge reliability: position bias small (pos-1 rate 45-55%), flip rate reported, 0 unparsed
- [ ] C7 Uncertainty: every headline rate has a 95% CI; differences use a paired test; multiple comparisons acknowledged
- [ ] C8 Reproducible: every run has a manifest (model, prompt hash, decoding, commit); `make eval` rebuilds offline in < 2 min
- [ ] C9 Metric validity: gate false positives checked on real outputs (name proxy fixed, with tests)
- [ ] C10 Cost and latency comparable: same price source for all; latency definition disclosed where it differs (harness includes revise loops)

### Regression Evals
- [ ] R1 Metric tests pass (pipeline/tests)
- [ ] R2 Eval-harness tests pass (hackathon/eval)
- [ ] R3 score_all output is deterministic (two runs give identical results.json)

### Success Criteria
- Capability: all PASS, or FAIL items fixed or disclosed in README Limitations before the 15:00 freeze
- Regression: 100%
