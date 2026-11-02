# Pairwise judge prompt

Loaded at runtime by `hackathon/eval/judge.py`. Only the text between `<!-- begin:NAME -->` and
`<!-- end:NAME -->` is sent. `{{NAME}}` placeholders are filled in one pass (filled values are never
re-scanned). Every section is part of the judge config hash stored on each row: editing any of them
makes old rows stale, and judge.py refuses to mix them (re-run with `--fresh` or a new `--out`).

Protocol (EVALS_AND_RL_PLAN §2.6–2.7): pairwise, forced choice `1|2|tie`, temperature 0, both orders.
A win counts only when both orders agree; otherwise it is a tie. FACTS and STYLE are sub-verdicts,
VERDICT is the overall call. Criteria (a)–(c) are one shared section so both rubrics use the same words.

## System

<!-- begin:system -->
You compare two rewrites of the same draft. The order of the rewrites is arbitrary. Be strict about facts.
<!-- end:system -->

## Criteria shared by both rubrics

<!-- begin:criteria -->
(a) Facts: the rewrite keeps every fact listed above and every number and name in the draft, and adds no fact, number, name, claim or quote that is not in the draft. A rewrite that drops, changes or invents a fact loses to one that does not. If both break facts, prefer the one with fewer breaks.
(b) Style: the rewrite reads like a skilled human wrote it: plain, specific, without stock phrases, filler or forced structure. Length by itself is not a reason to prefer either rewrite.
(c) Coverage: the rewrite is not thinner than needed: it still does the draft's job and keeps what a reader needs.
<!-- end:criteria -->

## User (eval set: drafts with a fact list)

<!-- begin:user -->
Facts that must be kept:
{{FACTS}}

Original draft:
<<<
{{DRAFT}}
>>>

Rewrite 1:
<<<
{{REWRITE_1}}
>>>

Rewrite 2:
<<<
{{REWRITE_2}}
>>>

Criteria:
{{CRITERIA}}

FACTS answers (a) alone. STYLE answers (b) alone. VERDICT weighs (a), then (b), then (c), in that order.
Answer with exactly these four lines and nothing after them. Each answer is one of: 1, 2, tie.
REASON: <one line>
FACTS: <answer>
STYLE: <answer>
VERDICT: <answer>
<!-- end:user -->

## User (held-out set: drafts with a human original)

<!-- begin:user_heldout -->
Facts that must be kept:
{{FACTS}}

Original draft:
<<<
{{DRAFT}}
>>>

Human original (the passage the draft was made from):
<<<
{{HUMAN}}
>>>

Rewrite 1:
<<<
{{REWRITE_1}}
>>>

Rewrite 2:
<<<
{{REWRITE_2}}
>>>

Criteria:
{{CRITERIA}}
(d) Voice: which rewrite is closer to the human original in voice (tone, rhythm, word choice)? Judge voice only, not content.

FACTS answers (a) alone. STYLE answers (b) alone. CLOSER answers (d) alone. VERDICT weighs (a), then (b), then (c), in that order, and ignores (d).
Answer with exactly these five lines and nothing after them. Each answer is one of: 1, 2, tie.
REASON: <one line>
FACTS: <answer>
STYLE: <answer>
CLOSER: <answer>
VERDICT: <answer>
<!-- end:user_heldout -->

## Facts placeholder when the item has no fact list

<!-- begin:no_facts -->
(no list given: every fact, number and name in the draft must be kept)
<!-- end:no_facts -->
