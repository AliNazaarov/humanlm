# Workflow verify pass 2 of 3: O3m_glm_plainclaim and O3n_glm_frame (13:56 PT, 2026-11-02)

Checker: separate verifier. I built nothing in this workflow and I fixed nothing.
Checklist: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md). I checked only the rows this work touches. Pass 1: [WORKFLOW_PASS1.md](WORKFLOW_PASS1.md).
State checked: local `HEAD` = `origin/main` = `fecce2b` (autopush 13:52). Every number below comes from a file I re-read or recomputed.

## Summary

| Status | Count |
|---|---|
| PASS | 11 |
| FAIL | 4 |
| NOT-YET | 2 |

Verdict: **the goal was not met.** O3m passes the gate floor, but the first eval judge rates its style clearly worse than O3c's. Kimi K3 gives O3m 15/54/61 against Claude strong (p=0.000), where O3c got 33/46/51 (p=0.177). O3m's wins are in the gates and the reader-tells count, and Kimi does not see them. That is the reward-hacking pattern this checklist row (F10) exists to catch. O3n is still below the floor on eval_all.

## Scores and deltas

Gates, recomputed from each row's `gates.pass` (unchanged since pass 1, same failing ids):

| Split | O3c | O3m | delta | O3n | delta |
|---|---|---|---|---|---|
| eval_all (130) | 124 = 95.4% | 125 = 96.2% | +1 item | **122 = 93.8%** | -2 items |
| heldout (120) | 118 = 98.3% | 118 = 98.3% | 0 | 116 = 96.7% | -2 items |
| real (80) | 78 = 97.5% | 79 = 98.75% | +1 item | 78 = 97.5% | 0 |

New since pass 1: the eval judge on eval_all, Kimi K3, both orders, vs `hack_strong_claude-opus-5-5.jsonl`. Source: `hackathon/report/results.json` `judges[]`, also in README:79 and RESULTS.md:264.

| System | overall W/L/T (p) | style W/L/T (p), flip rate | facts W/L/T (p) |
|---|---|---|---|
| O3c | 35/52/43 (0.086) | 33/46/51 (0.177), 0.369 | 9/15/106 (0.31) |
| O3m | **18/64/48 (0.000)** | **15/54/61 (0.000)**, 0.454 | **5/23/102 (0.001)** |
| delta | net -17 → -46 | net -13 → -39 | net -6 → -18 |

Proxy metrics that point the other way (`hackathon/report/reader_tells.json`, eval_all, share of outputs with any tell): O3c 37.7%, **O3m 14.6%**, O3n 36.9%, Claude strong 10.0%.

What I measured in the run files (eval_all, 130 items):

| | O3m | O3c | Claude strong |
|---|---|---|---|
| median output/draft word ratio | 0.766 | 0.864 | 0.880 |
| drafts with hashtags whose output drops all of them | **20/34** | 5/34 | 0/34 |
| drafts with a `Subject:` line whose output drops it | 1/36 | 0/36 | 0/36 |

Qwen 3.8 Max and spot-the-human for O3m, and every eval judge for O3n, are not in `results.json` yet.

## Checklist rows

| id | Row | Status | Evidence |
|---|---|---|---|
| rule / F11 | No tuning on the eval judges | PASS (with a caveat) | The dev judge is `glm-5p3` in all 7 summaries (`hackathon/runs/dev/judge/*.summary.json`). There is no "kimi" or "qwen" in either prompt (grep rc=1), in the three O3m logs in /tmp or in the three O3n logs. Caveat: `hackathon/runs/dev/README.md` disclosure 3 says the O3q lint patterns came from reading eval-judge *reasons*, and the O3m slogan/filler rules may share that source. No score was used, so this is not a breach, but it must be in the README (see FAIL 3). |
| F5 | No frontier text in prompts | PASS | The `diff prompt_v2.txt prompt_O3m_glm_plainclaim.txt` changes only one rule bullet and adds four new ones. The examples and the banned list are unchanged, and no Claude, Opus or GPT text appears. |
| J3 | Manifests present and repeatable | PASS | There are 6 manifests, all `provider: fireworks`, model `glm-5p3-flash`, `--loops 3`, style_round basic, T 0.7, top_p 0.9, max_tokens 1500, effort low. `prompt_sha256` matches the files (O3m `1dc3ce07ee2bc3b4`, O3n `0772e1efcbe1eb4f`). Commits 57a9d7ca, 0b3dd04b and 4744ec86 are ancestors of origin/main. |
| E3 | Same ids as the eval files | PASS | All six run files have exactly the eval file's id set (130/120/80). |
| C5 | Clean outputs | PASS | 0 `<think`, 0 empty outputs and `empty_outputs: []` in every manifest. |
| gate floor | Gates >= 95% (O3m) | PASS | 96.2 / 98.3 / 98.75. |
| gate floor | Gates >= 95% (O3n) | **FAIL** (unchanged) | eval_all is 122/130 = 93.8%. The README headline row reads "95% [92, 97]" because it pools 247 items (eval 130 + heldout 117). That pooled number hides the eval_all miss, and no README line marks O3n as failed. |
| push | Files pushed | PASS | The 16 deliverables (6 runs, 6 manifests, 2 prompts, 2 bus messages) are on origin/main with no local diff. The run logs are gitignored (.gitignore:19), or kept in /tmp for O3m, as disclosed. |
| bus | Handoff sent | PASS | `20261102T213803Z-ali-to-friend.md` and `20261102T213847Z-ali-to-friend.md` are on origin. Ruslan acknowledged both in `20261102T215242Z-friend-to-ali.md` ("Judging now: O3m Kimi + Qwen + spot-the-human; O3n queued"). |
| C11 | Harness tests | PASS | `python3 -m unittest hackathon.harness.test_harness`: Ran 13 tests, OK. |
| E8 (pass-1 fail 2) | Dev numbers trace to a committed file | PASS (fixed) | `hackathon/runs/dev/` holds the gen and judge files for O3c, O3m, O3n, O3p and O3q, plus a README with sha256 values. The table there matches pass 1. |
| C4 | Row cost, including dev spend | PASS | The dev README gives an estimate of about $0.17 for generation and $0.83 for the GLM-5.3 judge, and labels it "estimate, not from a bill". The row costs come from PRICES.md through score_all. |
| E10 | Every committed run has a row | PASS (fixed) | O3m and O3n are in `results.json`, HEADLINE.md and README:19/24. |
| E8 (new) | O3m eval-judge numbers trace to a committed file | **FAIL** | `results.json` `judges[18].file` = `hackathon/report/judge_hack_O3m_glm_plainclaim_vs_hack_strong_claude-opus-5-5.summary.json`. That file is not in the working tree or on origin/main (`git ls-tree` count 0), and neither is the per-item jsonl. README:79 cites numbers that a reader cannot check. Owner: Ruslan. |
| E10 / F11 (pass-1 fails 3 and 4) | Dropped variants and eval-shaped rules disclosed | **FAIL** (half fixed) | `hackathon/runs/dev/README.md` now discloses O3p and O3q, the O3n frame labels taken from eval items outside the dev slice, the q-check on dev-023/trick-06/trick-07 and the O3q lint source. But README:143 still says "About a dozen harness variants (O3 to O3k)". The README never mentions O3p or O3q and does not link the dev README. |
| F10 | Wins a reader would feel | **FAIL** (O3m) | See the rulings. The gates rise by 1 item and reader tells fall from 37.7% to 14.6%, yet Kimi style, overall and facts all get significantly worse. The headline table puts O3m above O3c with no note. |
| F6 / goal | Style up vs Claude strong, with Qwen and humans | NOT-YET | Qwen 3.8 Max and spot-the-human for O3m are queued (friend bus 21:52Z). O3n is not judged. The one eval judge in already says O3m is worse. |
| E6 | CI / significance on the new rows | NOT-YET | The O3m Kimi row has sign-test p values in results.json. The Qwen row is still missing. |

## Failure examples (quoted from `evals/runs/hack_O3m_glm_plainclaim.jsonl`; both pass all gates)

- **dev-059, the frame is cut.** The draft ends `Founders — when was the last time you raised your prices? 🤔` followed by `#SaaS #Pricing #StartupLessons #Growth #B2B`. O3m ends with `Customers pay for outcomes, not software. Price accordingly.` The closing question and all five hashtags are gone. O3c kept both, and Claude kept the hashtags. O3m's own prompt bans contrast pairs, and `outcomes, not software` is one, but the G3 gate passed it.
- **dev-039, the subject line is deleted.** The draft starts `Subject: Making Brightwater's New Office a Haven of Focus`. O3m starts at `Hi Jenna,`, so an email lost its subject line. The facts that remain (32 dB, 45 minutes, $6,400) are intact, so G1 passed.
- This pattern is systematic: O3m removes every hashtag from 20 of the 34 drafts that have hashtags. O3c does that 5 times and Claude never does. The prompt rule "Rebuild each paragraph around its facts instead of following the draft sentence by sentence" plus the "delete feeling sentences" rule produces shorter outputs (median ratio 0.766 vs O3c 0.864) that pass the gates but lose parts of the post. That is a plausible reason for the Kimi facts loss (5/23) even with G1 at 96%. I have not verified it item by item, because the per-item Kimi file is missing.

## Rulings on open disagreements

1. **Is O3m better than O3c?** No. The gates move by +1 item on two splits, which is noise. The one eval judge in reverses the style lean, from 33/46 n.s. to 15/54 (p=0.000), and facts go from 9/15 n.s. to 5/23 (p=0.001). O3c stays the entry. O3m keeps its row (no cherry-picking), but its headline line needs a note saying it loses style and facts to Claude on Kimi. Don't spend more on O3m beyond the Qwen and human judging already queued. Those results get reported whichever way they come out.
2. **Reader tells 14.6% vs 37.7%: is it a win?** No, not as a claim. reader_tells.json calls itself "post-hoc diagnostic from set 1 reader notes; not a headline gate". O3m's new rules target the same tell kinds (slogan, tagline, rhetorical Q&A, contrast), and the diagnostic was committed at 21:24Z, 8 minutes before the O3m prompt (21:32Z). So the drop is at least partly the prompt learning to avoid a list built from eval-item notes, not readers liking the text more. Do not quote it in the pitch as a style result.
3. **Is O3n a candidate?** No. This ruling is unchanged from pass 1: eval_all is 93.8%. The pooled "95%" in the headline must not be read as clearing the floor. Judge it only if the table needs it, and label it failed.
4. **Did O3m break the no-eval-judge-tuning rule?** No score from Kimi or Qwen was used, so there is no breach. But the dev README admits the lint and slogan patterns came partly from reading eval-judge reasons on eval items. Disclose that in the README limitations next to the F11 note. Treat O3m's eval_all numbers as optimistic. Its real-split numbers are the cleaner check.

## Fails to fix (owner in brackets)

1. [Ali] O3n is below the gate floor on eval_all (93.8%). Add a README note marking it failed, because the pooled 95% hides the miss.
2. [Ruslan] Commit `hackathon/report/judge_hack_O3m_glm_plainclaim_vs_hack_strong_claude-opus-5-5.{summary.json,jsonl,errors.jsonl}`. README:79 and results.json cite it, but it is not in the repo.
3. [Ali] Update README:143 to cover O3l through O3q, link `hackathon/runs/dev/README.md`, and copy disclosures 1 to 3 from it (eval-shaped frame labels, eval-item q-checks, lint and slogan rules taken from eval-judge reasons).
4. [both] F10: annotate the O3m headline row, or the text under it, with Kimi style 15/54 and facts 5/23 vs Claude, and the hashtag loss (20/34). Do not pitch O3m's gates or its reader-tells drop as a style gain.

Side note: `hackathon/VERIFY/WORKFLOW_PASS1.md` is untracked locally and not on origin yet. Autopush should pick it up. This is not a workflow deliverable.
