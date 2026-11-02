# Eval-check log (one line per feature gate)

| Time PT | Step | Check | Result |
|---|---|---|---|
| 11:33 | S1 stats | 9 unit tests; fact hard-fails on committed outputs, frontier-persona vs lora_v1, joined to eval_all by id | pass. Fails 53 vs 6 (matches CONTEXT.md). Exact CI 0.408 [0.322, 0.497] vs 0.046 [0.017, 0.098]; paired bootstrap diff 0.362 [0.269, 0.454]. Review: 2 HIGH fixed (mid-p +1 p-value, Clopper-Pearson for rates), NaN guard; 14 tests |
