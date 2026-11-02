import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import human_votes as hv  # noqa: E402

VOTES = """| Post | A | B | Both fine | Neither |
|---|---|---|---|---|
| 1 | 5 | 2 | 1 | 0 |
| 2 | 1 | 6 | 0 | 1 |
| 3 |  |  |  |  |
"""


class TestTelegram(unittest.TestCase):
    def test_key_as_side_letter(self):
        posts = hv.telegram_counts(VOTES, {"1": "A", "2": "B"})
        self.assertEqual([(p["ours"], p["theirs"]) for p in posts], [(5, 2), (6, 1)])

    def test_key_as_system_map_and_empty_rows_skipped(self):
        key = {"1": {"A": "frontier-strong:claude-opus-5-5", "B": "O3c_glm_prompt_harness_style"}, "3": "A"}
        posts = hv.telegram_counts(VOTES, key)
        self.assertEqual([(p["post"], p["ours"], p["theirs"]) for p in posts], [(1, 2, 5)])

    def test_summary_keeps_ties_separate(self):
        s = hv.summarise({"ours": 8, "theirs": 2, "both_fine": 5, "neither": 1})
        self.assertAlmostEqual(s["win_rate"], 0.8)
        self.assertEqual((s["both_fine"], s["neither"]), (5, 1))


class TestPage(unittest.TestCase):
    def test_version_filter_and_people_by_ballot(self):
        rows = [{"version": hv.PAIRS_VERSION, "ballot": "b1", "winner": "O3c_glm_prompt_harness_style", "vote": "B"},
                {"version": hv.PAIRS_VERSION, "ballot": "b1", "winner": None, "vote": "tie"},
                {"version": hv.PAIRS_VERSION, "ballot": "b2", "winner": "frontier-strong:claude-opus-5-5", "vote": "A"},
                {"version": "old", "ballot": "b3", "winner": "O3_glm_harness", "vote": "A"}]
        c = hv.page_counts(rows)
        self.assertEqual((c["ours"], c["theirs"], c["both_fine"], c["people"], c["votes"]), (1, 1, 1, 2, 3))


if __name__ == "__main__":
    unittest.main()
