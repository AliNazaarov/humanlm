# LinkedIn post (social prize: tag Fireworks, NVIDIA, Microsoft; reach 20 likes + 10 reshares)

## Post 1: now (what we're building). Image: a photo of us at TERRA with the laptop showing the agent bus or the eval table

I'm at Fireworks Deploy in SF today with Ruslan, building something that bugs me every week.

You ask an AI to "make this sound more human." It does. It also quietly cuts lines from your copy, and sometimes changes a number or adds a claim you never made.

We measured it on 250 marketing rewrites. A top frontier model dropped at least one sentence of the draft in about half of them. That's fine in a draft. It's a problem on a landing page, and a legal one if it's a review or a claim.

So today we're training an open model on Fireworks to do one job: make copy read like a person wrote it and leave every number, name and quote exactly as it was. We score every system on the same held-out set, frontier models included, and we publish the results either way.

Two of us, two Claude Code agents that message each other through our repo, about six hours.

Results at 4:30. I'll post them here.

@Fireworks AI @NVIDIA @Microsoft #FireworksDeploy

---

## Post 2: after results (fill only with numbers from hackathon/report/results.json). Image: the leaderboard bar chart

Results from Fireworks Deploy.

Task: rewrite AI marketing copy so it reads human without changing a single fact.
Test: [N] held-out rewrites, same cases and scoring for every system.

[Frontier model]: [X]% fact-safe human rewrites
Our fine-tuned open model on Fireworks: [Y]% ([+Z] points, [significant / not significant])
Cost: $[a] vs $[b] per 1,000 rewrites. Speed: [p50] vs [p50] ms.

What didn't work: [one honest line, e.g. prompting alone made it worse].

Code, data and eval are open: [repo link]

Built with Ruslan. @Fireworks AI @NVIDIA @Microsoft #FireworksDeploy

## Checklist before posting
- Real tags (type @ and pick the company page): Fireworks AI, NVIDIA, Microsoft.
- Post 1's only number ("about half" dropped a sentence) comes from hackathon/audit/AUDIT.md (Claude 50-51% of items vs our harness 17%). Re-check before posting.
- Both of us post (entries are counted per post). After 20 likes and 10 reshares, email a screenshot and the link to fireworks@hackersquad.io.

---

## Post 1 (short version), ready to paste

Ask an AI to make your copy "sound more human" and it will. It will also cut lines you needed and sometimes change a number.

We measured it today. On 250 marketing rewrites, a top frontier model dropped at least one sentence of the draft in about half of them.

So at Fireworks Deploy in SF, Ruslan and I are building FeatherLM: an open model on Fireworks that rewrites AI copy so it reads like a person wrote it, and keeps every fact exactly as it was. A checker catches anything invented or lost, and the model fixes it before you ever see it.

Results at 4:30.

@Fireworks AI @NVIDIA @Microsoft #FireworksDeploy
