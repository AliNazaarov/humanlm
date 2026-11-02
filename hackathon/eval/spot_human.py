"""Spot the human: can an open-model judge tell the real human original from a system's rewrite?

Ground truth, eval only (never a reward). CONTRACT hackathon/bus/msgs/20261102T204421Z-ali-to-friend.md.
On evals/heldout_pairs.jsonl (120 real human originals; the ids in hackathon/report/heldout_excluded.json
are dropped before anything else, so 117 are scored and the excluded texts never reach a judge), per system and id the judge sees the human
original and the system output as "Text 1"/"Text 2" in BOTH orders (prompt: SPOT_HUMAN_PROMPT.md):
  order "HS": human is Text 1, system is Text 2;  order "SH": system is Text 1, human is Text 2.
Per id:  fooled_strict = judge picks the system output as human in both orders;
         caught        = judge picks the human original in both orders;
         split         = the two orders disagree.
An empty or missing system output (a refusal, e.g. Claude strong ho-013/ho-054) is never sent to the
judge: it counts as caught and is listed under `empty_ids`. An id whose answer could not be parsed in
some order is left out of n and listed under `unparsed_ids`.

Rows:    hackathon/report/spot_human/<judge>_<system>.jsonl, one per (id, order); each carries `cfg`
         (judge config hash: model, provider, temperature, max_tokens, reasoning_effort, prompt) and `io`
         (hash of human + output). A cfg mismatch refuses the run (--fresh deletes); an io mismatch
         re-judges that id. Resume skips every (id, order) already parsed.
Summary: hackathon/report/spot_human.json {judge: {system: {...}}} rebuilt from all row files: fool
         strict / fool-or-split / caught rates with exact 95% CIs (stats.rate_ci), n, chrF vs the human
         original (audit.chrf, empty output = 0, mean over all scored ids), and, vs the reference system
         (Claude strong) on shared ids, paired_bootstrap_diff on fooled_strict plus a sign test on the
         ids where exactly one of the two systems fooled the judge.
Client:  judge.make_client / request_params (truststore, keys from ~/.config/humanlm/keys.env), judge._strip
         drops reasoning text. Every call is retried 3 times on any error.

CLI:  python hackathon/eval/spot_human.py --judge kimi [--systems F.jsonl ...] [--concurrency 8]
             [--budget 12] [--git-pull] [--limit N] [--fresh] [--price-in X --price-out Y]
      python hackathon/eval/spot_human.py --summary-only
Judges: kimi = accounts/fireworks/models/kimi-k3, qwen = accounts/fireworks/models/qwen3p8-max
(or --model ID with any --judge name). Default systems: the reference, F1H, O3c, X0, O1, then any
O3l*/O4*/O5*/O6* held-out run with a row for every scored id (re-globbed after each --git-pull).
"""
from __future__ import annotations

import argparse
import glob
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
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "hackathon", "audit"))
import judge as J  # noqa: E402
import stats  # noqa: E402

PROMPT_PATH = os.path.join(HERE, "SPOT_HUMAN_PROMPT.md")
HELDOUT = os.path.join(ROOT, "evals", "heldout_pairs.jsonl")
RUNS = os.path.join(ROOT, "evals", "runs")
OUT_DIR = os.path.join(ROOT, "hackathon", "report", "spot_human")
SUMMARY = os.path.join(ROOT, "hackathon", "report", "spot_human.json")
PRICES_MD = os.path.join(ROOT, "hackathon", "report", "PRICES.md")
EXCLUDED = os.path.join(ROOT, "hackathon", "report", "heldout_excluded.json")
REFERENCE = "strong_claude-opus-5-5"
JUDGES = {"kimi": "accounts/fireworks/models/kimi-k3", "qwen": "accounts/fireworks/models/qwen3p8-max"}
FIXED = ["hack_strong_claude-opus-5-5_heldout.jsonl", "hack_F1H_opus_heldout.jsonl",
         "hack_O3c_glm_prompt_harness_style_heldout.jsonl", "hack_X0_copy_draft_heldout.jsonl",
         "hack_O1_glm_base_heldout.jsonl"]
OPTIONAL = ["hack_O3l*_heldout.jsonl", "hack_O4*_heldout.jsonl", "hack_O5*_heldout.jsonl",
            "hack_O6*_heldout.jsonl"]
ORDERS = ("HS", "SH")  # HS: human is Text 1. SH: system is Text 1.
TEMPERATURE, MAX_TOKENS, EFFORT, PROVIDER = 0, 4096, "none", "fireworks"
TRIES = 3

PROMPT_RE = re.compile(r"<!--\s*begin:user\s*-->\n?(.*?)\n?<!--\s*end:user\s*-->", re.S)
HUMAN_RE = re.compile(r"HUMAN[\s*_`]*[:=\-]?[\s*_`]*(?:text\s*)?#?\s*([12])\b", re.I)
BARE_RE = re.compile(r"^[\s*_`]*(?:text\s*)?([12])[\s*_`.]*$", re.I)


# ---------- prompt / parse ----------

def load_prompt(path: str = PROMPT_PATH) -> str:
    with open(path, encoding="utf-8") as f:
        m = PROMPT_RE.search(f.read())
    if not m or "{{TEXT_1}}" not in m.group(1) or "{{TEXT_2}}" not in m.group(1):
        raise ValueError(f"{path}: no user section with {{{{TEXT_1}}}} and {{{{TEXT_2}}}}")
    return m.group(1).strip()


def build_messages(template: str, text1: str, text2: str) -> list[dict]:
    return [{"role": "user", "content": J.fill(template, {"TEXT_1": text1, "TEXT_2": text2})}]


def parse_pick(text: str) -> str | None:
    """'1' | '2' | None. Last 'HUMAN: n' wins; else a bare last line '1' / 'Text 2'."""
    text = J._strip(text)
    hits = HUMAN_RE.findall(text)
    if hits:
        return hits[-1]
    tail = [ln for ln in text.splitlines() if ln.strip()]
    m = BARE_RE.match(tail[-1]) if tail else None
    return m.group(1) if m else None


def picked_of(pick: str | None, order: str) -> str | None:
    """Map the positional pick back to 'human' | 'system'."""
    if pick not in ("1", "2"):
        return None
    human_pos = "1" if order == "HS" else "2"
    return "human" if pick == human_pos else "system"


# ---------- data / hashes ----------

def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def cfg_hash(model: str, template: str, mock: bool = False) -> str:
    return _hash({"task": "spot_human", "model": model, "provider": PROVIDER, "temperature": TEMPERATURE,
                  "max_tokens": MAX_TOKENS, "reasoning_effort": EFFORT, "prompt": template, "mock": mock})


def io_hash(human: str, output: str) -> str:
    return _hash({"human": human, "output": output})


def excluded_ids(path: str = EXCLUDED) -> set[str]:
    """Held-out ids whose licence is not established: never sent to a judge, never scored."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return set(json.load(f).get("ids") or [])


def load_humans(path: str = HELDOUT, excluded_path: str = EXCLUDED) -> dict[str, str]:
    drop = excluded_ids(excluded_path)
    return {r["id"]: r["human"] for r in J.read_jsonl(path) if r["id"] not in drop}


def system_name(path: str) -> str:
    s = os.path.splitext(os.path.basename(path))[0]
    s = s[len("hack_"):] if s.startswith("hack_") else s
    return s[:-len("_heldout")] if s.endswith("_heldout") else s


def load_system(path: str, humans: dict[str, str]) -> dict[str, str]:
    """{id: output} for every held-out id; missing ids map to '' (counted as caught)."""
    out, dups = J.load_outputs(path)
    if dups:
        sys.exit(f"{path}: duplicate ids {dups[:3]}")
    return {i: (out.get(i) or "").strip() for i in humans}


def covers(path: str, humans: dict[str, str]) -> bool:
    """A run is ready when it has a row for every scored held-out id."""
    return set(humans) <= {r["id"] for r in J.read_jsonl(path)}


def discover(humans: dict[str, str], runs: str = RUNS) -> list[str]:
    """The fixed systems (any row count: missing ids count as caught), then optional runs that cover every id."""
    paths = [os.path.join(runs, f) for f in FIXED if os.path.exists(os.path.join(runs, f))]
    for pat in OPTIONAL:
        for p in sorted(glob.glob(os.path.join(runs, pat))):
            if p not in paths and covers(p, humans):
                paths.append(p)
    return paths


def rows_path(out_dir: str, judge: str, system: str) -> str:
    return os.path.join(out_dir, f"{judge}_{system}.jsonl")


# ---------- prices / client ----------

def price_from_md(model: str, path: str = PRICES_MD) -> tuple[float, float] | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0] == PROVIDER and cells[1] == model:
                try:
                    return float(cells[2]), float(cells[3])
                except ValueError:
                    return None
    return None


def make_call(model: str, client=None):
    """callable(messages) -> {"text", "usage"}; raises on truncation / empty content (then retried)."""
    client = client or J.make_client(PROVIDER)
    params = J.request_params(model, PROVIDER, EFFORT, MAX_TOKENS)

    def call(messages):
        resp = client.chat.completions.create(messages=messages, **params)
        choice = resp.choices[0]
        if choice.finish_reason == "length":
            raise J.Truncated("finish_reason=length")
        text = J._strip(choice.message.content or "")
        if not text:
            raise J.EmptyOutput("empty content")
        return {"text": text, "usage": J._usage(resp)}
    return call


def mock_call(messages):
    """Offline: deterministic pick from the prompt hash."""
    h = int(hashlib.sha256(messages[-1]["content"].encode()).hexdigest(), 16)
    return {"text": f"HUMAN: {1 + h % 2}", "usage": {"prompt_tokens": 0, "completion_tokens": 0}}


def row_cost(usage: dict, price: tuple[float, float] | None) -> float:
    if not price:
        return 0.0
    return (usage.get("prompt_tokens", 0) * price[0] + usage.get("completion_tokens", 0) * price[1]) / 1e6


def spent_total(out_dir: str) -> float:
    total = 0.0
    for p in glob.glob(os.path.join(out_dir, "*.jsonl")):
        total += sum(r.get("cost_usd", 0.0) for r in J.read_jsonl(p))
    return total


# ---------- run one (judge, system) ----------

class Budget:
    def __init__(self, cap: float | None, spent: float):
        self.cap, self.spent, self.lock = cap, spent, threading.Lock()

    def add(self, x: float) -> None:
        with self.lock:
            self.spent += x

    def over(self) -> bool:
        return self.cap is not None and self.spent >= self.cap


def judge_one(template, human, output, order, call):
    text1, text2 = (human, output) if order == "HS" else (output, human)
    msgs = build_messages(template, text1, text2)
    last = None
    for attempt in range(TRIES):
        try:
            got = call(msgs)
            return got, attempt
        except Exception as e:  # noqa: BLE001 - retried, then logged
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def run_system(sys_path: str, judge: str, model: str, call, *, humans: dict[str, str], template: str,
               out_dir: str = OUT_DIR, concurrency: int = 8, limit: int | None = None, fresh: bool = False,
               price=None, budget: Budget | None = None, mock: bool = False, log=print) -> dict:
    system = system_name(sys_path)
    outputs = load_system(sys_path, humans)
    out_path = rows_path(out_dir, judge, system)
    cfg = cfg_hash(model, template, mock)
    os.makedirs(out_dir, exist_ok=True)
    if fresh and os.path.exists(out_path):
        os.remove(out_path)
    old = J.read_jsonl(out_path) if os.path.exists(out_path) else []
    foreign = [r for r in old if r.get("cfg") != cfg]
    if foreign:
        sys.exit(f"{out_path}: {len(foreign)} rows were made with a different judge config. Use --fresh.")
    ids = list(humans)[:limit] if limit else list(humans)
    io = {i: io_hash(humans[i], outputs[i]) for i in ids}
    done = {(r["id"], r["order"]) for r in old if io.get(r["id"]) == r.get("io") and r.get("picked")}
    todo = [(i, o) for i in ids for o in ORDERS if (i, o) not in done]
    base = {"judge": judge, "model": model, "system": system,
            "system_file": os.path.relpath(sys_path, ROOT).replace(os.sep, "/"), "cfg": cfg, "mock": mock}
    errors, calls = [], 0
    lock = threading.Lock()
    with open(out_path, "a", encoding="utf-8") as f:
        def write(row):
            with lock:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
        live = []
        for i, o in todo:
            if not outputs[i]:  # refusal / missing: caught, never sent
                write({**base, "id": i, "order": o, "io": io[i], "pick": None, "picked": "human",
                       "empty_output": True, "raw": "", "cost_usd": 0.0})
            else:
                live.append((i, o))

        def task(i, o):
            if budget and budget.over():
                return None
            got, retries = judge_one(template, humans[i], outputs[i], o, call)
            usage = got.get("usage") or {}
            cost = row_cost(usage, price)
            if budget:
                budget.add(cost)
            pick = parse_pick(got["text"])
            return {**base, "id": i, "order": o, "io": io[i], "pick": pick, "picked": picked_of(pick, o),
                    "empty_output": False, "raw": got["text"][-2000:], "retries": retries,
                    "cost_usd": round(cost, 8), **usage}

        with ThreadPoolExecutor(max(1, concurrency)) as pool:
            futs = {pool.submit(task, i, o): (i, o) for i, o in live}
            for fut in as_completed(futs):
                try:
                    row = fut.result()
                except Exception as e:  # noqa: BLE001
                    errors.append({"id": futs[fut][0], "order": futs[fut][1], "error": f"{type(e).__name__}: {e}"[:300]})
                    continue
                if row is None:
                    continue
                calls += 1
                write(row)
    stopped = bool(budget and budget.over())
    log(f"[{judge}] {system}: {calls} calls, {len(errors)} errors, todo was {len(todo)}"
        + (f", spent so far ${budget.spent:.3f}" if budget else "") + (" BUDGET STOP" if stopped else ""))
    if errors:
        with open(out_path[:-len(".jsonl")] + ".errors.jsonl", "w", encoding="utf-8") as ef:
            ef.writelines(json.dumps(e) + "\n" for e in errors)
    return {"system": system, "calls": calls, "errors": len(errors), "budget_stop": stopped}


# ---------- summary ----------

def per_id_outcomes(rows: list[dict], io: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """({id: 'fooled'|'caught'|'split'}, unparsed ids). Later rows replace earlier ones."""
    by: dict[str, dict[str, str | None]] = {}
    for r in rows:
        if io.get(r["id"]) != r.get("io"):
            continue
        by.setdefault(r["id"], {})[r["order"]] = r.get("picked")
    out, unparsed = {}, []
    for i in io:
        v = by.get(i, {})
        if any(v.get(o) is None for o in ORDERS):
            if v:
                unparsed.append(i)
            continue
        a, b = v["HS"], v["SH"]
        out[i] = "fooled" if a == b == "system" else "caught" if a == b == "human" else "split"
    return out, unparsed


def _rate(k, n):
    if not n:
        return None
    r, lo, hi = stats.rate_ci(k, n)
    return {"k": k, "n": n, "rate": round(r, 4), "lo": round(lo, 4), "hi": round(hi, 4)}


def summarize(out_dir: str = OUT_DIR, humans: dict[str, str] | None = None, reference: str = REFERENCE,
              price_by_model: dict | None = None) -> dict:
    from audit import chrf  # noqa: E402 - heavy import (pipeline metrics), only needed here
    humans = humans if humans is not None else load_humans()
    result: dict[str, dict] = {}
    outcomes: dict[tuple[str, str], dict[str, str]] = {}
    for p in sorted(glob.glob(os.path.join(out_dir, "*.jsonl"))):
        if p.endswith(".errors.jsonl"):
            continue
        rows = J.read_jsonl(p)
        if not rows:
            continue
        judge, system = rows[0]["judge"], rows[0]["system"]
        sys_path = os.path.join(ROOT, rows[0]["system_file"])
        outputs = load_system(sys_path, humans)
        io = {i: io_hash(humans[i], outputs[i]) for i in humans}
        cur = [r for r in rows if io.get(r["id"]) == r.get("io")]
        per, unparsed = per_id_outcomes(cur, io)
        outcomes[(judge, system)] = per
        n = len(per)
        k_f = sum(v == "fooled" for v in per.values())
        k_s = sum(v == "split" for v in per.values())
        k_c = sum(v == "caught" for v in per.values())
        picks = [r["pick"] for r in cur if r.get("pick") in ("1", "2")]
        ch = [chrf(outputs[i], humans[i]) if outputs[i] else 0.0 for i in humans]
        result.setdefault(judge, {})[system] = {
            "system_file": rows[0]["system_file"], "model": rows[0]["model"], "cfg": rows[0]["cfg"],
            "mock": rows[0].get("mock", False), "n": n, "n_expected": len(humans),
            "fooled_strict": _rate(k_f, n), "fool_or_split": _rate(k_f + k_s, n), "caught": _rate(k_c, n),
            "split": k_s, "empty_ids": sorted(i for i in humans if not outputs[i]),
            "unparsed_ids": sorted(unparsed), "incomplete_ids": sorted(i for i in humans if i not in per and i not in unparsed),
            "pos1_rate": round(picks.count("1") / len(picks), 4) if picks else None,
            "chrf_vs_human": round(sum(ch) / len(ch), 4) if ch else None,
            "prompt_tokens_total": sum(r.get("prompt_tokens", 0) for r in cur),
            "completion_tokens_total": sum(r.get("completion_tokens", 0) for r in cur),
            "reasoning_tokens_total": sum(r.get("reasoning_tokens", 0) for r in cur),
            "cost_usd_total": round(sum(r.get("cost_usd", 0.0) for r in rows), 4),
        }
    for judge, systems in result.items():
        ref = outcomes.get((judge, reference))
        for system, block in systems.items():
            per = outcomes[(judge, system)]
            if ref is None or system == reference:
                block["vs_reference"] = None
                continue
            shared = [i for i in humans if i in per and i in ref]
            if not shared:
                block["vs_reference"] = None
                continue
            a = [1.0 if per[i] == "fooled" else 0.0 for i in shared]
            b = [1.0 if ref[i] == "fooled" else 0.0 for i in shared]
            d, lo, hi, p = stats.paired_bootstrap_diff(a, b)
            only_sys = sum(1 for x, y in zip(a, b) if x and not y)
            only_ref = sum(1 for x, y in zip(a, b) if y and not x)
            block["vs_reference"] = {
                "reference": reference, "n_shared": len(shared),
                "fooled_strict_diff": round(d, 4), "diff_lo": round(lo, 4), "diff_hi": round(hi, 4),
                "bootstrap_p": round(p, 4), "only_system_fooled": only_sys, "only_reference_fooled": only_ref,
                "both_fooled": sum(1 for x, y in zip(a, b) if x and y),
                "sign_test_p": round(stats.judge_sign_test(only_sys, only_ref), 4)}
    return result


def write_summary(result: dict, path: str = SUMMARY, prices: dict | None = None) -> None:
    doc = {"_meta": {"task": "spot_human", "contract": "hackathon/bus/msgs/20261102T204421Z-ali-to-friend.md",
                     "eval": "evals/heldout_pairs.jsonl",
                     "excluded_ids": sorted(excluded_ids()),
                     "excluded_from": "hackathon/report/heldout_excluded.json", "prompt": "hackathon/eval/SPOT_HUMAN_PROMPT.md",
                     "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "reasoning_effort": EFFORT,
                     "orders": "HS = human is Text 1, SH = system is Text 1",
                     "fooled_strict": "judge picks the system output as human in both orders",
                     "caught": "judge picks the human original in both orders; empty/missing output counts as caught",
                     "split": "orders disagree", "ci": "exact Clopper-Pearson 95% (stats.rate_ci)",
                     "vs_reference": "paired_bootstrap_diff on fooled_strict (system - reference, shared ids, "
                                     "10000 reps, seed 0) + exact sign test on ids where exactly one fooled",
                     "chrf_vs_human": "audit.chrf(output, human), 0-1 scale, empty output = 0, mean over all ids",
                     "prices_usd_per_1m": prices or {}},
           **result}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)


def table(result: dict) -> str:
    lines = ["judge | system | fool strict [95% CI] | fool-or-split | caught | chrF | n | vs ref diff [CI] p | sign (sys/ref) p | cost"]
    for judge, systems in result.items():
        for system, b in systems.items():
            f, fs, c = b["fooled_strict"], b["fool_or_split"], b["caught"]
            if not f:
                continue
            v = b.get("vs_reference")
            vs = (f"{v['fooled_strict_diff']:+.3f} [{v['diff_lo']:+.3f},{v['diff_hi']:+.3f}] p={v['bootstrap_p']}"
                  if v else "-")
            sg = f"{v['only_system_fooled']}/{v['only_reference_fooled']} p={v['sign_test_p']}" if v else "-"
            lines.append(f"{judge} | {system} | {f['rate']:.3f} [{f['lo']:.3f},{f['hi']:.3f}] | {fs['rate']:.3f} | "
                         f"{c['rate']:.3f} | {b['chrf_vs_human']:.3f} | {b['n']} | {vs} | {sg} | ${b['cost_usd_total']:.3f}")
    return "\n".join(lines)


# ---------- CLI ----------

def git_pull(log=print) -> None:
    r = subprocess.run(["git", "pull", "--ff-only", "-q"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        log(f"git pull failed (continuing): {r.stderr.strip()[:200]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Spot-the-human judge on held-out human originals.")
    ap.add_argument("--judge", choices=sorted(JUDGES), default=None)
    ap.add_argument("--model", default=None, help="override the judge's model id")
    ap.add_argument("--systems", nargs="*", default=None, help="held-out run files (default: discover)")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--budget", type=float, default=12.0, help="USD cap over all rows in the spot_human dir")
    ap.add_argument("--price-in", type=float, default=None)
    ap.add_argument("--price-out", type=float, default=None)
    ap.add_argument("--git-pull", action="store_true", help="git pull --ff-only before each new system")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--summary", default=SUMMARY)
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args(argv)
    humans = load_humans()
    if not args.summary_only:
        if not args.judge:
            ap.error("--judge is required")
        model = args.model or JUDGES[args.judge]
        price = (args.price_in, args.price_out) if args.price_in is not None else price_from_md(model)
        if price is None and not args.mock:
            sys.exit(f"no price for {model}: pass --price-in/--price-out")
        template = load_prompt()
        call = mock_call if args.mock else make_call(model)
        budget = Budget(args.budget, spent_total(args.out_dir))
        done: set[str] = set()
        while True:
            if args.git_pull:
                git_pull()
            todo = [p for p in (args.systems or discover(humans)) if p not in done]
            if not todo:
                break
            p = todo[0]
            done.add(p)
            run_system(p, args.judge, model, call, humans=humans, template=template, out_dir=args.out_dir,
                       concurrency=args.concurrency, limit=args.limit, fresh=args.fresh, price=price,
                       budget=budget, mock=args.mock)
            if budget.over():
                print(f"budget cap ${args.budget} reached; stopping")
                break
    result = summarize(args.out_dir, humans)
    prices = {}
    for judge in result.values():
        for b in judge.values():
            pr = price_from_md(b["model"])
            if pr:
                prices[b["model"]] = list(pr)
    if args.price_in is not None and (args.model or args.judge):
        prices[args.model or JUDGES[args.judge]] = [args.price_in, args.price_out]
    if os.path.exists(args.summary):
        try:
            prices = {**json.load(open(args.summary, encoding="utf-8")).get("_meta", {}).get("prices_usd_per_1m", {}), **prices}
        except (ValueError, OSError):
            pass
    write_summary(result, args.summary, prices)
    print(table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
