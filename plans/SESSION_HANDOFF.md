# Session handoff: Role B (friend), 2026-11-02

Read this first after restarting Claude Code. Then `CLAUDE.md` and `plans/humanlm-role-b.md`.

## Who and what
- This laptop (Ruslan) is **Role B, friend**: eval, evidence, story. Ali's agent is Role A, on another machine.
- The blueprint `plans/humanlm-role-b.md` has steps S1–S9. Nothing in S1–S9 is built yet.
- Done: Step 0 repo hygiene, CLAUDE.md, the blueprint, an ACK to Ali's CONTRACT (two frontier arms: `frontier-live` + `frontier-strong`, plus the pre-existing persona row).
- Waiting on: our Q to Ali about which frontier model; NEEDS-HUMAN for an Anthropic or OpenAI key in `.env`.

## Restart checklist
1. Start DevFleet (user, in a terminal; agents run with `--dangerously-skip-permissions`):
   `powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\Asus\tools\claude-devfleet\start-windows.ps1`
   Check: `curl http://127.0.0.1:18801/api/status` returns 200; UI at http://localhost:3100.
   The MCP server is registered at user scope as `devfleet` -> `http://localhost:18801/mcp/`.
2. Restart the bus loop:
   `/loop 5m Run \`hackathon/bus/bus.sh recv friend\`. Act on any new message per hackathon/bus/PROTOCOL.md. Continue my role in hackathon/ROLE_B_FRIEND.md. Post status with \`bus.sh status friend\` after each finished task.`
3. Orchestrate S1, S2, S3 in parallel through DevFleet (`mcp__devfleet__create_project` with path = this repo, then `create_mission` per step with the step's brief from the blueprint; S4 depends on S1). Do S6 (the human A/B Artifact page) in the main session.

## The user's required workflow (apply to every feature)
- Research first: `/search-first` (done for S1–S9: numpy bootstrap + scipy binomtest, openai/anthropic SDKs, matplotlib, import `pipeline/metrics.py`, Artifact + db for the A/B page).
- Orchestration: `/everything-claude-code:claude-devfleet` / `/devfleet`, with `/orchestrate` and `/multi-execute` for coordination.
- Standards: `/coding-standards`.
- After every feature: tests, then `/eval-harness` + `/eval` (quality measurement), then `/code-review`.
- Testing: `/e2e` + `/e2e-testing` (Playwright) for the A/B test page and the demo flow.
- UI/UX (A/B page, any demo page): `/web-design-guidelines`, `/animatedwebs:design`, `/huashu-design`.
- Learning loop: `/continuous-learning-v2`, `/continuous-agent-loop`.
- Every 5 minutes, check the bus loop and other sessions' progress.
