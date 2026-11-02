# Workflow verify pass 1 of 3: O3m_glm_plainclaim and O3n_glm_frame (13:42 PT, 2026-11-02)

Checker: separate verifier. I built nothing in this workflow and I fixed nothing.
Checklist: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md). I checked only the rows this work touches.
State checked: `main` = `origin/main` = `a0d767d` (autopush at 13:42:30). Every number below comes from a file I re-read or recomputed.

## Summary

| Status | Count |
|---|---|
| PASS | 9 |
| FAIL | 4 |
| NOT-YET | 3 |

Verdict: **O3m passes the gate floor. O3n does not.** Neither variant shows a style gain yet. The dev judge shows no gain, and the eval judges have not run.

## Scores, recomputed from the run files (`gates.pass` per row)

| Split | O3c (last main row) | O3m | delta | O3n | delta |
|---|---|---|---|---|---|
| eval_all (130) | 124 = 95.4% | 125 = 96.2% | +1 item | **122 = 93.8%** | -2 items |
| heldout (120) | 118 = 98.3% | 118 = 98.3% | 0 | 116 = 96.7% | -2 items |
| real (80) | 78 = 97.5% | 79 = 98.75% | +1 item | 78 = 97.5% | 0 |

The failing ids match both reports exactly. O3m fails dev-023, dev-037, dev-046, dev-060, trick-06, ho-037, ho-097 and rr-016. O3n fails dev-001, dev-023, dev-034, dev-046, dev-080, trick-05, trick-06, trick-07, ho-018, ho-035, ho-037, ho-054, rr-011 and rr-016.

Dev style, from the GLM-5.3 dev judge on dev-031..070 against Claude strong (files in `/private/tmp/devjudge_*.summary.json`, all `model: accounts/fireworks/models/glm-5p3`):

| System | style W/L/T | overall W/L/T |
|---|---|---|
| O3c | 16/18/6 | 12/18/10 (13/19/8 on a rerun) |
| O3m | 12/14/14 | 12/15/13 |
| O3n | 7/25/8 | 9/24/7 |
| O3p_glm_positive (dev only, dropped) | 8/21/11 | 6/20/14 |

Two runs of the O3c dev judge give overall results one item apart, so ±1 is noise at n=40.

## Checklist rows

| id | Row | Status | Evidence |
|---|---|---|---|
| F11/rule | No tuning on the eval judges | PASS | Both dev summaries record judge `glm-5p3`. There is no "kimi" or "qwen" in the dev logs, the full-run logs or either prompt (grep rc=1). |
| F5/rule | No frontier text in prompts | PASS | `diff prompt_v2.txt` shows only new rule bullets in both prompts. The three examples and the banned list are unchanged. Neither prompt names Claude, Opus or GPT. |
| J3 | Manifests present and repeatable | PASS | There are 6 manifests, all `provider: fireworks`, model `glm-5p3-flash`. `prompt_sha256` matches sha256(file.strip()) as the harness computes it (harness.py:631,653): O3m `1dc3ce07ee2bc3b4`, O3n `0772e1efcbe1eb4f`. Commits 57a9d7ca, 0b3dd04b and 4744ec86 are all ancestors of origin/main. |
| E3 | Same ids as the eval files | PASS | All six run files have exactly the eval file's id set: 130/120/80. |
| C5 | Clean outputs | PASS | 0 `<think`, 0 empty outputs and `empty_outputs: []` in every manifest. |
| gate floor | Gates >= 95% (O3m) | PASS | 96.2 / 98.3 / 98.75. |
| gate floor | Gates >= 95% (O3n) | **FAIL** | eval_all 122/130 = 93.8%. The handoff discloses it. The total of 95.8% must not be used to cover the main-split miss. |
| push | Files pushed | PASS (late) | At 13:4x, before autopush, the O3m heldout files and all six O3n files were untracked. At `a0d767d` all 16 deliverables (runs, manifests, prompts, both bus messages) are on origin/main with no local diff. The run logs are not: `hackathon/runs/logs/` is gitignored (.gitignore:19), and the O3m logs are in /tmp. |
| bus | Handoff sent | PASS | `20261102T213803Z-ali-to-friend.md` and `20261102T213847Z-ali-to-friend.md` are on origin. Their dev numbers match the /tmp summaries. The cosmetic `%%` typo in the O3m message is disclosed. |
| C11 | Harness tests | PASS | `python3 -m unittest hackathon.harness.test_harness`: Ran 13 tests, OK. |
| C4 | Row cost | PASS (rows) | `cost_usd` is 0 and the manifest prices are 0.0 for O3c, O3m and O3n alike. score_all.row_cost computes PRICES.md (glm-5p3-flash $0.15/$0.50) x logged tokens, so the rows are fine. The dev-check spend (dev generations plus GLM-5.3 judge calls for O3m, O3n, O3p and O3q) is not recorded anywhere. |
| E8 | Dev numbers trace to a committed file | **FAIL** | The handoff's dev figures exist only in `/private/tmp/dev_O3{m,n,p,q}_*.jsonl` and `/private/tmp/devjudge_*`. None of them is in the repo, so a reader cannot check them. |
| E10/F11 | Abandoned variants disclosed | **FAIL** | O3p_glm_positive (dev style 8/21/11) and O3q_glm_lint were built, dev-judged and dropped in the same window. Neither appears in README, BOARD, OPEN or any bus message. O3q shows up only as a harness.py comment (lines 240 and 437). README:139 still says "O3 to O3k". |
| F11 | Eval items used for tuning are disclosed | **FAIL** | The dev slice dev-031..070 is inside the reported eval_all split. That is known, but the README's count is stale. Also, O3n's frame rule names the labels "Subhead:" and "Primary text:", and neither appears in the dev slice. "Primary text:" occurs in 8 eval_all items (dev-080, dev-082 and others), 0 of them in dev-031..070. "Subhead:" occurs in 17, also 0 in the slice. So the prompt was likely shaped by eval items outside the dev slice. Disclose it, or show where the label list came from. |
| E10 | Every committed run has a row | NOT-YET | `results.json` was built at 13:16, before both runs. |
| F10 | Wins a reader would feel | NOT-YET | Waiting on Kimi K3, Qwen 3.8 Max and spot-the-human. See the rulings below. |
| goal | Style up vs Claude strong | NOT-YET (no dev signal) | On dev, O3m is net -2 on style, the same as O3c. O3n is net -18. |

## Failure examples (quoted from the run files)

- **O3n trick-07** (G1 and G3 fail). The output keeps `"...Thank you so much." — Margaret, Fitzroy` and the slogan `This is why we do what we do.` The new rule "keep every word ... with its attribution" overrides the em-dash ban and the slogan cleanup. The frame rules conflict with the style rules, which explains the extra G3 fails.
- **O3n dev-080** (G3 fail). The output reads `Primary text: If you're tired of the daily "what's for dinner?" struggle, meet Pebble Pantry ... turns chaotic evenings into stress-free family time.` Keeping the frame also kept the ad-speak.
- **O3m dev-023** (G1 fail). The output adds `Nordhaus Creative, a team of 45, is one of many agencies that rely on Tabwise`. The "say what actually happens" rule pushes the model to write a concrete-sounding claim, and the gate flagged it as invented.

## Rulings on open disagreements

1. **Is O3n a candidate?** No. eval_all is 93.8%, below the 95% floor, and dev style is 7/25. Keep the row (no cherry-picking), label it failed, and don't spend eval-judge budget on it unless the row needs judging to complete the table.
2. **Is O3m better than O3c?** Not shown. The gate gain is +1 item on eval_all and +1 on real, which is noise. Dev style net is -2 for both. Dev overall is -3 vs -6, but the O3c rerun moved by 1 and the handoff itself calls it "within noise". The only real change is that O3m writes about 10% shorter (len ratio 0.769 vs 0.850). Shorter text gives the model fewer chances to invent, so the gates can rise without a reader noticing anything. Claim nothing about style until Kimi, Qwen and the humans have judged it.
3. **The O3m name collides** with BOARD.md:87, where an earlier "O3m idea" meant register-matched shots plus a style card. Note in the README row that O3m_glm_plainclaim is the prompt-rules variant.

## Fails to fix (owner: Ali)

1. O3n is below the gate floor on eval_all (93.8%). Mark it as failed. Do not pitch it.
2. Commit the dev generation and dev-judge files for O3m, O3n, O3p and O3q (for example under `hackathon/runs/dev/`) so the handoff numbers trace to the repo.
3. Disclose O3p and O3q (dropped at dev) in the README ablation note. Update README:139 to cover O3l through O3q.
4. Disclose that O3n's frame rules name eval-item formats that are not in the dev slice, or show where the label list came from.
