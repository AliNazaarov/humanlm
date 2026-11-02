# Students as a FeatherLM market: who, why, how big, and how to say it

> **Status: not adopted (2026-11-02).** The team kept founders as the only buyer (`board/DECISIONS.md`). This file is kept for reference only: do not use it in the pitch, README or deck.

Research date: 2026-11-02. This adds to `market/MARKET.md` and `market/COMPETITORS_DEEP.md` (2026-11-01), which already cover humanizers, detectors, admissions and TAM; read those for the full competitor picture. Labels:
- **[F]** fact from a named source
- **[V]** vendor or self-reported claim
- **[E]** our estimate (assumptions stated)
- **[?]** single-source or conflicting; check before putting it on a slide

FeatherLM numbers (fact-safe rate, cost, human A/B) come only from `hackathon/report/results.json` via `README.md`.

---

## 0. A decision to make first

This conflicts with two written decisions:
- `board/DECISIONS.md` (2026-11-01): "Audience: **businesses only**; no student essays."
- `CONTEXT.md` rules: "Never market this as detector evasion."

The student angle works only if we keep the second rule. Our recommendation is in section 6: target **students' own writing that's meant to persuade** (job and internship applications, cold emails, LinkedIn, writing that a course allows AI for) and **students wrongly flagged by detectors**. Don't target graded essays, and never say "beat Turnitin." If the team agrees, update `board/DECISIONS.md`.

---

## 1. Executive summary

1. **Almost every student uses AI.** 95% of UK undergraduates use AI in some way and 94% use it on assessed work, up from 51% a year earlier (HEPI/Kortext 2026, n=1,054) [F]. Among US graduating seniors, 46% used AI in their job search (NACE 2026 Student Survey) [F].
2. **Sounding like AI has a real cost, and it's often unfair.** Employers notice: 44% say they've detected AI-generated applications (NACE 2026 Job Outlook spring update, via Jobscan) [?]. About 20% of hiring managers say they would reject a candidate over an AI-written resume or cover letter (TopResume, n=600) [V]. At universities, students now sue over false AI accusations. An Adelphi student got a "100% AI" Turnitin finding annulled in court (2026) [F, multiple reports]. A Yale EMBA student is suing over a GPTZero flag [F, pending]. Detectors flagged 61% of TOEFL essays by non-native writers as AI, against near zero for native speakers (Liang et al., *Patterns*, 2023) [F, 3 years old; no independent 2026 replication found].
3. **The tools students use now change their facts.** Humanizers are paraphrasers sold on "undetectable." On HumanizerBench, the top tools keep only 66–67% of the meaning (see `COMPETITORS_DEEP.md`) [F]. In a cover letter, a changed number or an invented credential is a lie with your name on it.
4. **FeatherLM's measured edge is this exact failure.** On 247 items, our entry rewrites fact-safely 97% of the time, against 71% for Claude Opus 5.5 with a strong prompt. It costs $0.81 per 1k rewrites, against $9.11 for Claude (README results table, from `results.json`). That cost makes a student price point (single-digit dollars a month) workable, where frontier-API costs would not be.
5. **Recommendation:** pitch "**students sound like themselves, with every fact kept**" and lead with job and internship applications. That use is persuasive copy, which is what our eval measures. Use the false-positive story (international and ESL students) as the emotional hook. Never use "evade detection."

---

## 2. Who the user is (ranked)

| # | Segment | The pain, in their words | Evidence | Fit with what we built |
|---|---|---|---|---|
| 1 | **Graduating students and job seekers** (cover letters, internship applications, cold emails to recruiters, LinkedIn "open to work" posts) | "Recruiters can tell it's ChatGPT, and I get ignored" | 46% of US seniors used AI in their job search (NACE 2026) [F]; ~20% of hiring managers would reject AI-written applications (TopResume) [V]; 62% reject AI resumes that lack personalization (Resume Now, n=925) [V]; Robert Half: 67% of hiring managers say AI applications slowed hiring [V] | **Best fit.** This is persuasive copy (cold emails, LinkedIn, pitches), the same genre as our 130-item eval. A cover letter must not gain a skill or a number the student doesn't have, and that's exactly the check our verifier runs |
| 2 | **International and ESL students** who write in English with AI help | "I wrote it myself and still got flagged," and "AI fixes my grammar but then it sounds like a robot" | 1,177,766 international students in the US in 2024/25, including 294,253 on OPT who are looking for work (Open Doors 2025) [F]; 61% detector false-positive rate on non-native essays (Stanford 2023) [F, old] | Strong story, and it's ethically clean: the student wrote the ideas and we make the language read like them. Lower willingness to pay |
| 3 | **Students in courses that allow AI with disclosure** | "I'm allowed to use AI, but it reads as generic" | 37% of UK students say their institution encourages AI use and 36% disagree (HEPI 2026) [F]; policies are fragmented (Pitt focus groups) [F] | OK only where the course permits it; the product should say so in the UI |
| 4 | **Student founders, club leads, creators** (event emails, sponsor asks, LinkedIn) | Same as founders | Covered in `MARKET.md` §6 | Same as our founder buyer, but at student prices |
| ✗ | **Graded essays where AI is banned, "bypass Turnitin"** | n/a | Turnitin has shipped AI-bypasser detection since 2025-08-27 [F] | **Don't serve this.** It's an ethics, payment-processor and judging risk, and the detector arms race erases the value |

**Buyer vs user:** the user is the student, and they pay $5–15/month (the humanizer price band in `MARKET.md` §2.2). A second buyer is the **university career center**: Grammarly for Education is sold per institution in enrollment bands, with resellers listing a 1,000-seat minimum (CDW) [?]. Universities already pay for writing tools, and they'd pay more readily for one that is *not* a cheating tool.

---

## 3. Market size (every leap labelled)

### Top-down
- 19.4M US postsecondary students in fall 2025 (16.2M undergraduate, 3.2M graduate; National Student Clearinghouse, Feb 2026) [F].
- 1.18M international students in the US (Open Doors 2025) [F].
- AI writing-assistant software: $1.1–2.3B in 2024, $1.9–10B by 2030 across four analyst reports (`MARKET.md` §7) [?]. Use only as "billions."

### Bottom-up [E]
| Wedge | Calculation | Result |
|---|---|---|
| US job-seeking students | 19.4M × 25% actively applying in a given year [E] × 46% using AI for it [F, seniors only, applied loosely] × 3% choosing us [E] × $40/year (a few months at $8–10) [E] | ≈ **$2.7M/yr** |
| International students (US) | 1.18M × 46% [as above] × 5% (stronger pain) [E] × $40/year [E] | ≈ **$1.1M/yr** |
| Career-center licences | 50 US universities [E] × $10k/year [E] | ≈ **$0.5M/yr** |
| **US student SOM, 24 months** | sum of the above | **≈ $4M ARR [E]** (sum $4.3M; halve it if conversion is 1.5%), before the UK, India or other markets |

For scale: the humanizer category gets roughly 33M visits a month (`MARKET.md` §2.1) [E], and much of that is students. The demand is already there. What's missing is a product that doesn't change their facts.

---

## 4. Competitors students actually use

| Option | Price | Why it fails the student | Source |
|---|---|---|---|
| Humanizers (StealthWriter, Undetectable, WriteHuman, Phrasly, Walter) | ~$5–36/mo | Sold as detector evasion; meaning drops to 66–67% on HumanizerBench; billing complaints; detectors keep catching up | `MARKET.md` §2, `COMPETITORS_DEEP.md` |
| ChatGPT / Claude "make it sound human" | Free–$20/mo | Quietly drops or changes claims: Claude with a strong prompt is fact-safe only 71% of the time on our eval | README results table |
| Grammarly / Superhuman Humanizer | Free tier; institutional licences | The strongest incumbent. Its parent now also owns GPTZero, so the same company sells you the flag and the fix | `MARKET.md` §2.2, §4 |
| QuillBot (Learneo) | ~$99.95/yr [?] | Paraphraser-first; synonym swaps | `MARKET.md` §2.2 |
| Resume and cover-letter builders (Teal, Rezi, Kickresume, etc.) | Various | Generate from a template, so the output is generic by design. **Not researched in depth; do this before claiming a gap** | n/a |

**Our wedge in one line:** they rewrite, we rewrite *and check that every number, name and quote survived*, at open-model cost.

---

## 5. Risks and counter-evidence (say these before a judge does)

1. **The ethics optics.** "Helping students not sound like AI" can sound like cheating. The fix is the scope in section 2: applications and permitted writing, a clear "your facts, your words" UI, and no detector score as a selling point. This matches `CONTEXT.md`'s rule.
2. **Our own human test didn't favour us.** In the blind A/B, readers leaned toward Claude's prose, though not significantly (README). Our proven edge is **faithfulness and cost**, not "reads more human than Claude." Pitch what we measured.
3. **Not tested on student text.** The eval is marketing copy and held-out human prose. Cover letters are close in genre, but we have no cover-letter eval. A 5-item student test today would help (see section 7).
4. **Low willingness to pay and seasonality.** Students pay little and churn after the application season. Career-center licences and the founder/business tier are the steadier revenue; students drive volume and word of mouth.
5. **Incumbents bundle it free.** Grammarly's humanizer is free, and ChatGPT is adding voice learning (`MARKET.md` §4). Our defence is the measured fact-safety and the per-rewrite cost, which makes us also sellable as an API to the resume builders.
6. **Weak sources.** Most hiring-manager numbers come from resume-software vendors (TopResume, Resume Now) [V]. The 61% false-positive study is from 2023. Don't put a [V] or [?] number on a slide without saying where it's from.
7. **Policy.** Payment processors and app stores may restrict "bypass detection" tools (not researched; see `MARKET.md` §6). Our positioning avoids this, but marketing copy must stay in line.

---

## 6. Recommendation (the proposition)

**Positioning:** *FeatherLM makes AI-assisted writing sound like you wrote it, without changing a single fact. Built for the writing that decides your future: applications, cover letters and the emails that get you the interview.*

**Business-value story for judges (25%):**
- **Clear user:** students and new grads applying for jobs and internships. 46% already use AI to apply [F], and employers notice [?/V].
- **Valuable problem:** generic AI copy gets ignored, and "humanizers" change your facts. In an application, a changed fact is a lie with your name on it.
- **Why adopt:** it's fact-safe 97% of the time, against 71% for the frontier baseline, at about a tenth of the cost ($0.81 vs $9.11 per 1k rewrites). That cost is why a student price is possible.
- **Expansion:** the same model and API sell to founders, to marketers (the existing `CONTEXT.md` plan) and to resume and career platforms.

**Keep out of the pitch:** detector scores, "undetectable," and graded essays.

---

## 7. Cheap validation before 4:30 PM (optional)

1. Ask 5 students (per the short-test rule) to paste a real AI-drafted cover letter or internship email. Run O3c and Claude-strong, and ask which they'd send and whether any fact changed. Record it as a small, labelled anecdote, not a benchmark.
2. Add one slide or README line built from this file's [F] numbers only.
3. If the team adopts this, update `board/DECISIONS.md` (audience) and the README "Users" bullet.

---

## Sources

- HEPI/Kortext Student Generative AI Survey 2026: https://www.hepi.ac.uk/reports/student-generative-ai-survey-2026/ ; summary: https://advance-he.org/knowledge-hub/higher-education-policy-institute-hepi-student-generative-ai/ ; ERIC record (n=1,054): https://eric.ed.gov/?q=AI&ff1=eduHigher+Education&pg=15&id=ED682627
- NACE, class of 2026 / student survey: https://naceweb.org/about-us/press/2026/more-than-two-out-of-five-of-college-class-of-2026-had-a-job-offer-in-hand-by-graduation ; https://naceweb.org/about-us/press/2026/ready-or-reluctant-employer-expectations-for-ai-skills-meet-student-skepticism ; Jobscan guide citing NACE spring update: https://info.jobscan.co/hubfs/B2B/Downloadable%20Resources/Buyers-Guide.pdf
- TopResume hiring-manager survey: https://topresume.com/career-advice/ai-in-hiring-survey ; Black Enterprise summary: https://blackenterprise.com/hiring-managers-reject-ai-generated-job-applications ; US Chamber: https://uschamber.com/co/run/human-resources/hiring-ai-job-applications
- Adelphi case: https://www.plagiarismtoday.com/2025/10/14/adelphi-university-sued-over-ai-allegation/ ; https://www.plagiarismtoday.com/2026/02/11/adelphi-student-wins-ai-plagiarism-lawsuit/amp/
- Yale EMBA case: https://poetsandquants.com/2025/02/25/denying-alleged-ai-use-emba-student-sues-yale-som-over-year-long-suspension/ ; https://northeasttimes.com/2026/08/01/yale-ai-cheating-case-hinged-on-a-word-file-mix-up/
- University of Michigan case: https://govtech.com/education/higher-ed/student-sues-university-of-michigan-over-ai-misconduct-accusation
- Liang et al. 2023 (detector bias against non-native writers): https://arxiv.org/pdf/2304.02819 ; Times Higher Education: https://www.timeshighereducation.com/node/727071 ; 2026 EFL review: https://ejournal-fkip.unisi.ac.id/shelves/article/view/3557
- Open Doors 2025: https://www.iie.org/news/open-doors-2025-press-release/ ; fast facts: https://opendoorsdata.org/wp-content/uploads/2025/11/OD25_Fast-Facts.pdf
- National Student Clearinghouse, final fall 2025 enrollment: https://nscresearchcenter.org/final-fall-enrollment-trends/
- Grammarly for Education licensing (reseller): https://www.cdw.com/product/grammarly-for-education-institution-subscription-license/7455003 ; https://www.usagepricing.com/blueprint/grammarly
- Pitt GenAI conversations report: https://www.cyber.pitt.edu/sites/default/files/GenAI%20Conversations%20Report%20v.%202.pdf
- Earlier research in this repo: `market/MARKET.md`, `market/COMPETITORS_DEEP.md`, `market/RISKS.md`
