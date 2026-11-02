# YC Request for Startups: "LLMs That Write Well"

Researched 2026-11-01 via the user's Chrome (ycombinator.com/rfs, YC company directory) plus web search.

## 1. Exact RFS text (primary brief)

Batch: **Winter 2027** (the newest RFS; it is the default tab on the page). It is NOT in the Fall 2026 list (checked: Fall 2026 has Primer, Army defense, Small Software cloud, Multiplayer AI, Compute at Sea, Consumer for 1B, Aging, Physical-world OS, Crypto, Data for Real World, Proving You're Human, Compliance, Self-Maintaining APIs).
Author: **Jared Friedman** (YC General Partner, Scribd cofounder).
Link: https://www.ycombinator.com/rfs#llms-that-write-well
Publication date: not shown on the page. A secondary blurb (Whatfinger, byline "webmaster", no added commentary) ran 2026-10-29, so it went up on or before that date. A search tool put the essay at about mid-October 2026; unverified.

> **LLMs That Write Well**
> By Jared Friedman
>
> As LLMs have gotten better at coding and math, they've actually gotten worse at writing. You're not just imagining it: the current models really do sound more robotic than the models from 2024 and 2025.
>
> This appears to be not just a temporary glitch, but a structural issue. The same reward signals that make models good at code actively flatten voice and style.
>
> If forced to choose, the major labs will always choose to focus on coding and agentic workflows over style. This has left an opportunity open for a startup that cares about producing a model that people like talking to. So if this is something you'd like to work on, we'd love to hear from you.

## 2. What YC actually wants (plain reading)

- **Problem:** frontier models are RL-tuned on verifiable rewards (code, math, agents). That flattens voice. YC says it is structural, not a bug that will be patched.
- **What they ask for:** "a startup that ... produces **a model** that people like talking to." The ask is a model (a lab-style bet on style and voice), not a rewrite wrapper or a detector-bypass tool. The phrase "people like talking to" points at conversational and consumer quality, not only essays.
- **Why the gap exists:** the labs will always prioritise code and agents, so nobody big is optimising for taste.
- **Who pays:** the RFS does not say. Inferences (mine, not YC's): consumers of chat and companion products, writers and creators, marketing and brand teams, and anyone building products on LLM text who needs voice. Note the RFS says nothing about AI-detection evasion.
- **What a winning answer looks like (inference):** a model or post-training recipe that wins blind human preference on voice and style while staying competitive on instruction-following. The hard part YC implies is the reward signal: style has no verifiable reward (compare the Vertical Foundation Models RFS, where "verifiable rewards" is called the hard part). Training on pre-2023 human text fits the "structural" diagnosis, but the RFS does not suggest it. A solo founder would likely need a small or open-weight base plus preference data.
- **Caveat:** it is a 3-paragraph RFS with no market sizing, buyer or pricing. Treat it as validation, not a spec. The RFS page itself says you do not need to work on these ideas to apply.

## 3. Adjacent RFS items

Winter 2027 (https://www.ycombinator.com/rfs):
- The $15-an-Hour Expert (Brad Flora): AI turns ordinary workers into experts. #the-15-an-hour-expert
- Vertical Foundation Models (Diana Hu): small specialist models, verifiable rewards are the hard part. #vertical-foundation-models (closest in training logic)
- Own Your Intelligence (Jon Xu): companies own and tune open-weight models on their own data. #own-your-intelligence
- AI for the Air-Gapped Economy (Brad Flora): on-prem frontier AI. #ai-for-the-air-gapped-economy
- Also in the batch: Space access (Ankit Gupta), Robots Made in America, Plaid for Government Benefits, Wall Street for the Physical Buildout, AI for City Hall, Data Center Supply Chain. Not related.

Fall 2026 (same page, Fall 2026 tab):
- Proving You're Human (Max Kolysh): verified-human trust layer, bot-free replies and reviews. Adjacent to "human vs AI text".
- AI-Powered Consumer Products for 1 Billion People (Raphael Schaad): consumer AI, "agent like a person".
- The Primer (Andrew Miklas): adaptive AI tutor teaching reading and writing to young children.
- Multiplayer AI (Aaron Epstein): shared agent sessions for teams.
- A Cloud for Small Software (Pete Koomen).
- AI for the Aging Population (Max Kolysh): voice interfaces that hold real conversations.
- Others not related: Army defense, Compute at Sea, physical-world OS, crypto, Data for the Real World, compliance infra, Self-Maintaining APIs.

I did not read the Summer 2026 or Spring 2026 tabs; the writing item is not in Fall 2026.

## 4. YC companies in the space (YC directory, https://www.ycombinator.com/companies)

- **Vaero** (W23, consumer, SF): "AI for Human Writing". Appeared under the directory query "AI writing". I did not open its page.
- **TypeOS** (X25 / Spring 2025, per YC jobs page and a magazine profile): AI writing and humanizer in Google Docs; markets "99.8% undetectable" (self-claimed, unverified). Founders Daniel Martinez and Musa Aqeel. Roughly 3-4k Chrome users (single secondary source). https://typeos.com/ai-humanizer
- **Jasper.ai** (W18, B2B): AI marketing content.
- **Compose.ai** (W21, B2B): AI autocomplete for writing.
- Directory queries "humanizer" and "essay" returned nothing relevant (humanizer: Compra Rapida, Legacy, Human Interest, Flightfox, Lumina, Zenysis; essay: Edexia, an essay-grading tool, W25). "AI detection" returned only deepfake and fraud companies (Reality Defender, Verihubs, Aedilic, Inscribe), not text detection.
- No YC company found that trains its own style-first base model. That is the open space the RFS describes.

## 5. Commentary

- No Lightcone, X, or Hacker News discussion of this specific RFS found in two searches (search tools are weak on X). Only the Whatfinger repost (2026-10-29), which adds nothing.
- Worth manually checking: Jared Friedman's X account and the next Lightcone episode.

## Sources

- https://www.ycombinator.com/rfs (read in Chrome 2026-11-01; Winter 2027 and Fall 2026 tabs)
- https://startup.whatfinger.com/2026/10/29/llms-that-write-well/ (2026-10-29)
- https://www.ycombinator.com/companies?query=AI%20writing (also queries humanizer, essay, AI%20detection; 2026-11-01)
- https://typeos.com/ai-humanizer and https://huge-magazine.pages.dev/feature/typeos (Feb 2026 edition)
