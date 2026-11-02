"""R2_ensemble_select: per item, pick the best of several committed gate-passing runs (TASK R2, RUSLAN_TASKS.md).

Pool:        committed run files (hack_<run>.jsonl, _heldout, _real), at most 5 runs. Incumbent order = O3c first,
             then the others by fact-safe rate (gates.check pass share over that run's main + held-out rows).
Eligibility: gates.check(draft, out)["pass"] AND a two-way claim check by GLM-5.3 (one json_object call,
             temperature 0, returns draft_claims_missing + rewrite_claims_unsupported; eligible only if both are
             empty). A failed or unparsable check counts as NOT eligible.
Knockout:    ladder in incumbent order. The first eligible candidate is the incumbent; each later gate-passing
             candidate challenges it with the harness pair_pick prompt (PAIR_ASK copied from harness.py), both
             orders. Both orders agree on the challenger -> it takes over (if it is eligible). Both agree on the
             incumbent -> incumbent stays. Disagreement / no verdict = tie -> the longer candidate (all gate-passing
             candidates are within G4 by construction) if eligible, else the incumbent. Order 2 is skipped only when
             its answer cannot change the outcome. Claim checks run lazily, only on a challenger that would win.
Fallback:    no eligible candidate -> first gate-passing candidate in incumbent order; none -> O3c's output.
Cost rule:   cost_usd = sum of every pooled candidate's cost_usd for the item + selector cost (GLM-5.3 tokens at
             PRICES.md rates). latency_ms = max candidate latency_ms + selector wall time (calls are sequential).
Cache:       every selector call is cached in --cache by a hash of its request, with usage and latency, so a rerun
             is free and the per-row cost stays the cost of the calls that decided it.

Usage:
  python hackathon/train/ruslan/ensemble_select.py --split main [--ids-from FILE] [--out PATH]
  python hackathon/train/ruslan/ensemble_select.py --split heldout
  python hackathon/train/ruslan/ensemble_select.py --split real
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../.."))
sys.path[:0] = [os.path.join(ROOT, "hackathon/harness"), os.path.join(ROOT, "hackathon/eval")]
import gates  # noqa: E402

SYSTEM_NAME = "R2_ensemble_select"
SELECTOR = "accounts/fireworks/models/glm-5p3"
PRICE_IN, PRICE_OUT = 1.40, 4.40   # $/1M, docs.fireworks.ai/serverless/pricing (GLM 5.3, Standard), 2026-11-02
DEFAULT_POOL = ["O3c_glm_prompt_harness_style", "O3j_glm_bestof3_judged", "O3l_glm_style_claimcheck_bo3",
                "O3e_glm_harness_cliche", "O3d_glm_harness_anticopy"]
INCUMBENT = "O3c_glm_prompt_harness_style"
POOL_CAP = 5
SPLITS = {"main": ("", "evals/eval_all.jsonl"), "heldout": ("_heldout", "evals/heldout_pairs.jsonl"),
          "real": ("_real", "evals/real_readmes.jsonl")}

# copied verbatim from hackathon/harness/harness.py (PAIR_ASK + pair_pick message)
PAIR_SYSTEM = "You are a strict senior copy editor."
PAIR_ASK = ("Which rewrite reads more like a calm, skilled human copywriter wrote it, while saying exactly what the "
            "DRAFT says? Answer 1 or 2.")
CLAIM2_SYSTEM = "You are a strict fact checker."
CLAIM2_ASK = (
    "Compare the REWRITE with the DRAFT in both directions. Only substantive information counts: facts, features, "
    "numbers, names, dates, prices, conditions, offers, instructions and calls to action. Removing hype, adjectives, "
    "cliches, slogans, emotional filler, apologies or rhetorical framing is NOT a missing claim. Ignore pure wording, "
    "tone, order and formatting changes.\n"
    "1. draft_claims_missing: every claim, fact, detail, feature, number, name, condition, example or call to action "
    "stated in the DRAFT that the REWRITE no longer conveys.\n"
    "2. rewrite_claims_unsupported: every claim, detail, example, reason, scenario or statement of fact in the REWRITE "
    "that is not stated in the DRAFT and is not a direct restatement of it.\n"
    "Reply with a JSON object only: {\"draft_claims_missing\": [\"short quote\", ...], "
    "\"rewrite_claims_unsupported\": [\"short quote\", ...]}. Use an empty list when there is nothing.")
PROMPT_SHA = hashlib.sha256((PAIR_SYSTEM + PAIR_ASK + CLAIM2_SYSTEM + CLAIM2_ASK).encode()).hexdigest()[:16]


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def clean(t):
    t = re.sub(r"<think>.*?</think>", "", t or "", flags=re.S)
    return re.sub(r"^.*</think>", "", t, flags=re.S).strip()


def parse_pair(text):
    mt = re.match(r"^\s*([12])(?![0-9])", clean(text))
    return int(mt.group(1)) if mt else None


def parse_claims(text):
    """-> (missing, unsupported) lists, or None when unparsable."""
    mt = re.search(r"\{.*\}", clean(text), re.S)
    if not mt:
        return None
    try:
        d = json.loads(mt.group(0))
    except ValueError:
        return None
    if not isinstance(d, dict) or "draft_claims_missing" not in d or "rewrite_claims_unsupported" not in d:
        return None
    lst = lambda v: [x for x in (v if isinstance(v, list) else [v]) if isinstance(x, str) and x.strip()]
    return lst(d["draft_claims_missing"]), lst(d["rewrite_claims_unsupported"])


# ---------- selector client (cached) ----------

class Selector:
    """call(kind, messages) -> (text, usage, latency_s). `client` is an OpenAI-SDK-like object (fake in tests)."""

    def __init__(self, client, cache_path=None, model=SELECTOR, effort="low"):
        self.client, self.model, self.effort = client, model, effort
        self.cache_path, self.cache, self.lock = cache_path, {}, threading.Lock()
        if cache_path and os.path.exists(cache_path):
            for r in read_jsonl(cache_path):
                self.cache[r["key"]] = r

    def call(self, kind, messages):
        params = {"model": self.model, "temperature": 0, "max_tokens": 4096 if kind == "claims" else 1024,
                  "extra_body": {"reasoning_effort": self.effort}}
        if kind == "claims":
            params["response_format"] = {"type": "json_object"}
        key = hashlib.sha256(json.dumps([messages, params], sort_keys=True).encode()).hexdigest()
        with self.lock:
            hit = self.cache.get(key)
        if hit:
            return hit["text"], hit["usage"], hit["latency_s"]
        t0 = time.time()
        resp = self.client.chat.completions.create(messages=messages, **params)
        lat = time.time() - t0
        ch = resp.choices[0]
        text = ch.message.content or ""
        u = getattr(resp, "usage", None)
        usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0) or 0, "completion_tokens": getattr(u, "completion_tokens", 0) or 0}
        rec = {"key": key, "kind": kind, "text": text, "usage": usage, "latency_s": round(lat, 3),
               "finish": getattr(ch, "finish_reason", None)}
        with self.lock:
            self.cache[key] = rec
            if self.cache_path:
                with open(self.cache_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return text, usage, lat


class Meter:
    def __init__(self):
        self.pt = self.ct = 0; self.lat = 0.0; self.calls = 0

    def add(self, usage, lat):
        self.pt += usage.get("prompt_tokens", 0); self.ct += usage.get("completion_tokens", 0)
        self.lat += lat; self.calls += 1

    def cost(self):
        return (self.pt * PRICE_IN + self.ct * PRICE_OUT) / 1e6


def pair(sel, meter, draft, t1, t2):
    msg = [{"role": "system", "content": PAIR_SYSTEM},
           {"role": "user", "content": f"{PAIR_ASK}\n\nDRAFT:\n{draft}\n\nREWRITE 1:\n{t1}\n\nREWRITE 2:\n{t2}"
                                       "\n\nAnswer with the single digit 1 or 2 and nothing else."}]
    try:
        text, u, lat = sel.call("pair", msg)
    except Exception:
        return None
    meter.add(u, lat)
    return parse_pair(text)


def claims(sel, meter, draft, out):
    """-> {"ok": bool, "missing": [...], "unsupported": [...]} ; unavailable -> ok False."""
    msg = [{"role": "system", "content": CLAIM2_SYSTEM},
           {"role": "user", "content": f"{CLAIM2_ASK}\n\nDRAFT:\n{draft}\n\nREWRITE:\n{out}"}]
    for _ in range(2):
        try:
            text, u, lat = sel.call("claims", msg)
        except Exception:
            continue
        meter.add(u, lat)
        r = parse_claims(text)
        if r is not None:
            return {"ok": not r[0] and not r[1], "missing": r[0][:6], "unsupported": r[1][:6]}
        msg = msg + [{"role": "assistant", "content": text},
                     {"role": "user", "content": "That was not valid JSON with both keys. Reply with the JSON object only."}]
    return {"ok": False, "missing": None, "unsupported": None, "unavailable": True}


# ---------- selection ----------

def select_item(item, cands, sel, tie_rule="longer"):
    """cands: [{run, output, cost_usd, latency_ms}] in incumbent order. Returns (chosen cand, selection, meter)."""
    draft = item["ai_draft"]
    meter = Meter()
    seen, pool = {}, []
    for c in cands:
        if c["output"] in seen:
            c["dup_of"] = seen[c["output"]]
        else:
            seen[c["output"]] = c["run"]; pool.append(c)
    for c in pool:
        g = gates.check(draft, c["output"])
        c["gate_pass"], c["n_words"] = g["pass"], len(gates.m.words(c["output"]))
    gate_ok = [c for c in pool if c["gate_pass"]]
    elig = {c["run"]: (None if c["gate_pass"] else False) for c in pool}   # None = not claim-checked
    claim_log = {}

    def is_eligible(c):
        if elig[c["run"]] is None:
            r = claims(sel, meter, draft, c["output"])
            claim_log[c["run"]] = r
            elig[c["run"]] = r["ok"]
        return elig[c["run"]]

    picks, inc, rest = [], None, []
    for i, c in enumerate(gate_ok):
        if is_eligible(c):
            inc, rest = c, gate_ok[i + 1:]
            break
    fallback = None
    if inc is None:
        if gate_ok:
            inc, fallback = gate_ok[0], "no_eligible_first_gate_pass"
        else:
            inc = next((c for c in cands if c["run"] == INCUMBENT), cands[0]); fallback = "no_gate_pass_incumbent"
    else:
        for c in rest:
            longer = c["n_words"] > inc["n_words"]
            v1 = pair(sel, meter, draft, inc["output"], c["output"])   # incumbent is REWRITE 1
            v2 = None
            need_v2 = v1 == 2 or (v1 is None or v1 == 1) and tie_rule == "longer" and longer
            if need_v2:
                v2 = pair(sel, meter, draft, c["output"], inc["output"])   # challenger is REWRITE 1
            if v1 == 2 and v2 == 1:
                by, want = "agree", True
            elif v1 == 1 and v2 in (None, 2) and not need_v2:
                by, want = "agree_or_skipped", False
            elif v1 == 1 and v2 == 2:
                by, want = "agree", False
            else:
                by, want = "tie", (tie_rule == "longer" and longer)
            took = bool(want and is_eligible(c))
            picks.append({"incumbent": inc["run"], "challenger": c["run"], "v_inc_first": v1, "v_ch_first": v2,
                          "by": by, "winner": c["run"] if took else inc["run"],
                          "blocked_by_claims": bool(want and not took)})
            if took:
                inc = c
    selection = {"source_run": inc["run"], "eligible": elig, "picks": picks, "claims": claim_log,
                 "dups": {c["run"]: c["dup_of"] for c in cands if c.get("dup_of")}, "fallback": fallback,
                 "gate_pass": {c["run"]: c["gate_pass"] for c in pool}}
    return inc, selection, meter


def fact_safe_rate(run, drafts_by_split):
    n = k = 0
    for split in ("main", "heldout"):
        p = os.path.join(ROOT, f"evals/runs/hack_{run}{SPLITS[split][0]}.jsonl")
        if not os.path.exists(p):
            continue
        for r in read_jsonl(p):
            d = drafts_by_split[split].get(r["id"])
            if d is not None:
                n += 1; k += gates.check(d["ai_draft"], r.get("output", ""))["pass"]
    return k / n if n else 0.0


def order_pool(pool, drafts_by_split):
    rates = {r: fact_safe_rate(r, drafts_by_split) for r in pool}
    rest = sorted([r for r in pool if r != INCUMBENT], key=lambda r: -rates[r])
    ordered = ([INCUMBENT] if INCUMBENT in pool else []) + rest
    return ordered[:POOL_CAP], rates


def load_drafts():
    excl = set(json.load(open(os.path.join(ROOT, "hackathon/report/heldout_excluded.json"), encoding="utf-8"))["ids"])
    out = {}
    for s, (_, p) in SPLITS.items():
        out[s] = {r["id"]: r for r in read_jsonl(os.path.join(ROOT, p)) if r["id"] not in excl}
    return out, excl


def run(split, pool, sel, out_path, ids=None, concurrency=8, tie_rule="longer", drafts_by_split=None):
    drafts_by_split = drafts_by_split or load_drafts()[0]
    items = drafts_by_split[split]
    suffix = SPLITS[split][0]
    runs = {}
    for r in pool:
        p = os.path.join(ROOT, f"evals/runs/hack_{r}{suffix}.jsonl")
        if os.path.exists(p):
            runs[r] = {x["id"]: x for x in read_jsonl(p)}
    want = [i for i in items if (ids is None or i in ids)]

    def one(iid):
        cands = [{"run": r, "output": runs[r][iid].get("output", ""), "cost_usd": runs[r][iid].get("cost_usd") or 0.0,
                  "latency_ms": runs[r][iid].get("latency_ms") or 0} for r in pool if r in runs and iid in runs[r]]
        if not cands:
            return None
        ch, selection, meter = select_item(items[iid], cands, sel, tie_rule)
        g = gates.check(items[iid]["ai_draft"], ch["output"])
        return {"id": iid, "system": SYSTEM_NAME, "output": ch["output"],
                "latency_ms": int(max(c["latency_ms"] for c in cands) + meter.lat * 1000),
                "cost_usd": round(sum(c["cost_usd"] for c in cands) + meter.cost(), 6),
                "candidate_cost_usd": round(sum(c["cost_usd"] for c in cands), 6),
                "selector_cost_usd": round(meter.cost(), 6),
                "prompt_tokens": meter.pt, "completion_tokens": meter.ct, "selector_calls": meter.calls,
                "model": f"ensemble({','.join(c['run'] for c in cands)}) select={SELECTOR}",
                "gates": {k: g[k] for k in ("g1_nothing_invented", "g2_nothing_lost", "g3_no_ai_tells", "g4_not_gutted", "pass")},
                "selection": selection}

    with ThreadPoolExecutor(concurrency) as ex:
        rows = [r for r in ex.map(one, want) if r]
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def summarize(rows):
    from collections import Counter
    src = Counter(r["selection"]["source_run"] for r in rows)
    return {"rows": len(rows), "source_runs": dict(src), "gate_pass": sum(r["gates"]["pass"] for r in rows),
            "fallbacks": dict(Counter(r["selection"]["fallback"] for r in rows if r["selection"]["fallback"])),
            "selector_cost_usd": round(sum(r["selector_cost_usd"] for r in rows), 4),
            "cost_usd": round(sum(r["cost_usd"] for r in rows), 4),
            "selector_calls": sum(r["selector_calls"] for r in rows)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=sorted(SPLITS), default="main")
    ap.add_argument("--pool", nargs="*", default=None, help="run names (hack_<name>.jsonl); default the 5-run pool")
    ap.add_argument("--ids-from", default=None, help="jsonl whose ids restrict the items (dev slice)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cache", default=os.path.join(HERE, "R2_selector_calls.jsonl"))
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--tie", choices=("longer", "incumbent"), default="longer")
    ap.add_argument("--reasoning-effort", default="low")
    a = ap.parse_args(argv)
    import judge  # Fireworks OpenAI-SDK client with truststore + keys.env (keys never printed)
    client = judge.make_client("fireworks")
    sel = Selector(client, a.cache, SELECTOR, a.reasoning_effort)
    drafts, _ = load_drafts()
    pool, rates = order_pool(a.pool or DEFAULT_POOL, drafts)
    ids = {r["id"] for r in read_jsonl(a.ids_from)} if a.ids_from else None
    out = a.out or os.path.join(ROOT, f"evals/runs/hack_{SYSTEM_NAME}{SPLITS[a.split][0]}.jsonl")
    rows = run(a.split, pool, sel, out, ids, a.concurrency, a.tie, drafts)
    print(json.dumps({"pool": pool, "fact_safe_rates": {k: round(v, 4) for k, v in rates.items()}, "out": out,
                      **summarize(rows)}, indent=1))


if __name__ == "__main__":
    main()
