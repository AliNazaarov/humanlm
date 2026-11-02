"""Offline test of ensemble_select with a fake OpenAI-like client. Run: python hackathon/train/ruslan/test_ensemble_select.py"""
import json, os, sys, types, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ensemble_select as es  # noqa: E402

DRAFT = ("Acme Notes syncs your notes across 3 devices and keeps a 30-day history. It costs $5 a month. "
         "Teams can share folders, and admins can set read-only access for each member of the team.")
A = ("Acme Notes keeps your notes in sync on 3 devices and saves 30 days of history. It costs $5 a month. "
     "Teams can share folders and admins can give each member read-only access to them.")
B = ("Acme Notes syncs notes across 3 devices and holds 30 days of history, for $5 a month. Teams share "
     "folders, and an admin can make any member of the team read-only on any of those shared folders.")
BAD = "Acme Notes is great!!! It changes everything for 10 million people."


def resp(text):
    u = types.SimpleNamespace(prompt_tokens=100, completion_tokens=10)
    ch = types.SimpleNamespace(message=types.SimpleNamespace(content=text), finish_reason="stop")
    return types.SimpleNamespace(choices=[ch], usage=u)


class Fake:
    """Pairwise: always prefers whichever text is B. Claims: everything clean unless `dirty` text appears."""
    def __init__(self, dirty=(), pos1=False):
        self.dirty, self.pos1, self.n = dirty, pos1, 0
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))

    def create(self, messages, **kw):
        self.n += 1
        u = messages[-1]["content"]
        if kw.get("response_format"):
            rw = u.split("REWRITE:\n", 1)[1]
            bad = any(d in rw for d in self.dirty)
            return resp(json.dumps({"draft_claims_missing": ["x"] if bad else [], "rewrite_claims_unsupported": []}))
        if self.pos1:
            return resp("1")
        r1 = u.split("REWRITE 1:\n", 1)[1].split("\n\nREWRITE 2:", 1)[0]
        return resp("<think>hmm</think>1" if r1 == B else "2")


def cands(*pairs):
    return [{"run": r, "output": o, "cost_usd": 0.001, "latency_ms": 100 * (i + 1)} for i, (r, o) in enumerate(pairs)]


class T(unittest.TestCase):
    def test_challenger_wins_both_orders(self):
        sel = es.Selector(Fake())
        ch, s, m = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", B)), sel)
        self.assertEqual(ch["run"], "O3j"); self.assertEqual(s["source_run"], "O3j")
        self.assertEqual(s["picks"][0]["by"], "agree"); self.assertTrue(s["eligible"]["O3j"])
        self.assertAlmostEqual(m.cost(), m.pt * es.PRICE_IN / 1e6 + m.ct * es.PRICE_OUT / 1e6)

    def test_claims_block_winner(self):
        sel = es.Selector(Fake(dirty=(B,)))
        ch, s, _ = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", B)), sel)
        self.assertEqual(ch["run"], "O3c"); self.assertTrue(s["picks"][0]["blocked_by_claims"])
        self.assertFalse(s["eligible"]["O3j"])

    def test_position_bias_is_tie_longer_wins(self):
        sel = es.Selector(Fake(pos1=True))
        ch, s, _ = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", B)), sel)
        self.assertEqual(s["picks"][0]["by"], "tie")
        longer = max((A, B), key=lambda t: len(es.gates.m.words(t)))
        self.assertEqual(ch["output"], longer)
        ch2, s2, _ = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", B)), sel, tie_rule="incumbent")
        self.assertEqual(ch2["run"], "O3c")

    def test_gate_fail_never_picked_and_fallback(self):
        sel = es.Selector(Fake(dirty=(A, B)))
        ch, s, _ = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3x", BAD), ("O3j", B)), sel)
        self.assertFalse(s["gate_pass"]["O3x"]); self.assertFalse(s["eligible"]["O3x"])
        self.assertEqual(s["fallback"], "no_eligible_first_gate_pass"); self.assertEqual(ch["run"], "O3c")

    def test_duplicates_and_cache(self):
        f = Fake(); sel = es.Selector(f)
        es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", A), ("O3l", B)), sel)
        n = f.n
        ch, s, m = es.select_item({"ai_draft": DRAFT}, cands(("O3c", A), ("O3j", A), ("O3l", B)), sel)
        self.assertEqual(f.n, n)               # all cached
        self.assertEqual(s["dups"], {"O3j": "O3c"}); self.assertEqual(ch["run"], "O3l")
        self.assertGreater(m.cost(), 0)        # cached calls still cost the row

    def test_parse(self):
        self.assertEqual(es.parse_pair("<think>a</think> 2"), 2); self.assertIsNone(es.parse_pair("12"))
        self.assertIsNone(es.parse_claims("{}")); self.assertEqual(es.parse_claims(
            '{"draft_claims_missing": [], "rewrite_claims_unsupported": ["a"]}'), ([], ["a"]))


if __name__ == "__main__":
    unittest.main()
