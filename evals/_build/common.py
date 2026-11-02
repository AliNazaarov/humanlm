import re
ITEMS = []
TRICKS = []
NUM_RE = re.compile(r"[$€£₹]?(?:R\$ ?|KES ?)?\d[\d,.]*\s?(?:%|k|K|x|×|m|M|dB)?")
def _nums(facts):
    out = []
    for f in facts:
        for m in NUM_RE.findall(f):
            m = m.strip().rstrip('.,')
            if m and m not in out:
                out.append(m)
    return out
def D(type, product, audience, ask, facts, must_keep, draft, out, names=(), forbidden=()):
    ITEMS.append(dict(type=type, brief=dict(product=product, audience=audience, facts=list(facts),
        numbers=_nums(facts), names=list(names), ask=ask), must_keep=list(must_keep),
        forbidden=list(forbidden), ai_draft=draft.strip(), baseline=out.strip()))
def T(type, trick_kind, expected, product, audience, ask, facts, must_keep, draft, out,
      names=(), verbatim=(), forbidden=(), draft_is_ai=True):
    TRICKS.append(dict(type=type, trick_kind=trick_kind, expected_behavior=expected,
        draft_is_ai=draft_is_ai, brief=dict(product=product, audience=audience, facts=list(facts),
        numbers=_nums(facts), names=list(names), ask=ask), must_keep=list(must_keep),
        verbatim=list(verbatim), forbidden=list(forbidden), ai_draft=draft.strip(), baseline=out.strip()))
