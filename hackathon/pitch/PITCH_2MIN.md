# FeatherLM: 2-minute finals script

Spoken by Ali. Ruslan drives the deck (`hackathon/pitch/deck.html`, arrow keys). About 290 words, 1:55 at a calm pace. Every number in brackets is read from `hackathon/report/results.json` or `hackathon/audit/AUDIT.md` on the day; do not say a number that is not in one of those files.

---

**[Slide 1, title, 0:00]**

Every founder here has done this: you write a launch email with an AI, it reads like an AI, so you paste it into a frontier model and say "make this sound human."

**[Slide 2, the problem, 0:12]**

Here is what came back on one of our eval items. The draft is Google-ads copy for an uptime tool. Claude Opus 5.5 cleaned the style and then appended this: "Note: The rewritten Description 3 is 71 characters." A number that was never in the draft, inside copy that was about to be published. On another item it cut "Worth it? 100%" and "Because trust is everything" out of a founder's post. Style got better. The claims changed. For marketing copy that is an FTC problem, not a style problem.

**[Slide 3, approach, 0:40]**

FeatherLM is an open model on Fireworks, GLM-5.3 Flash, wrapped in a verifier loop. The model drafts; a checker compares the rewrite with the draft, number by number, name by name, quote by quote, plus five AI tells against a human band; the model fixes only what the checker lists; three loops max. The same checker is the leaderboard metric and the RL reward.

**[Slide 4, leaderboard, 1:00]**

Same 250 items, same prompt. Fact-safe human rewrite rate: Claude Opus 5.5 with a strong prompt, [RESULT]. GPT-6.1, [RESULT]. Our harness on a 30-cent-per-thousand open model, [RESULT], paired bootstrap, significant. The honest row: Claude plus our harness gets to [RESULT] too, at [RESULT] dollars per thousand. The loop is the product, the open model is the price.

**[Slide 5, audit, 1:25]**

You will ask whether we gamed our own metric. We audited it with signals the harness never sees: closeness to the real human originals, six tells not in the gates, copy rate, dropped sentences. With the metric's regex artefacts forgiven, the lead over Claude shrinks from [AUDIT] to [AUDIT] points and holds. Where we lose, the audit says so.

**[Slide 6, business, 1:40]**

Who pays: founders, marketers, agencies, and the agents now writing copy for them. The product is an API with a fact-safety guarantee at open-model prices. The moat is licence-clean reverse-distillation data, a verifier that is also the reward, and every pick a user makes.

**[Slide 7, ask, 1:52]**

We are asking for Fireworks credits to finish the SFT and RL rows, and ten design partners who publish copy every day. Thank you.

---

## Timing marks

| Slide | Start | Words |
|---|---|---|
| 1 Title | 0:00 | 35 |
| 2 Problem | 0:12 | 85 |
| 3 Approach | 0:40 | 60 |
| 4 Leaderboard | 1:00 | 65 |
| 5 Audit | 1:25 | 45 |
| 6 Business | 1:40 | 40 |
| 7 Ask | 1:52 | 25 |

## Before you say it

- The problem-slide quotes are exact strings from `evals/runs/hack_live_claude-opus-5-5.jsonl` (`dev-085`, `dev-060`). The earlier draft of this pitch used a "38 customers" example; no frontier row in the run files changes that number, so do not say it.
- If a judge asks for the lenient number, it is in `hackathon/audit/AUDIT.md` section E, computed by `hackathon/audit/audit.py`.
- Never say "detector", "undetectable" or "bypass". The product is fact-safe human-sounding copy, not evasion.
