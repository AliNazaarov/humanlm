"""Tests for pipeline/metrics.py. Run: python3 -m unittest discover -s pipeline/tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
sys.path.insert(0, PIPE)
import metrics as m  # noqa: E402

SLOP = ("In today's fast-paced world, it's important to note that we must delve into the "
        "rich tapestry of growth. Unlock your potential and elevate your brand — it's a game-changer!")
HUMAN = ("We shipped the billing fix on Tuesday. Three customers had been double charged since March. "
         "Refunds went out the same day.\n\nI wrote to each of them myself. Two replied. One left anyway.")


class TestPhrases(unittest.TestCase):
    def test_list_loads_about_150_entries(self):
        phrases = m.load_phrases()
        self.assertGreaterEqual(len(phrases), 140)
        self.assertIn("delv*", phrases)
        self.assertIn("tapestry", phrases)

    def test_stock_hits_longest_match_and_prefix(self):
        hits = m.stock_hits("We delved into a rich tapestry. Delving is fun.")
        self.assertIn("a rich tapestry", hits)
        self.assertNotIn("tapestry", hits)  # not double counted inside the longer phrase
        self.assertEqual(sum(h.startswith("delv") for h in hits), 2)

    def test_curly_apostrophe_matches(self):
        self.assertTrue(m.stock_hits("In today’s fast-paced world we win."))

    def test_no_partial_word_match(self):
        self.assertEqual(m.stock_hits("The unlocked door was elevated."), [])


class TestTextMetrics(unittest.TestCase):
    def setUp(self):
        self.slop = m.text_metrics(SLOP)
        self.human = m.text_metrics(HUMAN)

    def test_keys_are_numeric_and_separate(self):
        for k in ("stock_rate", "em_dash_rate", "tricolon_rate", "not_x_but_y_rate",
                  "question_share", "exclaim_share", "emoji_rate", "hedge_rate",
                  "sent_len_mean", "sent_len_std", "burstiness", "mattr", "avg_word_len",
                  "para_opener_repeat", "n_words"):
            self.assertIn(k, self.human)
            self.assertIsInstance(self.human[k], (int, float))
        self.assertNotIn("slop_score", self.human)  # no combined score, ever

    def test_slop_scores_worse_than_human(self):
        self.assertGreater(self.slop["stock_rate"], 10)
        self.assertEqual(self.human["stock_rate"], 0)
        self.assertGreater(self.slop["em_dash_rate"], 0)
        self.assertEqual(self.human["em_dash_rate"], 0)
        self.assertGreater(self.slop["exclaim_share"], 0)

    def test_rate_is_per_100_words(self):
        text = " ".join(["word"] * 99 + ["delve"])
        self.assertAlmostEqual(m.text_metrics(text)["stock_rate"], 1.0)

    def test_tricolon(self):
        t = "Our tool is fast, simple, and reliable. We value trust, speed and craft."
        self.assertEqual(m.tricolon_count(t), 2)
        self.assertEqual(m.tricolon_count("Bread and butter, please."), 0)

    def test_not_x_but_y(self):
        self.assertEqual(m.not_x_but_y_count("It's not just a tool, it's a movement."), 1)
        self.assertEqual(m.not_x_but_y_count("This isn't a product — it's a promise."), 1)
        self.assertEqual(m.not_x_but_y_count("Not because it's easy, but because it's hard."), 1)
        self.assertEqual(m.not_x_but_y_count("I did not go. It rained."), 0)

    def test_questions_and_emoji(self):
        r = m.text_metrics("Ready to grow? We can help. Want more? \U0001F680\U0001F525")
        self.assertAlmostEqual(r["question_share"], 2 / 3, places=3)
        self.assertGreater(r["emoji_rate"], 0)

    def test_hedges(self):
        self.assertGreater(m.text_metrics("This might perhaps help, arguably.")["hedge_rate"], 0)

    def test_burstiness_and_sentence_stats(self):
        flat = m.text_metrics("One two three four. Five six seven eight. Nine ten eleven twelve.")
        self.assertEqual(flat["sent_len_mean"], 4)
        self.assertEqual(flat["burstiness"], 0)
        self.assertGreater(self.human["burstiness"], 0)

    def test_mattr_bounds(self):
        self.assertAlmostEqual(m.mattr(["a"] * 80), 1 / 50)
        self.assertEqual(m.mattr(["a", "b", "c"]), 1.0)
        self.assertEqual(m.mattr([]), 0.0)

    def test_paragraph_opener_repetition(self):
        t = "We built it.\nWe tested it.\nWe shipped it.\nThen it broke."
        self.assertAlmostEqual(m.text_metrics(t)["para_opener_repeat"], 0.5)

    def test_empty_text_does_not_crash(self):
        r = m.text_metrics("")
        self.assertEqual(r["n_words"], 0)
        self.assertEqual(r["stock_rate"], 0)


class TestSetMetrics(unittest.TestCase):
    def test_distinct(self):
        self.assertEqual(m.distinct_n(["a b", "a b"], 1), 0.5)
        self.assertEqual(m.distinct_n(["a b", "c d"], 2), 1.0)
        self.assertEqual(m.distinct_n([], 2), 0.0)

    def test_self_bleu_lite(self):
        same = ["the cat sat on the mat"] * 3
        diff = ["the cat sat on the mat", "dogs run fast in parks", "rain fell over old hills"]
        self.assertAlmostEqual(m.self_bleu_lite(same), 1.0)
        self.assertLess(m.self_bleu_lite(diff), 0.2)
        self.assertEqual(m.self_bleu_lite(["only one"]), 0.0)


class TestFaithfulness(unittest.TestCase):
    SRC = "Acme cut onboarding from 14 days to 3 days for 1,200 customers, says Dana Ruiz."

    def test_faithful_rewrite_passes(self):
        out = "Onboarding at Acme now takes 3 days, down from 14. Dana Ruiz says 1200 customers got it."
        f = m.faithfulness(self.SRC, out)
        self.assertFalse(f["hard_fail"])
        self.assertEqual(f["numbers_added"], [])
        self.assertEqual(f["numbers_kept"], 1.0)

    def test_new_number_is_hard_fail(self):
        f = m.faithfulness(self.SRC, "Acme cut onboarding by 80% for 1,200 customers, says Dana Ruiz.")
        self.assertTrue(f["hard_fail"])
        self.assertIn("80", f["numbers_added"])

    def test_new_name_is_hard_fail(self):
        f = m.faithfulness(self.SRC, "Acme, backed by Sequoia, cut onboarding from 14 to 3 days for 1,200 users.")
        self.assertTrue(f["hard_fail"])
        self.assertIn("sequoia", f["names_added"])

    def test_dropped_facts_lower_kept_but_do_not_hard_fail(self):
        f = m.faithfulness(self.SRC, "Acme made onboarding faster.")
        self.assertFalse(f["hard_fail"])
        self.assertLess(f["numbers_kept"], 1.0)
        self.assertIn("ruiz", f["names_dropped"])

    def test_invented_attribution_is_hard_fail(self):
        src = "Shelfwise e-ink labels let grocers update prices from a phone. Batteries last 5 years."
        out = "Shelfwise labels let grocers update prices from a phone, says the CEO. Batteries last 5 years."
        f = m.faithfulness(src, out)
        self.assertTrue(f["attribution_added"])
        self.assertTrue(f["hard_fail"])

    def test_invented_quote_is_hard_fail(self):
        src = "Shelfwise e-ink labels let grocers update prices from a phone."
        out = "\u201cIt is easier than ever to update your prices,\u201d grocers can update prices from a phone."
        f = m.faithfulness(src, out)
        self.assertEqual(len(f["quotes_added"]), 1)
        self.assertTrue(f["hard_fail"])

    def test_kept_quote_passes(self):
        src = 'Dana Ruiz said "we cut onboarding to three days" last week.'
        out = 'Last week Dana Ruiz said "we cut onboarding to three days".'
        f = m.faithfulness(src, out)
        self.assertFalse(f["hard_fail"])


class TestNameProxy(unittest.TestCase):
    """Bug fix 2026-11-02: line labels, greeting lines and Title Case headlines are not names."""

    def test_line_label_is_sentence_initial(self):
        self.assertNotIn("planning", m._names("Primary text: Planning a move to Warsaw? Pokoik can help."))

    def test_title_case_headline_skipped(self):
        self.assertEqual(m._names("Break Language Barriers & Unlock Nordic Markets"), set())

    def test_greeting_line_start(self):
        self.assertNotIn("hi", m._names("Subject: launch\nHi there,\nWe ship today."))

    def test_real_names_still_caught(self):
        names = m._names("Headline: Close faster\nLedgerline now syncs with NetSuite for Dana Ruiz.")
        self.assertTrue({"netsuite", "dana", "ruiz"} <= names)

    def test_headline_rewrite_to_sentence_case_is_not_a_fact_change(self):
        src = "Headline: Your Warsaw Adventure Awaits!\nPokoik rents flats in Warsaw for 1-6 months."
        out = "Headline: Furnished flats in Warsaw\nPokoik rents flats in Warsaw for 1 to 6 months."
        f = m.faithfulness(src, out)
        self.assertEqual((f["names_added"], f["names_dropped"]), ([], []))


class TestGrammar(unittest.TestCase):
    def test_returns_none_without_languagetool(self):
        orig = m._lt_tool
        m._lt_tool = lambda: None
        try:
            self.assertIsNone(m.grammar("This are bad."))
        finally:
            m._lt_tool = orig

    def test_uses_tool_when_present(self):
        class Fake:
            def check(self, text):
                return [1, 2]
        orig = m._lt_tool
        m._lt_tool = lambda: Fake()
        try:
            self.assertAlmostEqual(m.grammar(" ".join(["w"] * 50)), 4.0)
        finally:
            m._lt_tool = orig


class TestBand(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "h.jsonl")
        rows = [{"human": HUMAN.replace("Three", w), "ai": SLOP} for w in
                ("Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Two", "Eleven")]
        rows.append({"other": "no field here"})
        with open(self.path, "w") as fh:
            fh.write("\n".join(json.dumps(r) for r in rows) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_percentile(self):
        self.assertEqual(m.percentile([1, 2, 3, 4, 5], 50), 3)
        self.assertAlmostEqual(m.percentile(list(range(11)), 10), 1.0)
        self.assertEqual(m.percentile([7], 90), 7)

    def test_band_and_in_band(self):
        band = m.human_band(self.path, field="human")
        self.assertEqual(band["_n"], 10)
        self.assertIn("stock_rate", band["metrics"])
        lo, hi = band["metrics"]["sent_len_mean"]
        self.assertLessEqual(lo, hi)
        ok = m.in_band(m.text_metrics(HUMAN), band)
        self.assertTrue(ok["stock_rate"]["ok"])
        bad = m.in_band(m.text_metrics(SLOP), band)
        self.assertFalse(bad["stock_rate"]["ok"])
        self.assertEqual(bad["stock_rate"]["side"], "high")

    def test_cli_score_and_band(self):
        script = os.path.join(PIPE, "metrics.py")
        out = subprocess.run([sys.executable, script, "band", self.path, "--field", "human"],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out)["_n"], 10)
        out = subprocess.run([sys.executable, script, "score", self.path, "--field", "ai",
                              "--source-field", "human"],
                             capture_output=True, text=True, check=True).stdout
        res = json.loads(out)
        self.assertEqual(len(res["rows"]), 10)
        self.assertIn("faithfulness", res["rows"][0])
        self.assertIn("distinct_2", res["summary"])
        self.assertIn("stock_rate", res["summary"]["mean"])


if __name__ == "__main__":
    unittest.main()
