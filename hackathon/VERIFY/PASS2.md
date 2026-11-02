# Verify pass 2 of 3 (14:48-15:08 PT, 2026-11-02)

Checker: separate verifier. Fixes nothing. Checklist: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md). Pass 1: [PASS1.md](PASS1.md).
Checked: private `main` moved from `adde483` to `1e55c9c` while I checked (14 commits landed). Rows were re-read at the newest commit where they changed. Public repo: `github.com/AliNazaarov/featherlm`, snapshot `fed640a` (one squashed commit).
Method: fresh `git clone`, fresh venv from `requirements.txt`, `make test`, `make eval` (at `be92015`), then `score_all.py` again at `3f16a9d`. Scripts over every new run file and manifest. Fresh clone of the public repo.

## Summary

| Status | Pass 1 | Pass 2 |
|---|---|---|
| PASS | 30 | 42 |
| FAIL | 17 | 8 |
| NOT-YET | 7 | 4 |
| Total | 54 | 54 |

Fixed since pass 1 (11): E9, E10, E11, E12, E21, J2, J4, F3, C2, C3, C9 (plus C7 now checkable, PASS). Still failing from pass 1: E8, E16, J3, F10, F11, C1, C4. New FAIL: C10 (was NOT-YET; QA.md placeholders remain after the pitch was marked "final").

## The main finding (reward hacking, again, on new rows)

The top two leaderboard rows are now `E2_ensemble_glm_deepseek` (100%) and `E1_ensemble` (99%). They pick, per item, the best of 7-8 earlier variants, and a variant is only eligible if it passes **the same four gates we score**. That is selection on the test metric. A reader would not feel this win.

- Kimi K3, E1 vs Claude strong (`judge_hack_E1_ensemble_vs_hack_strong_claude-opus-5-5.summary.json`): overall 30 / 51 / 49 (Claude preferred, p=0.026), facts 10 / 14, style 26 / 43. Qwen: overall 39 / 39, facts 10 / 11.
- E1 costs $15.12 per 1k rewrites (on 247 of 327 rows only), more than Claude strong at $9.11. The "cheap" story does not hold for this row.
- Failure example, `dev-022`. The draft says "a flexible monthly lease starting from just R$ 890". E1 (picked from O3d) writes "Pay R$ 890 a month on a flexible lease, and watch your energy bill …". The floor price became a flat price, and a new claim was added. All four gates pass (`g1_nothing_invented: true`, `pass: true`, `evals/runs/hack_E1_ensemble.jsonl`). Kimi, both orders: "drops 'from' (making the lease a fixed R$ 890, not 'from R$ 890') and adds claims not in the draft".
- Failure example, `dev-018`. E1 changes the headline word "insights" to "patterns" and adds "Your findings deserve an audience." Kimi flags it in both orders. Gates pass.
- `O3t_glm_ali_taste` was written from Ali's 20 style labels and the human A/B votes, which were cast on these same eval items. Its gate rate is 97%, but Kimi prefers Claude's style more than for O3c: 29 / 54 (p=0.008), against O3c's 33 / 46 (n.s.). The human evidence it was tuned on is in-sample.
- README:148 still says the judge "finds the fact edge in our favour". No judge file says that for any pitched row. O3c: Kimi facts 9 / 15, Qwen 11 / 19. E1: 10 / 14. O3t: Kimi 10 / 16, Qwen 14 / 19. Ali's bus handoff (22:48Z) repeats it: "Facts: we win clearly." README:9 says it right ("about even").

## FAIL table (single most important fix, owner)

| id | What is wrong (evidence) | Most important fix | Owner |
|---|---|---|---|
| F10 | E1/E2 top the table by picking per item on the scored gates. Kimi prefers Claude over E1 (30/51, p=0.026; facts 10/14). `dev-022`: "from R$ 890" becomes "R$ 890 a month" plus an invented claim, and all gates pass. O3t was tuned on the human votes and still loses style on Kimi (29/54, p=0.008). | Add one line under the results table: "E1/E2 pick per item among variants using the scored gates as eligibility, so their gate rate is inflated by selection. They are not entries. Kimi prefers Claude over E1 30/51." Keep O3c as the entry. | Ruslan |
| E8 | README:148 says the judge "finds the fact edge in our favour". Judge files show the opposite lean for every pitched row (O3c Kimi facts 9/15, Qwen 11/19). README:116 lists "an AI-feedback DPO" under Fine-tuning, but TRAIN_LOG says O6 was "prepared, not trained" and O7 "stopped at step 1; no model". TRAIN_LOG contradicts itself: lines 31, 58-59, 76 and 85 say O4m was never deployed or evaluated, and lines 106-114 say it was deployed and evaluated. | README:148: replace the clause with "rates facts about even, slightly towards Claude (O3c facts 9/15 Kimi, 11/19 Qwen, n.s.)". | Ruslan (README:148); Ali (README:116, TRAIN_LOG status lines) |
| F11 | The tuning disclosure (README "Ablations were tuned …") covers O3 to O3q only. O3t's prompt came from human votes on the same eval items. E1/E2 select on the eval gates. Neither is named there. | Add O3t, R3t, E1 and E2 to that bullet: "O3t/R3t prompts were written from the blind A/B votes on these items; E1/E2 select on the scored gates." | Ruslan |
| C1 | Fresh clone at `3f16a9d`, `score_all.py`: the diff is 4 files, and only the `L2h_qwen3_4b_dpo_harness` row changes (7% to 8%, 83 to 82 refused/failed). The L2h file is still growing. At `be92015` the diff dropped the O4c row, because the O4c manifest was not committed yet. | Stop L2h, then run `make eval` and commit, right before the snapshot is re-published. | Ruslan |
| J3 | `hackathon/runs/F1H_opus_harness_real.json` still names commit `6e34ff2…`, and `git cat-file -e` fails. This has not changed since pass 1. All new manifests (R3, R3t, E1, E2, O3t, O4m, O4c, L2h, WF) are present, their commits exist, and prompt hashes match the stripped prompt files. | Add a `notes` field to that manifest: "original commit lost in a rebase; the prompt hash matches F1_STRONG_PROMPT.txt". | Ruslan |
| C4 | `PRICES.md` has no `deepseek-v4p1-flash` row, so R3 and R3t show cost "n/a". E2's cost covers 247 of 327 rows and leaves out its R3 part. O4m and O4c show "n/a". TRAIN_LOG has a GPU-hour estimate (about $16 for O4m), but it is not in the table. The `glm-5p3` row from pass 1 is fixed. | Add the DeepSeek V4.1 Flash price row (URL + date) and re-score. Add a README note that SFT rows are billed per GPU-hour (O4m about $16, O4c about 13 min). | Ali |
| E16 | README is fixed ("Muhammadali Nazarov (Ali)", "Ruslan Kan"). OVERVIEW.md:51 at HEAD still says "Ali Nazarov … and Ruslan". | OVERVIEW Team: "Muhammadali Nazarov (Ali) and Ruslan Kan". | Ali |
| C10 | `hackathon/pitch/QA.md` at HEAD still has `[RESULT …]` at lines 44, 52 and 64. `CHECKLIST.md` hash is blank (expected until the freeze). | Fill QA.md:44/52/64 from `results.json` and TRAIN_LOG (O4m 33%, O4c 38%, no DPO model). | Ali |

## Checks you asked for

- **New rows.** R3, E1, E2, O3t, R3t, O4m, O4c (SFT C), L2h and WF all have manifests in `hackathon/runs/`. All are in `results.json` (31 systems) or `excluded_runs.json` (WF, O3h). Id parity: 130/120/80 rows, 0 duplicates, 0 `<think>`, 0 empty outputs. L2h has 18+ of 130 rows, and the missing ones are counted as fails ("147 not run"). README numbers match `results.json` for these rows. The claims around them do not (F10, F11). SFT B (O4m) is 33% and SFT C (O4c) is 38%, both well below Claude. The README table shows this honestly.
- **Human A/B.** README:44-47, HEADLINE, OVERVIEW:29, QA.md:9 and PITCH_2MIN:25/51 all say 58 / 87 / 50, 41 readers, 195 votes, p=0.020. That matches `human_votes.json`. The "164 votes, p=0.024" figure is out of date. It survives only on the bus (Ali 22:48Z) and in the O3t description. `human_ab.jsonl` has 206 lines, and the latest export commit says 42 readers / 198 picks. Refresh `human_votes.json` once more at the freeze so the counts agree.
- **Keys.** `git log -p --all | grep -nE "fw_…|sk-…|AIza…"` gives 0 hits in private history. It also gives 0 hits in the public snapshot. The `sk-ant-`/Bearer hits are checklist text only.
- **Pre-event results.** The public snapshot is one squashed commit (`fed640a`). It has no `out_lora*` or `score2_*` files. `plans/EVAL_LOG.md` no longer quotes lora numbers. `plans/humanlm-role-b.md:53` only names those files.
- **Deployments.** `humanlm-o4m`: delete accepted at about 14:01 PT. `humanlm-sftc`: DELETE at 14:49:40 PT, state DELETING (TRAIN_LOG:165; bus 22:53Z "deployment deleted"). DPO sessions deleted. The SFT B training session `ts-6280bbf3…` is "kept". Confirm with `firectl list deployments` that both show gone, not just DELETING.
- **Visibility.** `github.com/AliNazaarov/featherlm` returns 200 signed-out. `…/humanlm` returns 404 (the checklist URL is out of date). Put the featherlm URL in the form.
- **Founder rule.** Ali's 22:48Z handoff says L2h is pushed by "a Fable agent". The founder rule is no Fable agents. Not a checklist row; flagged for Ali.

## Full table

| id | Status | Evidence |
|---|---|---|
| E1 | PASS | README Team: 2 people. |
| E2 | PASS | One repo, one task, one headline metric (fact-safe rate). |
| E3 | PASS | Every run file has the eval_all/heldout ids, with no extra and no duplicate ids. Missing rows are counted as fails (Claude ho-013/054, L2h "not run"). |
| E4 | PASS | Unchanged since pass 1. SFT C data is gate-filtered train_modern. |
| E5 | PASS | 247 scored items (3 held-out excluded for licence) plus 80 real READMEs. |
| E6 | PASS | CI and paired Δ with p on every row, including the new ones. |
| E7 | PASS | Cost and p50 columns next to quality. Gaps are listed under C4. |
| E8 | FAIL | See the FAIL table. |
| E9 | PASS | Fixed. README:151 discloses Claude refusals on ho-013/ho-054 "in every attempt (first run plus two resumes per arm)". Method records effort and decoding per manifest. |
| E10 | PASS | Fixed. O3g, O3t, R3t, O4c and L2h have rows. WF and O3h are named in `excluded_runs.json` with a reason. |
| E11 | PASS | `https://github.com/AliNazaarov/featherlm` returns 200 signed-out. |
| E12 | PASS | Fixed. A fresh venv from `requirements.txt` imports scipy. `make test` exits 0. `make eval` runs. |
| E13 | NOT-YET | `CHECKLIST.md` hash `________________`. The snapshot hash changes on re-publish. |
| E14 | NOT-YET | No video link yet. |
| E15 | PASS | README "What it does" / "Who it's for". OVERVIEW has task, user, approach and value. |
| E16 | FAIL | See the FAIL table (OVERVIEW only). |
| E17 | PASS | README Sponsor track: Fireworks inference, judges, Serverless Training, deployments. |
| E18 | PASS | README "Pre-existing work vs built today". |
| E19 | PASS | README AI-assistance disclosure. |
| E20 | PASS | 0 key hits in private history and in the public snapshot. `.env` absent and ignored. |
| E21 | PASS | Fixed for the public repo. `DATA_NOT_PUBLISHED.md`: training pairs are not redistributed. `heldout_licences.json` covers 73 items. 3 items with no licence are removed. Minor: README:150 still says those licences "need" recovering. That is stale. |
| E22 | PASS | `provider: fireworks` on every O/R row. Judges are on Fireworks. |
| E23 | PASS | No NVIDIA claim. |
| J1 | PASS | O2 prompt row and O3* harness rows. |
| J2 | PASS | Fixed. O4m (SFT B) and O4c (SFT C) rows. TRAIN_LOG has session and run ids, loss, valid loss and cost estimates. |
| J3 | FAIL | See the FAIL table. |
| J4 | PASS | Chart re-rendered at `70971d2` from results `73f4c5b` (adds O3t, O4c, R3t). Re-render after C1. |
| J5 | PASS | README "Who it's for". |
| J6 | PASS | Carried from pass 1 (the notebook was not re-run this pass). |
| J7 | PASS | Carried from pass 1. The E1/O3t judges ran on Fireworks (Kimi, Qwen). |
| F1 | PASS | HEADLINE and README show strict and lenient on 247 items. |
| F2 | PASS | "copy editor for AI-drafted text". |
| F3 | PASS | Fixed. The public snapshot is one squashed commit with no pre-event results. |
| F4 | PASS | `SPLIT.md` source mix. Bulk training data is not published. |
| F5 | PASS | Training drafts come from open models only. |
| F6 | PASS | README 58/87/50, p=0.020, matches `human_votes.json`. Claude is significantly preferred, and the README says so (README:9). |
| F7 | PASS | README Limitations: Gemini 4 Argon untested. |
| F8 | NOT-YET | No LinkedIn post URL in the repo or on the bus. |
| F9 | PASS | Keys only in `~/.config/humanlm`. |
| F10 | FAIL | See the main finding and the FAIL table. |
| F11 | FAIL | See the FAIL table. |
| C1 | FAIL | See the FAIL table (one row off, L2h still landing). |
| C2 | PASS | Fixed. README Method follows the manifests. Minor: `CLAUDE.md:29` still says "temperature 0.7"; check whether it is in the public snapshot. |
| C3 | PASS | Fixed. Limitations no longer quote stale counts. |
| C4 | FAIL | See the FAIL table. |
| C5 | PASS | New files: 0 `<think>`, 0 empty outputs. |
| C6 | PASS | No weights tracked (private or public). |
| C7 | PASS | O4m and SFT C deployments deleted (DELETING confirmed), DPO sessions deleted. Confirm "gone" with `firectl` at the freeze. |
| C8 | NOT-YET | Working tree at 14:54 had uncommitted pitch edits and a growing L2h file. `WORKFLOW_PASS1-3.md` and `judge/` are untracked. |
| C9 | PASS | Fixed. AUDIT.md covers 20 systems, including the pitched O3c. E1/E2/O3t are not audited. They must not be pitched. |
| C10 | FAIL | See the FAIL table. |
| C11 | PASS | Fresh venv `make test` exits 0. |
| C12 | PASS | Both orders, judge id recorded, flip and pos-1 rates shown. |
| C13 | PASS | Every price that is used has a URL and a date. DeepSeek is unpriced, not mispriced (C4). |

## Rulings on open disagreements

1. **Entry row: O3c or E1 (Ali, bus 22:48Z, "or E1 if you prefer the 99.2%").** Ruling: **O3c.** E1 is selected on the scored gates, costs more than Claude ($15.12 vs $9.11 per 1k), and Kimi prefers Claude over it overall (30/51, p=0.026). Its 99% is the reward hack this checklist exists to catch. The pitch at HEAD already uses O3c. Keep it.
2. **"Facts: we win clearly" (Ali, bus 22:48Z) vs "facts about even" (README:9).** Ruling: **about even, leaning Claude.** We win clearly on the gates. Both independent judges lean Claude on facts for every pitched row, and neither result is significant. Say "on our gates" whenever the word "facts" goes with a win.
3. **Human A/B number to say on stage: 164 / p=0.024 or 195 / p=0.020.** Ruling: **whatever `human_votes.json` says at the freeze** (now 195 votes, 87 to 58, p=0.020). PITCH_2MIN:51 already says this.
4. **Does O3t count as "taste learned from humans"?** Ruling: **no, not as evidence.** It was written from votes on the same items. Its own judge style result is worse than O3c's. Call it an ablation.

## Next pass

Pass 3 re-runs: fresh-clone `make eval` diff (must be empty after L2h stops), the README:148 wording, the E1/E2 note, the F1H_real manifest, PRICES DeepSeek row, OVERVIEW Team, QA.md placeholders, `firectl` deployment list, and the public snapshot hash vs the form.
