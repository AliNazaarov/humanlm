import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot as pl  # noqa: E402


def _rate(r, n=100):
    return {"rate": r, "lo": max(0.0, r - 0.1), "hi": min(1.0, r + 0.1), "count": round(r * n), "n": n}


def _entry(label, r, vs=None):
    e = {"label": label, "n": 100, "missing": 0,
         "summary": {"pass": _rate(r), "gates": {g: _rate(min(1.0, r + 0.1 * k)) for k, g in enumerate(pl.GATES)},
                     "fact_fail": _rate(0.1)}}
    if vs is not None:
        e["vs_reference"] = {"n_shared": 100, "pass": vs}
    return e


def _vs(diff, p):
    return {"diff": diff, "lo": diff - 0.05, "hi": diff + 0.05, "p": p, "significant": p < 0.05}


def synthetic() -> dict:
    block = {"n_items": 100, "systems": [
        _entry("O4-sft", 0.62, _vs(0.214, 0.001)),
        _entry("F1", 0.41),
        _entry("O1-base", 0.38, _vs(-0.03, 0.4)),
        _entry("O6-rl-failed", 0.0, _vs(-0.41, 0.0001))]}
    return {"reference": "F1", "gates_rule": "G1..G4",
            "systems": [{"label": "F1", "files": [], "model": "m", "n": 100, "cost_per_1k_usd": 12.5,
                         "latency_ms": {"p50": 1200.0, "p95": 3000.0}},
                        {"label": "O4-sft", "files": [], "model": "m", "n": 100, "cost_per_1k_usd": 0.8,
                         "latency_ms": {"p50": 450.0, "p95": 900.0}},
                        {"label": "O1-base", "files": [], "model": "m", "n": 100, "cost_per_1k_usd": 0.5},
                        {"label": "O6-rl-failed", "files": [], "model": "m", "n": 100, "cost_per_1k_usd": None}],
            "blocks": {"all": block, "main": block, "dev": block, "trick": {"n_items": 30, "systems": []},
                       "heldout": {"n_items": 120, "systems": []}},
            "judges": []}


class TestNotes(unittest.TestCase):
    def test_notes(self):
        rows = {r[0]: r for r in pl.bar_rows(synthetic()["blocks"]["all"], "F1")}
        self.assertEqual(rows["F1"][4], "reference")
        self.assertTrue(rows["F1"][5])
        self.assertEqual(rows["O4-sft"][4], "+21.4 pp vs F1 · significant")
        self.assertEqual(rows["O1-base"][4], "-3.0 pp vs F1 · n.s.")
        self.assertEqual(rows["O6-rl-failed"][4], "-41.0 pp vs F1 · significant")

    def test_rows_keep_order_and_zero_rate(self):
        rows = pl.bar_rows(synthetic()["blocks"]["all"], "F1")
        self.assertEqual([r[0] for r in rows], ["O4-sft", "F1", "O1-base", "O6-rl-failed"])
        self.assertAlmostEqual(rows[0][1], 62.0)
        self.assertEqual((rows[-1][1], rows[-1][2]), (0.0, 0.0))

    def test_missing_pass_block(self):
        e = {"label": "X", "vs_reference": {"n_shared": 0}}
        self.assertEqual(pl.delta_note(e, "F1"), "no shared items with F1")


class TestPareto(unittest.TestCase):
    def test_null_cost_goes_to_footnote(self):
        res = synthetic()
        pts, no_cost = pl.pareto_points(res["blocks"]["all"], res["systems"], "F1")
        self.assertEqual(no_cost, ["O6-rl-failed"])
        self.assertNotIn("O6-rl-failed", [p[0] for p in pts])
        by = {p[0]: p for p in pts}
        self.assertAlmostEqual(by["F1"][3], 1.2)
        self.assertIsNone(by["O1-base"][3])
        self.assertTrue(by["F1"][4])

    def test_missing_system_meta_is_no_cost(self):
        res = synthetic()
        pts, no_cost = pl.pareto_points(res["blocks"]["all"], [], "F1")
        self.assertEqual((pts, len(no_cost)), ([], 4))

    def test_front(self):
        res = synthetic()
        pts, _ = pl.pareto_points(res["blocks"]["all"], res["systems"], "F1")
        self.assertEqual(pl.pareto_front(pts), ["O1-base", "O4-sft"])  # F1 is dearer and worse than O4


class TestGates(unittest.TestCase):
    def test_gate_rows(self):
        labels, mat = pl.gate_rows(synthetic()["blocks"]["all"])
        self.assertEqual(labels[0], "O4-sft")
        self.assertAlmostEqual(mat[0][0], 62.0)
        e = {"label": "X", "summary": {"gates": {"G1": {"rate": 0.5}}}}
        _, mat = pl.gate_rows({"systems": [e]})
        self.assertEqual(mat[0][0], 50.0)
        self.assertTrue(all(math.isnan(v) for v in mat[0][1:]))


class TestBlocks(unittest.TestCase):
    def test_all_falls_back_to_main(self):
        res = synthetic()
        del res["blocks"]["all"]
        self.assertEqual(pl.pick_block(res, "all")[0], "main")
        res["blocks"]["all"] = {"n_items": 0, "systems": []}
        self.assertEqual(pl.pick_block(res, "all")[0], "main")

    def test_empty_block_exits(self):
        with self.assertRaises(SystemExit) as cm:
            pl.pick_block(synthetic(), "heldout")
        self.assertIn("heldout", str(cm.exception.code))


class TestRender(unittest.TestCase):
    def test_png_written(self):
        with tempfile.TemporaryDirectory() as d:
            res_path, out = os.path.join(d, "results.json"), os.path.join(d, "leaderboard.png")
            with open(res_path, "w", encoding="utf-8") as f:
                json.dump(synthetic(), f)
            self.assertEqual(pl.main(["--results", res_path, "--out", out]), 0)
            self.assertGreater(os.path.getsize(out), 10000)
            with open(out, "rb") as f:
                self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n")

    def test_single_system_no_cost(self):
        res = synthetic()
        one = {"n_items": 130, "systems": [_entry("F1", 0.3)]}
        res["blocks"] = {"main": one}
        res["systems"] = [{"label": "F1", "files": [], "model": "m", "n": 130}]
        with tempfile.TemporaryDirectory() as d:
            out = pl.render(res, "all", os.path.join(d, "one.png"))
            self.assertGreater(os.path.getsize(out), 0)


if __name__ == "__main__":
    unittest.main()
