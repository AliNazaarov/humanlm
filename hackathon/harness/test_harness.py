"""Offline tests for harness.py selection: the one_pass `added` fix, --strict-claims, --select pairwise.
No network: chat, gates.check and claim_check are patched.
Run: python3 -m unittest discover -s hackathon/harness -p "test_*.py"
"""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402

PASS = {"pass": True, "n_fail": 0, "problems": [], "g1_nothing_invented": True}
FAIL = {"pass": False, "n_fail": 1, "problems": ["fix x"], "g1_nothing_invented": False}


def args(**kw):
    a = dict(retrieve=0, loops=0, provider="fireworks", model="m", system_prompt="s", dec={}, anti_copy=True,
             claim_check="cc", style_round=None, best_of=3, select="absolute", strict_claims=False,
             select_judge_model="accounts/fireworks/models/glm-5p3", judge_in_price=0.0, judge_out_price=0.0,
             in_price=0.0, out_price=0.0, system_name="t", pair_max_tokens=256)
    a.update(kw)
    return SimpleNamespace(**a)


class TestParsePair(unittest.TestCase):
    def test_strict(self):
        self.assertEqual(harness.parse_pair("1"), 1)
        self.assertEqual(harness.parse_pair(" 2.\n"), 2)
        self.assertEqual(harness.parse_pair("<think>hmm 1</think>2"), 2)
        self.assertIsNone(harness.parse_pair("Rewrite 1"))
        self.assertIsNone(harness.parse_pair(""))
        self.assertIsNone(harness.parse_pair("12"))
        self.assertIsNone(harness.parse_pair("3"))


class TestOnePassAdded(unittest.TestCase):
    def test_returns_last_added_of_best(self):
        a = args(loops=0)
        with mock.patch.object(harness, "chat", return_value=("out", 1, 1)), \
             mock.patch.object(harness.gates, "check", return_value=PASS), \
             mock.patch.object(harness, "claim_check", return_value=(["new claim"], 0, 0)):
            r = harness.one_pass("a draft text here", a)
        self.assertEqual(len(r), 7)
        self.assertEqual(r[6], ["new claim"])

    def test_style_round_rejected_keeps_best_added(self):
        a = args(loops=0, style_round="calm")
        # first claim check flags, style round's claim check also flags -> style rejected -> best's added returned
        cc = mock.Mock(side_effect=[(["x"], 0, 0), (["y"], 0, 0)])
        with mock.patch.object(harness, "chat", return_value=("out", 1, 1)), \
             mock.patch.object(harness.gates, "check", return_value=PASS), \
             mock.patch.object(harness, "claim_check", cc):
            r = harness.one_pass("a draft text here", a)
        self.assertEqual(r[6], ["x"])

    def test_style_round_accepted_is_clean(self):
        a = args(loops=0, style_round="calm")
        cc = mock.Mock(side_effect=[(["x"], 0, 0), ([], 0, 0)])
        with mock.patch.object(harness, "chat", return_value=("out", 1, 1)), \
             mock.patch.object(harness.gates, "check", return_value=PASS), \
             mock.patch.object(harness, "claim_check", cc):
            r = harness.one_pass("a draft text here", a)
        self.assertEqual(r[6], [])


def fake_pass(seq):
    """one_pass stub returning candidates in order: (out, copy, added)."""
    it = iter(seq)

    def f(draft, a):
        out, cp, added = next(it)
        return out, PASS, 0, 10, 5, cp, added
    return f


class TestSelection(unittest.TestCase):
    item = {"id": "x", "ai_draft": "draft"}

    def test_absolute_default_ignores_added(self):
        a = args()
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.5, ["bad"]), ("B", 0.6, []), ("C", 0.7, [])])), \
             mock.patch.object(harness, "judge_score", side_effect=[(9, 1, 1), (5, 1, 1), (5, 1, 1)]):
            row = harness.rewrite(self.item, a)
        self.assertEqual(row["output"], "A")   # old behaviour, so O3k reproduces
        self.assertEqual(row["selection"]["eligible"], 3)

    def test_strict_claims_drops_added(self):
        a = args(strict_claims=True)
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.5, ["bad"]), ("B", 0.6, []), ("C", 0.7, [])])), \
             mock.patch.object(harness, "judge_score", side_effect=[(5, 1, 1), (8, 1, 1)]):
            row = harness.rewrite(self.item, a)
        self.assertEqual(row["output"], "C")
        self.assertEqual(row["selection"]["eligible"], 2)
        self.assertEqual(row["selection"]["claim_flagged"], 1)

    def test_placeholder_counted(self):
        a = args(strict_claims=True)
        ph = [harness.CLAIM_UNAVAILABLE + ": re-verify"]
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.5, ph), ("B", 0.6, []), ("C", 0.7, [])])), \
             mock.patch.object(harness, "judge_score", side_effect=[(5, 1, 1), (8, 1, 1)]):
            row = harness.rewrite(self.item, a)
        self.assertEqual(row["selection"]["claim_unavailable"], 1)

    def test_pairwise_judge_decides_and_bye_is_lowest_copy(self):
        a = args(select="pairwise", strict_claims=True, judge_in_price=1.0, judge_out_price=2.0)
        calls = []

        def pp(x, y, draft, a):
            calls.append((x, y))
            # "B" always wins in both orders
            return (1 if x == "B" else 2 if y == "B" else 1), 100, 10
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.3, []), ("B", 0.6, []), ("C", 0.7, [])])), \
             mock.patch.object(harness, "pair_pick", side_effect=pp), \
             mock.patch.object(harness, "judge_score", side_effect=AssertionError("no absolute calls")):
            row = harness.rewrite(self.item, a)
        s = row["selection"]
        self.assertEqual(row["output"], "B")
        self.assertEqual(len(calls), 4)
        self.assertEqual(s["bye"], 0)                          # A has the lowest copy_overlap
        self.assertEqual(s["matches"][0]["pair"], [1, 2])      # B vs C first, by index
        self.assertEqual(s["decided_by"], "judge")
        self.assertEqual(s["judge_prompt_tokens"], 400)
        self.assertAlmostEqual(s["judge_cost_usd"], (400 * 1.0 + 40 * 2.0) / 1e6)
        self.assertEqual(s["flips"], 0)
        self.assertEqual(s["flip_rate"], 0.0)

    def test_pairwise_flip_falls_to_copy(self):
        a = args(select="pairwise", strict_claims=True)
        # position bias: always says 1 -> every match is a flip -> lower copy_overlap wins
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.3, []), ("B", 0.6, []), ("C", 0.5, [])])), \
             mock.patch.object(harness, "pair_pick", return_value=(1, 1, 1)):
            row = harness.rewrite(self.item, a)
        s = row["selection"]
        self.assertEqual(row["output"], "A")
        self.assertEqual(s["flips"], 2)
        self.assertEqual(s["flip_rate"], 1.0)
        self.assertEqual(s["decided_by"], "copy")

    def test_pairwise_no_verdict_logged(self):
        a = args(select="pairwise")
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.3, []), ("B", 0.6, [])])), \
             mock.patch.object(harness, "pair_pick", side_effect=[(None, 1, 1), (1, 1, 1)]):
            a.best_of = 2
            row = harness.rewrite(self.item, a)
        s = row["selection"]
        self.assertEqual(s["no_verdict"], 1)
        self.assertEqual(s["flips"], 1)
        self.assertEqual(row["output"], "A")

    def test_pairwise_one_eligible_no_calls(self):
        a = args(select="pairwise", strict_claims=True)
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.3, ["x"]), ("B", 0.6, []), ("C", 0.5, ["y"])])), \
             mock.patch.object(harness, "pair_pick", side_effect=AssertionError("no calls")):
            row = harness.rewrite(self.item, a)
        self.assertEqual(row["output"], "B")
        self.assertEqual(row["selection"]["matches"], [])
        self.assertEqual(row["selection"]["decided_by"], "only_eligible")

    def test_pairwise_zero_eligible_falls_back(self):
        a = args(select="pairwise", strict_claims=True)
        with mock.patch.object(harness, "one_pass", fake_pass([("A", 0.3, ["x"]), ("B", 0.6, ["y"]), ("C", 0.5, ["z"])])), \
             mock.patch.object(harness, "pair_pick", side_effect=AssertionError("no calls")):
            row = harness.rewrite(self.item, a)
        self.assertEqual(row["output"], "A")
        self.assertEqual(row["selection"]["decided_by"], "fallback")


class TestGuards(unittest.TestCase):
    def test_eval_judge_rejected(self):
        with self.assertRaises(SystemExit):
            harness.check_select_judge("accounts/fireworks/models/kimi-k3")
        harness.check_select_judge("accounts/fireworks/models/glm-5p3")


if __name__ == "__main__":
    unittest.main()
