"""Frontier baseline runner: same prompt and decoding as every other system, logged in the shared outputs schema.

Arms:      live = exact SYSTEM from pipeline/infer.py; strong = SYSTEM + FRONTIER_STRONG.md (labelled extra prompting).
Prompt:    load_system(path) parses SYSTEM with ast (infer.py imports torch); system_prompt(arm) builds the arm's prompt.
Prices:    load_prices(provider, model, path) -> (usd_per_1m_in, usd_per_1m_out) from hackathon/report/PRICES.md.
           cost_usd(prompt_tokens, completion_tokens, price_in, price_out).
Requests:  make_client(provider) (SDK retries off, timeout 120 s); complete(...) runs our own retry loop
           (5 attempts, exp backoff, Retry-After honoured; only 429/5xx/timeout/connection errors).
Run:       run(eval_rows, out_path, client, ...) -> (rows, failures). Resumes by id, appends under a lock, rewrites
           OUT sorted by id; failures go to OUT + ".failures.jsonl". check_out(...) -> list of problems.
Manifest:  build_manifest(...) -> dict; write_manifest(m) -> hackathon/runs/<slug(label)>.json, rewritten every run
           (prompt + eval sha256, decoding, prices, git commit, row count, UTC times, cost, latency p50/p95).
CLI:       python run_frontier.py EVAL.jsonl [OUT.jsonl] --provider anthropic|openai --model ID --arm live|strong
                  [--concurrency 4] [--limit N] [--price-in X --price-out Y]
           OUT defaults to default_out(): evals/runs/hack_<arm>_<model>.jsonl, + "_heldout" when EVAL is
           evals/heldout_pairs.jsonl. Run eval_all.jsonl (130) and heldout_pairs.jsonl (120) as separate files.
           F1 = --provider anthropic --model claude-opus-5-5 --arm strong, plus an --arm live row.
           No Gemini provider: google-genai is not installed here.
Rows add, beyond the shared schema: temperature, top_p, max_tokens, top_p_dropped, truncated, attempts,
retry_wait_ms, price_in, price_out (USD per 1M), and decoding_note when top_p was dropped.
Disclosure: infer.py also uses repetition_penalty=1.05 and enable_thinking=False on the open models; frontier APIs
have no repetition penalty. Models that refuse sampling params (Claude Opus 5.5) run with provider-default sampling,
adaptive thinking at effort low and max_tokens 1500 (see NO_SAMPLING); each row records what was sent.
Keys come from the environment, ~/.config/humanlm/keys.env ($HUMANLM_KEYS), then the repo .env; they are never printed, and neither are raw error messages.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
INFER_PATH = os.path.join(ROOT, "pipeline", "infer.py")
STRONG_PATH = os.path.join(HERE, "FRONTIER_STRONG.md")
PRICES_PATH = os.path.join(ROOT, "hackathon", "report", "PRICES.md")
RUNS_DIR = os.path.join(ROOT, "hackathon", "runs")  # manifests
OUT_DIR = os.path.join(ROOT, "evals", "runs")

TEMPERATURE, TOP_P, MAX_TOKENS = 0.7, 0.9, 400
MAX_ATTEMPTS, TIMEOUT_S, BACKOFF_S, BACKOFF_CAP_S = 5, 120, 1.0, 60.0
RETRY_NAMES = {"APITimeoutError", "APIConnectionError", "RateLimitError", "InternalServerError"}
THINK = re.compile(r"<think>.*?(?:</think>|\Z)", re.S | re.I)
SLEEP = time.sleep  # patched in tests


class PriceError(ValueError):
    pass


class ResumeError(ValueError):
    pass


class EmptyOutput(RuntimeError):
    pass


# --- prompt ---

def load_system(path: str = INFER_PATH) -> str:
    """The SYSTEM string literal from infer.py, without importing it."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"no SYSTEM assignment in {path}")


def system_prompt(arm: str, infer_path: str = INFER_PATH, strong_path: str = STRONG_PATH) -> str:
    system = load_system(infer_path)
    if arm == "live":
        return system
    if arm == "strong":
        with open(strong_path, encoding="utf-8") as f:
            return system + "\n\n" + f.read().strip()
    raise ValueError(f"unknown arm {arm!r}")


def strip_think(text: str | None) -> str:
    return THINK.sub("", text or "").strip()


def source_text(row: dict) -> str:
    src = row.get("ai_draft") or row.get("input")
    if not src:
        raise ValueError(f"eval row {row.get('id')!r} has neither 'ai_draft' nor 'input'")
    return src


# --- prices ---

def _num(cell: str) -> float | None:
    try:
        return float(cell.replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def load_prices(provider: str, model: str, path: str = PRICES_PATH) -> tuple[float, float]:
    """USD per 1M (input, output) tokens for the exact provider+model row; PriceError if missing or TODO."""
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in f if ln.lstrip().startswith("|")]
    for cells in rows:
        if len(cells) >= 4 and cells[0].lower() == provider.lower() and cells[1] == model:
            p_in, p_out = _num(cells[2]), _num(cells[3])
            if p_in is None or p_out is None:
                raise PriceError(f"{path}: price for {provider} {model} is not a number ({cells[2]!r}, {cells[3]!r}); "
                                 "fill it from the provider's pricing page or pass --price-in/--price-out")
            return p_in, p_out
    raise PriceError(f"{path}: no row for provider={provider!r} model={model!r}; "
                     "add one from the provider's pricing page or pass --price-in/--price-out")


def cost_usd(prompt_tokens: int, completion_tokens: int, price_in: float, price_out: float) -> float:
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000


# --- requests ---

def make_client(provider: str):
    from dotenv import load_dotenv
    try:  # use the OS certificate store (HTTPS-inspecting proxies); verification stays on
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    # keys.env outside the repo first (CONTRACT with Ali), then repo .env; first value wins
    load_dotenv(os.environ.get("HUMANLM_KEYS", os.path.expanduser("~/.config/humanlm/keys.env")))
    load_dotenv(os.path.join(ROOT, ".env"))
    if provider == "anthropic":
        import anthropic
        return anthropic.Anthropic(max_retries=0, timeout=TIMEOUT_S)
    if provider == "openai":
        import openai
        return openai.OpenAI(max_retries=0, timeout=TIMEOUT_S)
    raise ValueError(f"unknown provider {provider!r}")


def _status(err: Exception) -> int | None:
    s = getattr(err, "status_code", None)
    return s if isinstance(s, int) else None


def _retryable(err: Exception) -> bool:
    s = _status(err)
    return type(err).__name__ in RETRY_NAMES or s == 429 or (s is not None and s >= 500)


def _wait_s(err: Exception, attempt: int) -> float:
    try:
        ra = float(getattr(getattr(err, "response", None), "headers", {}).get("retry-after"))
        return min(max(ra, 0.0), BACKOFF_CAP_S)
    except (TypeError, ValueError, AttributeError):
        return min(BACKOFF_S * 2 ** (attempt - 1), BACKOFF_CAP_S)


def _with_retries(fn) -> tuple[object, int, float, float]:
    """Call fn until success. Returns (result, attempts, retry_wait_ms, latency_ms of the successful attempt).
    On final failure the exception gets .attempts set."""
    waited = 0.0
    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.perf_counter()
        try:
            r = fn()
            return r, attempt, waited * 1000, (time.perf_counter() - t0) * 1000
        except Exception as e:
            if attempt == MAX_ATTEMPTS or not _retryable(e):
                e.attempts = attempt
                raise
            w = _wait_s(e, attempt)
            waited += w
            SLEEP(w)
    raise AssertionError("unreachable")


SAMPLING_REJECTED: set[str] = set()  # models that refuse temperature/top_p; learned once per run
# Those models (Claude Opus 5.5) also refuse thinking "disabled": lowest setting is adaptive at effort "low".
# Thinking tokens count against max_tokens, so the cap is raised to leave room for the ~150-token rewrite.
NO_SAMPLING = {"thinking": {"type": "adaptive"}, "extra_body": {"output_config": {"effort": "low"}}, "max_tokens": 1500}


def _rejects_sampling(err: Exception) -> bool:
    """Claude Opus 5.5 answers 400 '`temperature` is deprecated for this model' (same for top_p, top_k)."""
    msg = str(err).lower()  # inspected, never printed
    return ("temperature" in msg or "top_p" in msg) and ("deprecated" in msg or "not supported" in msg
                                                          or "cannot both be specified" in msg)


def complete(client, provider: str, model: str, system: str, user: str) -> dict:
    """One logical request (with retries). Returns text, tokens, truncation, effective decoding and retry stats."""
    dec = {"temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": MAX_TOKENS, "top_p_dropped": False}
    if provider == "openai":
        r, att, wait, ms = _with_retries(lambda: client.chat.completions.create(
            model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=TEMPERATURE, top_p=TOP_P, max_completion_tokens=MAX_TOKENS))
        ch = r.choices[0]
        return {**dec, "text": ch.message.content or "", "pt": r.usage.prompt_tokens,
                "ct": r.usage.completion_tokens, "truncated": ch.finish_reason == "length",
                "attempts": att, "retry_wait_ms": wait, "latency_ms": ms}
    kw = dict(model=model, system=system, messages=[{"role": "user", "content": user}],
              max_tokens=MAX_TOKENS, temperature=TEMPERATURE, top_p=TOP_P)
    no_sampling = {"temperature": None, "top_p": None, "top_p_dropped": True,
                   "max_tokens": NO_SAMPLING["max_tokens"], "thinking": "adaptive, effort low"}
    extra = 0
    if model in SAMPLING_REJECTED:
        kw.pop("temperature"), kw.pop("top_p")
        kw.update(NO_SAMPLING)
        dec.update(no_sampling)
    try:
        r, att, wait, ms = _with_retries(lambda: client.messages.create(**kw))
    except Exception as e:
        # Newer Claude models refuse every sampling parameter: send none (provider default sampling), say so per row.
        if "temperature" not in kw or not _rejects_sampling(e):
            raise
        SAMPLING_REJECTED.add(model)
        kw.pop("temperature"), kw.pop("top_p")
        kw.update(NO_SAMPLING)
        dec.update(no_sampling)
        extra = getattr(e, "attempts", 1)
        r, att, wait, ms = _with_retries(lambda: client.messages.create(**kw))
    text = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "text") == "text")
    return {**dec, "text": text, "pt": r.usage.input_tokens, "ct": r.usage.output_tokens,
            "truncated": getattr(r, "stop_reason", None) == "max_tokens",
            "attempts": att + extra, "retry_wait_ms": wait, "latency_ms": ms}


def run_row(row: dict, client, provider: str, model: str, system: str, label: str,
            price_in: float, price_out: float) -> dict:
    c = complete(client, provider, model, system, source_text(row))
    output = strip_think(c["text"])
    if not output:
        raise EmptyOutput(f"empty output for {row['id']}")
    out = {"id": row["id"], "system": label, "output": output, "latency_ms": round(c["latency_ms"]),
           "cost_usd": round(cost_usd(c["pt"], c["ct"], price_in, price_out), 8),
           "prompt_tokens": c["pt"], "completion_tokens": c["ct"], "model": model,
           "temperature": c["temperature"], "top_p": c["top_p"], "max_tokens": c["max_tokens"],
           "top_p_dropped": c["top_p_dropped"], "truncated": c["truncated"], "attempts": c["attempts"],
           "retry_wait_ms": round(c["retry_wait_ms"]), "price_in": price_in, "price_out": price_out}
    if c["top_p_dropped"]:
        out["decoding_note"] = ("model rejects temperature/top_p and disabling thinking: sent no sampling params "
                                "(provider default sampling), adaptive thinking at effort low, max_tokens 1500")
        out["thinking"] = c.get("thinking")
    return out


# --- files ---

def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def write_jsonl(path: str, rows: list[dict]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def load_existing(out_path: str, label: str, model: str) -> list[dict]:
    """Rows already in OUT, cleaned: a cut-off last line and empty outputs are dropped, the file is rewritten
    sorted by id. ResumeError if a row is from another system/model, malformed mid-file, or duplicated."""
    if not os.path.exists(out_path):
        return []
    with open(out_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    rows = []
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            if i == len(lines) - 1:  # partial write at the end of the file: drop it
                print(f"note: dropped a cut-off last line in {out_path}", file=sys.stderr)
                continue
            raise ResumeError(f"{out_path}: line {i + 1} is not valid JSON")
    for r in rows:
        if r.get("system") != label or r.get("model") != model:
            raise ResumeError(f"{out_path} holds rows for system={r.get('system')!r} model={r.get('model')!r}, "
                              f"not {label!r} / {model!r}; use a different OUT file")
    rows = [r for r in rows if (r.get("output") or "").strip()]
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ResumeError(f"{out_path}: duplicate ids in existing rows")
    rows.sort(key=lambda r: r["id"])
    write_jsonl(out_path, rows)
    return rows


def check_out(rows: list[dict], expected_ids: set[str], eval_ids: set[str]) -> list[str]:
    """Problems with the final file (empty list = OK)."""
    ids = [r["id"] for r in rows]
    problems = []
    if len(set(ids)) != len(ids):
        problems.append("duplicate ids in output")
    missing = sorted(expected_ids - set(ids))
    if missing:
        problems.append(f"{len(missing)} expected ids missing (rerun to resume): {missing[:5]}")
    extra = sorted(set(ids) - eval_ids)
    if extra:
        problems.append(f"{len(extra)} output ids not in the eval file: {extra[:5]}")
    empty = [r["id"] for r in rows if not (r.get("output") or "").strip()]
    if empty:
        problems.append(f"empty outputs for {empty[:5]}")
    return problems


# --- run ---

def run(eval_rows: list[dict], out_path: str, client, provider: str, model: str, arm: str,
        price_in: float, price_out: float, concurrency: int = 4, limit: int | None = None
        ) -> tuple[list[dict], list[dict]]:
    eval_ids = [r["id"] for r in eval_rows]
    if len(set(eval_ids)) != len(eval_ids):
        raise ValueError("eval file has duplicate ids")
    selected = eval_rows[:limit] if limit is not None else eval_rows
    system, label = system_prompt(arm), f"frontier-{arm}:{model}"
    done = {r["id"] for r in load_existing(out_path, label, model)}
    todo = [r for r in selected if r["id"] not in done]
    lock, failures = threading.Lock(), []
    pool = ThreadPoolExecutor(max_workers=concurrency)
    try:
        with open(out_path, "a", encoding="utf-8") as out:
            futs = {pool.submit(run_row, r, client, provider, model, system, label, price_in, price_out): r["id"]
                    for r in todo}
            for fut in as_completed(futs):
                try:
                    row = fut.result()
                except Exception as e:  # leave the id for the next resume
                    fail = {"id": futs[fut], "error": type(e).__name__, "status": _status(e),
                            "attempts": getattr(e, "attempts", 1)}
                    failures.append(fail)
                    print(f"FAIL {fail['id']}: {fail['error']} status={fail['status']}", file=sys.stderr)
                    continue
                with lock:
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out.flush()
    except BaseException:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown()
    fail_path = out_path + ".failures.jsonl"
    if failures:
        write_jsonl(fail_path, sorted(failures, key=lambda f: f["id"]))
    elif os.path.exists(fail_path):
        os.remove(fail_path)
    rows = sorted(read_jsonl(out_path), key=lambda r: r["id"])
    write_jsonl(out_path, rows)
    return rows, failures


def summary(rows: list[dict], label: str, failures: list[dict] = ()) -> str:
    lat = sorted(r["latency_ms"] for r in rows)
    cost = sum(r["cost_usd"] for r in rows)
    trunc = sum(1 for r in rows if r.get("truncated"))
    dec = {(r.get("temperature"), r.get("top_p"), r.get("max_tokens")) for r in rows}
    line = (f"RUN_FRONTIER_DONE {label} rows={len(rows)} failures={len(failures)} cost_usd={cost:.4f} "
            f"latency_p50_ms={lat[len(lat) // 2] if lat else 'NA'} truncated={trunc} "
            f"top_p_dropped={sum(1 for r in rows if r.get('top_p_dropped'))}")
    if len(dec) > 1:
        line += f" WARNING_MIXED_DECODING={sorted(dec, key=str)}"
    return line


# --- manifest ---

def slug(text: str) -> str:
    return text.replace(":", "_").replace("/", "_")


def is_heldout(eval_path: str) -> bool:
    return "heldout" in os.path.basename(eval_path)


def default_out(arm: str, model: str, eval_path: str) -> str:
    return os.path.join(OUT_DIR, f"hack_{arm}_{slug(model)}{'_heldout' if is_heldout(eval_path) else ''}.jsonl")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=10, check=True).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _pct(sorted_vals: list[float], q: float) -> float | None:
    """Nearest-rank percentile."""
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, max(0, -(-len(sorted_vals) * q // 100) - 1))]


def _rel(path: str) -> str:
    try:
        return os.path.relpath(path, ROOT).replace(os.sep, "/")
    except ValueError:  # other drive on Windows
        return path


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sent_decoding(rows: list[dict]) -> dict:
    """What was actually sent (from the rows); 'mixed' if rows differ, the requested values if there are no rows."""
    out = {}
    for k, default in (("temperature", TEMPERATURE), ("top_p", TOP_P), ("max_tokens", MAX_TOKENS)):
        vals = {r.get(k) for r in rows}
        out[k] = default if not rows else vals.pop() if len(vals) == 1 else "mixed"
    return out


def build_manifest(rows: list[dict], *, provider: str, model: str, arm: str, eval_path: str, out_path: str,
                   price_in: float, price_out: float, started: str, finished: str) -> dict:
    label = f"frontier-{arm}:{model}"
    lat = sorted(r["latency_ms"] for r in rows)
    return {
        "system": label, "provider": provider, "model": model, "arm": arm,
        "prompt_sha256": sha256_text(system_prompt(arm)),
        "decoding": {**_sent_decoding(rows), "thinking": sorted({r.get("thinking") or "off" for r in rows}),
                     "requested": {"temperature": TEMPERATURE, "top_p": TOP_P},
                     "top_p_dropped": sum(1 for r in rows if r.get("top_p_dropped"))},
        "price_in": price_in, "price_out": price_out, "price_unit": "USD per 1M tokens",
        "git_commit": git_commit(),
        "eval_path": _rel(eval_path), "eval_sha256": sha256_file(eval_path), "out_path": _rel(out_path),
        "rows": len(rows), "started_utc": started, "finished_utc": finished,
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 8),
        "latency_ms_p50": _pct(lat, 50), "latency_ms_p95": _pct(lat, 95),
    }


def write_manifest(m: dict, eval_path: str, runs_dir: str | None = None) -> str:
    """hackathon/runs/<slug(label)>[_heldout].json; the suffix keeps the two eval sets from overwriting."""
    runs_dir = runs_dir or RUNS_DIR
    os.makedirs(runs_dir, exist_ok=True)
    path = os.path.join(runs_dir, slug(m["system"]) + ("_heldout" if is_heldout(eval_path) else "") + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("eval")
    ap.add_argument("out", nargs="?", help="default: evals/runs/hack_<arm>_<model>[_heldout].jsonl")
    ap.add_argument("--provider", required=True, choices=["anthropic", "openai"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--arm", required=True, choices=["live", "strong"])
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--price-in", type=float, help="USD per 1M input tokens (overrides PRICES.md)")
    ap.add_argument("--price-out", type=float, help="USD per 1M output tokens (overrides PRICES.md)")
    a = ap.parse_args(argv)
    if (a.price_in is None) != (a.price_out is None):
        ap.error("pass both --price-in and --price-out, or neither")
    try:
        p_in, p_out = (a.price_in, a.price_out) if a.price_in is not None else load_prices(a.provider, a.model)
    except PriceError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    a.out = a.out or default_out(a.arm, a.model, a.eval)
    eval_rows = read_jsonl(a.eval)
    label, started = f"frontier-{a.arm}:{a.model}", utc_now()
    try:
        rows, failures = run(eval_rows, a.out, make_client(a.provider), a.provider, a.model, a.arm,
                             p_in, p_out, a.concurrency, a.limit)
    except (ResumeError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    selected = eval_rows[:a.limit] if a.limit is not None else eval_rows
    problems = check_out(rows, {r["id"] for r in selected}, {r["id"] for r in eval_rows})
    m = build_manifest(rows, provider=a.provider, model=a.model, arm=a.arm, eval_path=a.eval, out_path=a.out,
                       price_in=p_in, price_out=p_out, started=started, finished=utc_now())
    print(f"manifest: {write_manifest(m, a.eval)}")
    print(summary(rows, label, failures))
    if problems:
        print("ERROR: " + "; ".join(problems) + (f" (see {a.out}.failures.jsonl)" if failures else ""),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
