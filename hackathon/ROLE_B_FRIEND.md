# Role B: friend (eval, evidence, story)

You own: `hackathon/eval/`, `hackathon/report/`, `hackathon/demo/`, root `README.md`, `Makefile`, `.env.example`. Branch `friend/*`. Do not edit A's paths except at syncs.

Goal by 15:00: `hackathon/report/RESULTS.md` with a fair, reproducible comparison (CIs included), a 60-s video, and a public-ready repo. The benchmark is 40% of the score; your work is most of that.

## What already exists (read for 10 minutes, do not rewrite)

| File | What |
|---|---|
| `evals/README.md` | The eval set, fields, caveats. Read the caveats; they go into limitations. |
| `evals/dev_set.jsonl` (100), `evals/trick_set.jsonl` (30) | Items. Fields: `id, type, brief{facts,numbers,names}, ai_draft, must_keep[], forbidden[]`, trick items add `verbatim[]`. |
| `evals/baseline_frontier.jsonl` (130) | Pre-existing frontier arm: Claude Opus persona prompt, hand-cleaned. No latency/cost. Keep it in the table as "frontier, strong prompt (pre-existing)". |
| `pipeline/metrics.py` | `score FILE --field output --source-field ai_draft --band evals/runs/band_v0.json` → per-row metrics + summary. 13 tell metrics, `in_band`, `faith_hard_fails` (added numbers/names/quotes = fail). Tests: `cd pipeline && python3 -m unittest tests.test_metrics`. |
| `pipeline/infer.py` | The SYSTEM prompt string. Every system uses it verbatim. |

## Step 0 (10:30–11:00): repo hygiene

1. `git checkout -b friend/eval`. Create `.env.example` with `FIREWORKS_API_KEY=`, `ANTHROPIC_API_KEY=`, `OPENAI_API_KEY=` (empty). Confirm `.env` is in `.gitignore` (add it).
2. Root `README.md` skeleton with headings: What it does / Results (table placeholder) / Setup / Reproduce the eval / Method / Limitations / Pre-existing work vs built today / AI-assistance disclosure / Team / Licence.
3. `Makefile`:
```make
eval:       ## score committed outputs, write hackathon/report/results.json + RESULTS.md
	python3 hackathon/eval/score_all.py
test:
	cd pipeline && python3 -m unittest tests.test_metrics
```
4. `requirements.txt` (pin nothing exotic: `requests`, `numpy`, `matplotlib`, `openai` or `anthropic` for the frontier/judge client).

Done when: a fresh clone + `pip install -r requirements.txt` + `make test` passes.

## Step 1 (11:00–11:45): frontier live re-run

Script: `hackathon/eval/run_frontier.py`

- Same SYSTEM, same user turn (`ai_draft`), temperature 0.7, top_p 0.9, max 400 tokens. Model: whatever Ali decides at 10:30 (Claude Sonnet/Opus via Anthropic API, or a GPT model via OpenAI). Record the exact model id string.
- Output: `evals/runs/hack_frontier_<model>.jsonl` in the shared schema (`id, system, output, latency_ms, cost_usd, prompt_tokens, completion_tokens, model`). Cost from the provider's listed price today; write prices to `hackathon/report/PRICES.md`.
- Retry on rate limits; resume by id; assert 130 rows at the end.
- This is the **fair** baseline: same prompt, no hand-cleaning. Do not improve its prompt and do not weaken it. If it ends up worse than the pre-existing persona arm, both rows stay in the table.

Done when: 130 rows, no empties, prices logged.

## Step 2 (11:45–12:30): judge + stats

`hackathon/eval/judge.py`: pairwise judge.
- Input: two output files (A, B) + the eval file. For each id, build a prompt: the brief's facts + the draft + rewrite 1 + rewrite 2. Ask: which rewrite (a) keeps every listed fact and adds none, (b) reads like a skilled human wrote it, (c) is not thinner than needed. Answer `1`, `2` or `tie`, with a one-line reason. Rubric text goes in `hackathon/eval/JUDGE_PROMPT.md`.
- Run **both orders** (A first, then B first) and count a win only if consistent; inconsistent = tie. Temperature 0.
- Judge model: a large open model on Fireworks (so the frontier is not grading itself and Fireworks is used again). Candidates: check fireworks.ai/models for a 70B+ instruct model (Llama 3.3 70B, DeepSeek V3, Qwen 235B). Record the id. Note the judge's own bias in limitations.
- Output: `hackathon/report/judge_<A>_vs_<B>.jsonl` and a summary `{win, loss, tie, n}`.

`hackathon/eval/stats.py`:
- `bootstrap_ci(values, stat=mean, n=1000, seed=0)` → (point, lo, hi) at 95%.
- Apply to: fact hard-fail rate, in-band share, stock-phrase rate, length ratio (output words / draft words), judge win rate, latency p50/p95 (report, no CI needed), cost per 1k rewrites (= mean cost_usd × 1000).
- Paired bootstrap for the difference between two systems on the same ids (resample ids, recompute both).

Dry run on `evals/baseline_frontier.jsonl` and a small synthetic placeholder file to shake out bugs before A's files arrive.

Done when: judge summary and CIs print for the dry run; a unit test in `hackathon/eval/test_stats.py` checks `bootstrap_ci` on a fixed array.

## Step 3 (12:30–13:30): score_all

`hackathon/eval/score_all.py`:
1. Discover `evals/runs/hack_*.jsonl` plus `evals/baseline_frontier.jsonl` (label "frontier-persona-preexisting", no cost/latency columns).
2. Join each output to `evals/eval_all.jsonl` by id (ai_draft, must_keep, forbidden, verbatim). Build `eval_all.jsonl` from dev + trick if missing.
3. Per system: call `metrics.score_file` (import from `pipeline/metrics.py`) with `--source-field ai_draft` and `band_v0.json`; add: `must_keep` coverage (fraction of must_keep facts whose numbers/names appear; a crude check is fine, say so), `forbidden` hits, `verbatim` misses on trick items, length ratio, latency p50/p95, cost per 1k.
4. Judge: FeatherLM-FT vs frontier-live, FeatherLM-FT vs base-untrained, both orders.
5. Write `hackathon/report/results.json` (all numbers + CIs + n + model ids + prices) and render `hackathon/report/RESULTS.md` with the table below. Never hand-type a number into RESULTS.md.
6. If `evals/heldout_pairs.jsonl` and `hack_*_heldout.jsonl` exist, add a second table (there the human original is a real reference: add a "closer to the human original" judge question).

Headline table columns: System | Fine-tuned on Fireworks? | Fact hard-fails /130 (95% CI) | In human range % | Stock phrases /100w | Length ratio | Judge win vs frontier (both orders) | Cost / 1k rewrites | p50 / p95 latency.

Done when: `make eval` regenerates both files from committed outputs in under 2 minutes with no network (judge results are read from the committed judge JSONL; a `--rejudge` flag re-runs the API).

## Step 4 (13:30–14:30): results + chart

- At SYNC 2 take A's FT outputs. Run `make eval`. Look at 10 random outputs per system yourself; paste 2 real before/after examples (one win, one miss) into `RESULTS.md`.
- `hackathon/eval/plot.py` → `hackathon/report/results.png`: one chart, two panels: fact hard-fails with CI bars, and cost per 1k rewrites (log scale). Plain labels. No decoration.
- Write Method (eval set source and size, train/eval separation and the leakage check, prompt, decoding, judge protocol, bootstrap) and Limitations (from `evals/README.md` caveats + judge bias + reverse-distilled drafts + metrics ≠ human preference + n=130).

Done when: RESULTS.md reads top to bottom without a placeholder.

## Step 5 (14:30–15:30): demo notebook, video, README

`hackathon/demo/demo.ipynb` (runs top to bottom in < 1 min with keys in `.env`): load one eval item → call frontier and FeatherLM-FT → show both outputs with the must_keep facts highlighted → load `results.json` → print the table → show the chart.

Video script (aim 50 s), `hackathon/demo/VIDEO_SCRIPT.md`:
1. 0–8 s: "Frontier models make AI copy sound human, but they drop facts. Here is a draft with 3 facts." (show item)
2. 8–22 s: frontier output with a dropped or changed number circled; FeatherLM output with all 3 kept.
3. 22–40 s: results chart. Say the three numbers: fact fails, cost per 1k, latency. Say the CI.
4. 40–50 s: "Open model, fine-tuned and served on Fireworks. Repo link. Built today: everything in hackathon/."
Record with QuickTime screen recording; one take is fine; no music. Export, upload (YouTube unlisted or the form's upload), link in README and the form.

README fills: results table (copy from RESULTS.md), setup, `make eval`, disclosure sections, team, sponsor track (Fireworks + NVIDIA award if Nemotron base), licence note (code MIT or Apache-2.0, Ali's call; data from Common Pile with its licences; eval set CC-BY).

## Step 6 (15:00 freeze → 15:30 submit)

Run `CHECKLIST.md` with the reviewer loop in `AGENT_INSTRUCTIONS.md`. Open the repo URL in an incognito window. Record the commit hash. Fill the form with Ali. Then finish the video by 16:00.

## Hand-offs

| From A | When | You do |
|---|---|---|
| `evals/heldout_pairs.jsonl` | 11:15 | add to score_all discovery |
| `hack_base_*.jsonl` + PRICES | 12:00 | first real `make eval` |
| `hack_humanlm_ft*.jsonl` + model/job id | 13:30 | final `make eval`, judge, chart |
| training facts | 14:30 | overview + README |

## Rules
- Same prompt and decoding for every system. Any difference is written in Method.
- No cherry-picking: every system that was run gets a row. Every metric computed is reported.
- Numbers only from `results.json`. If a number is estimated (e.g. cost from list prices when an API did not return usage), label it "estimated".
- Keys only in `.env`. Never print them in the notebook output; clear outputs that show request headers.
