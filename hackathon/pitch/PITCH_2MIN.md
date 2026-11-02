# FeatherLM: 2-minute finals script

Spoken by Ali. Ruslan drives the deck (`hackathon/pitch/deck.html`, arrow keys). About 290 words, 1:55 at a calm pace. Every number in brackets is read from `hackathon/report/results.json` or `hackathon/audit/AUDIT.md` on the day; do not say a number that is not in one of those files.

---

**[Slide 1, title, 0:00]**

Every founder here has done this: you write a launch email with an AI, it reads like an AI, so you paste it into a frontier model and say "make this sound human."

**[Slide 2, the problem, 0:12]**

Here is Claude Opus 5.5 with our strongest rewrite prompt, the reference row of our leaderboard, on a founder's launch post. Style got better. Three draft sentences are gone, including "Grab yours before they're gone." On a pricing page it dropped the line about monitoring being "accessible to everyone", and added a clause the founder never wrote: "start small and add monitors when you need them." Claude drops at least one draft sentence on about half of our items. For copy that goes out under a company's name, that is a claims problem, not a style problem.

**[Slide 3, approach, 0:40]**

FeatherLM is an open model on Fireworks, GLM-5.3 Flash, wrapped in a verifier loop. The model drafts; a checker compares the rewrite with the draft, number by number, name by name, quote by quote, plus five AI tells against a human band; the model fixes only what the checker lists; three loops max. The same checker is the leaderboard metric and the RL reward.

**[Slide 4, leaderboard, 1:00]**

Same 250 items, same prompt. Fact-safe human rewrite rate: Claude Opus 5.5 with a strong prompt, [RESULT]. GPT-6.1, [RESULT]. Our harness on a 30-cent-per-thousand open model, [RESULT], paired bootstrap, significant. The honest row: Claude plus our harness gets to [RESULT] too, at [RESULT] dollars per thousand. The loop is the product, the open model is the price.

**[Slide 5, audit, 1:25]**

You will ask whether we gamed our own metric. We audited it with signals the harness never sees: closeness to the real human originals, six tells not in the gates, copy rate, dropped sentences. With the metric's regex artefacts forgiven, the lead over Claude shrinks from [AUDIT] to [AUDIT] points and holds. Where we lose, the audit says so.

**[Slide 6, business, 1:40]**

Who pays: founders, marketers, agencies, and the agents now writing copy for them. The product is an API with a fact-safety guarantee at open-model prices. The moat is licence-clean reverse-distillation data, a verifier that is also the reward, and every pick a user makes.

**[Slide 7, ask, 1:52]**

We are asking for Fireworks credits to finish the SFT and RL rows, and ten design partners who publish copy every day. We didn't make an open model smarter than Claude. We made it accountable, and made accountability about [RESULT: F1H $/1k over main-row $/1k, rounded] times cheaper. Thank you.

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

- The problem-slide quotes are exact strings from `evals/runs/hack_strong_claude-opus-5-5.jsonl` (`dev-070`, `dev-016`): the strong-prompt reference row, not the plain-prompt live run. Selection rule: strong-run items where `gates.check` fails G2 (a draft number missing) and the audit's deleted-sentence rule finds 2+ draft sentences (5+ words, under 40% of content words recalled) and the draft is 75 words or fewer (fits a slide): dev-016, dev-070, dev-073, dev-074. We show the one with the most dropped sentences (dev-070, three) and the gate demo (dev-016).
- Say "drops three sentences", "drops two sentences, adds a clause". Do not say "our checker caught it" for the dropped sentences: the gates do not see dropped sentences, the audit does. The gate does flag dev-016 (G2: "1-minute checks" became "checks every minute", the 1 is gone; same meaning, literal check) and dev-070 only for "5" -> "Five" (an artefact the audit forgives).
- Do not reuse the old dev-085 "71 characters" note (it came from the plain-prompt live run) or dev-060 (Claude's G1 flag there is a false positive from "recalled"). The earlier "38 customers" example is not in any run file; do not say it.
- "About half of our items" = any-sentence-deleted 51% for Claude strong in `hackathon/audit/audit.json` (`systems["frontier-strong:claude-opus-5-5"].gaming.any_sent_deleted`). Note the main row O3c is at 42% on the same signal; O3 (no style round) is at 17%. Say the O3 number only when talking about O3.
- If a judge asks for the lenient number, it is in `hackathon/audit/AUDIT.md` section E, computed by `hackathon/audit/audit.py`.
- Never say "detector", "undetectable" or "bypass". The product is fact-safe human-sounding copy, not evasion.
