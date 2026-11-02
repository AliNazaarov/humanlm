# Master checklist (FeatherLM, Fireworks hackathon 2026-11-02)

Merged from `hackathon/CHECKLIST.md`, `hackathon/PLAN_V2_JUDGES.md`, `hackathon/README_HACKATHON.md` §1 (rules), the event rules, the judges' kickoff slides and the founder's requirements.
Where sources conflict, the newer one wins: founder > PLAN_V2 > CHECKLIST (for example, 250 items, not 130).

The checker marks each row PASS / FAIL / NOT-YET (expected later) with evidence. The checker never fixes. Max 3 passes (pass 1 now, pass 2 at 14:30 PT, pass 3 at 15:15 PT).

## E. Event rules

| id | Requirement | How to check | Owner |
|---|---|---|---|
| E1 | Team of 2-5, in person | README Team lists 2 people; both at the venue | both |
| E2 | One project | One repo, one task, one headline metric | both |
| E3 | Frontier baseline on the SAME held-out cases, consistent scoring | Every run file has the same ids as `evals/eval_all.jsonl` + `evals/heldout_pairs.jsonl`; one scorer (`score_all.py`) for all; missing rows counted as fails | Ruslan |
| E4 | Eval data separate from training | No eval draft text in `hackathon/data/train.jsonl`/`valid.jsonl`; 8-word overlap check; `SPLIT.md` says 0 | Ali |
| E5 | 100+ varied held-out examples | Count items per split in `results.json` | Ali |
| E6 | Confidence intervals / significance | Every row has a 95% CI and a paired test vs the reference | Ruslan |
| E7 | Quality / cost / latency tradeoffs disclosed | Cost and latency columns next to quality; tradeoff sentence in README | Ruslan |
| E8 | No fabricated results | Every claim in README, OVERVIEW, pitch, video script traces to a committed file | both |
| E9 | No weakened baseline | Frontier decoding, effort and retry policy recorded and disclosed; failures retried fairly | Ruslan |
| E10 | No cherry-picking | Every committed `evals/runs/hack_*.jsonl` system has a row; abandoned runs disclosed | both |
| E11 | Public GitHub repo, opens signed-out | `curl -s -o /dev/null -w "%{http_code}" https://github.com/AliNazaarov/humanlm` returns 200 | Ali |
| E12 | Setup + eval instructions + code to rerun both systems | Fresh clone, fresh venv, `pip install -r requirements.txt`, `make test`, `make eval`, demo notebook run | Ruslan |
| E13 | Git commit hash submitted | Hash in `hackathon/CHECKLIST.md` and the form; equals `git log -1` on main at freeze | Ali |
| E14 | Demo video < 120 s (aim < 60 s): problem, what was built, the comparison | Link in README and form; plays signed-out; length checked | Ruslan |
| E15 | Project overview: task, user, approach, business value | README "What it does" + "Who it's for"; `hackathon/pitch/OVERVIEW.md` | both |
| E16 | All team members listed: Muhammadali Nazarov (Ali), Ruslan Kan | Full names in README Team and OVERVIEW Team | both |
| E17 | Sponsor tracks named, tech use explained | README "Sponsor track" says what ran on Fireworks | Ruslan |
| E18 | Pre-existing work vs built today disclosed | README section; first commit `59f70c4` | both |
| E19 | AI-tool use disclosed | README "AI-assistance disclosure" | Ruslan |
| E20 | No keys, credentials or personal data in repo (incl. history) | `git log -p --all \| grep -nE "fw_[A-Za-z0-9]{10,}\|sk-[A-Za-z0-9]{20,}\|AIza[0-9A-Za-z_-]{30}"` empty; `.env` absent/ignored; no emails beyond event addresses | both |
| E21 | Licences respected; third-party credit | `LICENSE`; blader/humanizer MIT credit + licence file; per-item licence for every redistributed text | Ali |
| E22 | Fireworks is used (all prizes need it) | Run manifests show `provider: fireworks`; judge on Fireworks | Ali |
| E23 | NVIDIA award only if a Nemotron/NVIDIA angle is real | No NVIDIA claim unless a Nemotron row exists | Ali |

## J. Judges' kickoff (slides)

| id | Requirement | How to check | Owner |
|---|---|---|---|
| J1 | Harness + better prompting on open models | O2 (prompt) and O3* (harness) rows in the leaderboard | Ali |
| J2 | Fine-tune (SFT, ideally RL too) with a row in the leaderboard | O4/O5/O6 rows in `results.json`; job/session id, base, settings in `hackathon/train/TRAIN_LOG.md` | Ali |
| J3 | Runs repeatable: versions, prompts, settings, outputs tracked | Every run has a manifest in `hackathon/runs/` with model, prompt hash (matches the file), decoding, a commit that exists in history | both |
| J4 | Before/after leaderboard chart, significance per row, failed variants kept | `hackathon/report/leaderboard.png` has every system and a sig/n.s. label per row | Ruslan |
| J5 | Investable business problem | README "Who it's for": user, pain, product, cost, tradeoff | both |
| J6 | Clear demo task | `hackathon/demo/demo.ipynb` runs offline and shows one before/after | Ruslan |
| J7 | Closed models only for baselines/judges, budget $30-50 | Sum `cost_usd` of Claude/GPT rows | Ruslan |

## F. Founder's requirements

| id | Requirement | How to check | Owner |
|---|---|---|---|
| F1 | ONE benchmark: fact-safe human rewrite rate on 250 items, strict + lenient | `HEADLINE.md` and README show both | Ruslan |
| F2 | Task wording = rewriting AI-drafted copy (copy editing), not copywriting from scratch | grep README, OVERVIEW, pitch, video script | both |
| F3 | Pre-event CPU model results are NOT in the repo | `git grep` for `lora_v0/v1`, `out_lora`, `score2_`; history of the public snapshot | Ali |
| F4 | Licence-clean training data only, no copyrighted books | `SPLIT.md` source mix; Gutenberg = public domain only | Ali |
| F5 | No frontier text in training | Generator model of every pair; DPO pairs source | Ali |
| F6 | Human A/B reported honestly whichever way | README + `human_votes.json` | both |
| F7 | Gemini 4 Argon untested, disclosed | README Limitations | Ruslan |
| F8 | LinkedIn social-prize post done | Post URL recorded in the repo or bus | Ali |
| F9 | Keys only in `~/.config/humanlm`, never in git | `ls ~/.config/humanlm`; E20 grep | both |
| F10 | Headline wins are wins a human reader would feel (no reward hacking) | Gate winner vs independent judge facts/style and human A/B; quoted failure examples | both |
| F11 | Eval items not used to tune the system, or the tuning is disclosed | Count variants built while looking at the 250; is the reported row chosen before or after? | both |

## C. Carried over from `hackathon/CHECKLIST.md` (not already above)

| id | Requirement | How to check | Owner |
|---|---|---|---|
| C1 | `make eval` regenerates the committed `results.json`/`RESULTS.md` from committed outputs, offline | Fresh clone: `make eval`, then `git diff --stat` must be empty | Ruslan |
| C2 | Method and decoding described accurately | README Method vs run manifests (prompt file, max tokens, temperature, effort) | Ruslan |
| C3 | Limitations current and honest | Counts of systems/splits/judge pairs match `results.json` | Ruslan |
| C4 | Cost per row is complete | `cost_usd` includes every model call (including selection judges); price row in `PRICES.md` for every model | Ali |
| C5 | Outputs clean: no `<think>`, empty outputs counted, no silent echoes | Script over every run file | both |
| C6 | No model weights committed | `git ls-files \| grep -E "safetensors\|gguf\|\.bin$"` empty | Ali |
| C7 | Fireworks deployments / training sessions cleaned up | `firectl` or console note after the last run | Ali |
| C8 | Branch state at freeze: no uncommitted changes, both roles merged on main | `git status` clean at freeze | both |
| C9 | Independent audit covers the rows we pitch | `hackathon/audit/AUDIT.md` lists every pitched row | Ruslan |
| C10 | No placeholders in submission text | grep `[RESULT`, `[N]`, `ts-…`, `____` in OVERVIEW, LinkedIn post, CHECKLIST, TRAIN_LOG | both |
| C11 | `make test` green | Fresh venv | Ruslan |
| C12 | Judge protocol: both orders, inconsistent = tie, judge id recorded, judge not a compared system | `RESULTS.md` judge table | Ruslan |
| C13 | `PRICES.md` has source URLs and the date for every price used | Read the file | Ruslan |
