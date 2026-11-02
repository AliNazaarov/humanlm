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

    def test_gates(self):
        s = sa.item_scores(ITEM, "Ledgerline took close from 9 days to 4 days for 38 customers.", self.band)
        self.assertEqual((s["G1"], s["G2"], s["G3"], s["G4"], s["pass"]), (1, 1, 1, 1, 1))
        s = sa.item_scores(ITEM, "Ledgerline: 9 to 4 days.", self.band)  # gutted, lost 38
        self.assertEqual((s["G2"], s["G4"], s["pass"]), (0, 0, 0))

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
        items = {"dev-001": ITEM}
        for rows in ([{"id": "dev-001", "system": "s", "output": "x"}] * 2,
                     [{"id": "nope", "system": "s", "output": "x"}],
                     [{"id": "dev-001", "system": "s", "output": " "}]):
            with self.assertRaises(SystemExit):
                sa.load_systems([self._run(rows)], items)

    def test_main_and_heldout_files_group_by_label(self):
        held = {"id": "ho-001", "ai_draft": "Ledgerline closes books in 4 days."}
        items = {"dev-001": ITEM, "ho-001": held}
        a = self._run([{"id": "dev-001", "system": "s", "output": "Ledgerline: 9 to 4 days, 38 customers.",
                        "latency_ms": 800, "cost_usd": 0.0002}])
        b = self._run([{"id": "ho-001", "system": "s", "output": "Ledgerline closes the books in 4 days.",
                        "latency_ms": 600, "cost_usd": 0.0002}])
        systems = sa.load_systems([a, b], items)
        self.assertEqual(list(systems), ["s"])
        s = sa.score_system(systems["s"], items, BAND)
        self.assertEqual(len(s["per_item"]), 2)
        self.assertAlmostEqual(s["cost_per_1k_usd"], 0.2)
        self.assertEqual(s["latency_ms"]["p50"], 700.0)

    def test_build_reference_and_paired_delta(self):
        items = {"dev-001": ITEM}
        good = self._run([{"id": "dev-001", "system": "frontier-strong:x",
                           "output": "Ledgerline took close from 9 days to 4 days for 38 customers."}])
        bad = self._run([{"id": "dev-001", "system": "o1", "output": "Ledgerline: 9 to 4 days."}])
        with tempfile.TemporaryDirectory() as report_dir:  # empty: no stray judge summaries
            res = sa.build([good, bad], items, BAND, None, report_dir)
        self.assertEqual(res["reference"], "frontier-strong:x")
        o1 = next(e for e in res["blocks"]["all"]["systems"] if e["label"] == "o1")
        self.assertEqual(o1["vs_reference"]["pass"]["diff"], -1.0)
        self.assertIn("Fact-safe human rewrite rate", sa.render(res))

    def test_gap_in_a_run_split_counts_as_fail(self):
        held = {"id": "ho-001", "ai_draft": "Ledgerline closes books in 4 days."}
        held2 = {"id": "ho-002", "ai_draft": "Pebble plans 7 dinners a week."}
        items = {"dev-001": ITEM, "ho-001": held, "ho-002": held2}
        a = self._run([{"id": "ho-001", "system": "s", "output": "Ledgerline closes the books in 4 days."}])
        s = sa.score_system(sa.load_systems([a], items)["s"], items, BAND)
        self.assertEqual(s["missing_ids"], ["ho-002"])  # heldout ran, so its gap counts; dev never ran
        self.assertEqual((s["per_item"]["ho-002"]["pass"], s["per_item"]["ho-002"]["G1"]), (0, 1))
        res = sa.build([a], items, BAND, None, tempfile.mkdtemp())
        e = res["blocks"]["heldout"]["systems"][0]
        self.assertEqual((e["n"], e["counted_as_fail"]), (2, 1))
        self.assertIn("counted as fails", sa.render(res))


if __name__ == "__main__":
    unittest.main()
