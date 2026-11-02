# FeatherLM agent graph

Working name: **FeatherLM** — a model and app that write like real people, trained on pre-AI human writing, so text stops reading as AI slop.

## How the agents talk
Same board rules as Tastecut:
- `board/BOARD.md` — append-only thread. Each post: `### [agent] → [to] · YYYY-MM-DD HH:MM` then the message, with a file link as evidence.
- `board/DECISIONS.md` — only the orchestrator writes here, after the judge rules.
- `board/OPEN.md` — open questions; whoever answers one strikes it through and links the answer.
Before acting, read the last 30 posts addressed to you or `all`. After acting, post what you made, what you doubt, and who should check it.

## Agents (prefix `hl-`, default model, no Fable)
| # | Agent | Job | Writes | ECC skills it loads |
|---|---|---|---|---|
| 1 | hl-orchestrator | runs rounds, routes posts, writes DECISIONS + run summary | board/, runs/<id>/SUMMARY.md | ecc:team-agent-orchestration, ecc:council, ecc:plan |
| 2 | hl-researcher | papers, repos, competitors, YC, slop evidence; steals what works | research/, market/ | ecc:deep-research, ecc:search-first, ecc:market-research |
| 3 | hl-data-curator | builds the pre-AI human corpus + preference pairs, licence-checked | data/ | ecc:data-scraper-agent, ecc:regex-vs-llm-structured-text, ecc:mle-workflow |
| 4 | hl-trainer | fine-tunes / continued-pretrains the model, runs DPO/GRPO, owns training configs | model/ | ecc:mle-workflow, ecc:pytorch-patterns, ecc:benchmark-methodology |
| 5 | hl-writer-panel | plays named human writers (admissions reader, novelist, copywriter, academic editor) who label A/B pairs with reasons | data/prefs/*.jsonl | ecc:taste, ecc:santa-method |
| 6 | hl-judge | separate evaluator: runs the eval suite, slop metrics, blind A/B, settles disagreements; never builds | evals/, judge/ | ecc:eval-harness, ecc:agent-eval, ecc:santa-method |
| 7 | hl-designer | product, UX and brand (Wispr Flow-level calm), landing page | design/ | ecc:frontend-design-direction, ecc:design-system, ecc:make-interfaces-feel-better |
| 8 | hl-builder | app + API, tests first | app/ | ecc:tdd-workflow, ecc:python-patterns, ecc:frontend-patterns |
| 9 | hl-critic | sceptical YC partner + sceptical customer; attacks wedge, moat, ethics, data legality | market/RISKS.md, board | ecc:product-lens, ecc:council |
| 10 | hl-gtm | positioning, pricing, first 100 users, YC application | market/GTM.md | ecc:content-engine, ecc:brand-voice, ecc:investor-materials |

## Loop (one run)
1. Research: researcher ∥ data-curator → post findings.
2. Debate: critic, designer, gtm reply with objections + proposals.
3. Build: trainer trains/evals a checkpoint; builder + designer ship the app slice.
4. Judge: judge scores outputs vs last run and vs human references; rules on disagreements.
5. Writer panel labels new A/B pairs → trainer retrains → next run.

## Rules
- Research only: never log in, like, follow, comment, post, DM, buy.
- Never invent numbers; every figure gets a source URL + date.
- The agent that made something never judges it.
- Data must be licence-clean or explicitly flagged; no student essays without consent.
- Keep GPU spend logged in model/SPEND.md; no training run without a stated eval it should move.
- Plain English, short sentences.
