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
    PUB = bp.public(AB, flip=False)  # sys-k -> X, sys-z -> Y
    SETS = {VER: ev.pair_set(AB, PUB)}
    DUMP = [{"id": "u_1", "data": {"ballots": {
        "b1": {"version": VER, "picks": {"1": {"pick": "a", "first": "b", "reason": "warmer"}, "2": {"pick": "tie", "first": "a"}}},
        "b2": {"version": VER, "picks": {"2": {"pick": "b", "first": "a"}, "9": {"pick": "a"}, "1": {"pick": ""}}},
        "b3": {"version": "0ld0ld0ld0ld0ld0", "picks": {"1": {"pick": "a"}}}}}}]

    def test_store_maps_votes_to_systems(self):
        dropped = []
        rs = ev.from_store(self.DUMP, self.SETS, dropped)
        self.assertEqual(len(rs), 3)  # unknown pid 9, blank pick and the other-version ballot are skipped
        self.assertEqual([d[1] for d in dropped], ["b3"])
        r = rs[0]
        self.assertEqual((r["source"], r["ballot"], r["pid"], r["vote"], r["winner"], r["first_shown"]),
                         ("page", "b1", 1, "A", "sys-z", "b"))
        self.assertEqual([r["vote"] for r in rs], ["A", "tie", "B"])
        self.assertIsNone(rs[1]["winner"])

    def test_store_accepts_documents_wrapper(self):
        self.assertEqual(len(ev.from_store({"documents": self.DUMP}, self.SETS, [])), 3)

    def test_codes(self):
        text = f"hi! my code FLM1:{VER[:8]}:abc123:bt and again FLM1:{VER[:8]}:abc123:bt FLM1:deadbeef:zz:ab"
        dropped = []
        rs = ev.from_codes(text, self.SETS, dropped)
        self.assertEqual([(r["pid"], r["vote"], r["winner"]) for r in rs], [(1, "B", "sys-k"), (2, "tie", None)])
        self.assertEqual(len(dropped), 1)  # unknown version; the duplicate paste is ignored, not dropped

    def test_telegram_groups_map_through_pairs(self):
        votes = {"votes": [{"pid": 1, "choice": "X", "version": VER, "voter_hash": "h1"},   # X = sys-k = pair 1's b
                           {"pid": 2, "choice": "X", "version": VER, "voter_hash": "h1"},   # X = sys-k = pair 2's a
                           {"pid": 2, "choice": "Y", "version": VER, "voter_hash": "h1"},   # duplicate: first kept
                           {"pid": 1, "choice": "both_bad", "version": VER, "voter_hash": "h2"},
                           {"pid": 1, "choice": "X", "version": "nope", "voter_hash": "h3"}]}
        dropped = []
        rs = ev.from_telegram(votes, self.SETS, dropped)
        self.assertEqual([(r["ballot"], r["pid"], r["vote"], r["winner"]) for r in rs],
                         [("tg:h1", 1, "B", "sys-k"), ("tg:h1", 2, "A", "sys-k"), ("tg:h2", 1, "both_bad", None)])
        self.assertEqual(len(dropped), 1)


if __name__ == "__main__":
    unittest.main()
