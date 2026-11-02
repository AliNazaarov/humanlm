# FeatherLM: 50-second demo video

One take, screen recording, no music. Ruslan records; voice-over below. Fill every `[NUMBER]` from `hackathon/report/results.json` (or `HEADLINE.md`) at the 15:00 freeze, never from memory. Show `hackathon/demo/demo.ipynb` for shots 1–3 and `hackathon/report/leaderboard.png` for shot 4.

| Time | Screen | Voice-over |
|---|---|---|
| 0–8 s | Notebook: the dev-060 draft (Shelfwise recall post). Highlight "400 labels", "$7,000", "Worth it? 100%", "Because trust is everything". | "Founders paste AI drafts into a frontier model to make them sound human. This one has four claims that must survive." |
| 8–20 s | Claude Opus 5.5's rewrite next to it. Circle where "Worth it? 100%" and "Because trust is everything" disappeared; show the gate problem line. | "Claude cleans the style, and quietly drops two of the founder's own claims. In marketing copy, that's a changed claim." |
| 20–30 s | FeatherLM's rewrite: every claim kept, emoji and filler gone; gate line shows all four checks pass. | "FeatherLM, an open model on Fireworks inside a verify-and-revise loop, keeps every fact and removes the tells." |
| 30–45 s | Leaderboard chart. Point at the FeatherLM bar, Claude's bar, and the cost column. | "On 250 items: FeatherLM [O3c strict]% fact-safe, Claude Opus [F1 strong strict]%. Plus [Δ lenient] points even when we forgive harmless edits, significant. At [O3c $/1k] dollars per thousand rewrites, against [F1H $/1k] for Claude inside the same loop." |
| 45–50 s | README top: repo URL, "Built today: hackathon/". | "An LLM judge still prefers Claude's prose on some drafts; it's in the report. Open model, Fireworks, repo below." |

## Rules
- Use the dev-060 example, not dev-085 (on dev-085 FeatherLM barely edits; showing it would oversell).
- Say the judge caveat out loud; it is the honest counterweight to the headline.
- Under 60 s. Export, upload (YouTube unlisted or the form's upload), add the link to README and the form.
