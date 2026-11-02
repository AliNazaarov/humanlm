# Blueprint: FeatherLM Role B (eval, evidence, story), 2026-11-02

Objective: by 15:00 PT, `hackathon/report/RESULTS.md` is a fair, reproducible comparison with CIs, the human A/B test is done, and the demo, README and video script are ready. Sources: `hackathon/ROLE_B_FRIEND.md`, `hackathon/WIN_PLAN.md`, `CLAUDE.md`.

**Mode: direct.** No feature branches or PRs: `bus.sh` pushes the current branch, and Ali's agent reads `main`. Each step ends with a small commit to `main` after `git pull --rebase`, plus `bus.sh status friend "<step> done"`.

## Invariants (check after every step)
- `cd pipeline && python -m unittest tests.test_metrics` and `python -m unittest discover -s hackathon/eval -p "test_*.py"` pass.
- No key-like strings are staged: `git diff --cached | grep -nE "fw_|sk-|Bearer [A-Za-z0-9]"` returns nothing.
- Only Role B paths are touched (`hackathon/eval|report|demo`, `README.md`, `Makefile`, `.env.example`, `requirements.txt`, `plans/`).
- Same SYSTEM prompt and decoding for every system. Any extra prompting is labelled in the system name and in Method.

## Gates per feature step
1. **Tests:** unit tests for the pure functions, plus one offline dry run on existing files (`evals/baseline_frontier.jsonl` vs `evals/runs/out_lora_v1.jsonl`).
2. **Review:** a `python-reviewer` subagent on the diff. Fix CRITICAL and HIGH findings.
3. **Eval check:** the dry-run output is sane (130 rows, no NaN, CIs contain the point estimate). Log one line in `plans/EVAL_LOG.md`.

## Dependency graph
```
S1 stats ─┐
S2 frontier runner ─┤
S3 judge ───────────┼─> S4 score_all ─> S5 plot ─> S7 notebook
S6 human A/B page ──┘           └────> S8 README + RESULTS text + video script ─> S9 freeze
```
S1, S2, S3 and S6 can run in parallel: no shared files, no output dependencies.

---

## S1. `hackathon/eval/stats.py` + `test_stats.py` (default model, parallel)
Context: numpy percentile bootstrap. scipy's BCa fails on degenerate arrays such as all-zero fail rates.
Tasks:
- `bootstrap_ci(values, stat=np.mean, n=1000, seed=0) -> (point, lo, hi)`, 95%.
- `paired_bootstrap_diff(a, b, stat=np.mean, n=1000, seed=0) -> (diff, lo, hi, p_two_sided)`: resample shared ids together.
- `judge_sign_test(wins, losses) -> p` via `scipy.stats.binomtest` (ties excluded, disclosed).
- `percentiles(latencies) -> {p50, p95}`.
- Tests: a fixed array has a known mean inside the CI; a constant array gives a zero-width CI; identical a and b give diff 0 and p = 1; the result is deterministic for a given seed.
Exit: tests pass. Delete `test_smoke.py`.

## S2. `hackathon/eval/run_frontier.py` (default model, parallel; the live run needs a key)
Context: shared outputs schema in `CLAUDE.md`. Two arms: `frontier-live` (exact SYSTEM) and `frontier-strong` (SYSTEM + a strong rewrite instruction in `hackathon/eval/FRONTIER_STRONG.md`, labelled as extra prompting). The pre-existing `baseline_frontier.jsonl` stays as a third row.
Tasks: CLI `run_frontier.py EVAL OUT --provider anthropic|openai --model ID --arm live|strong [--concurrency 4] [--limit N]`. Use the SDKs (built-in retries, `max_retries=5`). Resume by id. Wall-clock latency per request. Cost = tokens × price from `hackathon/report/PRICES.md`. Strip `<think>`. At the end, assert row count, unique ids and no empty outputs.
Test: the request builder and resume logic, with the SDK client mocked (no network).
Exit: mocked test passes; a `--limit 3` live smoke run once a key exists (NEEDS-HUMAN).

## S3. `hackathon/eval/judge.py` + `JUDGE_PROMPT.md` (strongest model for the rubric, parallel)
Context: `evals/EVALS_AND_RL_PLAN.md` §2.6–2.7. Pairwise, forced choice `1|2|tie` + a one-line reason, temperature 0, both orders. A win counts only when both orders agree. The judge is a 70B+ open model on Fireworks (OpenAI-compatible `base_url=https://api.fireworks.ai/inference/v1`), so the frontier isn't grading itself.
Tasks: CLI `judge.py A.jsonl B.jsonl --eval evals/eval_all.jsonl --model ID --out hackathon/report/judge_A_vs_B.jsonl [--mock]`. Resume by (id, order). Write a summary `{win, loss, tie, n, flip_rate}`. `--mock` returns deterministic verdicts for offline tests. For the held-out set, add a "closer to the human original" question.
Test: verdict aggregation (agree, disagree → tie), the parser for messy model text, and resume.
Exit: the mock dry run prints a summary; one live call once the Fireworks key exists.

## S4. `hackathon/eval/score_all.py` (strongest model; needs S1)
Tasks: discover `evals/runs/hack_*.jsonl` + `evals/baseline_frontier.jsonl` ("frontier-persona-preexisting", no cost or latency). Join to `eval_all.jsonl` by id. Call `metrics.score_file(..., source_field="ai_draft", band=band_v0)`. Add `must_keep` coverage (crude, disclosed), `forbidden` hits, trick `verbatim` misses, length ratio, latency p50/p95, and cost per 1k. Read judge JSONLs if present (`--rejudge` re-runs them). Write `results.json` (numbers, CIs, n, model ids, prices) and render `RESULTS.md` from it. Add the held-out table when `hack_*_heldout.jsonl` exists.
Check: match the existing "in human range" definition from `MORNING_REPORT_2026-11-01.md` and `score2_*.json` before choosing one.
Exit: `make eval` (or `python hackathon/eval/score_all.py`) runs offline in under 2 minutes on the dry-run files, and the table renders.

## S5. `hackathon/eval/plot.py` (default; needs S4)
One figure, `hackathon/report/results.png`. Panel 1: fact hard-fails with CI bars. Panel 2: Pareto chart of quality (fact-fail rate or judge win) vs cost per 1k (log x), with p50 latency as the label. Plain labels.

## S6. Blind human A/B test page (default; parallel; UI/UX skills + Playwright e2e)
Artifact page with a shared database (`db` capability). 20 pairs from `eval_all`: the original draft, then rewrites A and B in random order per viewer. Votes `A|B|tie` + optional reason, mobile first. No model names shown until the end. A results view tallies votes. Pairs are generated by `hackathon/eval/make_ab_pairs.py` into `hackathon/demo/ab_pairs.json`: placeholder now (frontier-persona vs lora_v1), swapped for frontier-live vs FeatherLM-FT at SYNC 2.
Gates: `web-design-guidelines` review, then a Playwright e2e run (vote, reload, tally) at phone and desktop sizes.
Exit: URL ready by 13:45 for the 14:00–15:00 venue test. Votes are exported to `hackathon/report/human_ab.jsonl` for score_all.

## S7. `hackathon/demo/demo.ipynb` (default; needs S4, S5)
One item → frontier vs FeatherLM-FT side by side with `must_keep` facts highlighted → `results.json` table → chart. Runs in under 1 minute; no headers or keys in outputs.

## S8. README, RESULTS prose, video script (default; needs S4)
README leads with the results table (copied from the generated RESULTS.md), then setup, `make eval`, Method, Limitations (evals/README caveats, judge bias, reverse-distilled drafts, metrics ≠ preference, n = 130), pre-existing vs built today, AI disclosure, team, licence. 3 honest failure cases. `hackathon/demo/VIDEO_SCRIPT.md` (50 s).

## S9. Freeze (15:00)
`hackathon/CHECKLIST.md` reviewer loop, security scan, open the public repo in incognito, record the commit hash.

## Human-only items (NEEDS-HUMAN)
- An Anthropic or OpenAI key in `.env` (S2 live run).
- The Fireworks key, shared by Ali or created (S3 live judge).
- Running the venue A/B test with people (S6), recording the video, Submit.

## Timeline
| PT | Steps |
|---|---|
| 11:30–12:15 | S1, S2, S3, S6 in parallel |
| 12:15–13:00 | S4 (dry run), S5 |
| 13:00–13:30 | S7 draft, S8 Method + Limitations |
| 13:30 SYNC 2 | Real runs land → `make eval`, judge, swap A/B pairs |
| 14:00–15:00 | Venue A/B test, failure cases, README, video script |
| 15:00 | S9 freeze |
