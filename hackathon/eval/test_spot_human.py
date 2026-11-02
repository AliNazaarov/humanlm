"""Offline tests for spot_human.py (fake client, temp dirs; no network)."""
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spot_human as S  # noqa: E402

TEMPLATE = S.load_prompt()


class FakeClient:
    """Picks as 'human' the text that contains the marker given by `rule(id_text_1, id_text_2)`."""

    def __init__(self, decide, content_fmt="HUMAN: {}"):
        self.decide, self.fmt, self.calls = decide, content_fmt, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, messages, **params):
        self.calls.append((messages, params))
        user = messages[-1]["content"]
        t1 = user.split("Text 1:\n", 1)[1].split("\n\nText 2:\n", 1)[0]
        t2 = user.split("\n\nText 2:\n", 1)[1]
        pick = self.decide(t1, t2)
        usage = SimpleNamespace(prompt_tokens=1000, completion_tokens=10, completion_tokens_details=None)
        msg = SimpleNamespace(content=self.fmt.format(pick))
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=msg)], usage=usage)


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class TestParse(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(S.parse_pick("Text 2 reads natural.\nHUMAN: 1"), "1")
        self.assertEqual(S.parse_pick("**HUMAN:** 2"), "2")
        self.assertEqual(S.parse_pick("HUMAN: Text 2"), "2")
        self.assertEqual(S.parse_pick("HUMAN: 1 maybe\nHUMAN: 2"), "2")
        self.assertEqual(S.parse_pick("<think>HUMAN: 1</think>HUMAN: 2"), "2")
        self.assertEqual(S.parse_pick("Text 1"), "1")
        self.assertIsNone(S.parse_pick("I cannot tell."))

    def test_picked_of(self):
        self.assertEqual(S.picked_of("1", "HS"), "human")
        self.assertEqual(S.picked_of("1", "SH"), "system")
        self.assertEqual(S.picked_of("2", "SH"), "human")
        self.assertIsNone(S.picked_of(None, "HS"))

    def test_prompt_fill(self):
        m = S.build_messages(TEMPLATE, "AAA", "BBB")
        self.assertEqual(len(m), 1)
        self.assertIn("HUMAN: 1 or HUMAN: 2", m[0]["content"])
        self.assertLess(m[0]["content"].index("AAA"), m[0]["content"].index("BBB"))


class TestRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.out = os.path.join(d, "out")
        ids = [f"ho-{i:03d}" for i in range(1, 7)]
        self.humans = {i: f"HUMANTEXT {i}" for i in ids}
        # sys A: ho-001,002 fool (judge picks SYS text as human in both orders), 003 split, rest caught, 006 empty
        self.sys_a = os.path.join(d, "hack_A_heldout.jsonl")
        write_jsonl(self.sys_a, [{"id": i, "output": ("" if i == "ho-006" else f"SYSTEXT {i}")} for i in ids])
        self.ref = os.path.join(d, "hack_strong_claude-opus-5-5_heldout.jsonl")
        write_jsonl(self.ref, [{"id": i, "output": f"REFTEXT {i}"} for i in ids if i != "ho-005"])

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def decide(t1, t2):
        def fooling(t):
            return any(t.startswith(p) for p in ("SYSTEXT ho-001", "SYSTEXT ho-002", "REFTEXT ho-001",
                                                   "REFTEXT ho-004"))
        if fooling(t1) or fooling(t2):
            return "1" if fooling(t1) else "2"
        if "ho-003" in t1:  # split: always say Text 1
            return "1"
        return "1" if t1.startswith("HUMANTEXT") else "2"

    def _run(self, path, client, **kw):
        return S.run_system(path, "fake", "m", S.make_call("m", client), humans=self.humans, template=TEMPLATE,
                            out_dir=self.out, concurrency=2, price=(3.0, 15.0), log=lambda *_: None, **kw)

    def test_outcomes_resume_and_summary(self):
        c = FakeClient(self.decide)
        r = self._run(self.sys_a, c)
        self.assertEqual(r["calls"], 10)  # 5 non-empty ids x 2 orders; empty ho-006 never sent
        self.assertTrue(all("" != m[0][-1]["content"] for m in c.calls))
        self.assertEqual(c.calls[0][1]["temperature"], 0)
        self.assertEqual(c.calls[0][1]["max_tokens"], 4096)
        self.assertEqual(c.calls[0][1]["extra_body"], {"reasoning_effort": "none"})
        c2 = FakeClient(self.decide)
        self.assertEqual(self._run(self.sys_a, c2)["calls"], 0)  # resume
        self.assertEqual(len(c2.calls), 0)
        self._run(self.ref, FakeClient(self.decide))
        res = S.summarize(self.out, self.humans)["fake"]
        a = res["A"]
        self.assertEqual(a["n"], 6)
        self.assertEqual(a["fooled_strict"]["k"], 2)
        self.assertEqual(a["split"], 1)
        self.assertEqual(a["caught"]["k"], 3)
        self.assertEqual(a["fool_or_split"]["k"], 3)
        self.assertEqual(a["empty_ids"], ["ho-006"])
        self.assertAlmostEqual(a["cost_usd_total"], 10 * (1000 * 3 + 10 * 15) / 1e6, places=6)
        ref = res["strong_claude-opus-5-5"]
        self.assertEqual(ref["empty_ids"], ["ho-005"])  # missing row = caught
        self.assertEqual(ref["fooled_strict"]["k"], 2)
        v = a["vs_reference"]
        self.assertEqual(v["n_shared"], 6)
        self.assertEqual((v["only_system_fooled"], v["only_reference_fooled"], v["both_fooled"]), (1, 1, 1))
        self.assertAlmostEqual(v["fooled_strict_diff"], 0.0)
        self.assertEqual(v["sign_test_p"], 1.0)
        self.assertIsNone(ref["vs_reference"])

    def test_cfg_mismatch_refused(self):
        self._run(self.sys_a, FakeClient(self.decide))
        with self.assertRaises(SystemExit):
            S.run_system(self.sys_a, "fake", "other-model", S.make_call("other-model", FakeClient(self.decide)),
                         humans=self.humans, template=TEMPLATE, out_dir=self.out, log=lambda *_: None)

    def test_unparsed_is_retried_on_resume_and_excluded(self):
        self._run(self.sys_a, FakeClient(self.decide, "no idea {}"))
        res = S.summarize(self.out, self.humans)["fake"]["A"]
        self.assertEqual(res["n"], 1)  # only the empty id
        self.assertEqual(len(res["unparsed_ids"]), 5)
        c = FakeClient(self.decide)
        self.assertEqual(self._run(self.sys_a, c)["calls"], 10)

    def test_errors_retried_then_logged(self):
        class Boom(FakeClient):
            def create(self, messages, **params):
                self.calls.append(1)
                raise RuntimeError("down")
        S.time.sleep, orig = (lambda *_: None), S.time.sleep
        try:
            c = Boom(self.decide)
            r = self._run(self.sys_a, c)
        finally:
            S.time.sleep = orig
        self.assertEqual(r["errors"], 10)
        self.assertEqual(len(c.calls), 10 * S.TRIES)

    def test_budget_stop(self):
        b = S.Budget(0.0, 0.0)
        c = FakeClient(self.decide)
        r = self._run(self.sys_a, c, budget=b)
        self.assertEqual(r["calls"], 0)
        self.assertTrue(r["budget_stop"])

    def test_excluded_ids_dropped(self):
        held = os.path.join(self.tmp.name, "held.jsonl")
        write_jsonl(held, [{"id": "ho-001", "human": "a"}, {"id": "ho-007", "human": "b"}])
        exc = os.path.join(self.tmp.name, "exc.json")
        with open(exc, "w") as f:
            json.dump({"ids": ["ho-007"]}, f)
        self.assertEqual(S.load_humans(held, exc), {"ho-001": "a"})

    def test_real_exclusion_file(self):
        humans = S.load_humans()
        for i in S.excluded_ids():
            self.assertNotIn(i, humans)
        self.assertEqual(len(humans), 120 - len(S.excluded_ids()))


if __name__ == "__main__":
    unittest.main()
