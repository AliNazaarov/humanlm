# Prices used for cost_usd

`hackathon/eval/run_frontier.py` reads this table. A row must match the `--provider` and `--model` passed to the script exactly, and both prices must be plain numbers in USD per 1M tokens. A missing row or a `TODO` makes the script stop with an error (unless `--price-in`/`--price-out` are passed on the command line, which should then be copied here).

Fill each row from the provider's official pricing page on the day of the run. Do not estimate.

| provider | model | $/1M input | $/1M output | source URL | date read |
|---|---|---|---|---|---|
| anthropic | claude-opus-5-5 | 4 | 20 | https://platform.claude.com/docs/en/about-claude/pricing (redirect from docs.anthropic.com/en/docs/about-claude/pricing); base input/output, no caching | 2026-11-02 |
| openai | gpt-6.1-terra | 1 | 5 | https://openai.com/api/pricing/ (redirects to openai.com/business/pricing/#api); Standard processing, context <272K; cache read $0.05/1M not used; Batch -50% not used | 2026-11-02 |
| fireworks | accounts/fireworks/models/glm-5p3-flash | 0.15 | 0.50 | https://docs.fireworks.ai/serverless/pricing; Standard tier, global (not US-only); cached input $0.03/1M not used; Priority/US/batch (50%) tiers not used | 2026-11-02 |
| fireworks | accounts/fireworks/models/kimi-k3 | 3.00 | 15.00 | https://docs.fireworks.ai/serverless/pricing; Standard tier, global (not Fast/US); cached input $0.30/1M not used; Priority/batch (50%) tiers not used | 2026-11-02 |
| fireworks | accounts/fireworks/models/glm-5p3 | 1.40 | 4.40 | https://docs.fireworks.ai/serverless/pricing (Standard tier; selection/dev judge, R2 claim check) | 2026-11-02 |
| fireworks | accounts/fireworks/models/qwen3p8-max | 2.00 | 6.00 | https://docs.fireworks.ai/serverless/pricing (Standard tier; second eval judge) | 2026-11-02 |
