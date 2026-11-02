# Workflow verify pass 3 of 3: O3m_glm_plainclaim and O3n_glm_frame (about 14:15 PT / 22:15 UTC, 2026-11-02)

Checker: a separate verifier. I built nothing in this workflow and I fixed nothing.
Checklist: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md). I checked only the rows this work touches. Earlier passes: [WORKFLOW_PASS1.md](WORKFLOW_PASS1.md), [WORKFLOW_PASS2.md](WORKFLOW_PASS2.md).
State checked: `origin/main` = `b137601`. Local `HEAD` = `7cd0e82` is an ancestor of it, and the only diff is the human A/B export. Every number below comes from a file I re-read or recomputed.

## Summary

| Status | Pass 2 | Pass 3 |
|---|---|---|
| PASS | 11 | 14 |
| FAIL | 4 | 4 |
| NOT-YET | 2 | 1 |

Verdict: **the goal was not met.** Neither variant raises style against Claude strong. O3m now has both eval judges in. It is worse than O3c on every column of both: Kimi style 15/54 vs 33/46, and Qwen style 31/31 vs 44/27. O3n fails the gate floor on eval_all. O3c stays the entry. Three of the four pass-2 fails are fixed. Two new fails come from a README that drops a disclosure and misstates the human result.

## Scores and deltas

Gates, recomputed from each row's `gates.pass`. The failing ids are the same as in passes 1 and 2:

| Split | O3c | O3m | delta | O3n | delta |
|---|---|---|---|---|---|
| eval_all (130) | 124 = 95.4% | 125 = 96.2% | +1 item | **122 = 93.8%** | -2 items |
| heldout (120) | 118 = 98.3% | 118 = 98.3% | 0 | 116 = 96.7% | -2 items |
| real (80) | 78 = 97.5% | 79 = 98.75% | +1 item | 78 = 97.5% | 0 |

Eval judges, both orders, eval_all, vs `hack_strong_claude-opus-5-5.jsonl`. These are read from the committed summaries `hackathon/report/judge{,2qwen}_hack_<sys>_vs_hack_strong_claude-opus-5-5.summary.json`:

| Judge | System | overall W/L/T | style W/L/T | facts W/L/T | n complete |
|---|---|---|---|---|---|
| Kimi K3 | O3c | 35/52/43 | 33/46/51 | 9/15/106 | 130 |
| Kimi K3 | O3m | 18/64/48 | **15/54/61** | **5/23/102** | 130 |
| Qwen 3.8 Max | O3c | 39/43/25 | 44/27/37 | 11/19/78 | 107 (19 unparsed) |
| Qwen 3.8 Max | O3m (**new**) | 24/50/35 | **31/31/46** | 5/20/83 | 109 (21 incomplete, 24 unparsed) |

New this pass: Qwen for O3m. The style edge O3c held on Qwen (net +17) goes to zero for O3m (net 0). O3n has no eval-judge run, and none is needed because it failed the floor.

Human A/B: only O3c and O3 were shown to readers. In `hackathon/report/human_ab.jsonl` on origin, O3c vs Claude strong stands at 53 / 80 / 31 tie (164 picks). By my sign test without ties that is p = 0.024. The committed `human_votes.json` (156 picks) reads 51 / 75 / 30, p = 0.040. Pass 1 cited 13/23/7 n.s., so the human lean to Claude is now significant. O3m and O3n have no human or spot-the-human data.

## Checklist rows

| id | Row | Status | Evidence |
|---|---|---|---|
| rule / F11 | No tuning on the eval judges | PASS | No change since pass 2. The dev judge is `glm-5p3` in every `hackathon/runs/dev/judge/*.summary.json`. Neither prompt contains "kimi", "qwen", "claude", "opus" or "gpt" (grep count 0 for both). No judge score fed a prompt. |
| F11 (disclosure) | Eval-shaped rules disclosed where readers look | **FAIL** (new) | Ali's contract `hackathon/bus/msgs/20261102T220102Z-ali-to-friend.md` asked README:145 to say that O3q's lint patterns, and possibly O3m's slogan and filler rules, "came from reading eval-judge *reasons*", and that O3n was quick-checked on dev-023, trick-06 and trick-07. README:145 on origin cut that sentence. It only links `hackathon/runs/dev/README.md`, where disclosures 2 and 3 live. Reading the eval judges' reasons is the closest this project came to the hard rule, so it belongs in the README, not one link away. Owner: Ruslan. |
| F5 | No frontier text in prompts | PASS | The prompts are unchanged since `fe1f4ef` (13:32). There are no frontier-model words in them, and the examples are the same as in `prompt_v2`. |
| J3 | Manifests present and repeatable | PASS | 6 manifests. All say `provider: fireworks`, `glm-5p3-flash`, loops 3, style_round basic. `prompt_sha256` is the sha256 of the stripped prompt text (`harness.py:631,653`). Recomputed: O3m `1dc3ce07ee2bc3b4` and O3n `0772e1efcbe1eb4f`, both matching. The commits 57a9d7ca, 0b3dd04b and 4744ec86 are all ancestors of origin/main. |
| E3 | Same ids as the eval files | PASS | All six run files have exactly the eval file's id set (130/120/80). |
| C5 | Clean outputs | PASS | 0 `<think`, 0 empty outputs. |
| gate floor | Gates >= 95% (O3m) | PASS | 96.2 / 98.3 / 98.75. |
| gate floor | Gates >= 95% (O3n) | **FAIL** (now disclosed) | eval_all is 122/130 = 93.8%, so the variant fails the floor. Pass-2 fail 1 is fixed: README:146 says "O3n missed its own gate floor ... Kept as a row, not pitched", and the dev README has the per-split table. The README gives held-out as 113/117 because it scores the pooled 117 items. The run file has 116/120 on all 120. Both are true. |
| push | Files pushed | PASS | All 16 deliverables (6 runs, 6 manifests, 2 prompts, 2 bus messages) are on origin/main with no local diff. |
| bus | Handoff sent | PASS | Both handoffs are on origin. Ruslan acked them in `20261102T215242Z-friend-to-ali.md`, and the Kimi and Qwen judging he was asked for is committed. The "~10%%" typo is cosmetic, and the bus message gives the real ratio. |
| C11 | Harness tests | PASS | `python3 -m unittest hackathon.harness.test_harness`: Ran 13 tests, OK. |
| E8 | O3m eval-judge numbers trace to a committed file | PASS (fixed) | The Kimi and Qwen summary, per-item and errors files for O3m are on origin. The per-item jsonl has 260 rows each, and my recount of item-level losses matches the summaries (Kimi facts 23, style 54; Qwen facts 20, style 31). |
| E10 | Every variant disclosed | PASS (fixed) | README:145 now says "15 harness variants (O3 to O3q)" and links the dev README. `excluded_runs.json` lists O3h, WF and R3. |
| F10 | O3m's wins are not sold as felt wins | PASS (fixed) | README:147 says "O3m is not a style gain" and gives both judges and the hashtag loss. Neither the pitch nor HEADLINE.md mentions O3m (`git grep` found nothing in `hackathon/pitch`). |
| F6 | Human A/B reported honestly | **FAIL** (new) | README:9 says the human test "leaned to Claude as well, not significantly". README:43 in the same file gives "51 / 75 / 30 ... sign test p=0.040", and the newer `human_ab.jsonl` gives 53/80/31, p = 0.024. At the usual 0.05 cut, that lean is significant. README:9 is stale and understates the loss, and `human_votes.json` lags `human_ab.jsonl` by 8 picks. Owner: Ruslan. |
| E6 | Significance on the new rows | PASS | Both O3m judge rows have sign-test p values in RESULTS.md:257 and :272. The Qwen row shows n = 109. |
| C4 | Cost includes dev spend | PASS | No change since pass 2: the dev README estimates about $1.00 and labels it "estimate, not from a bill". |
| goal | Style up vs Claude strong, gates >= 95% | **FAIL** | No variant from this workflow beats O3c on style on any judge. See the rulings. |
| spot-the-human | O3m vs real text | NOT-YET (and not needed) | It was asked for in the 21:38Z handoff and never run. I rule below that it is not worth the spend. |

## Failure examples (quoted from `evals/runs/hack_O3m_glm_plainclaim.jsonl`; both pass all four gates)

Pass 2 guessed that O3m's facts losses came from dropping hashtags. The per-item judge files are now committed, and they show that guess was wrong. Of the 23 Kimi facts losses, only 4 are hashtag-drop items (dev-068, 070, 076, 085). For Qwen it is 3 of 20. That is the base rate: 20 of the 130 items are hashtag drops, about 15%. The real cause is invented qualitative claims. They pass G1 because G1 checks only numbers, names, quotes and attributions.

- **dev-005.** The draft says Patchwork CI is "automatically detecting and quarantining flaky tests in GitHub Actions". O3m writes: `Patchwork CI watches your GitHub Actions pipeline, spots the tests that fail at random, and pulls them out of the way. Your team merges without reruns and ships faster.` "Without reruns" is a new product claim. Kimi's facts reason: `Rewrite 1 invents "watches your pipeline," "spots tests that fail at random," and "merges without reruns," none of which are in the draft`.
- **dev-001.** The draft says only "faster, smarter, and more accurate close". O3m writes: `closing the books takes less time and produces fewer errors ... which removes the usual month-end pressure on the finance team.` Kimi's reason: `Rewrite 1 adds "produces fewer errors" and "removes the usual month-end pressure," which are not in the draft`.
- **The source is O3m's own rule** (`prompt_O3m_glm_plainclaim.txt:7`): "Spend the freed words on how the product works, using only the draft's facts." When the draft has no mechanism, the model writes one. A reader at a law-sensitive client would notice. The gates do not.
- In fairness to O3c: the same blind spot exists there at a lower rate. On dev-001, O3c adds `spreadsheets everywhere, chasing mismatches`. Kimi still scores O3c's facts 9/15 vs Claude, compared with 5/23 for O3m.

## Rulings on open disagreements

1. **O3m vs O3c: which is better?** O3c. Both eval judges now agree. O3m loses overall, style and facts to Claude by more than O3c does, on Kimi (18/64, 15/54, 5/23) and on Qwen (24/50, 31/31, 5/20). Its +1 gate item and its drop in reader tells are proxy wins that no judge sees. Closed: O3m keeps its row and is never pitched.
2. **Why did O3m lose facts at 96% G1?** Invented mechanism sentences, not hashtag loss (see the examples). Ali should correct the "plausible reason" sentence in the dev README's Pass 3 section. Any later variant that tells the model to "say what happens" or "explain how it works" should be expected to fail this way.
3. **Run Qwen, Kimi or spot-the-human on O3n, or spot-the-human on O3m?** No. O3n failed the floor, and O3m lost on both judges. More spend cannot change the entry, so save the credits for the O7 run already going.
4. **Is the human A/B "not significant"?** No. With 164 picks it is 53/80/31, p = 0.024, and the committed json says p = 0.040. Report it as a significant human preference for Claude's prose, and still a fact-safety win for us. This is F6: report it whichever way it goes.
5. **Did anyone break the no-eval-judge-tuning rule?** No score from Kimi or Qwen was used. The reading of judge reasons is disclosed in the dev README but missing from the main README. That is a disclosure gap, not a breach. It must be closed before the freeze.
6. **Is the "~10%%" typo in the handoff worth a resend?** No. It is cosmetic.

## Fails (owner in brackets)

1. [Ruslan] README:145 is missing the contracted sentence on eval-shaped rules. Those rules are O3n's frame labels from eval items, the q-checks on dev-023, trick-06 and trick-07, and the O3q lint patterns plus possibly O3m's slogan rules taken from eval-judge reasons. Paste it from `20261102T220102Z-ali-to-friend.md` item 3.
2. [Ruslan] README:9 says the human A/B leaned to Claude "not significantly". README:43 says p = 0.040, and the newest export gives p = 0.024. Fix line 9, and regenerate `human_votes.json` from the current `human_ab.jsonl`.
3. [Ali] O3n is below the gate floor on eval_all (93.8%). The disclosure is now correct, so this is a closed fail: there is nothing to fix, only nothing to pitch.
4. [both] The workflow goal was not met. No variant improves style against Claude strong while keeping the gates at 95% or more. O3c stays the entry.

Side notes, not fails: `WORKFLOW_PASS1.md` and `WORKFLOW_PASS2.md` are still untracked and not on origin, so autopush does not pick up `hackathon/VERIFY/`. Also, the dev README's facts-loss hypothesis should be corrected (ruling 2).
