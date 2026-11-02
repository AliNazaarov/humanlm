# Verify pass 1 of 3 (12:30-12:50 PT, 2026-11-02)

Checker: separate verifier (did not build anything here; fixes nothing). Checklist: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md).
Checked commit: `e54b1f5` on main (after `git pull --rebase --autostash`: already up to date). Untracked at check time: `hack_O3h_*` (61/60 rows), `hack_O3j_glm_bestof3_judged_real.jsonl`, `hack_O3k_*`.
Method: a fresh `git clone` of the committed state into a scratch folder, a fresh venv from `requirements.txt`, then `make test`, `make eval` (twice), the demo notebook, and scripts over every run file and manifest.

## Summary

| Status | Count |
|---|---|
| PASS | 30 |
| FAIL | 17 |
| NOT-YET | 7 |
| Total | 54 |

Deltas vs the last check (Ruslan's 13:20 dry pass, bus `20261102T201727Z`): "J6 all 34 run files have rows" was PASS, now FAIL (O3g is committed and has no row). "make eval offline + deterministic" is confirmed deterministic (two runs, identical `results.json`), but it fails on a fresh install (scipy missing), and the committed report is stale.

## The main finding (reward hacking)

The top leaderboard row wins on our own gates in a way a reader would not feel.

- `O3j_glm_bestof3_judged` is ranked first: 98% strict fact-safe vs Claude 72%.
- The independent judge (Kimi K3, both orders) says the opposite on facts for that row. Facts: ours 4, Claude 25, ties 101 (p=0.000). The same is true for `O3d` (5/22, p=0.002). Source: `hackathon/report/RESULTS.md`, judge table.
- Example, `dev-006`. The draft has no carrier and no cat. O3j writes: "Your dog hates the carrier. Your cat vanishes at the sight of it." It passes all four gates (`pass: True` in `evals/runs/hack_O3j_glm_bestof3_judged.jsonl`). Kimi, both orders: "Rewrite 1 invents claims about dogs hating carriers and cats vanishing, which are not in the draft." G1 only catches new numbers, names, quotes and attribution verbs. An invented claim made of ordinary words passes.
- Example, `trick-03` (from `hackathon/audit/AUDIT.md` §G). Claude writes "2,047 freelancers invoiced KES 84,312,500 …" and fails G2 for dropping the redundant "Over 2,000". The O3 harness passes. It keeps "The future of freelancing is here" and adds "and this is what it looks like in Kenya", which is not in the draft.
- Human A/B: Claude 4, ours 0, tie 1 (one founder ballot). The audit (§A) shows every system, including ours, ends up further from the human original than the raw AI draft (chrF 0.713 for the draft vs 0.607-0.666 for the systems).
- README still says the harness "keeps facts much better than Claude" (README:9). Limitations says the judge "finds the fact edge in our favour" (README:106). For O3d and O3j the judge finds the opposite, and it is significant.

## FAIL table (single most important fix, owner)

| id | What is wrong (evidence) | Most important fix | Owner |
|---|---|---|---|
| F10 | Reward hacking on the top row. O3j passes the gates on `dev-006` while inventing "Your dog hates the carrier". The judge rates O3j's facts worse than Claude's (4/25, p=0.000) and O3d's too (5/22, p=0.002). README:9 and README:106 claim the fact edge is ours. | Pitch O3c, not O3j. Rewrite README:106 to quote the judge facts column per row. Add one Limitations line: "G1 misses invented claims that have no number or name (example dev-006)". | both |
| E8 | Unsupported claims. README:74 says "plus DPO on human labels; job ids and settings in TRAIN_LOG.md". `human_rl/ai_labels_summary.json`: 66 DPO pairs, 65 kept from GLM labels, only 3 Ali labels. TRAIN_LOG has no job ids (placeholder "ts-… / run-… (filled from the log below)", and there is no log). README:122 says "the Fireworks fine-tune and serving" and "the video" are built. | Change README:74 and :122 to what is true now: SFT running, no row yet; DPO labels are GLM-5.3 AI labels plus 3 human. Re-word at freeze. | both |
| J2 | No fine-tune row. No O4/O5/O6 in `results.json`. Bus 12:24: SFT at step 214/313. TRAIN_LOG has no session or run id, no loss log, no outcome. | Paste the real session/run id and the loss log into TRAIN_LOG.md now. Land O4 on 250 items by 14:30, or write "SFT did not finish in time" in README and OVERVIEW. | Ali |
| F11 | Tuning on the test set is not disclosed. Eleven harness variants (O3, O3b-O3k) were built after reading results on the same 250 items. The top row is picked after the fact. Only the 80-item real-README split was built after most of the tuning. | Name one system as the entry (O3c: run at 11:26, before O3d-O3k; Ruslan proposed it as the main row at 13:09), call the rest ablations, and add a Limitations line: "variants were tuned on these 250 items; the real-README split is the least-tuned check". | both |
| E10 | Cherry-picking by omission. `hack_O3g_glm_calm_retrieval_claimcheck{,_heldout}.jsonl` is committed (130+120 rows, manifest present). It has no row in the committed RESULTS.md, README or chart. In a fresh `make eval` it scores 92% [88, 95]. O3h (61/60 rows, untracked) was abandoned and is not disclosed. | Run `make eval` and commit (C1). Add one README line naming O3h (and O3k if it does not finish) as incomplete runs. | both |
| C1 | The committed report is stale. Fresh clone + `make eval` changes 4 files (`results.json` +2846/-1452, RESULTS.md 47 lines). It adds O3g everywhere, and the Real README split gains O3 99%, O3b 98%, O3c 98%, O3f 98% (the committed version shows only Claude and F1H). | Run `make eval` on main and commit the outputs after the last run lands. Pass 2 re-diffs. | Ruslan |
| J4 | The chart is missing O3g (same cause as C1). | Re-render with `make eval` / `plot.py` after C1. | Ruslan |
| E12 | A fresh setup fails. `make eval` in a fresh venv from `requirements.txt` gives `ModuleNotFoundError: No module named 'scipy'` (`hackathon/eval/stats.py:17`). The demo notebook also needs `ipykernel`, which is not listed. | Add `scipy` and `ipykernel` to `requirements.txt`. | Ruslan |
| C2 | README Method is wrong about prompt and decoding. It says every system gets the same system prompt "at temperature 0.7, top_p 0.9 and at most 400 tokens" (README:98). Manifests show `max_tokens` 1500 for every row. O2/O3b-k use `prompt_v2.txt` or `prompt_v3_calm.txt`. Claude gets no temperature or top_p, with adaptive thinking at effort "low". GPT and GLM run at `reasoning_effort` "low". CLAUDE.md repeats the 400-token rule. | Rewrite the Method bullet from the manifests: a prompt file per row, max_tokens 1500, effort low, Claude sampling params not sent. | Ruslan |
| E9 | Baseline handling is not disclosed. Claude strong and live ran at effort "low". The 2 `EmptyOutput` items (`ho-013`, `ho-054`, `*.failures.jsonl`, `attempts: 1`) count as Claude fails after one try, while the harness gets up to 4 tries. | Retry ho-013 and ho-054 for Claude (3 attempts; raise max_tokens if thinking used up the budget), rescore, and state "effort low" in README. | Ruslan |
| C4 | O3j's cost leaves out its selection judge. 245 of 250 rows called `glm-5p3` with `judge_cost_usd` 0 (`--judge-in-price` defaults to 0.0, `harness.py:343`). The 150,634 input and 5,018 output judge tokens are logged but not priced. `PRICES.md` has no `glm-5p3` row. $2.56/1k is understated. | Add the `glm-5p3` price row (URL + date) and recompute O3j/O3k cost from the logged tokens. | Ali |
| F3 | Pre-event CPU model results are still in the repo. `plans/EVAL_LOG.md:5-6` quotes lora_v1 numbers ("Fails 53 vs 6", "53/6/15"). `hackathon/ROLE_B_FRIEND.md:15,57` points to `out_lora_v1.jsonl` ("v1 (CPU, 0.6B)"). The git history (`59f70c4`) holds `out_lora_v0/v1.jsonl`, `score2_*.json` and `MORNING_REPORT`. | Delete those lines, and publish from the squashed snapshot that PLAN_V2 already plans, so the history does not ship. | Ali |
| E21 | Licences for redistributed text are not recorded. README:112 itself says 73 held-out items from Common Pile CCCC "need their licence recovered before redistribution". `train.jsonl` holds 2,924 CCCC rows the same way (`SPLIT.md`). A public repo redistributes them without attribution. | Before going public, recover each document's licence and URL from Common Pile metadata. Otherwise, leave the CCCC rows out of the public snapshot and say so. | Ali |
| E16 | Full names are missing. README Team: "**Ali** (AliNazaarov)" and "**Ruslan Kan**". OVERVIEW.md:64: "Ali Nazarov … and Ruslan". Neither has "Muhammadali Nazarov". | README and OVERVIEW: "Muhammadali Nazarov (Ali)" and "Ruslan Kan". | both |
| C3 | Limitations are stale. README:108 says "We report 9 systems on 5 splits and 6 judge pairs". `results.json` now has 18 systems (19 with O3g), 7 splits and 10 judge pairs. | Update the counts from `results.json`, and re-check that "headline differences survive a correction" still holds. | Ruslan |
| C9 | The audit does not cover the pitched rows. `AUDIT.md` was generated at 11:36 over 10 systems, without O3d, O3e, O3f, O3g or O3j. | Re-run `python hackathon/audit/audit.py` after the last run and commit. | Ruslan |
| J3 | One manifest points to a commit that is not in history. `hackathon/runs/F1H_opus_harness_real.json` has commit `6e34ff2…`, and `git cat-file -e` fails (lost in a rebase). The other 17 commits exist, and prompt hashes match the stripped prompt files. | Re-record that manifest's commit, or add a note in it. | Ruslan |

## Full table

| id | Status | Evidence |
|---|---|---|
| E1 | PASS | README Team: 2 people. In-person not checkable from the repo. |
| E2 | PASS | One repo, one task, one headline metric. |
| E3 | PASS | Every committed run file has the same 130 + 120 ids, with no extra and no duplicate ids. Claude strong/live heldout have 118 rows, with 2 missing counted as fails (`score_all`, gate note in RESULTS.md). |
| E4 | PASS | 0 eval_all drafts exact or 8-gram in train/valid/train_modern. 0 held-out drafts/humans exact in train. 21 held-out items share an 8-gram with training text (my recount; README says 22). This is disclosed, with a `heldout_clean` table. |
| E5 | PASS | 250 items (100 dev, 30 trick, 120 held-out) plus 80 real README items. |
| E6 | PASS | Clopper-Pearson CIs and a paired bootstrap Δ with p per row (RESULTS.md). |
| E7 | PASS | $/1k and p50 latency columns sit next to the quality columns. README "Tradeoff" bullet. (O3j cost is understated, see C4.) |
| E8 | FAIL | See the FAIL table. |
| E9 | FAIL | See the FAIL table. |
| E10 | FAIL | See the FAIL table. |
| E11 | NOT-YET | `https://github.com/AliNazaarov/humanlm` and the API both return 404 signed-out at 12:3x. |
| E12 | FAIL | scipy missing. `make test` passes once scipy is installed (34 + 143 tests OK). The notebook runs offline once `ipykernel` is installed. |
| E13 | NOT-YET | `CHECKLIST.md` hash blank. |
| E14 | NOT-YET | `hackathon/demo/VIDEO_SCRIPT.md` is 50 s and covers problem, build and comparison. No video yet. |
| E15 | PASS | README "What it does" (about 90 words), "Who it's for". OVERVIEW has task, user, approach and business value. |
| E16 | FAIL | See the FAIL table. |
| E17 | PASS | README "Sponsor track: Fireworks": inference, judge. (The fine-tune line is an overclaim, see E8.) |
| E18 | PASS | README "Pre-existing work vs built today"; first commit `59f70c4`. Re-check the "built today" list at freeze (E8). |
| E19 | PASS | README "AI-assistance disclosure" (Claude Code). |
| E20 | PASS | The given `git log -p --all` grep returns nothing. No `sk-ant-`/Bearer hits either. `.env` absent and ignored. Only event emails found. Minor: `pipeline/overnight_watchdog.sh:3-4` has a local `/Users/muhammadali/...` path (username only). |
| E21 | FAIL | `LICENSE` MIT. blader/humanizer credited (README Licence, `third_party/blader_humanizer/LICENSE`). Per-document CC licences are missing (see the FAIL table). |
| E22 | PASS | Manifests show `provider: fireworks` for every O-row. Kimi K3 judge on Fireworks. |
| E23 | PASS | No NVIDIA claim. OVERVIEW.md:60 says the track is not claimed. `N1_nemotron_base.log` shows 4-457 s per item, all fails, 10 items. |
| J1 | PASS | O2 (prompt) and O3-O3j (harness) rows. |
| J2 | FAIL | See the FAIL table. |
| J3 | FAIL | See the FAIL table. 41 manifests have model, prompt hash and decoding. |
| J4 | FAIL | `leaderboard.png` has a sig/n.s. label per row and keeps failed variants (O1, O2h, F2h, X0). It is missing O3g. |
| J5 | PASS | README "Who it's for": users, pain (legal risk), product, cost, tradeoff. |
| J6 | PASS | `demo.ipynb` executed offline in a fresh clone (nbconvert, about 630 KB output, no errors). |
| J7 | PASS | Closed-model `cost_usd` across all run files: $22.57. Kimi judge on Fireworks, about $9.55 at list price. |
| F1 | PASS | `HEADLINE.md`/README: strict + lenient, 250 items, CIs, Δ. Note: the label "250 items (eval 130 + held-out 120)" is honest; do not say "250 held-out" on stage. |
| F2 | PASS | README:4 "a copy editor for AI-drafted text: it rewrites AI-sounding marketing copy". No "copywriting from scratch" wording found. |
| F3 | FAIL | See the FAIL table. |
| F4 | PASS | `SPLIT.md` mix: cccc 58%, news 17%, Gutenberg 8% (public domain), foodista 8%, PD Review 8%. No in-copyright books. |
| F5 | PASS | `data/pairs/*.jsonl` generators: `qwen3.5-2b-q4` 6,861, `qwen3.5-4b-q4` 3,966. DPO candidates come from GLM-5.3 Flash (`pref_cand*.json`). |
| F6 | PASS | README/HEADLINE: "venue_founder: 0 / 4 / 1 … p=0.125"; informal classmates session marked "not counted". |
| F7 | PASS | README:110 "Gemini 4 Argon was not tested (no paid quota on the day)". |
| F8 | NOT-YET | No post URL in the repo or on the bus. Cannot verify without logging in. Note: `LINKEDIN_POST.md` Post 2 says "Our fine-tuned open model". Do not use it unless an SFT row exists. |
| F9 | PASS | `~/.config/humanlm/` holds `keys.env` and `gemini.env`, mode 600. The runners read from there (`harness.py:36-37`). |
| F10 | FAIL | See the main finding and the FAIL table. |
| F11 | FAIL | See the FAIL table. |
| C1 | FAIL | See the FAIL table. `make eval` is deterministic (two runs, `cmp` identical) and takes about 64 s, not "seconds". |
| C2 | FAIL | See the FAIL table. |
| C3 | FAIL | See the FAIL table. |
| C4 | FAIL | See the FAIL table. |
| C5 | PASS | 0 `<think>` in all run files. Empty outputs: only the Claude rows' 2 failures, counted as fails. Exact echoes of the draft: X0 (by design), O2 3, O2h 2, O3b 1, O3e 1. They are scored as is, not hidden. |
| C6 | PASS | No weights in `git ls-files`. `.gitignore` blocks `*.safetensors`, `*.gguf`, `*.bin`, `lora_*/`. |
| C7 | NOT-YET | No `firectl` or console note yet. SFT is still running. |
| C8 | NOT-YET | Untracked O3h/O3j_real/O3k files at check time. Expected while runs land. |
| C9 | FAIL | See the FAIL table. |
| C10 | NOT-YET | `[RESULT: …]` in OVERVIEW.md (many), `[N]/[X]%` in LINKEDIN_POST Post 2, CHECKLIST hash blank, TRAIN_LOG "ts-…". |
| C11 | PASS | Fresh venv (+scipy): pipeline 34 tests OK, hackathon/eval 143 tests OK. The "FAIL dev-001: StatusError" lines are expected test output. |
| C12 | PASS | Judge table: both orders, a win needs both to agree, judge `accounts/fireworks/models/kimi-k3` recorded, flip and pos-1 rates shown. Kimi is not a compared system. |
| C13 | PASS | `PRICES.md`: 4 rows with URLs, dated 2026-11-02. (Missing the `glm-5p3` row, see C4.) |

## Rulings on open disagreements

1. **Which row is "FeatherLM" in the pitch: O3c or O3j?** Ruling: **O3c**. It was run at 11:26 (`hackathon/runs/logs/O3c.log`), before O3d-O3k were built. Ruslan proposed it as the main row at 13:09 (bus `20261102T200901Z`). It is 97% [94, 99] strict and 98% lenient. Its judge result is n.s. vs Claude overall (35/52) and n.s. on facts (9/15). O3j's lead is a gate artefact: the judge flags its facts (4/25), and the `dev-006` invention passes the gates. Keep O3j in the table as a variant, and say why it is not the pick.
2. **Strict or lenient as the spoken headline?** Ruling: **say lenient, show both.** The audit (§E) shows part of the strict margin comes from regex artefacts ("5" to "five", "Kenyan" to "Kenya", "despite" read as a name). Lenient O3c is +13 pp [+9, +18] vs Claude strong, still significant. The video script's "[Δ lenient]" line already does this. Keep it.
3. **"Matches Claude inside the same harness" (README:9).** Ruling: **allowed, with its scope stated.** On gates, O3 93% vs F1H 94% (CIs overlap). On the judge, O3 vs F1H is n.s. on the main split (40/47) and ahead on held-out style (41/17). Say "on our gates" and add the judge result in the same sentence.
4. **dev-060 on stage (bus 20:07Z).** Ruling: **agree with Ruslan.** Call it content loss, never "the checker caught it". Claude's G1 flag there is a false positive.

## Next pass

Pass 2 at 14:30 PT re-runs: fresh-clone `make eval` diff (must be empty), the requirements install, the key grep, the run-file/row parity script, the judge facts column for whatever row is pitched, TRAIN_LOG ids, and the public URL.
