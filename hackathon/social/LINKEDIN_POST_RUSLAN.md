# LinkedIn post (Ruslan), live blind test call. Image: hackathon/report/leaderboard.png or a phone showing the test page

Numbers: hackathon/report/results.json, block "all", 247 items (O3c 96.8% strict fact-safe, Claude Opus 5.5 strong prompt 71.3%; cost per 1k rewrites $0.81 vs $9.11). Human test lean: hackathon/report/human_ab.jsonl (11 readers at 13:10 PT; the laptop clock is UTC-7 and showed 14:10). Re-check both before posting.

---

I'm at Fireworks Deploy in SF today with Ali, and I'd love 4 minutes of your eyes.

The problem: ask an AI to "make this sound more human" and it will. It will also cut lines you needed, and sometimes change a number or add a claim you never made.

So we're building FeatherLM, an open model running on Fireworks that rewrites AI marketing copy so it reads like a person wrote it and keeps the facts as they were. A checker flags any new or missing numbers and names, and the model fixes them before you ever see the text.

On 247 held-out rewrites, 96.8% of ours come back fact-safe and free of the usual AI tells. Claude Opus 5.5 with a strong prompt lands at 71.3%. Ours costs $0.81 per 1,000 rewrites; Claude costs $9.11.

But scores aren't taste. So we're asking real people which rewrite actually sounds human. It's blind, 5 pairs, about 4 minutes on your phone, no signup:
https://featherlm-ab.vercel.app/

Honest update: so far readers lean slightly toward Claude's voice, which is exactly why we want more of you. Results at 4:30, and I'll share them here either way.

@Fireworks AI @NVIDIA @Microsoft #FireworksDeploy
