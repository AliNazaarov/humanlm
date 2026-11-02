"""Offline tests for --style-round lint (O3q): style_lint(), safe_trim() and the accept rule in lint_round().
Synthetic strings only (no eval text). No network: chat and gates.check are patched.
Run: python3 -m unittest discover -s hackathon/harness -p "test_*.py"
"""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402

PASS = {"pass": True, "n_fail": 0, "problems": []}
FAIL = {"pass": False, "n_fail": 1, "problems": ["x"]}
LONG = "We moved the warehouse to a bigger building near the river last spring."


def lint(draft, out):
    return harness.style_lint(draft, out, cap=None)


def has(hits, prefix):
    return [h for h in hits if h.startswith(prefix)]


class TestSlogans(unittest.TestCase):
    def test_each_slogan_regex(self):
        for s in ["For us, speed is everything.", "You asked, we listened.", "It's that simple.", "It is that simple.",
                  "And here we are.", "Your shop could be next.", "The future of baking is here.",
                  "The future is here.", "Was it hard? Absolutely.", "Worth it? 100%."]:
            hits = lint(LONG, LONG + " " + s)
            self.assertTrue(has(hits, "Replace this tagline"), s)

    def test_split_contrast(self):
        for s in ["This tool is not a toy. It's a workshop.", "The app isn't a tracker. This is a coach.",
                  "We're not just a bakery. That is a promise."]:
            self.assertTrue(has(lint(LONG, LONG + " " + s), "Replace this tagline"), s)
        self.assertFalse(has(lint(LONG, LONG + " The door is not locked. Come in."), "Replace this tagline"))

    def test_span_is_located(self):
        h = has(lint(LONG, LONG + " Worth it? 100%."), "Replace this tagline")[0]
        self.assertIn("Worth it? 100%.", h)


class TestShortRuns(unittest.TestCase):
    def test_run_of_two_short_new_sentences(self):
        out = LONG + " It was cold. We left early. " + LONG
        self.assertTrue(has(lint(LONG, out), "Join these into one complete sentence: It was cold. We left early."))

    def test_short_sentences_in_draft_are_ignored(self):
        d = "It was cold. We left early. " + LONG
        self.assertFalse(has(lint(d, d), "Join these"))

    def test_single_short_sentence_ok(self):
        self.assertFalse(has(lint(LONG, LONG + " It was cold. " + LONG), "Join these"))

    def test_label_hashtag_and_final_cta_lines_excluded(self):
        out = "Headline: Fast. Cheap.\n" + LONG + "\n#Fast #Cheap\n"
        self.assertFalse(has(lint(LONG, out), "Join these"))
        out2 = LONG + "\nSign up today. It is free."
        self.assertFalse(has(lint(LONG, out2), "Join these"))


class TestQuestions(unittest.TestCase):
    def test_opening_question_not_in_draft(self):
        out = "Tired of waiting for your bread to rise in a cold kitchen every winter morning? " + LONG
        self.assertTrue(has(lint(LONG, out), "Make this a plain statement"))

    def test_short_question_not_in_draft(self):
        self.assertTrue(has(lint(LONG, LONG + " Sound good?"), "Make this a plain statement"))

    def test_draft_question_kept_is_fine(self):
        d = LONG + " Would that be of interest?"
        self.assertFalse(has(lint(d, d), "Make this a plain statement"))

    def test_long_mid_question_ok(self):
        out = LONG + " Would you like to see how the new building handles the extra orders this year?"
        self.assertFalse(has(lint(LONG, out), "Make this a plain statement"))


class TestValues(unittest.TestCase):
    def test_values_sentence_overlap(self):
        d = LONG + " Freshness is and always will be our top priority."
        out = LONG + " Freshness is our top priority and always will be."
        self.assertTrue(has(lint(d, out), "Cut or restate as a fact"))

    def test_values_sentence_with_digit_exempt(self):
        d = LONG + " We are humbled that 300 of you joined."
        self.assertFalse(has(lint(d, d), "Cut or restate as a fact"))

    def test_low_overlap_ok(self):
        d = LONG + " Freshness is our top priority."
        out = LONG + " We bake every loaf the same morning it ships."
        self.assertFalse(has(lint(d, out), "Cut or restate as a fact"))


class TestVague(unittest.TestCase):
    def test_vague_verbs(self):
        for s in ["It helps you plan.", "The app handles the rest.", "Your shop stands out.",
                  "We take care of billing.", "Speed matters more than ever."]:
            self.assertTrue(has(lint(LONG, LONG + " " + s), "Say what it actually does"), s)


class TestStructure(unittest.TestCase):
    def test_labels_missing_or_out_of_order(self):
        d = "Headline: Bread\nSubhead: " + LONG + "\nCTA: Order now"
        self.assertFalse(has(lint(d, d), "Keep the draft's field labels"))
        self.assertTrue(has(lint(d, "Headline: Bread\n" + LONG + "\nCTA: Order now"), "Keep the draft's field labels"))
        self.assertTrue(has(lint(d, "Subhead: " + LONG + "\nHeadline: Bread\nCTA: Order now"),
                            "Keep the draft's field labels"))

    def test_hashtags_missing(self):
        d = LONG + "\n#Bread #Bakery"
        self.assertTrue(has(lint(d, LONG + "\n#Bread"), "Put back these hashtags from the draft: #Bakery"))
        self.assertFalse(has(lint(d, LONG + "\n#bread #bakery"), "Put back"))

    def test_quotes_after_normalisation(self):
        d = 'One customer wrote: "Best rye I have had — ever!" and came back.'
        self.assertFalse(has(lint(d, 'One customer wrote: "Best rye I have had, ever." and came back.'), "Restore"))
        self.assertTrue(has(lint(d, "One customer said the rye was the best and came back."), "Restore"))
        short = 'She said "so good" twice.'
        self.assertFalse(has(lint(short, "She praised it twice."), "Restore"))

    def test_cap(self):
        out = LONG + " Speed is everything. Sound good? It helps you. Ready? It's that simple. Here we are. Go?"
        self.assertGreater(len(harness.style_lint(LONG, out, cap=None)), 6)
        self.assertEqual(len(harness.style_lint(LONG, out)), 6)

    def test_clean_text_no_hits(self):
        self.assertEqual(lint(LONG, LONG), [])


class TestSafeTrim(unittest.TestCase):
    def test_drops_echo_sentence_numbers_survive(self):
        t = "Setup takes six minutes on a 2024 laptop. Six minutes. Then you are done."
        r = harness.safe_trim(t)
        self.assertEqual(r, "Setup takes six minutes on a 2024 laptop. Then you are done.")
        self.assertIn("2024", r)

    def test_keeps_short_sentence_with_new_number(self):
        t = "Setup takes six minutes. Just 6."
        self.assertEqual(harness.safe_trim(t), t)
        t2 = "Setup takes six minutes. Nine minutes."
        self.assertEqual(harness.safe_trim(t2), t2)

    def test_keeps_question_and_new_content(self):
        t = "Setup takes six minutes. Six minutes? Totally new idea."
        self.assertEqual(harness.safe_trim(t), t)

    def test_echo_line_removed_cleanly(self):
        t = "We cut costs by 40%.\n\nCosts cut.\n\nNext year we grow."
        self.assertEqual(harness.safe_trim(t), "We cut costs by 40%.\n\nNext year we grow.")

    def test_collapses_repeated_sequence(self):
        self.assertEqual(harness.safe_trim("We ship on time on time every week."), "We ship on time every week.")
        self.assertEqual(harness.safe_trim("We had had enough."), "We had had enough.")   # single words kept

    def test_noop(self):
        self.assertEqual(harness.safe_trim(LONG), LONG)


def args(**kw):
    a = dict(retrieve=0, loops=0, provider="fireworks", model="m", system_prompt="s", dec={}, anti_copy=False,
             claim_check=None, style_round="lint", best_of=1)
    a.update(kw)
    return SimpleNamespace(**a)


class TestAcceptRule(unittest.TestCase):
    DRAFT = LONG
    BAD = LONG + " Speed is everything. Sound good?"   # 3 hits: tagline, short run, short question
    ONE = LONG + " Speed is everything."               # 1 hit
    GOOD = LONG

    def run_lint(self, replies, gate_results):
        log = {}
        with mock.patch.object(harness, "chat", side_effect=[(r, 1, 1) for r in replies]), \
             mock.patch.object(harness.gates, "check", side_effect=gate_results):
            out, g, cp, pt, ct = harness.lint_round(self.DRAFT, self.BAD, PASS, 0.0, args(), log)
        return out, g, log

    def test_accepts_when_gates_pass_and_hits_drop(self):
        out, g, log = self.run_lint([self.GOOD], [PASS])
        self.assertEqual(out, self.GOOD)
        self.assertEqual((log["lint_before"], log["lint_after"], log["lint_rounds"], log["lint_kept"]), (3, 0, 1, 1))

    def test_rejects_gate_failure_keeps_previous(self):
        out, g, log = self.run_lint([self.GOOD, self.GOOD], [FAIL, FAIL])
        self.assertEqual(out, self.BAD)
        self.assertTrue(g["pass"])
        self.assertEqual((log["lint_rounds"], log["lint_kept"], log["lint_after"]), (2, 0, 3))

    def test_rejects_when_hits_do_not_drop(self):
        worse = self.BAD + " It's that simple."
        out, g, log = self.run_lint([self.BAD, worse], [PASS, PASS])
        self.assertEqual(out, self.BAD)
        self.assertEqual(log["lint_kept"], 0)

    def test_two_rounds_max_and_partial_progress(self):
        out, g, log = self.run_lint([self.ONE, self.GOOD], [PASS, PASS])
        self.assertEqual(out, self.GOOD)
        self.assertEqual((log["lint_rounds"], log["lint_kept"], log["lint_after"]), (2, 2, 0))

    def test_no_hits_no_calls(self):
        log = {}
        with mock.patch.object(harness, "chat") as ch:
            out, *_ = harness.lint_round(self.DRAFT, self.GOOD, PASS, 0.0, args(), log)
        ch.assert_not_called()
        self.assertEqual((out, log["lint_rounds"]), (self.GOOD, 0))

    def test_one_pass_runs_basic_style_then_lint(self):
        # draft call -> PASS; basic style round -> PASS (kept); lint revision -> PASS with fewer hits (kept)
        replies = [(self.BAD, 1, 1), (self.BAD, 1, 1), (self.GOOD, 1, 1)]
        log = {}
        with mock.patch.object(harness, "chat", side_effect=replies) as ch, \
             mock.patch.object(harness.gates, "check", return_value=PASS):
            r = harness.one_pass(self.DRAFT, args(), log)
        self.assertEqual(len(r), 7)
        self.assertEqual(r[0], self.GOOD)
        self.assertEqual(ch.call_args_list[1][0][3][-1]["content"], harness.STYLE_ASK)
        self.assertEqual(log["lint_kept"], 1)

    def test_no_lint_when_gates_fail(self):
        log = {}
        with mock.patch.object(harness, "chat", return_value=(self.BAD, 1, 1)) as ch, \
             mock.patch.object(harness.gates, "check", return_value=FAIL):
            harness.one_pass(self.DRAFT, args(), log)
        self.assertEqual(ch.call_count, 1)
        self.assertEqual(log, {})


if __name__ == "__main__":
    unittest.main()
