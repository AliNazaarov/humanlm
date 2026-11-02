"""Offline tests for judge.py on tmp fixtures: parser, aggregation, flip rate, resume, config and io
hashes, truncation, join reporting, mock dry run.
Run: python -m unittest discover -s hackathon/eval -p "test_*.py"
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge  # noqa: E402

MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"
ANSWER = "REASON: r\nFACTS: 1\nSTYLE: 2\nVERDICT: 1"


class TestParser(unittest.TestCase):
    def check(self, text, verdict, reason=None):
        v, r = judge.parse_verdict(text)
        self.assertEqual(v, verdict, text)
        if reason is not None:
            self.assertEqual(r, reason)

    def test_clean(self):
        self.check("REASON: keeps all facts\nVERDICT: 1", "1", "keeps all facts")

    def test_rewrite_word_and_case(self):
        self.check("reason: fewer stock phrases\nverdict: Rewrite 2", "2", "fewer stock phrases")

    def test_tie_words(self):
        self.check("VERDICT: TIE", "tie")
        self.check("VERDICT: neither.", "tie")
        self.check("VERDICT: draw", "tie")

    def test_markdown(self):
        self.check("**Reason:** cleaner\n**Verdict:** **2**", "2", "cleaner")

    def test_last_verdict_wins(self):
        self.check("VERDICT: 1\nOn reflection 1 invents a number.\nREASON: 1 invents 17%\nVERDICT: 2", "2")

    def test_think_block_ignored(self):
        self.check("<think>VERDICT: 1</think>\nREASON: r\nVERDICT: 2", "2")

    def test_bare_last_line(self):
        self.check("Rewrite 1 keeps every fact.\nRewrite 1", "1")

    def test_template_echo_rejected(self):
        self.check("REASON: <one line>\nVERDICT: 1, 2 or tie", None, "unparsed")
        self.check("VERDICT: <answer>", None, "unparsed")

    def test_trailing_text_rejected(self):
        self.check("VERDICT: 2, both are close but 2 keeps the price", None, "unparsed")

    def test_closer_only_tail(self):
        # No VERDICT line; the last line is CLOSER, which must not be read as the verdict.
        self.check("REASON: r\nCLOSER: 1", None, "unparsed")
        self.assertEqual(judge.parse_closer("REASON: r\nCLOSER: 1"), "1")

    def test_unparsed(self):
        self.check("I cannot decide between these two rewrites.", None, "unparsed")
        self.check("", None, "unparsed")
        self.assertIsNone(judge.parse_closer("VERDICT: 1"))
        self.assertIsNone(judge.parse_field("FACTS: unclear", "facts"))

    def test_sub_verdicts(self):
        self.assertEqual(judge.parse_field(ANSWER, "facts"), "1")
        self.assertEqual(judge.parse_field(ANSWER, "style"), "2")


def rows(pairs, field="verdict"):
    """pairs: {id: (value_AB, value_BA)} -> judge rows."""
    out = []
    for i, (ab, ba) in pairs.items():
        out += [{"id": i, "order": "AB", field: ab}, {"id": i, "order": "BA", field: ba}]
    return out


class TestAggregate(unittest.TestCase):
    def test_winner_mapping(self):
        self.assertEqual(judge.winner("1", "AB"), "A")
        self.assertEqual(judge.winner("1", "BA"), "B")
        self.assertEqual(judge.winner("2", "BA"), "A")
        self.assertEqual(judge.winner("tie", "AB"), "tie")

    def test_agree_is_win(self):
        per_id, s = judge.aggregate(rows({"x": ("1", "2"), "y": ("2", "1")}))
        self.assertEqual((per_id["x"]["final"], per_id["y"]["final"]), ("A", "B"))
        self.assertEqual((s["win"], s["loss"], s["tie"], s["n"], s["flip_rate"]), (1, 1, 0, 2, 0.0))

    def test_disagree_is_tie(self):
        per_id, s = judge.aggregate(rows({"x": ("1", "1")}))  # always picks position 1
        self.assertEqual(per_id["x"]["final"], "tie")
        self.assertTrue(per_id["x"]["flip"])

    def test_flip_rate(self):
        _, s = judge.aggregate(rows({"a": ("1", "2"), "b": ("1", "1"), "c": ("tie", "tie"), "d": ("2", "tie")}))
        self.assertEqual((s["n"], s["flip_rate"], s["win"], s["tie"]), (4, 0.5, 1, 3))

    def test_unparsed_or_missing_order_is_incomplete(self):
        _, s = judge.aggregate(rows({"x": ("1", None)}) + [{"id": "y", "order": "AB", "verdict": "1"}])
        self.assertEqual(s["n"], 0)

    def test_pos1_rate(self):
        self.assertEqual(judge.pos1_rate(rows({"a": ("1", "1"), "b": ("2", "tie")})), round(2 / 3, 4))


class TestPrompt(unittest.TestCase):
    def test_fill_single_pass(self):
        self.assertEqual(judge.fill("{{A}}-{{B}}", {"A": "{{B}}", "B": "x"}), "{{B}}-x")
        with self.assertRaises(KeyError):
            judge.fill("{{NOPE}}", {})

    def test_messages(self):
        p = judge.load_prompts()
        item = {"id": "t", "ai_draft": "DRAFT TEXT", "facts": ["fact one"], "human": "HUMAN TEXT"}
        m = judge.build_messages(item, "OUT {{DRAFT}}", "OUT TWO", p)
        user = m[1]["content"]
        for s in ("- fact one", "DRAFT TEXT", "OUT {{DRAFT}}", "OUT TWO", "FACTS:", "STYLE:", "VERDICT:"):
            self.assertIn(s, user)
        self.assertNotIn("HUMAN TEXT", user)
        self.assertIn("order of the rewrites is arbitrary", m[0]["content"])
        held = judge.build_messages(item, "1", "2", p, heldout=True)[1]["content"]
        self.assertIn("HUMAN TEXT", held)
        self.assertIn("CLOSER:", held)
        self.assertIn(p["criteria"], user)
        self.assertIn(p["criteria"], held)  # same (a)-(c) wording in both rubrics

    def test_item_facts_word_boundary(self):
        row = {"brief": {"facts": ["Close went from 19 days to 4"], "numbers": ["9", "4", "38"], "names": ["Ledger"]},
               "must_keep": ["Ledgerline"]}
        facts = judge.item_facts(row)
        self.assertEqual(facts[-1], "Numbers and names to keep exactly: 9, 38, Ledger")

    def test_family(self):
        self.assertEqual(judge.judge_family(MODEL), "llama")
        self.assertEqual(judge.judge_family("accounts/fireworks/models/qwen3-235b-a22b"), "qwen")
        self.assertEqual(judge.judge_family("claude-opus-5-5"), "claude")


class Fixture(unittest.TestCase):
    """Tiny eval / A / B / fact files in a temp dir."""
    IDS = ["x-1", "x-2", "x-3", "x-4"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.eval = self.write("eval.jsonl", [{"id": i, "ai_draft": f"draft {i}"} for i in self.IDS])
        self.facts = self.write("facts.jsonl", [{"id": i, "brief": {"facts": [f"fact {i}"]}} for i in self.IDS[:3]])
        self.a = self.write("a.jsonl", [{"id": i, "output": f"a {i}"} for i in self.IDS])
        self.b = self.write("b.jsonl", [{"id": i, "output": f"b {i}"} for i in self.IDS])
        self.out = os.path.join(d, "judge_a_vs_b.jsonl")
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\n" for r in data)
        return path

    def judge(self, answer=ANSWER):
        def call(messages, item_id, order):
            self.calls.append((item_id, order))
            if isinstance(answer, Exception):
                raise answer
            return answer
        return call

    def run_judge(self, call=None, **kw):
        kw.setdefault("model", MODEL)
        kw.setdefault("concurrency", 1)
        return judge.run(self.a, self.b, self.eval, self.out, call or self.judge(), fact_files=[self.facts], **kw)


class TestRun(Fixture):
    def test_summary_and_rows(self):
        s = self.run_judge()
        got = judge.read_jsonl(self.out)
        self.assertEqual(len(got), 8)
        for r in got:
            self.assertTrue({"id", "order", "verdict", "facts", "style", "reason", "raw", "cfg", "io", "mock"} <= set(r))
            self.assertFalse(r["mock"])
        # ANSWER always says 1: AB favours A, BA favours B -> every id ties, every id flips.
        self.assertEqual((s["win"], s["loss"], s["tie"], s["n"], s["flip_rate"]), (0, 0, 4, 4, 1.0))
        self.assertEqual(s["pos1_rate"], 1.0)
        self.assertEqual(s["facts"]["tie"], 4)
        self.assertEqual((s["n_expected"], s["n_complete"], s["empty_facts"]), (4, 4, 1))
        self.assertEqual((s["judge_family"], s["mock"], s["errors"], s["unparsed"]), ("llama", False, 0, 0))
        with open(judge.summary_path(self.out), encoding="utf-8") as f:
            saved = json.load(f)
        for key in ("a", "b", "model", "win", "loss", "tie", "flip_rate"):  # score_all.py contract
            self.assertIn(key, saved)

    def test_resume_skips_done_pairs(self):
        self.run_judge(limit=2)
        self.assertEqual(len(self.calls), 4)
        s = self.run_judge(limit=2)
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(s["skipped_resume"], 4)
        self.assertEqual(s["n_complete"], 2)

    def test_limit_is_seeded_sample(self):
        self.run_judge(limit=2, seed=1)
        first = {i for i, _ in self.calls}
        self.calls.clear()
        os.remove(self.out)
        self.run_judge(limit=2, seed=1)
        self.assertEqual({i for i, _ in self.calls}, first)

    def test_stale_io_rejudged(self):
        self.run_judge()
        self.calls.clear()
        self.write("a.jsonl", [{"id": i, "output": f"a {i}" + (" CHANGED" if i == "x-2" else "")} for i in self.IDS])
        s = self.run_judge()
        self.assertEqual(sorted(self.calls), [("x-2", "AB"), ("x-2", "BA")])
        self.assertEqual(s["n_complete"], 4)

    def test_cfg_mismatch_exits_unless_fresh(self):
        self.run_judge()
        with self.assertRaises(SystemExit):
            self.run_judge(model="accounts/fireworks/models/qwen3-235b-a22b")
        s = self.run_judge(model="accounts/fireworks/models/qwen3-235b-a22b", fresh=True)
        self.assertEqual(s["n_complete"], 4)

    def test_mock_rows_rejected_in_live_run(self):
        self.run_judge(judge.mock_judge(), mock=True)
        with self.assertRaises(SystemExit):
            self.run_judge()

    def test_claude_judge_refused(self):
        with self.assertRaises(SystemExit):
            self.run_judge(model="claude-opus-5-5")

    def test_truncated_output_is_error_and_retried(self):
        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="length", message=SimpleNamespace(content="REASON: half"))]))))
        s = self.run_judge(judge.make_live_judge(MODEL, client=fake))
        self.assertEqual((s["errors"], s["finish_length"], s["n_complete"]), (8, 8, 0))
        self.assertEqual(s["incomplete_ids"]["count"], 4)
        self.assertEqual(len(judge.read_jsonl(judge.errors_path(self.out))), 8)
        self.assertFalse(os.path.getsize(self.out))
        s = self.run_judge()  # resume retries all of them
        self.assertEqual((s["errors"], s["n_complete"]), (0, 4))

    def test_empty_content_raises(self):
        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="  "))]))))
        with self.assertRaises(judge.EmptyOutput):
            judge.make_live_judge(MODEL, client=fake)([], "x", "AB")

    def test_unparsed_counted_incomplete(self):
        s = self.run_judge(self.judge("VERDICT: 1, 2 or tie"))
        self.assertEqual((s["unparsed"], s["n_complete"]), (8, 0))

    def test_join_drop_reported(self):
        self.write("b.jsonl", [{"id": i, "output": "b"} for i in self.IDS[:3]] + [{"id": "extra", "output": "b"}])
        with self.assertRaises(SystemExit):
            self.run_judge()
        s = self.run_judge(allow_partial=True)
        self.assertEqual(s["missing_in_b"], {"count": 1, "first": ["x-4"]})
        self.assertEqual(s["not_in_eval"], {"count": 1, "first": ["extra"]})
        self.assertEqual((s["n_expected"], s["n_complete"]), (4, 3))
        self.assertEqual(s["incomplete_ids"]["first"], ["x-4"])

    def test_duplicate_ids_fatal(self):
        self.write("a.jsonl", [{"id": "x-1", "output": "a"}] * 2)
        with self.assertRaises(SystemExit):
            self.run_judge(allow_partial=True)


class TestCli(Fixture):
    def main(self, *extra):
        argv = [self.a, self.b, "--eval", self.eval, "--model", MODEL, *extra]
        with contextlib.redirect_stdout(io.StringIO()) as buf, contextlib.redirect_stderr(io.StringIO()):
            rc = judge.main(argv)
        return rc, json.loads(buf.getvalue())

    def test_mock_dry_run_needs_no_key_and_is_marked(self):
        os.environ.pop("FIREWORKS_API_KEY", None)
        rc, s = self.main("--mock", "--out", self.out)
        mock_out = judge.force_mock_name(self.out)
        self.assertIn("_mock", os.path.basename(mock_out))
        self.assertFalse(os.path.exists(self.out))
        self.assertEqual((rc, s["mock"], s["model"], s["n"]), (0, True, "mock:" + MODEL, 4))
        self.assertTrue(all(r["mock"] for r in judge.read_jsonl(mock_out)))
        with open(judge.summary_path(mock_out), encoding="utf-8") as f:
            self.assertTrue(json.load(f)["mock"])
        # Deterministic: same verdicts on a fresh rerun.
        before = sorted((r["id"], r["order"], r["verdict"]) for r in judge.read_jsonl(mock_out))
        self.main("--mock", "--out", self.out, "--fresh")
        self.assertEqual(before, sorted((r["id"], r["order"], r["verdict"]) for r in judge.read_jsonl(mock_out)))

    def test_default_out_name(self):
        self.assertTrue(judge.default_out("x/A.jsonl", "B.jsonl", True, True).endswith("judge_A_vs_B_heldout_mock.jsonl"))
        self.assertTrue(judge.default_out("A.jsonl", "B.jsonl", False, False).endswith("judge_A_vs_B.jsonl"))


if __name__ == "__main__":
    unittest.main()
