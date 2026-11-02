"""Score every system on the same items and render the leaderboard. Offline: reads committed run files and judge summaries.
Usage: score_all.py [--runs A.jsonl ...] [--reference LABEL] [--out-dir hackathon/report]

Items: evals/eval_all.jsonl ids (dev 100 + trick 30, extra fields from dev_set/trick_set) + evals/heldout_pairs.jsonl
(120) = 250. Systems: every evals/runs/hack_*.jsonl (main and *_heldout files of one system share its `system` label)
+ evals/baseline_frontier.jsonl ("frontier-persona-preexisting", main split only). --runs replaces discovery.

Headline (hackathon/PLAN_V2_JUDGES.md): fact-safe human rewrite rate = share of items passing all gates,
as defined once in hackathon/harness/gates.py:
  G1 nothing invented  faithfulness hard_fail is False
  G2 nothing lost      numbers_kept == 1 and names_kept >= 0.9
  G3 no AI tells       stock, em-dash, not-x-but-y, emoji, exclaim each <= the human band's upper bound
  G4 not gutted        0.7 <= output words / draft words <= 1.3
Secondary: in-range share (16 tells inside the 10-90th human band), stock phrases /100w, length ratio,
must-keep coverage (crude), forbidden hits, trick verbatim misses. Rates: exact CIs. Means: bootstrap CIs.
Differences vs the reference (F1): paired bootstrap on shared ids, "significant" when p < 0.05.
Judge results come from hackathon/report/judge_*.summary.json (mock summaries are skipped).
"""
from __future__ import annotations

import argparse, glob, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path[:0] = [HERE, os.path.join(ROOT, "pipeline"), os.path.join(ROOT, "hackathon/harness")]
import gates as gt  # noqa: E402  the one G1-G4 definition, shared with the harness
import metrics as m  # noqa: E402
import stats as st  # noqa: E402

PREEXISTING = {"baseline_frontier.jsonl": "frontier-persona-preexisting"}
GATES = ("G1", "G2", "G3", "G4")

SPLITS = ("dev", "trick", "heldout")
NUM = re.compile(r"\d[\d,.]*")
CAP = re.compile(r"\b[A-Z][A-Za-z0-9]+\b")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def split_of(item_id: str) -> str:
    return "heldout" if item_id.startswith("ho-") else "trick" if item_id.startswith("trick") else "dev"


def all_items() -> dict[str, dict]:
    items = {}
    for f in ("evals/dev_set.jsonl", "evals/trick_set.jsonl", "evals/heldout_pairs.jsonl"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            items.update({r["id"]: r for r in read_jsonl(p)})
    return items


def discover() -> list[str]:
    runs = [p for p in glob.glob(os.path.join(ROOT, "evals/runs/hack_*.jsonl"))
            if ".jsonl." not in os.path.basename(p)]  # skip side files such as X.jsonl.failures.jsonl
    return sorted(runs) + [os.path.join(ROOT, "evals/baseline_frontier.jsonl")]


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
    tm, g = m.text_metrics(out), gt.check(draft, out)
    s = {
        "G1": int(g["g1_nothing_invented"]),
        "G2": int(g["g2_nothing_lost"]),
        "G3": int(g["g3_no_ai_tells"]),
        "G4": int(g["g4_not_gutted"]),
        "pass": int(g["pass"]),
        "fact_fail": int(not g["g1_nothing_invented"]),
        "in_range": statistics.fmean(v["ok"] for v in m.in_band(tm, band).values()),
        "stock_per100": tm["stock_rate"],
        "len_ratio": g["len_ratio"],
    }
    if item.get("must_keep"):
        s["must_keep"] = statistics.fmean(kept(f, out) for f in item["must_keep"])
    if "forbidden" in item:
        s["forbidden_hit"] = int(any(f.lower() in out.lower() for f in item["forbidden"]))
    if item.get("verbatim"):
        s["verbatim_miss"] = int(any(v not in out for v in item["verbatim"]))
    return s


def load_systems(paths: list[str], items: dict) -> dict[str, dict]:
    """Group run files by system label; reject duplicate ids, unknown ids and empty outputs."""
    systems: dict[str, dict] = {}
    for path in paths:
        rows = read_jsonl(path)
        if not rows:
            continue
        label = PREEXISTING.get(os.path.basename(path)) or rows[0].get("system") or os.path.basename(path)
        sysd = systems.setdefault(label, {"label": label, "files": [], "rows": {}, "model": rows[0].get("model")})
        sysd["files"].append(rel(path))
        for r in rows:
            if r["id"] in sysd["rows"]:
                raise SystemExit(f"{label}: duplicate id {r['id']} ({rel(path)})")
            if r["id"] not in items:
                raise SystemExit(f"{label}: id {r['id']} not in the eval items ({rel(path)})")
            if not (r.get("output") or "").strip():
                sysd.setdefault("empty_ids", []).append(r["id"])  # refusal: scored as a gap (counts as a fail)
                continue
            sysd["rows"][r["id"]] = r
    return systems


def missing_scores(item: dict) -> dict:
    """An item the system was asked to rewrite but has no row for (a refusal or a failed call) is scored as an
    empty rewrite: nothing invented, everything lost. It counts against the headline; secondary metrics skip it."""
    g = gt.check(item["ai_draft"], "")
    s = {"G1": int(g["g1_nothing_invented"]), "G2": int(g["g2_nothing_lost"]), "G3": int(g["g3_no_ai_tells"]),
         "G4": int(g["g4_not_gutted"]), "pass": int(g["pass"]), "fact_fail": 0, "missing": 1}
    return s


def prices() -> dict[str, tuple[float, float]]:
    """model id (and its last path segment) -> (USD per 1M input, per 1M output) from PRICES.md; TODO rows skipped."""
    out = {}
    path = os.path.join(ROOT, "hackathon/report/PRICES.md")
    for line in open(path, encoding="utf-8") if os.path.exists(path) else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            try:
                pin, pout = float(cells[2]), float(cells[3])
            except ValueError:
                continue
            out[cells[1]] = out[cells[1].split("/")[-1]] = (pin, pout)
    return out


PRICES = prices()


def row_cost(r: dict) -> float | None:
    """Logged cost_usd; if it is 0/missing but tokens were logged, tokens x PRICES.md; None if no price is known."""
    if r.get("cost_usd"):
        return float(r["cost_usd"])
    model = str(r.get("model", ""))
    p = PRICES.get(model) or PRICES.get(model.split("/")[-1])
    if p is None or not isinstance(r.get("prompt_tokens"), (int, float)):
        return None
    return (r["prompt_tokens"] * p[0] + (r.get("completion_tokens") or 0) * p[1]) / 1e6


def score_system(sysd: dict, items: dict, band: dict) -> dict:
    rows = sysd["rows"]
    sysd["per_item"] = {i: item_scores(items[i], r["output"], band) for i, r in rows.items()}
    ran = {split_of(i) for i in rows}  # a split the system ran at all must be complete; gaps count as failures
    gaps = sorted(i for i in items if split_of(i) in ran and i not in rows)
    sysd["per_item"].update({i: missing_scores(items[i]) for i in gaps})
    sysd["missing_ids"] = gaps
    lat = [r["latency_ms"] for r in rows.values() if isinstance(r.get("latency_ms"), (int, float))]
    cost = [row_cost(r) for r in rows.values()]
    cost = [c for c in cost if c is not None]
    if any(not r.get("cost_usd") for r in rows.values()) and cost:
        sysd["cost_source"] = "hackathon/report/PRICES.md x logged tokens"
    if lat and len(lat) == len(rows):
        sysd["latency_ms"] = st.percentiles(lat)
    if cost and len(cost) == len(rows):
        sysd["cost_per_1k_usd"] = st.cost_per_1k(cost)
    return sysd


def rate(vals: list[int]) -> dict:
    r, lo, hi = st.rate_ci(sum(vals), len(vals))
    return {"rate": r, "lo": lo, "hi": hi, "count": sum(vals), "n": len(vals)}


def summarise(per: list[dict]) -> dict:
    out = {"pass": rate([p["pass"] for p in per]), "gates": {g: rate([p[g] for p in per]) for g in GATES},
           "fact_fail": rate([p["fact_fail"] for p in per])}
    for key in ("in_range", "stock_per100", "len_ratio", "must_keep"):
        vals = [p[key] for p in per if key in p]
        if vals:
            out[key] = dict(zip(("mean", "lo", "hi"), st.bootstrap_ci(vals)), n=len(vals))
    for key in ("forbidden_hit", "verbatim_miss"):
        vals = [p[key] for p in per if key in p]
        if vals:
            out[key] = rate(vals)
    return out


def paired(a: dict, b: dict, ids: list[str]) -> dict:
    shared = [i for i in ids if i in a["per_item"] and i in b["per_item"]]
    res = {"n_shared": len(shared)}
    if not shared:
        return res
    for key in ("pass", *GATES, "in_range"):
        ids_k = [i for i in shared if key in a["per_item"][i] and key in b["per_item"][i]]
        if not ids_k:
            continue
        d, lo, hi, p = st.paired_bootstrap_diff([a["per_item"][i][key] for i in ids_k],
                                                [b["per_item"][i][key] for i in ids_k])
        res[key] = {"diff": d, "lo": lo, "hi": hi, "p": p, "significant": p < 0.05}
    return res


def pick_reference(labels: list[str], wanted: str | None) -> str:
    if wanted:
        if wanted not in labels:
            raise SystemExit(f"reference {wanted!r} not among systems {labels}")
        return wanted
    for prefix in ("frontier-strong", "frontier-live", "frontier"):
        hit = next((l for l in labels if l.startswith(prefix)), None)
        if hit:
            return hit
    return labels[0]


def block(systems: list[dict], ids: list[str], ref: dict) -> dict:
    """One leaderboard over the given item ids. Systems missing every id in the block are left out."""
    rows = []
    for s in systems:
        per = [s["per_item"][i] for i in ids if i in s["per_item"]]
        if not per:
            continue
        counted = sum(1 for i in ids if s["per_item"].get(i, {}).get("missing"))
        entry = {"label": s["label"], "n": len(per), "missing": len(ids) - len(per),
                 "counted_as_fail": counted, "summary": summarise(per)}
        if s is not ref:
            entry["vs_reference"] = paired(s, ref, ids)
        rows.append(entry)
    rows.sort(key=lambda e: -e["summary"]["pass"]["rate"])
    return {"n_items": len(ids), "systems": rows}


def judges(report_dir: str) -> list[dict]:
    out = []
    for f in sorted(glob.glob(os.path.join(report_dir, "judge_*.summary.json"))):
        j = json.load(open(f, encoding="utf-8"))
        if j.get("mock") or str(j.get("model", "")).startswith("mock"):
            continue  # mock verdicts are for pipeline tests only
        j["file"] = rel(f)
        j["sign_test_p"] = st.judge_sign_test(j["win"], j["loss"])
        out.append(j)
    return out


def build(paths: list[str], items: dict, band: dict, reference: str | None, report_dir: str) -> dict:
    systems = [score_system(s, items, band) for s in load_systems(paths, items).values()]
    if not systems:
        raise SystemExit("no run files found")
    ref_label = pick_reference([s["label"] for s in systems], reference)
    ref = next(s for s in systems if s["label"] == ref_label)
    by_split = {sp: sorted(i for i in items if split_of(i) == sp) for sp in SPLITS}
    rule = gt.__doc__.split("all four gates pass:")[1].strip("\n")
    res = {"reference": ref_label, "gates_rule": rule,
           "systems": [{"label": s["label"], "files": s["files"], "model": s["model"], "n": len(s["per_item"]),
                        **{k: s[k] for k in ("cost_per_1k_usd", "latency_ms") if k in s}} for s in systems],
           "blocks": {"all": block(systems, sorted(items), ref),
                      "main": block(systems, by_split["dev"] + by_split["trick"], ref),
                      **{sp: block(systems, ids, ref) for sp, ids in by_split.items()}},
           "judges": judges(report_dir)}
    return res


def pct(d: dict) -> str:
    return f"{100*d['rate']:.0f}% [{100*d['lo']:.0f}, {100*d['hi']:.0f}]"


def mean(d: dict, as_pct: bool = False) -> str:
    if as_pct:
        return f"{100*d['mean']:.0f}% [{100*d['lo']:.0f}, {100*d['hi']:.0f}]"
    return f"{d['mean']:.2f} [{d['lo']:.2f}, {d['hi']:.2f}]"


def delta(e: dict, key: str = "pass") -> str:
    v = e.get("vs_reference", {}).get(key)
    if not v:
        return "reference"
    return f"{100*v['diff']:+.0f} pp [{100*v['lo']:+.0f}, {100*v['hi']:+.0f}], " + \
        ("significant" if v["significant"] else "n.s.") + f" (p={v['p']:.3f})"


def leaderboard(res: dict, key: str, title: str) -> list[str]:
    b = res["blocks"][key]
    meta = {s["label"]: s for s in res["systems"]}
    lines = [f"## {title} ({b['n_items']} items)", "",
             "| System | Fact-safe human rate | Δ vs reference | G1 invented | G2 lost | G3 tells | G4 gutted "
             "| $ / 1k | p50 latency |", "|---|---|---|---|---|---|---|---|---|"]
    for e in b["systems"]:
        g, s = e["summary"]["gates"], meta[e["label"]]
        cost = f"${s['cost_per_1k_usd']:.2f}" if "cost_per_1k_usd" in s else "n/a"
        lat = f"{s['latency_ms']['p50']/1000:.1f}s" if "latency_ms" in s else "n/a"
        miss = (f" ({e['missing']} not run)" if e["missing"] else "") +             (f" ({e['counted_as_fail']} refused/failed, counted as fails)" if e.get("counted_as_fail") else "")
        lines.append(f"| `{e['label']}`{miss} | {pct(e['summary']['pass'])} | {delta(e)} | "
                     + " | ".join(f"{100*g[x]['rate']:.0f}%" for x in GATES) + f" | {cost} | {lat} |")
    return lines + ["", "Gate columns show the share of items that pass each gate. An item a system refused or failed "
                    "is scored as an empty rewrite (G1 and G3 pass, G2 and G4 fail), so it counts against that system.", ""]


def secondary(res: dict) -> list[str]:
    lines = ["## Secondary metrics (main split)", "",
             "| System | Fact hard-fails | In human range | Stock /100w | Length ratio | Must-keep (crude) |",
             "|---|---|---|---|---|---|"]
    for e in res["blocks"]["main"]["systems"]:
        sm = e["summary"]
        ff = sm["fact_fail"]
        mk = mean(sm["must_keep"], True) if "must_keep" in sm else "n/a"
        lines.append(f"| `{e['label']}` | {ff['count']}/{ff['n']} ({pct(ff)}) | {mean(sm['in_range'], True)} | "
                     f"{mean(sm['stock_per100'])} | {mean(sm['len_ratio'])} | {mk} |")
    return lines + [""]


def render(res: dict) -> str:
    out = ["# Results", "", "_Generated by `hackathon/eval/score_all.py` from `results.json`. Do not edit by hand._", "",
           f"Reference (F1): `{res['reference']}`. 95% CIs in brackets. Δ is a paired bootstrap on shared items.", "",
           "**Fact-safe human rewrite rate** = items passing all four gates:", "", "```", res["gates_rule"], "```", ""]
    out += leaderboard(res, "all", "Leaderboard, all items")
    for key, title in (("main", "Main eval: dev + trick"), ("dev", "Dev split"), ("trick", "Trick split"),
                       ("heldout", "Held-out pairs (real human references)")):
        if res["blocks"][key]["systems"]:
            out += leaderboard(res, key, title)
    out += secondary(res)
    if res["judges"]:
        out += ["## Pairwise judge (both orders; a win needs both orders to agree)", "",
                "| A vs B | Judge | A wins | B wins | Ties | Flip rate | Sign test p |", "|---|---|---|---|---|---|---|"]
        for j in res["judges"]:
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
    res = build(a.runs or discover(), all_items(), band, a.reference, a.out_dir)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "results.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(a.out_dir, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(res))
    print(f"scored {len(res['systems'])} systems on {res['blocks']['all']['n_items']} items -> "
          f"{rel(a.out_dir)}/results.json, RESULTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
