"""run_frontier tests with a mocked SDK client (no network, no keys)."""
import json
import os
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_frontier as rf  # noqa: E402

SCHEMA = {"id", "system", "output", "latency_ms", "cost_usd", "prompt_tokens", "completion_tokens", "model",
          "temperature", "top_p", "max_tokens", "top_p_dropped", "truncated", "attempts", "retry_wait_ms",
          "price_in", "price_out"}


class StatusError(Exception):
    def __init__(self, status, retry_after=None):
        super().__init__(f"secret-ish message {status}")
        self.status_code = status
        self.response = NS(headers={"retry-after": retry_after} if retry_after else {})


class FakeAnthropic:
    """Records calls. fail(draft, n) -> exception for the first n calls on that draft (n=None: always)."""

    def __init__(self, reject_top_p=False, text="<think>plan</think>Plain rewrite.", stop_reason="end_turn",
                 fail=None):
        self.calls, self.reject_top_p, self.text, self.stop_reason = [], reject_top_p, text, stop_reason
        self.fail, self.seen, self.lock = fail or {}, {}, threading.Lock()
        self.messages = NS(create=self._create)

    def _create(self, **kw):
        draft = kw["messages"][0]["content"]
        with self.lock:
            self.calls.append(kw)
            self.seen[draft] = self.seen.get(draft, 0) + 1
            n = self.seen[draft]
        if draft in self.fail:
            status, times = self.fail[draft]
            if times is None or n <= times:
                raise StatusError(status)
        if self.reject_top_p and ("top_p" in kw or "temperature" in kw):
            raise ValueError("`temperature` is deprecated for this model.")  # Claude Opus 5.5 wording
        return NS(content=[NS(type="text", text=self.text)], stop_reason=self.stop_reason,
                  usage=NS(input_tokens=100, output_tokens=50))


class FakeOpenAI:
    def __init__(self, finish_reason="stop"):
        self.calls, self.finish_reason = [], finish_reason
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        return NS(choices=[NS(message=NS(content="Rewritten."), finish_reason=self.finish_reason)],
                  usage=NS(prompt_tokens=200, completion_tokens=80))


EVAL = [{"id": f"dev-{i:03d}", "ai_draft": f"Draft number {i}."} for i in range(1, 6)]
IDS = {e["id"] for e in EVAL}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out.jsonl")
        self._saved = rf.SLEEP, rf.RUNS_DIR, rf.git_commit
        rf.SLEEP, rf.RUNS_DIR, rf.git_commit = (lambda s: None), os.path.join(self.tmp.name, "runs"), lambda: "abc123"

    def tearDown(self):
        rf.SLEEP, rf.RUNS_DIR, rf.git_commit = self._saved
        self.tmp.cleanup()

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def go(self, client, rows=EVAL, model="claude-x", arm="live", **kw):
        return rf.run(rows, self.out, client, "anthropic", model, arm, 3.0, 15.0, **kw)


class TestPrompt(Base):
    def test_system_parsed_from_infer(self):
        s = rf.load_system()
        self.assertTrue(s.startswith("Rewrite the user's text"))
        self.assertTrue(s.endswith("Add nothing."))

    def test_strong_contains_system(self):
        live, strong = rf.system_prompt("live"), rf.system_prompt("strong")
        self.assertEqual(live, rf.load_system())
        self.assertTrue(strong.startswith(live + "\n\n"))
        self.assertGreater(len(strong), len(live) + 200)

    def test_strip_think(self):
        self.assertEqual(rf.strip_think("<think>a\nb</think>\n Out."), "Out.")
        self.assertEqual(rf.strip_think("Out.<think>unclosed"), "Out.")
        self.assertEqual(rf.strip_think(None), "")

    def test_source_text(self):
        self.assertEqual(rf.source_text({"id": "x", "input": "in"}), "in")
        with self.assertRaisesRegex(ValueError, "neither"):
            rf.source_text({"id": "x"})


class TestPrices(Base):
    TABLE = ("| provider | model | $/1M input | $/1M output | source URL | date read |\n|---|---|---|---|---|---|\n"
             "| anthropic | m-1 | 3.00 | 15 | https://x | 2026-11-02 |\n| openai | m-2 | TODO | TODO | TODO | TODO |\n")

    def test_cost_math(self):
        self.assertAlmostEqual(rf.cost_usd(1_000_000, 0, 3.0, 15.0), 3.0)
        self.assertAlmostEqual(rf.cost_usd(100, 50, 3.0, 15.0), (100 * 3 + 50 * 15) / 1e6)

    def test_reads_row(self):
        p = self.write(os.path.join(self.tmp.name, "P.md"), self.TABLE)
        self.assertEqual(rf.load_prices("anthropic", "m-1", p), (3.0, 15.0))

    def test_missing_or_todo_errors(self):
        p = self.write(os.path.join(self.tmp.name, "P.md"), self.TABLE)
        with self.assertRaisesRegex(rf.PriceError, "no row"):
            rf.load_prices("anthropic", "other", p)
        with self.assertRaisesRegex(rf.PriceError, "not a number"):
            rf.load_prices("openai", "m-2", p)

    def test_cli_exits_on_missing_price_before_any_request(self):
        ev = self.write(os.path.join(self.tmp.name, "e.jsonl"), "")
        orig = rf.make_client
        rf.make_client = lambda p: self.fail("client created despite missing price")
        try:
            code = rf.main([ev, self.out, "--provider", "openai", "--model", "no-such-model", "--arm", "live"])
        finally:
            rf.make_client = orig
        self.assertEqual(code, 2)


class TestRun(Base):
    def test_schema_and_request(self):
        c = FakeAnthropic()
        rows, failures = self.go(c, concurrency=2)
        self.assertEqual((len(rows), failures), (5, []))
        self.assertEqual([r["id"] for r in rows], sorted(IDS))
        for r in rows:
            self.assertTrue(SCHEMA <= set(r), SCHEMA - set(r))
            self.assertEqual(r["system"], "frontier-live:claude-x")
            self.assertEqual(r["output"], "Plain rewrite.")
            self.assertEqual((r["prompt_tokens"], r["completion_tokens"]), (100, 50))
            self.assertAlmostEqual(r["cost_usd"], (100 * 3 + 50 * 15) / 1e6)
            self.assertEqual((r["temperature"], r["top_p"], r["max_tokens"]), (0.7, 0.9, 400))
            self.assertEqual((r["price_in"], r["price_out"], r["attempts"]), (3.0, 15.0, 1))
            self.assertFalse(r["truncated"] or r["top_p_dropped"])
        kw = c.calls[0]
        self.assertEqual(kw["system"], rf.load_system())
        self.assertEqual((kw["temperature"], kw["top_p"], kw["max_tokens"]), (0.7, 0.9, 400))
        self.assertEqual(rf.check_out(rows, IDS, IDS), [])

    def test_openai_request_and_truncation(self):
        c = FakeOpenAI(finish_reason="length")
        rows, _ = rf.run(EVAL, self.out, c, "openai", "gpt-x", "strong", 1.0, 2.0, limit=2)
        self.assertEqual([r["id"] for r in rows], ["dev-001", "dev-002"])
        kw = c.calls[0]
        self.assertEqual(kw["messages"][0], {"role": "system", "content": rf.system_prompt("strong")})
        self.assertEqual((kw["temperature"], kw["top_p"]), (0.7, 0.9))
        self.assertEqual(rows[0]["system"], "frontier-strong:gpt-x")
        self.assertAlmostEqual(rows[0]["cost_usd"], (200 * 1 + 80 * 2) / 1e6)
        self.assertTrue(all(r["truncated"] for r in rows))

    def test_anthropic_truncation_flag(self):
        rows, _ = self.go(FakeAnthropic(stop_reason="max_tokens"), rows=EVAL[:1])
        self.assertTrue(rows[0]["truncated"])
        self.assertIn("truncated=1", rf.summary(rows, "x"))

    def test_resume_skips_existing(self):
        prior = {"id": "dev-002", "system": "frontier-live:claude-x", "output": "kept", "latency_ms": 1,
                 "cost_usd": 0, "prompt_tokens": 0, "completion_tokens": 0, "model": "claude-x"}
        self.write(self.out, json.dumps(prior) + "\n")
        c = FakeAnthropic()
        rows, _ = self.go(c)
        self.assertEqual(len(c.calls), 4)
        self.assertNotIn("Draft number 2.", [k["messages"][0]["content"] for k in c.calls])
        self.assertEqual([r["output"] for r in rows if r["id"] == "dev-002"], ["kept"])
        c2 = FakeAnthropic()
        self.go(c2)
        self.assertEqual(c2.calls, [])

    def test_resume_drops_empty_rows(self):
        prior = {"id": "dev-001", "system": "frontier-live:claude-x", "output": "  ", "model": "claude-x"}
        self.write(self.out, json.dumps(prior) + "\n")
        c = FakeAnthropic()
        rows, _ = self.go(c)
        self.assertEqual(len(c.calls), 5)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rf.check_out(rows, IDS, IDS), [])

    def test_resume_tolerates_cut_off_last_line(self):
        good = {"id": "dev-001", "system": "frontier-live:claude-x", "output": "kept", "latency_ms": 1,
                "cost_usd": 0, "model": "claude-x"}
        self.write(self.out, json.dumps(good) + "\n" + '{"id": "dev-002", "outp')
        c = FakeAnthropic()
        rows, _ = self.go(c)
        self.assertEqual(len(c.calls), 4)
        self.assertEqual([r["id"] for r in rows], sorted(IDS))
        self.assertEqual(len(rf.read_jsonl(self.out)), 5)

    def test_resume_with_other_model_aborts(self):
        prior = {"id": "dev-001", "system": "frontier-live:claude-old", "output": "x", "model": "claude-old"}
        self.write(self.out, json.dumps(prior) + "\n")
        c = FakeAnthropic()
        with self.assertRaisesRegex(rf.ResumeError, "different OUT"):
            self.go(c)
        self.assertEqual(c.calls, [])

    def test_duplicate_eval_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.go(FakeAnthropic(), rows=EVAL + EVAL[:1])

    def test_sampling_rejected_sends_none_and_learns_once(self):
        rf.SAMPLING_REJECTED.clear()
        self.addCleanup(rf.SAMPLING_REJECTED.clear)
        c = FakeAnthropic(reject_top_p=True)
        rows, _ = self.go(c, rows=EVAL[:1], model="claude-new")
        self.assertEqual(len(c.calls), 2)
        self.assertNotIn("temperature", c.calls[1])
        self.assertNotIn("top_p", c.calls[1])
        r = rows[0]
        self.assertTrue(r["top_p_dropped"])
        self.assertIsNone(r["temperature"])
        self.assertIsNone(r["top_p"])
        self.assertIn("provider default", r["decoding_note"])
        c2 = FakeAnthropic(reject_top_p=True)  # model now known: no rejected first call
        rf.complete(c2, "anthropic", "claude-new", "sys", "draft")
        self.assertEqual(len(c2.calls), 1)
        self.assertNotIn("temperature", c2.calls[0])

    def test_unrelated_400_not_swallowed(self):
        rf.SAMPLING_REJECTED.clear()
        self.assertFalse(rf._rejects_sampling(ValueError("max_tokens: must be at least 1")))
        self.assertTrue(rf._rejects_sampling(ValueError("`top_p` is deprecated for this model.")))

    def test_mixed_decoding_warns(self):
        rows = [{"latency_ms": 1, "cost_usd": 0, "temperature": 0.7, "top_p": 0.9, "max_tokens": 400},
                {"latency_ms": 1, "cost_usd": 0, "temperature": 0.7, "top_p": None, "max_tokens": 400}]
        self.assertIn("WARNING_MIXED_DECODING", rf.summary(rows, "x"))

    def test_empty_output_not_written(self):
        rows, failures = self.go(FakeAnthropic(text="<think>only</think>"), rows=EVAL[:2])
        self.assertEqual(rows, [])
        self.assertEqual({f["error"] for f in failures}, {"EmptyOutput"})
        self.assertTrue(rf.check_out(rows, {"dev-001", "dev-002"}, IDS))

    def test_transient_errors_retried(self):
        c = FakeAnthropic(fail={"Draft number 1.": (429, 2)})
        rows, failures = self.go(c, rows=EVAL[:1])
        self.assertEqual(failures, [])
        self.assertEqual(rows[0]["attempts"], 3)
        self.assertGreater(rows[0]["retry_wait_ms"], 0)

    def test_client_error_not_retried(self):
        c = FakeAnthropic(fail={"Draft number 1.": (401, None)})
        rows, failures = self.go(c, rows=EVAL[:1])
        self.assertEqual(len(c.calls), 1)
        self.assertEqual(failures, [{"id": "dev-001", "error": "StatusError", "status": 401, "attempts": 1}])

    def test_failing_id_not_written_and_retried_on_resume(self):
        c = FakeAnthropic(fail={"Draft number 3.": (500, None)})
        rows, failures = self.go(c)
        self.assertEqual(sorted(r["id"] for r in rows), sorted(IDS - {"dev-003"}))
        self.assertEqual(failures[0]["attempts"], rf.MAX_ATTEMPTS)
        fails = rf.read_jsonl(self.out + ".failures.jsonl")
        self.assertEqual([f["id"] for f in fails], ["dev-003"])
        self.assertNotIn("secret", json.dumps(fails))
        c2 = FakeAnthropic()
        rows, failures = self.go(c2)
        self.assertEqual([k["messages"][0]["content"] for k in c2.calls], ["Draft number 3."])
        self.assertEqual((len(rows), failures), (5, []))
        self.assertFalse(os.path.exists(self.out + ".failures.jsonl"))

    def test_concurrency_with_failure_no_duplicates(self):
        many = [{"id": f"dev-{i:03d}", "ai_draft": f"Draft number {i}."} for i in range(1, 41)]
        c = FakeAnthropic(fail={"Draft number 17.": (503, None)})
        rows, failures = self.go(c, rows=many, concurrency=4)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), 39)
        self.assertEqual(len(set(ids)), 39)
        self.assertEqual([f["id"] for f in failures], ["dev-017"])
        rows, _ = self.go(FakeAnthropic(), rows=many, concurrency=4)
        all_ids = {r["id"] for r in many}
        self.assertEqual(rf.check_out(rows, all_ids, all_ids), [])

    def test_check_out_set_checks(self):
        rows = [{"id": "dev-001", "output": "a"}, {"id": "zzz", "output": "b"}]
        problems = " ".join(rf.check_out(rows, {"dev-001", "dev-002"}, IDS))
        self.assertIn("missing", problems)
        self.assertIn("not in the eval file", problems)

    def test_main_exit_1_on_failures(self):
        ev = self.write(os.path.join(self.tmp.name, "e.jsonl"), "".join(json.dumps(e) + "\n" for e in EVAL[:2]))
        orig = rf.make_client
        rf.make_client = lambda p: FakeAnthropic(fail={"Draft number 2.": (500, None)})
        try:
            code = rf.main([ev, self.out, "--provider", "anthropic", "--model", "m", "--arm", "live",
                            "--price-in", "1", "--price-out", "2"])
        finally:
            rf.make_client = orig
        self.assertEqual(code, 1)


class TestManifest(Base):
    FIELDS = {"system", "provider", "model", "arm", "prompt_sha256", "decoding", "price_in", "price_out",
              "git_commit", "eval_path", "eval_sha256", "rows", "started_utc", "finished_utc", "cost_usd",
              "latency_ms_p50", "latency_ms_p95"}

    def eval_file(self, name="eval_all.jsonl"):
        return self.write(os.path.join(self.tmp.name, name), "".join(json.dumps(e) + "\n" for e in EVAL))

    def manifest(self, arm="strong", ev=None):
        ev = ev or self.eval_file()
        rows, _ = self.go(FakeAnthropic(), model="claude-opus-5-5", arm=arm)
        return rf.build_manifest(rows, provider="anthropic", model="claude-opus-5-5", arm=arm, eval_path=ev,
                                 out_path=self.out, price_in=3.0, price_out=15.0, started="s", finished="f")

    def test_fields_and_values(self):
        m = self.manifest()
        self.assertTrue(self.FIELDS <= set(m), self.FIELDS - set(m))
        self.assertEqual(m["system"], "frontier-strong:claude-opus-5-5")
        self.assertEqual((m["rows"], m["git_commit"]), (5, "abc123"))
        self.assertEqual(m["decoding"], {"temperature": 0.7, "top_p": 0.9, "max_tokens": 400, "top_p_dropped": 0, "thinking": ["off"],
                                         "requested": {"temperature": 0.7, "top_p": 0.9}})
        self.assertAlmostEqual(m["cost_usd"], 5 * (100 * 3 + 50 * 15) / 1e6)
        self.assertIsNotNone(m["latency_ms_p95"])

    def test_hashes_stable_and_arm_specific(self):
        ev = self.eval_file()
        a, b = self.manifest(ev=ev), self.manifest(ev=ev)
        self.assertEqual((a["prompt_sha256"], a["eval_sha256"]), (b["prompt_sha256"], b["eval_sha256"]))
        self.assertEqual(a["prompt_sha256"], rf.sha256_text(rf.load_system() + "\n\n" + open(rf.STRONG_PATH, encoding="utf-8").read().strip()))
        os.remove(self.out)
        self.assertNotEqual(self.manifest(arm="live", ev=ev)["prompt_sha256"], a["prompt_sha256"])
        self.assertEqual(len(a["eval_sha256"]), 64)

    def test_write_paths_and_slug(self):
        ev = self.eval_file()
        m = self.manifest(ev=ev)
        p = rf.write_manifest(m, ev)
        self.assertEqual(os.path.basename(p), "frontier-strong_claude-opus-5-5.json")
        hp = rf.write_manifest(m, os.path.join(self.tmp.name, "heldout_pairs.jsonl"))
        self.assertTrue(hp.endswith("_heldout.json"))
        with open(p, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["eval_sha256"], m["eval_sha256"])
        self.assertEqual(rf.slug("a:b/c"), "a_b_c")

    def test_default_out(self):
        self.assertTrue(rf.default_out("strong", "claude-opus-5-5", "evals/eval_all.jsonl")
                        .endswith(os.path.join("evals", "runs", "hack_strong_claude-opus-5-5.jsonl")))
        self.assertTrue(rf.default_out("live", "x/y", "evals/heldout_pairs.jsonl").endswith("hack_live_x_y_heldout.jsonl"))

    def test_main_writes_manifest_on_resume(self):
        ev = self.eval_file()
        orig = rf.make_client
        rf.make_client = lambda p: FakeAnthropic()
        args = [ev, self.out, "--provider", "anthropic", "--model", "m", "--arm", "live",
                "--price-in", "1", "--price-out", "2"]
        try:
            self.assertEqual(rf.main(args + ["--limit", "2"]), 0)
            mp = os.path.join(rf.RUNS_DIR, "frontier-live_m.json")
            with open(mp, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["rows"], 2)
            self.assertEqual(rf.main(args), 0)
            with open(mp, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["rows"], 5)
        finally:
            rf.make_client = orig

    def test_percentile(self):
        self.assertEqual(rf._pct(list(range(1, 101)), 50), 50)
        self.assertEqual(rf._pct(list(range(1, 101)), 95), 95)
        self.assertEqual(rf._pct([7], 95), 7)
        self.assertIsNone(rf._pct([], 50))


if __name__ == "__main__":
    unittest.main()
