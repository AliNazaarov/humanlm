# FeatherLM: 2-minute finals script (final numbers)

Two speakers. **Ali**: problem and proof. **Ruslan**: solution and next step. Deck: `hackathon/pitch/deck.html` (8 slides, arrow keys). About 300 words. Every number below is listed with its source in `hackathon/pitch/FINAL_CHECK.md`; do not say a number that is not there.

---

**[Slide 1, title, 0:00] ALI**

Every founder here has done this: an AI writes your launch email, it reads like an AI, so you paste it into Claude and say "make this sound human."

**[Slide 2, the problem, 0:10] ALI**

Here is Claude Opus 5.5 with our strongest rewrite prompt. The style got better. Three draft sentences are gone. On a pricing page it added a clause the founder never wrote. Claude drops at least one draft sentence on about half of our items. For copy that goes out under a company's name, that is a claims problem.

**[Slide 3, solution, 0:30] RUSLAN**

FeatherLM is an open model on Fireworks, GLM-5.3 Flash, inside a verifier loop. The model drafts; a checker compares the rewrite with the draft, number by number, name by name, quote by quote, plus AI tells against a human band; the model fixes only what failed; three rounds max. The checker is also our leaderboard metric, so we audited it with signals the loop never sees.

**[Slide 4, leaderboard, 0:55] ALI**

Same 247 items, same prompt. Fact-safe rewrite rate: Claude with a strong prompt, 71 percent. FeatherLM, 97 percent, at 81 cents per thousand rewrites against 9 dollars 11: about 11 times cheaper. On 80 real GitHub READMEs we never tuned on: 98 against 76. Claude inside our harness gets to 94, so the harness is the contribution and Fireworks makes it cheap. An ensemble reaches 99; the same harness on DeepSeek reaches 95, so it transfers across model families.

**[Slide 6, style, 1:25] ALI**

On style it is not a win. In a blind test, 41 readers preferred Claude's prose, 87 votes to 58, p 0.02. One judge model leans Claude, another leans us. Readers flag choppy fragments in ours far more often.

**[Slide 8, next step, 1:40] RUSLAN**

So the next step is training toward real human writing. We trained three SFT models on Fireworks today and a local DPO model where the real human original is the preferred answer. Serving fine-tunes needs a dedicated deployment, so only one is evaluated; that is what we are asking for.

**[1:55] ALI**

We didn't make an open model smarter than Claude. We made it accountable, and made accountability about 20 times cheaper.

---

## Timing marks

| Slide | Speaker | Start |
|---|---|---|
| 1 Title | Ali | 0:00 |
| 2 Problem | Ali | 0:10 |
| 3 Solution | Ruslan | 0:30 |
| 4 Leaderboard (skip 5 Audit unless asked) | Ali | 0:55 |
| 6 Style | Ali | 1:25 |
| 8 Next step + close | Ruslan, then Ali | 1:40 |

## Before you say it

- "About 11 times cheaper" = Claude strong $9.11 / FeatherLM $0.81 per 1k (11.3). "About 20 times cheaper" (closing line) = Claude inside our harness $15.85 / FeatherLM $0.81 (19.7): the accountable version of Claude against ours. Both from `results.json: systems[].cost_per_1k_usd`.
- Human A/B is 195 votes from 41 readers in `human_votes.json` (O3c vs Claude strong): ours 58, Claude 87, both fine 50, sign test p=0.020. Say "87 votes to 58"; do not say 164 or p=0.024 (not in the current file).
- Judges on O3c: Kimi K3 style 33/46/51 (leans Claude, p=0.177 n.s.); Qwen 3.8 Max style 44/27/37 (leans ours, p=0.057 n.s.). Do not say either judge "prefers" significantly.
- The problem-slide quotes are exact strings from `evals/runs/hack_strong_claude-opus-5-5.jsonl` (dev-070, dev-016). "About half" = audit `any_sent_deleted` 51% for Claude strong.
- R3 (DeepSeek) has no cost row in results.json; do not quote a price for it.
- Never say "detector", "undetectable" or "bypass".
