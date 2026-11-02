# FeatherLM — brief (2026-11-01)

Working name. A model and app that write like real people, not AI slop.

## What YC asked for
**"LLMs That Write Well"** — Jared Friedman, Winter 2027 RFS (not Fall 2026). Models got better at code and worse at writing; the reward signals that make them good at code "flatten voice and style"; big labs will always pick coding over style. They want "a model that people like talking to." No mention of detectors or humanizers. → [research/YC_RFS.md](research/YC_RFS.md)

**Reading:** YC wants a *model company with taste*, not a humanizer wrapper. Fall 2026 neighbours: "Proving You're Human", "The Primer" (AI that teaches kids to read and write).

## What the research says
1. **Your thesis is mostly right, one part unproven.** Post-training (SFT → DPO → RL) measurably flattens style, and models sound like each other (Artificial Hivemind, NeurIPS 2025 best paper; Narrative Flattening, 2026). "2023 models wrote better" is not proven — don't lead with it until we test it. → [research/TECH.md](research/TECH.md)
2. **Humanizers are a bad business to copy.** ~33M visits/mo across 23 sites, quality is synonym-swap mush, traffic falling, ethics exposure (Common App fraud policy, payment processors). Grammarly/Superhuman ships one and just bought GPTZero. → [market/MARKET.md](market/MARKET.md)
3. **Closest real competitor:** Marker (London, $13M seed, Index, Jul 2026) — anti-slop word processor, no known model. Sudowrite trained a fiction model but is small.
4. **The gap nobody fills:** every tool fixes the *output* (rewrite or police it). Nobody fixes the *input* — pulling out the person's real, specific details and writing in their own voice — and nobody measures voice fidelity against the person's own past writing. That is exactly what admissions readers say AI essays lack.
5. **You don't need to train from scratch.** Cheapest strong path: API + anti-slop sampler baseline → LoRA SFT on human prose + FTPO/DPO on an open 8–12B model (~$400–2k) → continued pretraining on 5–10B pre-2022 tokens only if blind tests demand it (~$1–3k more). Scratch >1B isn't worth it.
6. **Data:** ~28–30B commercially safe pre-2022 tokens exist (Common Pile, Common Corpus, Gutenberg, Wikipedia, Stack Exchange). The missing piece — modern human essays, ads, blogs, fiction — must be *licensed or commissioned*. That proprietary human data is the moat. → [data/DATA_SOURCES.md](data/DATA_SOURCES.md)
7. **Your evals/RL notes apply directly:** blind writer A/B is the ground truth, detectors are a monitor never the reward, diversity across samples is a first-class eval (collapse is the core risk), reuse your Tastecut Bradley-Terry reward model. → [evals/EVALS_AND_RL_PLAN.md](evals/EVALS_AND_RL_PLAN.md)
8. **Design:** Wispr Flow = warm paper, serif + sans, product demos itself, one hotkey everywhere, "zero-edit rate" as north star. → [design/WISPR_TEARDOWN.md](design/WISPR_TEARDOWN.md)

## Ideas (ranked)
**A. "Sounds like you" — voice model + hotkey (recommended).** Import 20+ things you wrote before 2023 (emails, essays, posts). We build your voice profile. Select any text anywhere → hotkey → rewritten in *your* voice, with a "voice match" score. North star: % sent without edits. Wedge users: founders/creators posting on LinkedIn/X, then applicants.

**B. The interviewer, not the ghostwriter (admissions wedge).** For applicants: the app interviews you like a great counsellor (your ex-admissions edge), pulls out specific stories, then drafts *with* you in your voice. Positioned as "write your own essay better", not "beat the detector". Sellable to counsellors and schools, not only students.

**C. The model itself (the YC answer).** An open-weight-based "writes-well" model with an API, trained on licensed pre-AI human prose + writer preference data, ranked #1 on a public blind human-writing leaderboard *we* publish. Sold to apps that need text people like (companions, brands, email tools).

**Sequence:** A or B is the product that earns users and preference data → that data trains C → C becomes the company. The app is the data engine; the model is the moat.

**Don't:** sell detector evasion; train from scratch; market "2023 was better" untested.

## Open questions for you
See chat.
