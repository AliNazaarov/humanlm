"""Score every system on the same items and render the report. Offline: reads committed outputs and judge files.
Usage: score_all.py [--runs A.jsonl B.jsonl ...] [--reference SYSTEM_LABEL] [--out-dir hackathon/report]

Systems: evals/runs/hack_*.jsonl (held-out runs: hack_*_heldout.jsonl) + evals/baseline_frontier.jsonl
("frontier-persona-preexisting"). --runs replaces discovery (dry runs before the real files land).
Per item: fact hard fail (pipeline/metrics.faithfulness), in-range share (share of the 16 tell metrics inside the
human 10-90th band, the definition used in MORNING_REPORT), stock phrases /100 words, length ratio vs draft,
must-keep coverage (crude: numbers/names, else 60% of content words), forbidden-phrase hit, trick verbatim misses.
Rates get exact CIs, means get bootstrap CIs, differences vs the reference get a paired bootstrap on shared ids.
Judge results are read from hackathon/report/judge_*.summary.json (made by judge.py; never re-run here).
Writes results.json, then RESULTS.md from results.json only.
"""
from __future__ import annotations

import argparse, glob, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path[:0] = [HERE, os.path.join(ROOT, "pipeline")]
import metrics as m  # noqa: E402
import stats as st  # noqa: E402

PREEXISTING = {"baseline_frontier.jsonl": "frontier-persona-preexisting"}
NUM = re.compile(r"\d[\d,.]*")
CAP = re.compile(r"\b[A-Z][A-Za-z0-9]+\b")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def eval_items() -> dict[str, dict]:
    items = {}
    for f in ("evals/dev_set.jsonl", "evals/trick_set.jsonl"):
        for r in read_jsonl(os.path.join(ROOT, f)):
            items[r["id"]] = r
    return items


def heldout_items() -> dict[str, dict]:
    p = os.path.join(ROOT, "evals/heldout_pairs.jsonl")
    return {r["id"]: r for r in read_jsonl(p)} if os.path.exists(p) else {}


def discover(heldout: bool) -> list[str]:
    runs = sorted(glob.glob(os.path.join(ROOT, "evals/runs/hack_*.jsonl")))
    runs = [r for r in runs if r.endswith("_heldout.jsonl") == heldout]
    if not heldout:
        runs.append(os.path.join(ROOT, "evals/baseline_frontier.jsonl"))
    return runs


def kept(fact: str, out: str) -> bool:
    """Crude must-keep check: every number and capitalised name in the fact appears; else 60% of content words."""
    low = out.lower()
    hard = NUM.findall(fact) + CAP.findall(fact)
    if hard:
        return all(h.lower() in low for h in hard)
    words = [w for w in re.findall(r"[a-z]+", fact.lower()) if len(w) > 3]
    return not words or sum(w in low for w in words) / len(words) >= 0.6


def item_scores(item: dict, out: str, band: dict) -> dict:
    draft = item["ai_draft"]
    tm = m.text_metrics(out)
    ib = m.in_band(tm, band)
    s = {
        "fact_fail": int(m.faithfulness(draft, out)["hard_fail"]),
        "in_range": statistics.fmean(v["ok"] for v in ib.values()),
        "stock_per100": tm["stock_rate"],
        "len_ratio": len(m.words(out)) / max(len(m.words(draft)), 1),
    }
    if item.get("must_keep"):
        s["must_keep"] = statistics.fmean(kept(f, out) for f in item["must_keep"])
    if "forbidden" in item:
        s["forbidden_hit"] = int(any(f.lower() in out.lower() for f in item["forbidden"]))
    if item.get("verbatim"):
        s["verbatim_miss"] = int(any(v not in out for v in item["verbatim"]))
    return s


def score_system(path: str, items: dict, band: dict) -> dict:
    rows = read_jsonl(path)
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{rel(path)}: duplicate ids")
    unknown = set(ids) - set(items)
    if unknown:
        raise SystemExit(f"{rel(path)}: {len(unknown)} ids not in the eval set, e.g. {sorted(unknown)[:3]}")
    if any(not (r.get("output") or "").strip() for r in rows):
        raise SystemExit(f"{rel(path)}: empty output rows")
    label = PREEXISTING.get(os.path.basename(path)) or rows[0].get("system") or os.path.basename(path)
    per = {r["id"]: item_scores(items[r["id"]], r["output"], band) for r in rows}
    sysd = {"label": label, "file": rel(path), "n": len(rows), "missing_ids": len(set(items) - set(ids)),
            "model": rows[0].get("model"), "per_item": per}
    lat = [r["latency_ms"] for r in rows if isinstance(r.get("latency_ms"), (int, float))]
    cost = [r["cost_usd"] for r in rows if isinstance(r.get("cost_usd"), (int, float))]
    if len(lat) == len(rows):
        sysd["latency_ms"] = st.percentiles(lat)
    if len(cost) == len(rows):
        sysd["cost_per_1k_usd"] = st.cost_per_1k(cost)
    return sysd


def summarise(sysd: dict) -> dict:
    per = list(sysd["per_item"].values())
    out = {}
    k = sum(p["fact_fail"] for p in per)
    out["fact_fail"] = dict(zip(("rate", "lo", "hi"), st.rate_ci(k, len(per))), count=k, n=len(per))
    for key in ("in_range", "stock_per100", "len_ratio", "must_keep"):
        vals = [p[key] for p in per if key in p]
        if vals:
            out[key] = dict(zip(("mean", "lo", "hi"), st.bootstrap_ci(vals)), n=len(vals))
    for key in ("forbidden_hit", "verbatim_miss"):
        vals = [p[key] for p in per if key in p]
        if vals:
            out[key] = dict(zip(("rate", "lo", "hi"), st.rate_ci(sum(vals), len(vals))), count=sum(vals), n=len(vals))
    return out


def paired(a: dict, b: dict) -> dict:
    shared = sorted(set(a["per_item"]) & set(b["per_item"]))
    res = {"n_shared": len(shared)}
    for key in ("fact_fail", "in_range", "stock_per100", "len_ratio"):
        x = [a["per_item"][i][key] for i in shared]
        y = [b["per_item"][i][key] for i in shared]
        res[key] = dict(zip(("diff", "lo", "hi", "p"), st.paired_bootstrap_diff(x, y)))
    return res


def judges(report_dir: str) -> list[dict]:
    out = []
    for f in sorted(glob.glob(os.path.join(report_dir, "judge_*.summary.json"))):
        j = json.load(open(f, encoding="utf-8"))
        if str(j.get("model", "")).startswith("mock"):
            continue  # mock verdicts are for pipeline tests only
        j["file"] = rel(f)
        j["sign_test_p"] = st.judge_sign_test(j["win"], j["loss"])
        out.append(j)
    return out


def build(runs: list[str], items: dict, band: dict, reference: str | None, report_dir: str) -> dict:
    systems = [score_system(p, items, band) for p in runs]
    labels = [s["label"] for s in systems]
    if len(set(labels)) != len(labels):
        raise SystemExit(f"duplicate system labels: {labels}")
    ref = reference or next((l for l in labels if l.startswith("frontier-live")), None) \
        or next((l for l in labels if l.startswith("frontier")), labels[0])
    ref_sys = next(s for s in systems if s["label"] == ref)
    res = {"reference": ref, "n_items": len(items), "systems": []}
    for s in systems:
        entry = {k: v for k, v in s.items() if k != "per_item"}
        entry["summary"] = summarise(s)
        if s is not ref_sys:
            entry["vs_reference"] = paired(s, ref_sys)
        res["systems"].append(entry)
    return res


def fmt_rate(d: dict) -> str:
    return f"{d['count']} ({100*d['rate']:.0f}% [{100*d['lo']:.0f}, {100*d['hi']:.0f}])"


def fmt_mean(d: dict, pct: bool = False, nd: int = 2) -> str:
    if pct:
        return f"{100*d['mean']:.0f}% [{100*d['lo']:.0f}, {100*d['hi']:.0f}]"
    return f"{d['mean']:.{nd}f} [{d['lo']:.{nd}f}, {d['hi']:.{nd}f}]"


def table(block: dict, title: str) -> list[str]:
    n = block["n_items"]
    lines = [f"## {title}", "", f"Reference for differences: `{block['reference']}`. 95% CIs in brackets.", "",
             f"| System | Fact hard-fails /{n} | In human range | Stock phrases /100w | Length ratio | Must-keep (crude) "
             "| Cost / 1k rewrites | p50 / p95 latency |",
             "|---|---|---|---|---|---|---|---|"]
    for s in block["systems"]:
        sm = s["summary"]
        cost = f"${s['cost_per_1k_usd']:.2f}" if "cost_per_1k_usd" in s else "n/a"
        lat = f"{s['latency_ms']['p50']/1000:.1f}s / {s['latency_ms']['p95']/1000:.1f}s" if "latency_ms" in s else "n/a"
        mk = fmt_mean(sm["must_keep"], pct=True) if "must_keep" in sm else "n/a"
        lines.append(f"| `{s['label']}` | {fmt_rate(sm['fact_fail'])} | {fmt_mean(sm['in_range'], pct=True)} | "
                     f"{fmt_mean(sm['stock_per100'])} | {fmt_mean(sm['len_ratio'])} | {mk} | {cost} | {lat} |")
    diffs = [s for s in block["systems"] if "vs_reference" in s]
    if diffs:
        lines += ["", "Paired differences vs the reference (system minus reference, shared ids):", "",
                  "| System | Δ fact-fail rate | p | Δ in range | p |", "|---|---|---|---|---|"]
        for s in diffs:
            f, r = s["vs_reference"]["fact_fail"], s["vs_reference"]["in_range"]
            lines.append(f"| `{s['label']}` | {100*f['diff']:+.0f} pts [{100*f['lo']:+.0f}, {100*f['hi']:+.0f}] | "
                         f"{f['p']:.4f} | {100*r['diff']:+.0f} pts [{100*r['lo']:+.0f}, {100*r['hi']:+.0f}] | {r['p']:.4f} |")
    return lines + [""]


def render(results: dict) -> str:
    out = ["# Results", "", "_Generated by `hackathon/eval/score_all.py` from `results.json`. Do not edit by hand._", ""]
    out += table(results["main"], "Main eval (dev 100 + trick 30)")
    if results.get("heldout"):
        out += table(results["heldout"], "Held-out pairs with real human references")
    if results["judges"]:
        out += ["## Pairwise judge (both orders; a win needs both orders to agree)", "",
                "| A vs B | Judge | A wins | B wins | Ties | Flip rate | Sign test p |", "|---|---|---|---|---|---|---|"]
        for j in results["judges"]:
            out.append(f"| `{j['a']}` vs `{j['b']}` | `{j['model']}` | {j['win']} | {j['loss']} | {j['tie']} | "
                       f"{100*j['flip_rate']:.0f}% | {j['sign_test_p']:.4f} |")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+")
    ap.add_argument("--reference")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "hackathon/report"))
    a = ap.parse_args(argv)
    band = json.load(open(os.path.join(ROOT, "evals/runs/band_v0.json"), encoding="utf-8"))
    results = {"main": build(a.runs or discover(False), eval_items(), band, a.reference, a.out_dir)}
    held = discover(True) if not a.runs else []
    if held:
        results["heldout"] = build(held, heldout_items(), band, None, a.out_dir)
    results["judges"] = judges(a.out_dir)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(results, f, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(results))
    print(f"scored {len(results['main']['systems'])} systems -> {rel(a.out_dir)}/results.json, RESULTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
