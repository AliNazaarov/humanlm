# Eval-check log (one line per feature gate)

| Time PT | Step | Check | Result |
|---|---|---|---|
| 11:33 | S1 stats | 9 unit tests; dry run on pre-event files (pre-event dry-run file, not part of the submission) | pass; numbers matched the then-committed pre-event report. Review: 2 HIGH fixed (mid-p +1 p-value, Clopper-Pearson for rates), NaN guard; 14 tests |
| 11:50 | S4 score_all | 6 unit tests; dry run on pre-event files (pre-event dry-run file, not part of the submission) | pass; reproduced the then-committed pre-event figures offline in 2.6 s |
| 12:05 | S4 v2 score_all (plan v2 gates) | 8 tests; dry run baseline_frontier on 250-item frame | pass. Persona frontier passes all gates on 7% [3, 13] of main items (G1 59%, G2 12%, G3 99%, G4 25%); secondary metrics unchanged (53/130 fails, 70% in range) |
