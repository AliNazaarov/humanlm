# FeatherLM pitch, rewritten by FeatherLM itself (O3c: GLM-5.3 Flash on Fireworks + harness)

Each speaker block was passed through our own entry system (prompt_v2, --loops 3, --style-round). Every block passed all four gates: no number, name or quote added or lost. Compare with `PITCH_2MIN.md` and use whichever reads better.

**[Slide 1, title, 0:00] ALI**

Anyone can ship an app overnight now. Features are cheap. What's hard is distribution: getting real people to read what you send.

And they've stopped trusting AI-written text. When AI "polishes" your copy, it drops lines and changes facts. Most businesses and nonprofits can't take that risk, or frontier prices on every email.

FeatherLM makes outreach copy read like a person wrote it. It keeps every fact, at about a tenth of the cost.

_gates: pass=True, revision rounds 2_

**[Slide 2, the problem, 0:10] ALI**

Claude Opus 5.5 handled our strongest rewrite prompt well. The style got better. But it dropped three sentences from a draft, and on a pricing page it added a clause the founder never wrote. That happens on about half our items: at least one sentence gone. When copy goes out under a company's name, that is a claims problem.

_gates: pass=True, revision rounds 1_

**[Slide 3, solution, 0:30] RUSLAN**

FeatherLM is an open model on Fireworks, GLM-5.3 Flash, inside a verifier loop. The model drafts; a checker compares the rewrite with the draft, number by number, name by name, quote by quote, plus AI tells against a human band; the model fixes only what failed; three rounds max. The checker is also our leaderboard metric, so we audited it with signals the loop never sees.

_gates: pass=True, revision rounds 1_

**[Slide 4, leaderboard, 0:55] ALI**

We ran the same 247 items through the same prompt. Claude, with a strong prompt, rewrote 71 percent of them without breaking facts. FeatherLM hit 97 percent. And it costs 81 cents per thousand rewrites against 9 dollars 11, roughly 11 times less. On 80 real GitHub READMEs we never tuned on, it scored 98 against 76. Put Claude inside our setup and it reaches 94, so the setup is doing the work. Fireworks just makes it cheap. An ensemble gets to 99. The same setup on DeepSeek reaches 95, so it transfers across model families.

_gates: pass=True, revision rounds 2_

**[Slide 6, style, 1:25] ALI**

On style, we lose. In a blind test, 41 readers picked Claude's prose, 87 votes to 58, p 0.02. One judge model leans Claude, another leans us. And readers flag choppy fragments in ours far more often.

_gates: pass=True, revision rounds 1_

**[Slide 8, next step, 1:40] RUSLAN**

Next step: training toward real human writing. Today we trained three SFT models on Fireworks, plus a local DPO model where the real human original is the preferred answer. Serving fine-tunes needs a dedicated deployment, so we can only evaluate one. That's the one we're asking for.

_gates: pass=True, revision rounds 1_
