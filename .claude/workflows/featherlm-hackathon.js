export const meta = {
  name: 'featherlm-hackathon',
  description: 'Orchestrated FeatherLM round: research ideas, judge them, build the best one, verify on the benchmark, update the pitch',
  whenToUse: 'Run when you want one more improvement round on FeatherLM: args = {goal, minutes}. Example: {goal: "close the style gap vs Claude without losing facts", minutes: 45}',
  phases: [
    { title: 'Plan', detail: 'ecc:planner turns the goal into 3 candidate ideas + success metric' },
    { title: 'Research', detail: 'hl-researcher finds evidence and prior art per idea' },
    { title: 'Evaluate', detail: 'hl-critic + ecc:mle-reviewer score each idea; orchestrator picks one' },
    { title: 'Build', detail: 'hl-builder implements the winner as a harness flag + smoke test' },
    { title: 'Verify', detail: 'hl-judge runs a 30-item sample vs Claude strong; adversarial check for gaming' },
    { title: 'Pitch', detail: 'hl-gtm updates pitch/deck lines from verified numbers only' },
  ],
}

// Orchestrator = this script. Every stage hands off structured output; weak work loops back once.
const goal = (args && args.goal) || 'close the style gap vs Claude Opus 5.5 strong without losing fact-safety'
const minutes = (args && args.minutes) || 45
const RULES = `Repo: FeatherLM hackathon (read CLAUDE.md, hackathon/PLAN_V2_JUDGES.md, hackathon/report/RESULTS.md).
Hard rules: never train on evals/*, no frontier text in training data, never weaken the Claude baseline, every number must come from a committed file,
Ali's agent owns hackathon/harness, hackathon/train, evals/runs/hack_*; Ruslan's agent owns hackathon/eval, hackathon/report, README.md. Time box: ${minutes} minutes total.`

const IDEAS = {type: 'object', required: ['ideas', 'metric'], properties: {
  metric: {type: 'string'},
  ideas: {type: 'array', items: {type: 'object', required: ['name', 'what', 'why', 'cost_minutes'], properties: {
    name: {type: 'string'}, what: {type: 'string'}, why: {type: 'string'}, cost_minutes: {type: 'number'}}}}}}
const SCORE = {type: 'object', required: ['score', 'risks', 'verdict'], properties: {
  score: {type: 'number', description: '0-10 expected impact on the goal within the time box'},
  risks: {type: 'array', items: {type: 'string'}}, verdict: {type: 'string', enum: ['build', 'skip']}}}
const BUILD = {type: 'object', required: ['flag', 'files', 'smoke_ok', 'notes'], properties: {
  flag: {type: 'string', description: 'harness.py flag(s) that enable the idea'}, files: {type: 'array', items: {type: 'string'}},
  smoke_ok: {type: 'boolean'}, notes: {type: 'string'}}}
const VERIFY = {type: 'object', required: ['pass_rate', 'judge_style', 'judge_facts', 'gaming_risk', 'keep'], properties: {
  pass_rate: {type: 'string'}, judge_style: {type: 'string'}, judge_facts: {type: 'string'},
  gaming_risk: {type: 'string'}, keep: {type: 'boolean'}, evidence_files: {type: 'array', items: {type: 'string'}}}}

phase('Plan')
const plan = await agent(`${RULES}\nGoal: ${goal}\nPropose 3 distinct, buildable ideas (different mechanisms) and the one metric that decides success. Read hackathon/pitch/WINNING_IDEAS.md and hackathon/audit/AUDIT.md first if they exist.`,
  {agentType: 'ecc:planner', schema: IDEAS, label: 'planner'})
log(`Plan: ${plan.ideas.map(i => i.name).join(' | ')} · metric: ${plan.metric}`)

// Research + evaluate each idea as an independent pipeline (no barrier between stages).
const scored = await pipeline(plan.ideas,
  idea => agent(`${RULES}\nResearch prior art and evidence for this idea, with links, in under 10 minutes: ${idea.name}: ${idea.what}. Return a short evidence summary and the most likely failure mode.`,
    {agentType: 'hl-researcher', phase: 'Research', label: `research:${idea.name}`}),
  (evidence, idea) => parallel([
    () => agent(`${RULES}\nAs a sceptical YC partner, score this idea for the goal "${goal}". Idea: ${idea.what}. Evidence: ${evidence}`,
      {agentType: 'hl-critic', phase: 'Evaluate', schema: SCORE, label: `critic:${idea.name}`}),
    () => agent(`${RULES}\nAs an ML engineering reviewer, score feasibility and eval-validity of: ${idea.what} (est. ${idea.cost_minutes} min). Evidence: ${evidence}`,
      {agentType: 'ecc:mle-reviewer', phase: 'Evaluate', schema: SCORE, label: `mle:${idea.name}`}),
  ]).then(vs => ({idea, evidence, votes: vs.filter(Boolean),
    score: vs.filter(Boolean).reduce((s, v) => s + v.score, 0) / Math.max(1, vs.filter(Boolean).length)})))

const ranked = scored.filter(Boolean).filter(s => s.votes.some(v => v.verdict === 'build')).sort((a, b) => b.score - a.score)
if (!ranked.length) { log('No idea passed evaluation; stopping.'); return {plan, scored} }
const pick = ranked[0]
log(`Orchestrator picks: ${pick.idea.name} (score ${pick.score.toFixed(1)})`)

phase('Build')
let built = await agent(`${RULES}\nImplement this idea as an opt-in flag in hackathon/harness/harness.py (default off so old rows reproduce), tests first where possible. Idea: ${pick.idea.what}. Risks to avoid: ${pick.votes.flatMap(v => v.risks).join('; ')}. Smoke-test with --limit 3 on evals/eval_all.jsonl. Do not launch full runs.`,
  {agentType: 'hl-builder', schema: BUILD, label: 'builder'})
if (!built.smoke_ok) {
  log('Smoke test failed; one repair loop.')
  built = await agent(`${RULES}\nThe smoke test failed for flag ${built.flag}: ${built.notes}. Fix it with the smallest diff and re-run the smoke test.`,
    {agentType: 'ecc:python-reviewer', schema: BUILD, label: 'repair'})
}

phase('Verify')
const verify = await agent(`${RULES}\nRun the new harness flag (${built.flag}) on a fixed 30-item sample of evals/eval_all.jsonl (--limit 30) as system "WF_${pick.idea.name.replace(/\W+/g, '_')}", then score with pipeline/metrics.py + hackathon/harness/gates.py and judge vs evals/runs/hack_strong_claude-opus-5-5.jsonl with hackathon/eval/judge.py (Kimi K3, both orders, --allow-partial). Report pass rate, judge style and facts splits, and whether the gain could be gaming the gates.`,
  {agentType: 'hl-judge', schema: VERIFY, label: 'judge'})
const refute = await agent(`${RULES}\nTry to REFUTE this result as gaming or noise (30 items, judge flips, metric overlap). Default to refuted if unsure. Result: ${JSON.stringify(verify)}`,
  {phase: 'Verify', schema: {type: 'object', required: ['refuted', 'why'], properties: {refuted: {type: 'boolean'}, why: {type: 'string'}}}, label: 'skeptic'})

phase('Pitch')
const pitch = (verify.keep && !refute.refuted)
  ? await agent(`${RULES}\nAdd one honest line to hackathon/pitch/QA.md and a row note to hackathon/pitch/FINAL_CHECK.md about the new variant ${pick.idea.name}: ${JSON.stringify(verify)}. Numbers only from the files it lists.`,
      {agentType: 'hl-gtm', label: 'pitch'})
  : 'skipped: result not kept or refuted'

return {goal, picked: pick.idea, score: pick.score, built, verify, refute, pitch}
