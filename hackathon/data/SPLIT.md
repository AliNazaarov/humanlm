# Split (built 2026-11-02 during the hackathon)

- Raw pairs read: 10827; kept after filters: 8728
- Dropped: {'quote_lost': 705, 'attribution_lost': 558, 'reported_speech': 574, 'eval_overlap': 162, 'duplicate': 100}
- Eval-overlap rule: drop a pair if its AI draft or human text shares 8+ consecutive words with dev/trick/frontier eval files
- Held out: 120 (`evals/heldout_pairs.jsonl`), the first 120 pairs by md5(pid)
- Valid: 200; Train: 5000 (news capped at 25%, max 5000)
- Train source mix: cccc_filtered 2924 (58%), news_filtered 852 (17%), project_gutenberg_filtered 424 (8%), foodista_filtered 406 (8%), public_domain_review_filtered 394 (8%)
- Remaining eval overlap in train/valid: 0
- Licence: Common Pile filtered subsets (openly licensed / public domain). No frontier-model text in training.
- System prompt (same as pipeline/infer.py and every eval run): Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, correct grammar. Keep every fact, name and number. Add nothing.
