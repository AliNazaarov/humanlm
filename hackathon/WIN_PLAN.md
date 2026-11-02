# How we win 1st (everyone has the same models and credits; we win on evidence)

| Criterion | What we do | Owner |
|---|---|---|
| Benchmark 40% | Strict fact-gate count (invented/broken numbers, names, quotes) as the headline metric | Friend (score_all) |
| | Strong, fair frontier baseline: same SYSTEM + strong rewrite prompt, never weakened | Friend |
| | Ablation: Fireworks base vs base+prompt vs fine-tuned, same 130 items | Ali |
| | Second test set: 120 held-out pairs with real human references | Ali (done) + Friend |
| | Paired bootstrap 95% CIs + significance test on every headline number | Friend |
| | Mini blind human test: 5–10 people at the venue, 20 pairs, A/B hidden labels | Both, 2:00–3:00 |
| | Pareto chart: quality vs $ per 1k rewrites and p50/p95 latency | Friend |
| | 3 honest failure cases in the report | Friend |
| Business 25% | User: founders/marketers + AI agents that post copy. Pain: fake-sounding copy and rewrites that change facts (FTC risk). Cost per 1k vs frontier. API for agents | Ali (overview) |
| Technical 20% | Licence-clean pipeline, attribution filter, leakage check, tests, Fireworks SFT + deploy. Clear "built today" list | Both |
| Presentation 10% | 50-s video: frontier changes a fact (red), ours keeps it and reads human; then one chart | Friend |
| Docs 5% | `make eval` reproduces everything; README leads with the results table | Friend |
| Finals | 2-min pitch + answers: why not just prompt GPT? is the data legal? how do you know it's human? | Ali |
| NVIDIA award | Nemotron base on Fireworks if SFT-supported; say so in overview | Ali |
