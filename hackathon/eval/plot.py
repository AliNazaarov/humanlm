"""Leaderboard chart for the FeatherLM report, drawn from hackathon/report/results.json (score_all.py). Offline.
Usage: plot.py [--results PATH] [--block all|main|heldout|dev|trick] [--out PATH]

pick_block(res, name)          -> (name, block); "all" falls back to "main" when missing/empty; SystemExit if no systems
delta_note(entry, reference)   -> "reference" | "+X.X pp vs REF · significant" | "-X.X pp vs REF · n.s."
bar_rows(block, reference)     -> [(label, rate, lo, hi, note, is_ref)], rates in %, block order (pass rate desc)
pareto_points(block, systems)  -> ([(label, cost_per_1k, rate, p50_s | None, is_ref)], no_cost_labels)
pareto_front(points)           -> labels on the cost/rate frontier, cheapest first
gate_rows(block)               -> (labels, [[G1..G4 rate in %, NaN if absent]])
render(res, name, out)         -> writes the 3-panel PNG (~1600x1000)
Rates in results.json are fractions; everything here is shown in %. Cost/latency come from the top-level systems[]
(whole run, not per block); null, missing or non-positive cost goes to the footnote, never onto the log axis.
"""
from __future__ import annotations

import argparse, json, math, os, sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
from matplotlib.transforms import blended_transform_factory, offset_copy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
GATES = ("G1", "G2", "G3", "G4")
GATE_NAMES = {"G1": "G1 nothing\ninvented", "G2": "G2 nothing\nlost", "G3": "G3 no AI\ntells", "G4": "G4 not\ngutted"}
BLOCKS = ("all", "main", "heldout", "dev", "trick")
# colorblind-safe pair from the dataviz reference palette (blue / orange); text stays in ink, never series color
SYS, REF = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def pick_block(res: dict, name: str = "all") -> tuple[str, dict]:
    blocks = res.get("blocks") or {}
    b = blocks.get(name) or {}
    if name == "all" and not b.get("systems"):
        name, b = "main", blocks.get("main") or {}
    if not b.get("systems"):
        raise SystemExit(f"plot: block {name!r} has no systems in results.json")
    return name, b


def delta_note(entry: dict, reference: str) -> str:
    vs = entry.get("vs_reference")
    if vs is None:
        return "reference"
    p = vs.get("pass") or {}
    d = _num(p.get("diff"))
    if d is None:
        return f"no shared items with {reference}"
    return f"{100*d:+.1f} pp vs {reference} · " + ("significant" if p.get("significant") else "n.s.")


def bar_rows(block: dict, reference: str) -> list[tuple]:
    rows = []
    for e in block.get("systems") or []:
        p = (e.get("summary") or {}).get("pass") or {}
        r = _num(p.get("rate"))
        if r is None:  # no pass rate: keep the row, never draw it as 0%
            rows.append((e.get("label", "?"), math.nan, math.nan, math.nan, "n/a: no pass rate in results.json",
                         e.get("label") == reference))
            continue
        lo, hi = _num(p.get("lo")), _num(p.get("hi"))
        rows.append((e.get("label", "?"), 100 * r, 100 * (r if lo is None else lo), 100 * (r if hi is None else hi),
                     delta_note(e, reference), e.get("label") == reference))
    return rows


def pareto_points(block: dict, systems: list[dict], reference: str | None = None) -> tuple[list[tuple], list[str]]:
    meta = {s.get("label"): s for s in systems or []}
    points, no_cost = [], []
    for e in block.get("systems") or []:
        lab, s = e.get("label", "?"), meta.get(e.get("label")) or {}
        cost = _num(s.get("cost_per_1k_usd"))
        if cost is None or cost <= 0:
            no_cost.append(lab)
            continue
        p50 = _num((s.get("latency_ms") or {}).get("p50"))
        rate = _num(((e.get("summary") or {}).get("pass") or {}).get("rate"))
        if rate is None:
            continue
        points.append((lab, cost, 100 * rate, None if p50 is None else p50 / 1000, lab == reference))
    return points, no_cost


def pareto_front(points: list[tuple]) -> list[str]:
    """A point is on the front when nothing cheaper (or equal cost) has a pass rate at least as high."""
    front, best = [], -1.0
    for lab, cost, rate, *_ in sorted(points, key=lambda p: (p[1], -p[2])):
        if rate > best:
            front.append(lab)
            best = rate
    return front


def gate_rows(block: dict) -> tuple[list[str], list[list[float]]]:
    labels, mat = [], []
    for e in block.get("systems") or []:
        g = (e.get("summary") or {}).get("gates") or {}
        labels.append(e.get("label", "?"))
        mat.append([100 * v if (v := _num((g.get(k) or {}).get("rate"))) is not None else math.nan for k in GATES])
    return labels, mat


def coverage_note(entry: dict, n_items) -> str:
    """'n=250', or 'n=130 of 250 items only' when the system never ran part of the block, plus counted refusals."""
    n = ((entry.get("summary") or {}).get("pass") or {}).get("n", entry.get("n", "?"))
    note = f"n={n} of {n_items} items only" if entry.get("missing") else f"n={n}"
    shared = (entry.get("vs_reference") or {}).get("n_shared")
    if entry.get("missing") and shared:
        note += f"; Δ on {shared} shared items"
    if entry.get("counted_as_fail"):
        k = entry["counted_as_fail"]
        note += f", {k} refusal{'s' if k != 1 else ''}/no-output counted as fail"
    return note


def cost_note(meta: dict) -> str:
    """'$8.93 per 1k rewrites · 3.9 s p50' from a top-level systems[] entry; 'cost n/a' when unknown or $0."""
    cost = _num(meta.get("cost_per_1k_usd"))
    p50 = _num((meta.get("latency_ms") or {}).get("p50"))
    note = f"${cost:.2f} per 1k rewrites" if cost and cost > 0 else "cost n/a"
    return note + (f" · {p50 / 1000:.1f} s p50" if p50 is not None else "")


def _leaderboard(ax, rows: list[tuple], name: str, n_items, notes: dict[str, str]) -> None:
    y = list(range(len(rows)))[::-1]  # first (best) row on top
    for yi, (lab, r, lo, hi, note, is_ref) in zip(y, rows):
        if math.isnan(r):
            continue
        ax.barh(yi, r, height=0.62, color=REF if is_ref else SYS, hatch="//" if is_ref else None,
                edgecolor="white", linewidth=2, zorder=2)
        ax.errorbar(r, yi, xerr=[[max(0, r - lo)], [max(0, hi - r)]], fmt="none", ecolor=INK, elinewidth=1.4,
                    capsize=4, zorder=3)
    ax.set_yticks(y, [r[0] for r in rows])
    for t, row in zip(ax.get_yticklabels(), rows):
        t.set_fontweight("bold" if row[5] else "normal")
    ax.set_xlim(0, 100)
    pad = max(0.0, (6 - len(rows)) / 2)  # keep bars thin when there are few systems
    ax.set_ylim(-0.6 - pad, len(rows) - 0.4 + pad)
    ax.set_xlabel("Fact-safe human rewrite rate (%), passes G1-G4; whiskers = 95% CI")
    ax.set_title(f"Leaderboard: block '{name}', {n_items} items", loc="left", fontsize=14, color=INK)
    tr = blended_transform_factory(ax.transAxes, ax.transData)
    below = offset_copy(tr, fig=ax.figure, y=-13, units="points")  # third line: coverage
    for yi, (lab, r, lo, hi, note, is_ref) in zip(y, rows):
        head = "n/a" if math.isnan(r) else f"{r:.1f}% [{lo:.1f}, {hi:.1f}]"
        ax.text(1.02, yi, head, transform=tr, va="bottom", fontsize=10.5,
                color=INK, fontweight="bold" if is_ref else "normal")
        ax.text(1.02, yi, note, transform=tr, va="top", fontsize=9.5, color=INK2)
        ax.text(1.02, yi, notes.get(lab, ""), transform=below, va="top", fontsize=8.5, color=INK2)
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.set_axisbelow(True)


def _pareto(ax, points: list[tuple], no_cost: list[str], name: str) -> None:
    ax.set_title(f"Pass rate vs cost (block '{name}')", loc="left", fontsize=12, color=INK)
    ax.set_ylabel("Fact-safe human rate (%)")
    ax.set_xlabel("$ per 1k rewrites (log scale, whole run)")
    if points:
        front = set(pareto_front(points))
        fp = sorted((p for p in points if p[0] in front), key=lambda p: p[1])
        ax.step([p[1] for p in fp], [p[2] for p in fp], where="post", color=INK2, linewidth=1, linestyle="--",
                zorder=1, label="cost/rate frontier")
        placed = []  # (log cost, rate) of labels already drawn; a close neighbour puts this label left of its point
        for lab, cost, rate, p50, is_ref in sorted(points, key=lambda p: (-p[2], p[1])):
            ax.scatter(cost, rate, s=90, color=REF if is_ref else SYS, marker="D" if is_ref else "o",
                       edgecolor="white", linewidth=2, zorder=3)
            txt = lab + (f"\n{p50:.1f} s p50" if p50 is not None else "")
            near = any(abs(math.log10(cost) - c) < 0.5 and abs(rate - r) < 8 for c, r in placed)
            ax.annotate(txt, (cost, rate), xytext=(-8, 4) if near else (7, 4), textcoords="offset points",
                        ha="right" if near else "left", fontsize=8.5, color=INK)
            placed.append((math.log10(cost), rate))
        ax.set_xscale("log")
        costs = [p[1] for p in points]
        ax.set_xlim(min(costs) / 2, max(costs) * 4)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:g}"))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"${v:g}" if str(f"{v:g}")[0] in "25" else ""))
        ax.legend(loc="lower right", fontsize=8, frameon=False)
    else:
        ax.text(0.5, 0.5, "no systems with cost data", transform=ax.transAxes, ha="center", va="center", color=INK2)
        ax.set_xticks([])
    ax.set_ylim(0, 112)  # headroom so labels of ~95% points stay under the title
    ax.set_yticks(range(0, 101, 20))
    ax.grid(color=GRID, zorder=0)
    ax.set_axisbelow(True)
    if no_cost:
        ax.text(0, -0.24, "not on the log axis (cost unknown or $0): " + ", ".join(no_cost), transform=ax.transAxes, fontsize=8.5,
                color=INK2, va="top", wrap=True)


def _gates(ax, labels: list[str], mat: list[list[float]]) -> None:
    ax.set_title("Each gate separately (% of items passing)", loc="left", fontsize=12, color=INK)
    ax.imshow(mat, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i, row in enumerate(mat):
        for j, v in enumerate(row):
            txt, dark = ("n/a", False) if math.isnan(v) else (f"{v:.0f}%", v >= 60)
            ax.text(j, i, txt, ha="center", va="center", fontsize=9, color="white" if dark else INK)
    ax.set_xticks(range(len(GATES)), [GATE_NAMES[g] for g in GATES], fontsize=8.5)
    ax.set_yticks(range(len(labels)), labels, fontsize=8.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def render(res: dict, name: str, out: str) -> str:
    name, b = pick_block(res, name)
    ref = res.get("reference") or ""
    rows = bar_rows(b, ref)
    points, no_cost = pareto_points(b, res.get("systems") or [], ref)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False})
    # Leaderboard across the top with its notes in a wide right-hand column; Pareto and gates share the bottom row.
    fig = plt.figure(figsize=(16, 13), dpi=100, facecolor="white")
    meta = {s.get("label"): s for s in res.get("systems") or []}
    notes = {e.get("label"): coverage_note(e, b.get("n_items", "?")) + " · " + cost_note(meta.get(e.get("label")) or {})
             for e in b["systems"]}
    _leaderboard(fig.add_axes((0.22, 0.46, 0.40, 0.45)), rows, name, b.get("n_items", "?"), notes)
    _pareto(fig.add_axes((0.06, 0.10, 0.34, 0.25)), points, no_cost, name)
    _gates(fig.add_axes((0.62, 0.06, 0.35, 0.30)), *gate_rows(b))
    fig.suptitle("FeatherLM: fact-safe human rewrite rate vs the frontier reference", x=0.015, ha="left",
                 fontsize=16, fontweight="bold", color=INK)
    ref_line = (f"Reference (hatched orange): {ref}." if any(r[5] for r in rows)
                else f"Reference {ref} is not in this block, so no Δ is shown.")
    fig.text(0.015, 0.935, ref_line + " Δ = paired bootstrap on shared items; significant when p < 0.05. "
             "Each rate is over that system's n. Failed rows stay in.", fontsize=10, color=INK2)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(ROOT, "hackathon/report/results.json"))
    ap.add_argument("--block", default="all", choices=BLOCKS)
    ap.add_argument("--out", default=os.path.join(ROOT, "hackathon/report/leaderboard.png"))
    a = ap.parse_args(argv)
    if not os.path.exists(a.results):
        raise SystemExit(f"plot: {a.results} not found (run score_all.py first)")
    with open(a.results, encoding="utf-8") as f:
        res = json.load(f)
    out = render(res, a.block, a.out)
    print(f"plot -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
