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
from matplotlib.transforms import Bbox, blended_transform_factory, offset_copy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
GATES = ("G1", "G2", "G3", "G4")
GATE_NAMES = {"G1": "G1 nothing\ninvented", "G2": "G2 nothing\nlost", "G3": "G3 no AI\ntells", "G4": "G4 not\ngutted"}
BLOCKS = ("all", "main", "heldout", "heldout_clean", "dev", "trick", "real")
# colorblind-safe pair from the dataviz reference palette (blue / orange); text stays in ink, never series color
SYS, REF = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
LEN = "#1b1b3a"  # lenient tick: dark navy, reads on both the blue and the hatched orange bar


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
    note = f"n={n} of {n_items} only" if entry.get("missing") else f"n={n}"
    shared = (entry.get("vs_reference") or {}).get("n_shared")
    if entry.get("missing") and shared:
        note += f"; Δ on {shared} shared"
    if entry.get("counted_as_fail"):
        note += f", {entry['counted_as_fail']} no-output = fail"  # refusals and empty outputs count as fails
    return note


def lenient_bits(entry: dict) -> tuple[float | None, str, str]:
    """(lenient rate %, ' · lenient 98.0%', ' · lenient +13.2 pp sig') from summary.pass_lenient; blanks if absent."""
    p = ((entry.get("summary") or {}).get("pass_lenient") or {})
    r = _num(p.get("rate"))
    if r is None:
        return None, "", ""
    v = ((entry.get("vs_reference") or {}).get("pass_lenient") or {})
    d = _num(v.get("diff"))
    delta = "" if d is None else f" · lenient {100*d:+.1f} pp " + ("sig" if v.get("significant") else "n.s.")
    return 100 * r, f" · lenient {100*r:.1f}%", delta


def cost_note(meta: dict) -> str:
    """'$8.93 per 1k rewrites · 3.9 s p50' from a top-level systems[] entry; 'cost n/a' when unknown or $0."""
    cost = _num(meta.get("cost_per_1k_usd"))
    p50 = _num((meta.get("latency_ms") or {}).get("p50"))
    note = f"${cost:.2f} per 1k rewrites" if cost and cost > 0 else "cost n/a"
    return note + (f" · {p50 / 1000:.1f} s p50" if p50 is not None else "")


def _leaderboard(ax, rows: list[tuple], name: str, n_items, notes: dict[str, str],
                 lenient: dict[str, tuple] | None = None) -> None:
    lenient = lenient or {}
    y = list(range(len(rows)))[::-1]  # first (best) row on top
    for yi, (lab, r, lo, hi, note, is_ref) in zip(y, rows):
        if math.isnan(r):
            continue
        ax.barh(yi, r, height=0.62, color=REF if is_ref else SYS, hatch="//" if is_ref else None,
                edgecolor="white", linewidth=2, zorder=2)
        ax.errorbar(r, yi, xerr=[[max(0, r - lo)], [max(0, hi - r)]], fmt="none", ecolor=INK, elinewidth=1.4,
                    capsize=4, zorder=3)
        lr = (lenient.get(lab) or (None,))[0]
        if lr is not None:  # lenient rate as a tall tick across the bar
            ax.plot([lr], [yi], marker="|", markersize=22, markeredgewidth=2.6, color=LEN, zorder=4)
    ax.set_yticks(y, [clip(display(r[0])) for r in rows])
    for t, row in zip(ax.get_yticklabels(), rows):
        t.set_fontweight("bold" if row[5] else "normal")
    ax.set_xlim(0, 100)
    pad = max(0.0, (6 - len(rows)) / 2)  # keep bars thin when there are few systems
    ax.set_ylim(-0.6 - pad, len(rows) - 0.4 + pad)
    ax.set_xlabel("Fact-safe human rewrite rate (%), passes G1-G4; bar = strict with 95% CI"
                  + ("; | = lenient (numerals/demonyms normalised)" if lenient else ""))
    ax.set_title(f"Leaderboard: block '{name}', {n_items} items", loc="left", fontsize=14, color=INK)
    tr = blended_transform_factory(ax.transAxes, ax.transData)
    below = offset_copy(tr, fig=ax.figure, y=-13, units="points")  # third line: coverage
    for yi, (lab, r, lo, hi, note, is_ref) in zip(y, rows):
        _, lhead, ldelta = lenient.get(lab) or (None, "", "")
        head = "n/a" if math.isnan(r) else f"{r:.1f}% [{lo:.1f}, {hi:.1f}]" + (" strict" if lhead else "") + lhead
        ax.text(1.02, yi, head, transform=tr, va="bottom", fontsize=10.5,
                color=INK, fontweight="bold" if is_ref else "normal")
        ax.text(1.02, yi, note + ldelta, transform=tr, va="top", fontsize=9.5, color=INK2)
        ax.text(1.02, yi, notes.get(lab, ""), transform=below, va="top", fontsize=8.5, color=INK2)
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.set_axisbelow(True)


# Label positions tried in order (offset in points, alignment): four snug spots, then rings of 8 directions at
# growing distance; ring spots get a leader line.
_SNUG = [(7, 4, "left"), (-8, 4, "right"), (7, -24, "left"), (-8, -24, "right")]
_RINGS = [(round(d * math.cos(t)), round(d * math.sin(t)) - 8, "left" if math.cos(t) >= 0 else "right")
          for d in (34, 56, 80) for t in [k * math.pi / 4 for k in (0, 4, 1, 3, 7, 5, 2, 6)]]
_SPOTS = _SNUG + _RINGS


# Readable row names for the deck (raw ids stay in results.json). Each name carries the system code so a reader can
# match the row to RESULTS.md; harness variants not listed read "GLM harness ablation (O3x)".
DISPLAY = {
    "O3c_glm_prompt_harness_style": "FeatherLM (O3c)",
    "frontier-strong:claude-opus-5-5": "Claude Opus 5.5 (strong prompt)",
    "frontier-live:claude-opus-5-5": "Claude Opus 5.5 (shared prompt)",
    "F1H_opus_harness": "Claude Opus 5.5 + our harness",
    "F1h_opus_humanizer": "Claude + humanizer prompt",
    "F2_gpt61_terra": "GPT-6.1 Terra",
    "F2h_gpt61_humanizer": "GPT-6.1 + humanizer",
    "O1_glm_base": "GLM-5.3 Flash base",
    "O2_glm_prompt": "GLM-5.3 + better prompt",
    "O2h_glm_humanizer": "GLM-5.3 + humanizer",
    "X0_copy_draft (no rewrite: control)": "Unchanged draft (control)",
    "frontier-persona-preexisting": "Claude persona (pre-event)",
}


def display(label: str) -> str:
    """Human name plus the system code, e.g. 'GPT-6.1 Terra · F2'; unknown O3x rows become 'GLM harness ablation (O3x)'."""
    code = short(label)
    name = DISPLAY.get(label)
    if name is None:
        return f"GLM harness ablation ({code})" if code.startswith("O3") else label
    return name if code in name else f"{name} · {code}"


def clip(label: str, n: int = 44) -> str:
    """Row label for the chart: long system names end in an ellipsis (the full name stays in results.json)."""
    return label if len(label) <= n else label[: n - 1].rstrip("_ ") + "…"


def short(label: str) -> str:
    """Point label on the cost panel: the system code ('O3c', 'F1H', 'X0'), or 'F1 strong' / 'F1 live' / 'persona'."""
    if label.startswith("frontier-"):
        kind = label.split(":")[0].removeprefix("frontier-")
        return {"strong": "F1 strong", "live": "F1 live", "persona-preexisting": "persona"}.get(kind, kind)
    return label.split("_")[0].split(" ")[0]


def _area(a: Bbox, b: Bbox) -> float:
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return w * h if w > 0 and h > 0 else 0.0


def _place_labels(ax, points: list[tuple]) -> None:
    """Greedy: highest rate first, each label at the first spot whose box hits no earlier label, no point and stays
    inside the axes; if none is free, the spot with the least overlap."""
    r = ax.figure.canvas.get_renderer()
    frame = ax.get_window_extent(r)
    pts = [Bbox.from_bounds(x - 7, y - 7, 14, 14) for x, y in ax.transData.transform([(p[1], p[2]) for p in points])]
    boxes = []
    for lab, cost, rate, p50, is_ref in sorted(points, key=lambda p: (-p[2], p[1])):
        code = short(lab)
        ablation = code.startswith("O3") and code != "O3c"  # the crowded harness cluster: code only, to stay legible
        txt = code + (f" · {p50:.1f} s" if p50 is not None and not ablation else "")
        best = None
        for i, (dx, dy, ha) in enumerate(_SPOTS):
            a = ax.annotate(txt, (cost, rate), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=8.5,
                            color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7, shrinkA=1, shrinkB=5))
            bb = a.get_window_extent(r).expanded(1.03, 1.08)
            clash = sum(_area(bb, o) for o in boxes + pts) + bb.width * bb.height - _area(bb, frame)
            if best is None or clash < best[0]:  # keep only the best try so far on the axes
                if best is not None:
                    best[1].remove()
                best = (clash, a, bb)
            else:
                a.remove()
            if clash == 0:
                break
        boxes.append(best[2])


def _pareto(ax, points: list[tuple], no_cost: list[str], name: str) -> None:
    ax.set_title(f"Pass rate vs cost (block '{name}'; code · p50 latency, ablations code only)", loc="left", fontsize=12,
                 color=INK)
    ax.set_ylabel("Fact-safe human rate (%)")
    ax.set_xlabel("$ per 1k rewrites (log scale, whole run)")
    if points:
        front = set(pareto_front(points))
        fp = sorted((p for p in points if p[0] in front), key=lambda p: p[1])
        ax.step([p[1] for p in fp], [p[2] for p in fp], where="post", color=INK2, linewidth=1, linestyle="--",
                zorder=1, label="cost/rate frontier")
        ax.set_xscale("log")
        costs = [p[1] for p in points]
        ax.set_xlim(min(costs) / 2, max(costs) * 4)
        ax.set_ylim(0, 112)  # limits first: label placement below measures in display space
        for lab, cost, rate, p50, is_ref in points:
            ax.scatter(cost, rate, s=90, color=REF if is_ref else SYS, marker="D" if is_ref else "o",
                       edgecolor="white", linewidth=2, zorder=3)
        _place_labels(ax, points)
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
        ax.text(0, 0, "not on the log axis (cost unknown or $0): " + ", ".join(display(x) for x in no_cost), fontsize=8.5,
                transform=offset_copy(ax.transAxes, fig=ax.figure, y=-58, units="points"),
                color=INK2, va="top", wrap=True)


def _gates(ax, labels: list[str], mat: list[list[float]]) -> None:
    ax.set_title("Each gate separately (% of items passing)", loc="left", fontsize=12, color=INK)
    ax.imshow(mat, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i, row in enumerate(mat):
        for j, v in enumerate(row):
            txt, dark = ("n/a", False) if math.isnan(v) else (f"{v:.0f}%", v >= 60)
            ax.text(j, i, txt, ha="center", va="center", fontsize=9, color="white" if dark else INK)
    ax.set_xticks(range(len(GATES)), [GATE_NAMES[g] for g in GATES], fontsize=8.5)
    ax.set_yticks(range(len(labels)), [clip(display(lab)) for lab in labels], fontsize=8.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def render(res: dict, name: str, out: str) -> str:
    name, b = pick_block(res, name)
    ref = res.get("reference") or ""
    rows = [(lab, r, lo, hi, note.replace(f"vs {ref}", f"vs {short(ref)}"), is_ref)  # "vs F1 strong", not the raw id
            for lab, r, lo, hi, note, is_ref in bar_rows(b, ref)]
    points, no_cost = pareto_points(b, res.get("systems") or [], ref)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False})
    # Leaderboard across the top with its notes in a wide right-hand column; Pareto and gates share the bottom row.
    # Heights in inches grow with the row count so three-line row notes never touch: top, board, gap, bottom, margin.
    n = max(len(rows), 1)
    top, board, gap, bottom, margin = 1.15, max(4.2, 0.52 * n + 0.5), 1.3, max(3.0, 0.24 * n + 0.4), 1.0
    H = top + board + gap + bottom + margin
    fig = plt.figure(figsize=(16, H), dpi=100, facecolor="white")
    meta = {s.get("label"): s for s in res.get("systems") or []}
    notes = {e.get("label"): coverage_note(e, b.get("n_items", "?")) + " · " + cost_note(meta.get(e.get("label")) or {})
             for e in b["systems"]}
    lenient = {e.get("label"): lenient_bits(e) for e in b["systems"] if lenient_bits(e)[0] is not None}
    _leaderboard(fig.add_axes((0.265, (margin + bottom + gap) / H, 0.37, board / H)), rows, name,
                 b.get("n_items", "?"), notes, lenient)
    _pareto(fig.add_axes((0.06, margin / H, 0.34, bottom / H)), points, no_cost, name)
    _gates(fig.add_axes((0.62, (margin - 0.4) / H, 0.35, (bottom + 0.45) / H)), *gate_rows(b))
    fig.suptitle("FeatherLM: fact-safe human rewrite rate vs the frontier reference", x=0.015, y=1 - 0.3 / H,
                 ha="left", fontsize=16, fontweight="bold", color=INK)
    ref_line = (f"Reference (hatched orange): {display(ref)}." if any(r[5] for r in rows)
                else f"Reference {display(ref)} is not in this block, so no Δ is shown.")
    fig.text(0.015, 1 - 0.75 / H, ref_line + " Δ = paired bootstrap on shared items; significant when p < 0.05. "
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
