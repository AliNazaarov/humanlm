# LinkedIn post (Ruslan), results after the event. Image: hackathon/report/leaderboard.png

Numbers: hackathon/report/results.json, block "all", 247 items (O3c 96.8% strict fact-safe, Claude Opus 5.5 strong prompt 71.3%; cost per 1k rewrites $0.81 vs $9.11). Human test: hackathon/report/human_votes.json, frozen at 15:15 PT (45 readers, 209 picks: Claude 89, FeatherLM 64, about the same 56; sign test p=0.052). Re-check both before posting.

---

I spent today at Fireworks Deploy in SF with Ali, and 45 of you gave us a few minutes of your eyes. Thank you.

The problem we worked on: ask an AI to "make this sound more human" and it will. It will also cut lines you needed, and sometimes change a number or add a claim you never made.

So we built FeatherLM, an open model running on Fireworks that rewrites AI marketing copy so it reads like a person wrote it and keeps the facts as they were. A checker flags any new or missing numbers and names, and the model fixes them before you ever see the text.

On 247 held-out rewrites, 96.8% of ours came back fact-safe and free of the usual AI tells. Claude Opus 5.5 with a strong prompt landed at 71.3%. Ours costs $0.81 per 1,000 rewrites; Claude costs $9.11.

And the part I promised to share either way: in the blind test, you leaned toward Claude's voice, 89 picks to 64. Your notes told us why. Our rewrites read like "every LinkedIn post nowadays": short punchy fragments, slogan endings. That's the next thing we're fixing.

Facts we can check by machine. Taste we have to earn from readers. Thanks for helping with the second one.

@Fireworks AI @NVIDIA @Microsoft #FireworksDeploy
