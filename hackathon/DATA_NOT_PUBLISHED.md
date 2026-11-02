# Data in this public snapshot

Published: all evaluation data (`evals/`: 130 eval drafts, held-out pairs with per-row licences, 80 real GitHub README intros), every run output (`evals/runs/`), manifests (`hackathon/runs/`), judge and human-vote results (`hackathon/report/`), and all code.

Not published: the bulk training pairs (`data/pairs/`, `hackathon/data/train*.jsonl`, DPO pair files). They are reverse-distillation pairs built from Common Pile's openly licensed subsets, and per-document licences for the CC-web rows are not yet confirmed one by one, so we don't redistribute them. Regenerate them with `pipeline/fetch.py` → `passages.py` → `shard.py` → `gen_pairs.py`, then `hackathon/data/make_split.py` (deterministic; counts and the leakage rule are in `hackathon/data/SPLIT.md`).

Three held-out items (ho-007, ho-027, ho-071) whose licence could not be established are removed from this snapshot and excluded from all scoring.
