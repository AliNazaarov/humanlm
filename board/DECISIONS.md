## 2026-11-01 — founder vision (user answers)
- Start with **C: model + API first** (direct answer to YC W27 "LLMs That Write Well").
- First styles: **social posts (LinkedIn/X) + copywriting** (ads, landing pages, emails).
- GPU budget: **under $2k** → LoRA SFT + FTPO/DPO on an open 8–12B model; no continued pretraining or scratch training yet.
- YC: **apply later, after traction**.
Implications: eval set = social + copy prompts with blind writer A/B vs frontier models; data gap = licence-clean pre-2022 social/copy text (mostly must be commissioned or licensed); public leaderboard + API is the launch.
## 2026-11-01 — revised after founder follow-up
- Product order: ONE simple copy tool for everyone (2-version picker) → personal voice → API for agents. Same in-house model underneath.
- "Human" defined in PLAN_30D.md §2 (blind test, no tells, specific, grammar + faithfulness hard gates; detectors monitor only).
- First style: copywriting. Next style chosen from usage in week 4.
- Not a wrapper: own LoRA-tuned open 8–12B model by week 2; frontier model only as the baseline.
## 2026-11-01 — founder answers round 2
- First buyer: **founders** (landing pages, launch emails, cold emails, LinkedIn/X posts). $19/mo entry.
- Rewrites: **founder writes them himself** → use reverse distillation to scale: collect good human copy, have a model generate the AI-slop version, train slop→human. Founder writes/edits ~10/day and labels picks.
- GPUs: **Tenki** — but Tenki Starter is CPU-only (4 CPU / 8 GB). Not enough for an 8B LoRA. OPEN: rent a GPU per run (~$2–3/hr H100; a LoRA run ≈ $10–50) or find GPU credits.
- Audience: **businesses only**; no student essays.
## 2026-11-02 — student positioning reviewed, not adopted
- Considered students (job/internship applications, ESL students flagged by detectors) as a buyer; research in `market/STUDENTS.md`.
- Decision: **founders only** stays the buyer for the hackathon pitch, README and deck. No student messaging.
