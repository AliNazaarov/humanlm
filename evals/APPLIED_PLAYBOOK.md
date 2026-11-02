# HumanLM: the evals + RL playbook, applied

Written 2026-11-01. Revised the same day after the hl-critic review (`market/RISKS.md` R1-R7).
Applies `AI Learning/EVALS_RL_PLAYBOOK.md` (the startup-agnostic playbook) to HumanLM.
It sits next to `evals/EVALS_AND_RL_PLAN.md` (the plan) and does not repeat it. Where the plan already covers something, this file links to its section (`PLAN §x`) and says what to build. Where the plan is wrong or missing something, section 1 says so.

Inputs read: `BRIEF.md`, `GRAPH.md`, `board/DECISIONS.md`, `research/TECH.md`, `data/DATA_SOURCES.md`, `evals/EVALS_AND_RL_PLAN.md`, the 10 agent files `~/.claude/agents/hl-*.md`, and `Tastecut/app/engine/{reward,tells}.py`.
Skills loaded: ecc:eval-harness (capability vs regression evals, code > rule > model > human graders, pass@k / pass^k, no flaky graders in release gates) and ecc:agent-eval (pinned, reproducible tasks; at least one deterministic judge per task; 3+ runs per arm; track cost next to pass rate).

Status key: **exists** = built and running · **partial** = designed on paper (usually in the plan), nothing built · **missing** = not designed and not built.
Reality check: `app/`, `model/` and the board are empty. Nothing in this file "exists" as code yet, except reusable pieces in Tastecut.

> **Update 2026-11-01 (DECISIONS: revised product order):** the founder later chose a simple copy tool for everyone first, then personal voice, then the API, all on our own model. The app is no longer deferred: section 12 items (pick logging, zero-edit rate, edit pairs) start in week 2 with the one-screen tool (PLAN_30D.md §1, §6). Read "deferred" below as "week 2+".

**Product decision this file is built on:** Founder picked C: model + API first (DECISIONS 2026-11-01). The app is deferred. First styles: social posts (LinkedIn/X) and copywriting (ads, landing pages, emails). GPU budget under $2k: LoRA SFT + FTPO/DPO on an open 8-12B model, no continued pretraining. Everything app-side (reward ladder, bandit, zero-edit rate, per-user voice) lives in section 12, "Deferred until an app exists". If a later DECISIONS entry switches to A, section 12 moves back up.

---

## 0. Ali's time budget, first 2 weeks

Target: **under 6 hours** of Ali's own time (the first draft of this file needed about 12-15).

| Item | Hours |
|---|---|
| Write `docs/intent.md` + `docs/autonomy.md` | 1.0 |
| 100-output error analysis (section 4), stop early on saturation | 3.0 max |
| J1 + J6 dev labels, 40 each (section 5) | 0.7 |
| Weekly manual pass, read 20 outputs, x2 weeks (section 10) | 1.0 |
| **Total** | **about 5.7** |

Not on Ali's clock: judge held-out labels (paid rater, week 3+), the blind A/B pilot (named paid raters, not Ali), J2-J5 (unlabelled for now).

---

## 1. Corrections to EVALS_AND_RL_PLAN.md

The plan is strong on model-level evals and RL safety. Fix these:

1. **13 agents vs 10.** GRAPH.md and `~/.claude/agents/` define 10 `hl-*` agents. PLAN §4.1 invents 13 different ones. Resolution: keep the 10 and give the 13 jobs to them (table in section 9). No new agent is needed now. One optional split is named there.
2. **`hl-writer-panel` is an LLM playing writers. Its labels are not human labels.** Its agent file says it "produces preference data". If those rows train the reward model, the reward is an LLM judge in disguise, which breaks playbook principles 6 and 13, and Artificial Hivemind (TECH §A) shows LLM judges mis-model human taste. PLAN §3.2 copies Tastecut's "panel 1.0" source weight (`reward.py` line 19). Change: panel weight = **0** for reward and DPO data. It is also out of the eval loop until validated (section 10). It can earn a weight (capped at 0.3) only after its pairwise accuracy against held-out human labels reaches 0.75 after length control.
3. **Gold is the model A/B, scoped to the chosen styles.** Under C the gold is a blind, length-matched A/B against frontier models on frozen `gate` prompts for social posts and copy (section 2). The per-user "sounds like you" voice eval is deferred with the app (section 12).
4. **Product-level outcomes are deferred, not forgotten.** The app reward ladder, bandit and edit-pair engine wait for an app (section 12). Until then the only learning signal is human pairs from paid raters plus code-level FTPO.
5. **Wrong first genres.** PLAN §2 starts with four genres (admissions, creative, copy, academic) and ~390 frozen prompts per genre. DECISIONS names social posts and copywriting. Start there: LinkedIn/X posts, ads, landing pages, emails, 100 outputs. Admissions and academic wait.
6. **No fact or meaning preservation check.** Copy that invents a product claim, a number, a customer name or a testimonial is the worst failure for an API that writes ads and landing pages (legal and trust risk for API customers). A rewrite request that flips the brief's meaning is next. Add judges J1 and J6.
7. **CPT is listed as stage 0.** PLAN §3.0 starts with continued pretraining. DECISIONS says no CPT yet, and TECH §G line 159 puts few-shot and best-of-N first. CPT only after a new DECISIONS entry (section 7).
8. **No control in the eval.** Every checkpoint is compared against a frozen reference (the best frontier prompt and the previous checkpoint), never only against itself.
9. **Do not port Tastecut's aggregate slop score.** `tells.py` adds tells into one weighted 100-point score. PLAN §2.3 rightly says never collapse tells into one number. Port the feature code and the evidence/"instead" strings, not the weighted sum. Port `reward.py`'s shape (Bradley-Terry, MIN_PAIRS guard, prior fallback, 5-fold held-out) but change the features and the source weights.
10. **Hooks are named, not built.** PLAN §4.4 lists guardrails. None exist. Copy a previous project's spend-guard hook pattern.
11. **Leaderboard honesty.** C ships a public blind leaderboard that *we* run. That is the exact Llama 4 trap (playbook principle 26). Pre-register the protocol and publish the exact checkpoint, sample size and dates.

---

## 2. Gold outcome vs proxies

**Model gold (the main gold).** Blind, length-matched A/B win rate of the HumanLM checkpoint against the best frontier models (each with a "write like a human" prompt and few-shot human examples), on frozen `gate` prompts for social posts and copy (ads, landing pages, emails). PLAN §2.5 has the protocol.
- Raters are named in each report, and are people who did not build or prompt the arms. Ali is not a rater on gold A/Bs.
- Report win rate with a Wilson 95% CI, per style (post, ad, landing page, email), never pooled only.
- Length-matched: each pair is within ±15% words; otherwise the pair is regenerated, not scored.

**Proxies (useful, never the reward, never the selector):** code tells inside the human band, binary judge pass rate, reward-model score, detector scores, perplexity on held-out human text.
Every report shows proxies next to the latest gold number for the same checkpoint.

The later app gold (what users actually keep and pay for) is in section 12.

---

## 3. Principle-by-principle table

Priority: **P0** = before any checkpoint is reported · **P1** = before training · **P2** = before DPO/RL, the API launch or the public leaderboard.

| # | Principle | What it means here | Concrete artefact to build | Status | Priority |
|---|---|---|---|---|---|
| 1 | Eval and verifier are the product | Under C we train the model: a LoRA on an open 8-12B base. What makes it defensible is the eval (gate prompts, human bands, validated judges), the licence-clean human data and the pre-registered leaderboard. The weights are the output of that, not the moat | `evals/` suite as in PLAN §2.8; `data/` licence ledger | partial (PLAN) | P0 |
| 2 | Measure before you automate | Record today's numbers for the plain frontier prompt and the base open model before any fine-tune | `evals/baseline.json` from the 4-arm run (section 4) | missing | P0 |
| 3 | Read 100 outputs yourself | Ali reads 100 posts and copy outputs, blind to arm | `evals/error_analysis/2026-11/sheet.csv` → `evals/failure_modes.yaml` | partial (PLAN §2.1) | P0 |
| 4 | Reward only real outcomes | Model: blind expert A/B vs frontier. Training pairs come only from humans | `docs/intent.md` gold definition | missing | P0 |
| 5 | Label the content, not the event | A rater's "B is better" means little without why. Every ranking carries a reason (voice, fact, slop, length, structure) | reason field in `data/preferences/*.jsonl`; reason taxonomy in `failure_modes.yaml` | missing | P1 |
| 6 | Judges gate, never reward | Judges block, retry or route to human. Trainer sees only human pairs and capped code terms | Rule in `docs/intent.md` + hook that blocks judge outputs from `data/preferences` | partial (PLAN §2.4, 3.5) | P0 |
| 7 | Binary, validated judges | Start with J1 and J6 only; PASS/FAIL + quoted evidence; promotion on Wilson lower bound (section 5) | `evals/judges/J1.md`, `J6.md`, `evals/labels/*.csv`, `evals/judges/report.md` | partial (PLAN §2.4 lists candidates) | P0 |
| 8 | Maker never grades itself | Generation (hl-trainer) and grading (hl-judge) are separate agents, different model family, fresh context | Already in GRAPH rules; add model-family field to every judge run log | partial | P0 |
| 9 | Facts in context, every claim sourced | The "facts" are the request's brief (product, offer, audience, numbers). Every name, number, claim or testimonial in the output must appear in it | `evals/tells/facts_in_input.py` (code) + J1 for paraphrased claims | missing | P0 |
| 10 | Small, curated context | Training and eval prompts use one fixed request schema (style, audience, brief, length). No giant system prompts | `specs/request_schema.json`; context-hash logged | missing | P1 |
| 11 | Deterministic pipeline, small typed LLM steps | API flow = code: validate request → model → code tells → J1/J6 → return (JSON: text, claims_used[]) | `api/pipeline.py` with schemas; flow diagram in `specs/` | missing | P1 |
| 12 | Log every decision with stable IDs | Every sample and every rating joins back to checkpoint and prompt | `data/llm_calls`, `data/ratings` (item_id, rater_id, checkpoint, prompt_version, sampler, context_hash, seed); schema test that fails on a missing ID | missing | P0 |
| 13 | A-vs-B picks | Paid writers rank 4 samples per prompt with a reason; 10% repeats for self-consistency | `data/preferences/*.jsonl`; writer viewer `evals/human/viewer.html` | partial (PLAN §3.2) | P1 |
| 14 | Review where a mistake multiplies | Ali approves the gate prompt set, the ban list, judge promotions, training data sources and any spend line, not single outputs | `board/DECISIONS.md` approval entries; `docs/autonomy.md` | missing | P1 |
| 15 | Bandit + permanent control | Deferred (section 12). For the model: every checkpoint is evaluated against a frozen control (best frontier prompt) and the previous checkpoint | control arm in `evals/arms.yaml` | missing | P1 |
| 16 | Watch proxy vs gold | One chart per checkpoint: judge pass rate and tell distance vs blind A/B win rate | `runs/dashboard.html`; alert "proxy up, gold flat" tested with a fake bad run | missing | P1 |
| 17 | Learning ladder | Prompted base / few-shot → antislop filter + best-of-N (pass/fail filter, random pick) → LoRA SFT + FTPO → DPO (only if label budget approved) → GRPO. CPT only after a new DECISIONS entry | Section 7; `model/LADDER.md` with current rung | partial (PLAN §3.0, wrong order) | P0 |
| 18 | KL anchor | Training: β·KL to SFT ref and a KL budget (PLAN §3.6). Eval: frozen reference prompt and checkpoint | `prompts/reference_v1.md` frozen; diff check in hl-judge | partial | P1 |
| 19 | Every failure becomes a case | Every invented claim, every repeated rater reason, every judge disagreement → a case | `evals/v1/cases/*.json` (capability vs regression tags); pass^3 = 1.00 on regression | partial (PLAN §2.8) | P0 |
| 20 | Hard rules in hooks | No agent posts or publishes. hl-trainer cannot write `evals/`, `judges/`, `prompts/gate`. GPU spend capped at $2k; labels on their own budget line | `.claude/hooks/hl_guard.sh` (pre-tool), `model/SPEND.md` + cap file | partial (PLAN §4.4, none built) | P0 |
| 21 | Write the intent down | Success = posts and copy that win blind A/Bs against frontier without inventing facts. Never traded: the brief's facts, data licences, detector honesty. Checks agents may never loosen | `docs/intent.md` | missing | P0 |
| 22 | Loop engineering | Eval runs and build loops have a provable goal, budget, max iterations, stop | `runs/loop.yaml` (caps), orchestrator reads it | partial (PLAN §4) | P1 |
| 23 | Ralph loop | For building the eval code and API, not for training | `plans/prd.json`, `progress.txt`, `ralph-once.sh` | missing | P2 |
| 24 | Eval loop + harness | Section 10: weekly manual pass now, nightly only with new human rows. Writes `lessons.md` that prompts read | `runs/<date>/SUMMARY.md`, `lessons.md` | partial (PLAN §4.2) | P1 |
| 25 | Skills over agents; prove every line | Each line of the training/eval prompt template must beat its own removal on the eval set | `evals/ablations/` run per prompt version | missing | P2 |
| 26 | Show the version that ran | Leaderboard and pitch numbers name checkpoint, n, dates, raters. No "2023 models wrote better" claim until tested | `evals/leaderboard/PROTOCOL.md` pre-registered | missing | P2 |

---

## 4. The first 100-output error analysis

Goal: a counted table of how outputs fail on the chosen styles, written by the person whose taste sets the bar. This replaces PLAN §4.5 step 1 (freezing ~390 prompts per genre is too heavy for week 1).

**Who:** Ali, as benevolent dictator for open coding only (playbook principle 3). He reads blind to arm, and none of the outputs or human controls are his own writing, so memory does not break blindness. He is not a rater on the gold A/Bs (section 2) and not the only labeller on judges (section 5).

**Inputs (25 tasks x 4 arms = 100 outputs):**
- 13 social tasks: a brief (topic, audience, 3-5 points) → LinkedIn or X post.
- 12 copy tasks: a product brief (offer, audience, facts) → ad, landing-page section or email (4 each).
- Arms, shuffled and blind:
  - **A3 (main arm)** open 8-12B model (Mistral-Nemo-12B or OLMo 3 7B base) prompted as a document with 2-3 human examples. This is the model we will train; its failures set the training plan. Run locally; no Tenki sandbox.
  - A0 frontier model, plain prompt "write this so it sounds human" (baseline).
  - A1 frontier + the same human examples (the bar to beat).
  - A2 A1 + code ban-list filter and retry (antislop-style regenerate; the API has no token sampler).
- Mix in 10 licence-clean, pre-2022 human-written posts/ads on similar briefs as human controls (not counted in the 100). If Ali flags them as "AI", the rubric has a bug.

**Method (PLAN §2.1):**
1. Viewer: one row per output, arm hidden. Fields: output, brief, "first thing wrong" (one sentence), "would I ship this? yes / after edits / no".
2. Open coding: one note per output, first upstream problem only. Stop early if 20 in a row add nothing new. Hard cap 3 hours.
3. Axial coding: an LLM clusters the notes; Ali renames and merges by hand; add "none of the above". The agent may count and find more instances; it may not invent categories.
4. Count by arm and by style. Rank by harm x frequency. Expected modes to check for (not to assume): invented claim or number, brief meaning dropped, generic hook, moral closer, slop phrases, listicle structure, too long.
5. Triage each mode: prompt fix, code check, training data, or judge.
6. Save `evals/failure_modes.yaml` v1 (mode, definition, 2 examples, count per arm, fix type, owner).
7. The weekly pass (section 10) back-labels with the taxonomy; no separate second session.

**Outputs:** `evals/baseline.json` (would-ship rate per arm, n=25 each, with Wilson CI), `failure_modes.yaml`, the first 10 regression cases, the human-control false-positive count, and J1/J6 dev-label candidates.

**Cost:** about $2-5 of API, 3 hours max of Ali.

**Gate to leave:** a counted failure table; the top 3 modes each have an owner and a fix or a case.

---

## 5. Judges: start with two, validate before blocking

Code checks come first (PLAN §2.3 tells: banned phrases, em-dash band, "not X but Y", tricolon, template leak, length ratio, MATTR, burstiness, cross-sample diversity). They are not judges. Judges cover what code cannot decide.

**Active now:**

| ID | Judge (PASS/FAIL + quoted evidence) | Why it matters here | Code help first | Blocking? |
|---|---|---|---|---|
| J1 | `invented_fact`: output states a claim, number, name, customer, testimonial or credential not in the brief | Legal and trust risk for copy; worst failure for the API | `facts_in_input.py` catches numbers, names, dates; judge catches paraphrased claims | Only after promotion (below) |
| J6 | `meaning_changed`: output drops, adds or flips a point, offer or call to action from the brief | Copy that misstates the offer is unusable | `claims_used[]` JSON from the generator, checked by code against the brief | Only after promotion (below) |

**Report-only, unlabelled until J1 and J6 pass promotion:** J2 `generic_hook` (first line restates the prompt), J3 `told_not_shown`, J4 `unearned_moral_closer`, J5 `brand_voice_mismatch` (only if an API customer supplies a style guide). The error analysis decides whether any of them is worth labelling at all.

**Validation plan (PLAN §2.7):**
- Dev set: about 40 labels per judge, by Ali, blind to the judge's verdict, used to tune the prompt.
- Held-out set: **at least 40 FAIL and 40 PASS** per judge. If real failures are rare, add hard cases from other arms; do not invent fake failures. Never tune on held-out.
- Raters: a primary rater labels held-out; **a second rater (a paid writer) double-labels 20% of judge labels. Report Cohen's kappa. If kappa is under 0.6, the rubric is ambiguous; rewrite it before promotion.** J1 and J6 are close to objective, so a paid rater can be primary; Ali arbitrates disagreements.
- Report: confusion matrix, TPR (failures caught) and TNR (good outputs let through), each with Wilson 95% CI. Plain agreement is not reported alone.
- **Promotion: a judge becomes blocking only when the Wilson 95% lower bound of both TPR and TNR is at least 0.75.** (For scale: 36/40 gives a lower bound of about 0.77; 13/15 gives about 0.62, which is why the old "0.85 on 30 held-out" bar was noise.)
- Stability: run each judge twice; verdict flips above 5% means the rubric text is ambiguous; rewrite it.
- Model: a different family from the generator, fresh context, told to assume one defect.
- Drift: re-run held-out labels on every new checkpoint and monthly. Judge-vs-human disagreements go to a queue; they are the best new cases.
- Headroom: a judge passing 95%+ for a month leaves the gate and becomes a regression test.
- Workload: 2 judges x (40 dev + 80+ held-out) is about 240 labels, half the old 480, and only the 80 dev labels are Ali's.

---

## 6. Preference-data pipeline

Every row: `{pair_id, item_id, rater_id, source, style, context_hash, prompt_version, checkpoint, chosen, rejected, reason, edit_ratio, tiny_diff, licence, created_at}`. Join on IDs only.

| Source | How it is made | Weight in reward model / DPO | Notes |
|---|---|---|---|
| S3 Paid writer rankings | 1-2 writers per style rank 4 samples per prompt, with a reason; 10% repeats for self-consistency | 3.0 | Commission under a training licence (DATA_SOURCES §5); cost comes from the pilot, not from estimates (below) |
| S4 Human-vs-model pairs | Real licence-clean human passage vs model text from the same back-translated brief (Gutenberg-DPO shape, refreshed with a current model) | 0.5 | Teaches "looks human", not quality; never alone |
| S5 FTPO slop pairs | From antislop backtracking events on our own model | FTPO only | Token-level; not mixed into DPO |
| S6 hl-writer-panel (LLM) | Persona labels | **0** | Not used until validated (correction 2) |
| S1/S2 App edits and picks | Deferred | - | Section 12 |

**Rules:**
- Licence: every human passage and every writer label carries a `licence` field; no row without one enters training.
- Length control: chosen is not systematically longer; add counter-pairs or regress length out (PLAN §3.2).
- Tiny-diff flag: edit_ratio under 3% of tokens → `tiny_diff=true`, excluded from plain DPO, routed to FTPO/SFT.
- Same-reason rule: when a rater reason repeats 3 times, hl-judge opens a case or a code check.
- Holdout: 20% of prompts and one writer never enter training; `gate` and `canary` sets never enter anything.

**Label budget (separate from the $2k GPU cap):** DPO needs about 2,000-3,000 human pairs; at $30-100 an hour that can cost more than the whole GPU cap, and those numbers are estimates. So: **the 150-pair pilot measures pairs per hour and cost per pair. Record these in `model/SPEND.md` under a separate label budget line. No DPO plan until real cost x pairs needed is approved in DECISIONS. Until then, R3 (SFT + FTPO on human prose, no pairs needed) is the ceiling.** A reward model v1 (interpretable Bradley-Terry, about 500 pairs) falls under the same rule.

---

## 7. Training and optimisation ladder, with exit gates

Rule: one rung at a time; move up only when the rung below has plateaued on the eval set. GPU costs from TECH §D/G are estimates and all sit under the $2k cap in `model/SPEND.md`.

| Rung | What | Cost | Exit gate (all on frozen `gate` prompts, social + copy) |
|---|---|---|---|
| R0 Prompted baseline | A3 open base model prompted as a document + frontier arms A0/A1 as references | ~$0-20 | Baseline recorded; would-ship rate measured; eval suite and J1/J6 running in CI |
| R1 Filter + best-of-N | Antislop sampler on the open model (ban-list regenerate on frontier arms); N=8 at T=0.9. Judges and code tells only filter, pass/fail. Pick at random among the outputs that pass, or by a reward model trained only on human pairs that has passed the split-RM test. Log tell distance; never select on it | ~$20-50 | Best-of-N beats R0 in a blind A/B, 150 length-matched pairs, lower CI bound above 50%. The R1 blind A/B names its raters, and Ali is not one of them. Cost per output logged |
| R3 LoRA SFT + FTPO | Open 8-12B base, licence-clean human prose in brief→passage form (no model text as targets), then FTPO on its own slop | ~$100-500 | Beats R1 blind A/B; cross-sample diversity at or above R1; lm-eval-harness not worse by more than 2 points |
| R4 DPO / ORPO | 2-3k clean S3 pairs, small β, SFT term, ref = R3. **Only after the label budget is approved in DECISIONS (section 6)** | ~$50-300 GPU + label line | PLAN §2.8 gate passes vs R3; diversity floor holds; no length drift; chosen/rejected log-probs both tracked |
| (CPT) | Not on the ladder. CPT only after a new DECISIONS entry: DECISIONS 2026-11-01 rules it out, and the old estimate ($1-3k) breaks the $2k cap | - | - |
| R6 GRPO | Mixed reward (PLAN §3.5), KL budget, split-RM test done | ~$150-600 | Beats R4 *and* best-of-N on blind A/B; over-optimisation test clean; otherwise ship R4, R3 or best-of-N |

(R2, the app bandit, is in section 12.)

Every rung writes an observation-ledger entry (`runs/<id>/report.md`: change, metric movement, slice movement, decision, rollback artifact).

---

## 8. Reward-hacking defences

PLAN §3.6 covers the training-side defences (KL budget, split-RM test, pessimistic ensemble, length band, secret canary tells, anti-memorisation). These are the extra hacks this model invites:

| Hack | What it looks like | Defence |
|---|---|---|
| H2 Copying the training set | Output reuses whole sentences from training passages or few-shot examples | n-gram overlap gate vs training and example text (no span over 8 words) |
| H3 Em-dash and ban-list zeroing | Tells drop to zero, new tics appear | Band-shaped targets (human band, not zero); alarm when a tell falls below the lowest human decile; secret canary tell list; tells never used to select (R1) |
| H4 Flattery / puffery | Copy makes the product sound grander than the brief; raters like it; it is false | J1 blocks; puffery probe set in `canary` |
| H6 Judge gaming | Best-of-N learns the judge's quirks | Judges are pass/fail filters only; pick at random among passes; hl-critic reads 20 passing outputs each weekly pass |
| H7 Detector chasing | Pressure to "beat GPTZero" | Detectors never in reward or selection; one held-out detector; report human-control false-positive rate next to every detector number (PLAN §2.6) |
| H8 Agent loosens a check | An agent edits a threshold to make a run pass | `docs/intent.md` lists protected files; pre-tool hook blocks writes to `evals/judges`, `evals/labels`, `prompts/gate`, `runs/loop.yaml` from every agent except via an Ali-approved commit |
| H9 Self-reported leaderboard | We run and report our own leaderboard | Pre-registered protocol, external named raters, exact checkpoint and n published, raw pairs released |

App-side hacks H1 (no-op rewrite) and H5 (lazy users) are in section 12.

---

## 9. Agents: the 13 plan jobs mapped onto the 10 graph agents

| PLAN §4.1 job | Runs as | Why there |
|---|---|---|
| hl-orchestrator | **hl-orchestrator** | same |
| hl-generator (sampling) | **hl-trainer** (sample mode) | the maker; it never grades |
| hl-tells (code graders) | **hl-judge** (script step) | deterministic; judge owns `evals/` |
| hl-judge | **hl-judge** | same |
| hl-gatekeeper | **hl-judge** (gate mode) | separate from the trainer; fail closed |
| hl-error-analyst | **hl-judge** (cluster/count only) | Ali names modes; agent counts |
| hl-case-writer | **hl-judge** | cases live in `evals/` |
| hl-grader-audit | **hl-critic** | someone other than the judge must check the judge |
| hl-skeptic (red team) | **hl-critic** | already its job |
| hl-pair-builder | **hl-data-curator** | builds the labelling queue |
| hl-corpus-scout | **hl-data-curator** | licence-clean corpus is its job |
| hl-reward-modeler | **hl-trainer** (RM mode) | trained only on human pairs; evaluated by hl-judge; only after the label budget is approved |
| (none) human labels | **paid writers + Ali (dev labels, arbitration)** | hl-writer-panel is out until validated (weight 0) |

No new agent is required. One optional split: if hl-judge's run passes 30 minutes or its context gets crowded, move gate mode into a new `hl-gatekeeper` (read-only tools: Read, Glob, Grep, Write to `runs/<id>/GATE.md` only; loads ecc:eval-harness). Also update `~/.claude/agents/hl-writer-panel.md` to say its rows are not preference data (needs Ali's OK; not done here).

---

## 10. The eval loop

Local only (no Tenki sandboxes running). Caps in `runs/loop.yaml`: max API spend per run, max 1 retry per agent, max outputs, stop on any alarm. Training is not in the loop; it runs only on triggers (PLAN §4.3).

**Now (until a checkpoint or real users exist): a weekly manual pass.**

| Step | Agent | Does | Writes |
|---|---|---|---|
| 1 | hl-trainer (sample mode) | Samples the current arm(s) and the control on dev prompts, 3 seeds each | `runs/<date>/outputs.jsonl` |
| 2 | hl-judge | Code tells, J1 and J6, regression cases (pass^3) | `runs/<date>/judge.json`, new cases |
| 3 | hl-critic | Reads 20 outputs (passing ones included), notes anything the judges missed | `runs/<date>/critic.md` |
| 4 | Ali | Reads the summary and the 20 outputs, 30 minutes | `board/DECISIONS.md` if anything changes |

**Later:** go nightly only when hl-data-curator has new human rows (writer labels). A new checkpoint triggers one full eval run, not a nightly schedule. hl-writer-panel stays out of the loop until it passes validation (correction 2).

Not in the loop: hl-researcher, hl-designer, hl-builder, hl-gtm (they run in build rounds).
Alarms that stop a run: judge TPR/TNR drift over 0.05, diversity floor breached, length drift, proxy up and gold flat across two checkpoints, spend cap hit.

---

## 11. Top 5 actions for the next 2 weeks (cheapest first)

1. **Write `docs/intent.md` and `docs/autonomy.md`** (free, 1 hour of Ali). Gold = blind A/B vs frontier on social + copy; never invent facts; protected files; what agents may never do. Approve corrections 1-2 (agent mapping; panel weight 0) and the deferral of the app (section 12).
2. **Run the 100-output error analysis** ($2-5 API, 3 hours max of Ali). 25 social + copy briefs x 4 arms with A3 (open model) as the main arm, blind, plus 10 licence-clean human controls. Output `failure_modes.yaml` v1 and `baseline.json`.
3. **Port the code tells and build human bands** (free, agent time). Reuse Tastecut's `tells.py` as separate metrics (no aggregate), add `facts_in_input.py` and n-gram overlap vs examples, and compute bands from licence-clean pre-2022 posts and copy.
4. **Write J1 and J6 and start validating them** (~$5 API, 40 min of Ali for dev labels). Hire one paid rater for held-out labels (40 FAIL + 40 PASS per judge) with 20% double-labelled and kappa reported. No judge blocks until the Wilson lower bound of TPR and TNR is at least 0.75. J2-J5 stay report-only and unlabelled.
5. **Run the first blind pilot and price the labels** (~$150-300 for 1-2 paid writers, on the label budget line). 150 blind, length-matched pairs: best of A1/A2/A3 vs plain frontier, raters named, Ali not one of them. Record pairs per hour and cost per pair in `model/SPEND.md`. This sets the number every later rung must beat and the real cost of any DPO plan.

Not in these 2 weeks: any fine-tune, DPO, CPT, the leaderboard, anything app-side.

---

## 12. Deferred until an app exists

None of this is built or planned until a DECISIONS entry starts the app. It is kept so the design is not lost.

**App gold.** The text the user actually used, and they keep using HumanLM: still using it after 4 weeks, then paid. Wispr's "zero-edit rate" (BRIEF item 8) is the right shape, but it is hackable (H1) and never read alone.

**Only reward events HumanLM can see with consent:** accepted in the HumanLM box, edited in the HumanLM box, an explicit Send/Copy-final button. "Sent" outside the app is unknown and scores 0. A hotkey that works in any app cannot see a send in Gmail or LinkedIn without logging keystrokes, and Wispr got a viral backlash for exactly that (`design/WISPR_TEARDOWN.md` line 84).

| Event (all inside the HumanLM box) | Reward | Notes |
|---|---|---|
| User pays / renews | gold, user level | weekly review only, not in the bandit |
| Accepted unedited (Copy-final / Send button), change ratio above floor **and J6 passes** | +1.0 | the floor alone is beaten by synonym swaps, so it is paired with the meaning check |
| Accepted after light edit (under 10% of tokens changed) | +0.6 | edit becomes an SFT/FTPO pair |
| Accepted after heavy edit | +0.2 | edit becomes a DPO pair; ask one-word reason |
| Copied without the final button, or sent outside the app | 0 | unknown; do not guess |
| Regenerated | -0.3 | |
| Undo / reverted to original text | -0.6 | |
| "Doesn't sound like me" or "changed my meaning" flag | -1.0 | also opens an error-analysis case |
| Thumbs-up, star rating | 0 | logged, never rewarded (playbook principle 5) |

**Bandit (old R2).** Thompson over 3-5 approved prompt arms, permanent control at 15-20% of traffic, floor, ±20% weekly cap, min 100 outputs per arm, per segment (post vs email), offline replay first. Exit: 4 weeks of data; winning arm beats control on accepted-unedited rate *and* not worse on retention.

**App preference sources.** S1 in-box edit diffs (chosen = accepted text, rejected = shown text, weight 3.0); S2 in-box A/B picks on 10% of calls (weight 3.0, position randomised, length-matched). Consent: a user's private drafts train only that user's voice profile by default; shared-model use only with explicit opt-in; no minors' or applicants' essays without a consent flow. Run a detector as a filter on profile uploads and flag, not reject.

**Per-user voice eval.**
- Proxy (code): stylometric authorship classifier on the user's profile pieces vs a generic pool.
- Gold (human): the "which did this person write?" test. **The voice test is run only by someone who knows the person's writing but did not write the pieces. Never by the author.** Held-out pieces never enter a prompt or a training set. Voice lives in retrieval + style card first; per-user LoRA only after retrieval plateaus.

**App-side hacks.**
- H1 No-op rewrite: output is nearly the input, accepted unedited. Defence: change-ratio floor paired with J6, a no-op arm in offline replay, report accepted-unedited *and* "used again within 7 days".
- H5 Lazy users: some users never edit, so their outputs look perfect. Defence: per-segment bandit, weight users by edit history, never pool raw zero-edit rates.
- H2 for voice: no span over 8 words copied from the user's profile.

**App logging.** `data/llm_calls`, `data/reward_events` (item_id, user_id, variant_id, prompt_version, voice_profile_version, model, context_hash, arm_prob, policy_version) with a schema test, shipped in the first app slice.

---

## Rejected or amended critic points

- **Fix 4, "Ali labels the 100 outputs" (partly rejected).** Ali still does the open coding of the 100-output error analysis. That is playbook principle 3 (one person whose taste sets the bar), and under C none of the outputs or controls are his own writing, so his memory does not break blindness. Accepted the rest: second rater with kappa on judge labels, the voice test never by the author, Ali not a rater on gold A/Bs.
- **Fix 5, loop trigger (amended).** Kept "nightly only when hl-data-curator has new human rows", and added that a new checkpoint triggers one full eval run rather than a nightly schedule. A checkpoint with no new human rows still needs evaluating.
- **Fix 1, "A3 the main arm" (amended).** A3 is the main arm, but the frontier arms A0/A1/A2 stay in the run as the reference bar, because model gold is defined as beating them.
