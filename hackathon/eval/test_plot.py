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

    def test_coverage_note(self):
        full = dict(_entry("F1", 0.5), counted_as_fail=2)
        self.assertEqual(pl.coverage_note(full, 250), "n=100, 2 no-output = fail")
        part = dict(_entry("P", 0.1, _vs(-0.3, 0.001)), missing=120)
        part["vs_reference"]["n_shared"] = 130
        part["summary"]["pass"]["n"] = 130
        self.assertEqual(pl.coverage_note(part, 250), "n=130 of 250 only; Δ on 130 shared")
        self.assertEqual(pl.coverage_note(_entry("Q", 0.2), 100), "n=100")

    def test_lenient_bits(self):
        e = _entry("O", 0.9, _vs(0.25, 0.001))
        self.assertEqual(pl.lenient_bits(e), (None, "", ""))
        e["summary"]["pass_lenient"] = _rate(0.98)
        e["vs_reference"]["pass_lenient"] = _vs(0.132, 0.001)
        r, head, delta = pl.lenient_bits(e)
        self.assertAlmostEqual(r, 98.0)
        self.assertEqual((head, delta), (" · lenient 98.0%", " · lenient +13.2 pp sig"))

    def test_display_names(self):
        self.assertEqual(pl.display("O3c_glm_prompt_harness_style"), "FeatherLM (O3c)")
        self.assertEqual(pl.display("frontier-strong:claude-opus-5-5"), "Claude Opus 5.5 (strong prompt) · F1 strong")
        self.assertEqual(pl.display("F2_gpt61_terra"), "GPT-6.1 Terra · F2")
        self.assertEqual(pl.display("O3k_glm_calm_claimcheck_bo3"), "GLM harness ablation (O3k)")
        self.assertEqual(pl.display("O4_glm_sft"), "O4_glm_sft")  # unknown non-ablation ids stay as they are
        for lab in pl.DISPLAY:
            self.assertLessEqual(len(pl.display(lab)), 44)

    def test_clip_long_labels(self):
        self.assertEqual(pl.clip("O3c_glm_prompt_harness_style"), "O3c_glm_prompt_harness_style")
        long = "WF_Pairwise_both_orders_knockout_selector_with_fact_aware_eligibility"
        self.assertTrue(len(pl.clip(long)) <= 44 and pl.clip(long).endswith("…"))

    def test_short_labels(self):
        self.assertEqual([pl.short(x) for x in ("O3c_glm_prompt_harness_style", "F1H_opus_harness", "F1h_opus_humanizer",
                                                 "frontier-strong:claude-opus-5-5", "frontier-live:claude-opus-5-5",
                                                 "frontier-persona-preexisting", "X0_copy_draft (no rewrite: control)")],
                         ["O3c", "F1H", "F1h", "F1 strong", "F1 live", "persona", "X0"])

    def test_cost_note(self):
        self.assertEqual(pl.cost_note({"cost_per_1k_usd": 8.925, "latency_ms": {"p50": 3867.0}}),
                         "$8.93 per 1k rewrites · 3.9 s p50")
        self.assertEqual(pl.cost_note({"cost_per_1k_usd": 0.0}), "cost n/a")
        self.assertEqual(pl.cost_note({}), "cost n/a")

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
