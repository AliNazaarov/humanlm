import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_all as sa  # noqa: E402

ITEM = {"id": "dev-001", "ai_draft": "Ledgerline cuts close from 9 days to 4 days across 38 customers.",
        "must_keep": ["Ledgerline", "9 days to 4 days", "works with NetSuite"],
        "forbidden": ["seamlessly"], "verbatim": ["$29"]}


BAND = json.load(open(os.path.join(sa.ROOT, "evals/runs/band_v0.json"), encoding="utf-8"))


class TestKept(unittest.TestCase):
    def test_numbers_and_names(self):
        self.assertTrue(sa.kept("9 days to 4 days", "We went from 9 to 4 days."))
        self.assertFalse(sa.kept("9 days to 4 days", "We went from 9 to 5 days."))

    def test_content_words_fallback(self):
        self.assertTrue(sa.kept("bank and card transactions", "It matches card and bank transactions."))
        self.assertFalse(sa.kept("bank and card transactions", "It matches payments."))


class TestItemScores(unittest.TestCase):
    def setUp(self):
        self.band = json.load(open(os.path.join(sa.ROOT, "evals/runs/band_v0.json"), encoding="utf-8"))

    def test_added_number_is_a_fact_fail(self):
        s = sa.item_scores(ITEM, "Ledgerline cuts close from 9 days to 4 days across 38 customers, saving 50%.", self.band)
        self.assertEqual(s["fact_fail"], 1)

    def test_clean_rewrite(self):
        s = sa.item_scores(ITEM, "Ledgerline took close from 9 days to 4 for 38 customers, seamlessly.", self.band)
        self.assertEqual(s["fact_fail"], 0)
        self.assertEqual(s["forbidden_hit"], 1)
        self.assertEqual(s["verbatim_miss"], 1)
        self.assertTrue(0 <= s["in_range"] <= 1)


class TestScoreSystem(unittest.TestCase):
    def _run(self, rows):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for r in rows:
            f.write(json.dumps(r) + "\n")
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_rejects_duplicates_unknown_ids_and_empty(self):
        band = BAND
        items = {"dev-001": ITEM}
        for rows in ([{"id": "dev-001", "output": "x"}] * 2,
                     [{"id": "nope", "output": "x"}],
                     [{"id": "dev-001", "output": " "}]):
            with self.assertRaises(SystemExit):
                sa.score_system(self._run(rows), items, band)

    def test_cost_and_latency_only_when_complete(self):
        p = self._run([{"id": "dev-001", "system": "s", "output": "Ledgerline: 9 to 4 days, 38 customers.",
                        "latency_ms": 800, "cost_usd": 0.0002}])
        s = sa.score_system(p, {"dev-001": ITEM}, BAND)
        self.assertAlmostEqual(s["cost_per_1k_usd"], 0.2)
        self.assertEqual(s["latency_ms"]["p50"], 800.0)


if __name__ == "__main__":
    unittest.main()
