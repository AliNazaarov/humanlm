# Prices used for cost_usd

`hackathon/eval/run_frontier.py` reads this table. A row must match the `--provider` and `--model` passed to the script exactly, and both prices must be plain numbers in USD per 1M tokens. A missing row or a `TODO` makes the script stop with an error (unless `--price-in`/`--price-out` are passed on the command line, which should then be copied here).

Fill each row from the provider's official pricing page on the day of the run. Do not estimate.

| provider | model | $/1M input | $/1M output | source URL | date read |
|---|---|---|---|---|---|
| anthropic | claude-opus-5-5 | 4 | 20 | https://platform.claude.com/docs/en/about-claude/pricing (redirect from docs.anthropic.com/en/docs/about-claude/pricing); base input/output, no caching | 2026-11-02 |
| openai | TODO | TODO | TODO | TODO | TODO |
