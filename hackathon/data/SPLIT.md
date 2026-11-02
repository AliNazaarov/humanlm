# Split (built 2026-11-02 during the hackathon)

- Raw pairs read: 10827; kept after filters: 8890
- Dropped: {'quote_lost': 705, 'attribution_lost': 558, 'reported_speech': 574, 'duplicate': 100}
- Eval-overlap rule: drop a pair if its AI draft or human text shares 9+ consecutive words with dev/trick/frontier eval files
- Held out: 120 (`evals/heldout_pairs.jsonl`), the first 120 pairs by md5(pid)
- Valid: 200; Train: 5000 (news capped at 25%, max 5000)
- Train source mix: cccc_filtered 2905 (58%), news_filtered 847 (17%), project_gutenberg_filtered 426 (9%), public_domain_review_filtered 412 (8%), foodista_filtered 410 (8%)
- Licence: Common Pile filtered subsets (openly licensed / public domain). No frontier-model text in training.
- System prompt (same as pipeline/infer.py and every eval run): Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, correct grammar. Keep every fact, name and number. Add nothing.
