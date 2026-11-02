"""Offline tests for the blind A/B page helpers (hackathon/demo/ab_page)."""
import importlib.util, json, os, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.normpath(os.path.join(HERE, "../demo/ab_page"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PAGE, name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


bp, ev = _load("build_pairs"), _load("export_votes")

AB = {"meta": {"x": "x.jsonl", "y": "y.jsonl", "seed": 0, "n": 2}, "pairs": [
    {"pid": 1, "id": "dev-001", "draft": "d1", "a": "a1", "b": "b1", "a_system": "sys-z", "b_system": "sys-k"},
    {"pid": 2, "id": "trick-01", "draft": "d2", "a": "a2", "b": "b2", "a_system": "sys-k", "b_system": "sys-z"}]}
VER = bp.version(AB)


class TestBuildPairs(unittest.TestCase):
    def test_no_system_names_published(self):
        txt = json.dumps(bp.public(AB))
        self.assertNotIn("sys-z", txt); self.assertNotIn("sys-k", txt); self.assertNotIn("_system", txt)

    def test_groups_consistent_and_recoverable(self):
        for flip in (False, True):
            pub = bp.public(AB, flip=flip)
            m = bp.reveal_map(AB, pub)
            self.assertEqual(sorted(m), ["X", "Y"]); self.assertEqual(sorted(m.values()), ["sys-k", "sys-z"])
            for q, p in zip(pub["pairs"], AB["pairs"]):
                self.assertEqual(m[q["a_group"]], p["a_system"]); self.assertEqual(m[q["b_group"]], p["b_system"])

    def test_version_tracks_text(self):
        self.assertEqual(bp.public(AB)["meta"]["version"], VER)
        changed = {"meta": AB["meta"], "pairs": [dict(AB["pairs"][0], a="other"), AB["pairs"][1]]}
        self.assertNotEqual(bp.version(changed), VER)

    def test_rejects_same_system_pair(self):
        bad = {"meta": AB["meta"], "pairs": [dict(AB["pairs"][0], b_system="sys-z")]}
        with self.assertRaises(ValueError):
            bp.public(bad)


class TestExportVotes(unittest.TestCase):
    DUMP = [{"id": "u_1", "data": {"ballots": {
        "b1": {"version": VER, "picks": {"1": {"pick": "a", "first": "b", "reason": "warmer"}, "2": {"pick": "tie", "first": "a"}}},
        "b2": {"version": VER, "picks": {"2": {"pick": "b", "first": "a"}, "9": {"pick": "a"}, "1": {"pick": ""}}},
        "b3": {"version": "old", "picks": {"1": {"pick": "a"}}}}}}]

    def test_rows_map_votes_to_systems(self):
        stale = []
        rs = ev.rows(self.DUMP, AB, stale)
        self.assertEqual(len(rs), 3)  # unknown pid 9, blank pick and the stale ballot are skipped
        self.assertEqual(stale, ["b3"])
        r = rs[0]
        self.assertEqual((r["ballot"], r["pid"], r["vote"], r["a_system"], r["first_shown"]), ("b1", 1, "A", "sys-z", "b"))
        self.assertEqual([r["vote"] for r in rs], ["A", "tie", "B"])

    def test_accepts_documents_wrapper_and_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            dump, ab, out = (os.path.join(d, n) for n in ("dump.json", "ab.json", "out.jsonl"))
            with open(dump, "w") as f: json.dump({"documents": self.DUMP}, f)
            with open(ab, "w") as f: json.dump(AB, f)
            self.assertEqual(ev.main([dump, ab, out]), 0)
            with open(out) as f: self.assertEqual(len(f.read().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
