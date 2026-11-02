"""Human A/B votes as one self-contained HTML page. Usage: build_human_dashboard.py [--in human_ab.jsonl] [--out ...html]
Reads the committed export (hackathon/report/human_ab.jsonl, written by hackathon/demo/ab_page/export_votes.py) and
writes hackathon/report/human_votes_dashboard.html: totals, FeatherLM share of decisive picks with its 95% interval and
sign test (hackathon/eval/stats.py, the same functions as the report), picks per passage, per reader, readers' notes.
Set 1 only (FeatherLM O3c vs Claude Opus 5.5 strong prompt). Re-run after every export; numbers come only from the file.
The live version of this page is a Claude dashboard on the Supabase table; its queries are in human_votes_dashboard.sql.
"""
import argparse, html, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "hackathon", "eval"))
from stats import judge_sign_test, rate_ci  # noqa: E402

SRC = os.path.join(HERE, "human_ab.jsonl")
OUT = os.path.join(HERE, "human_votes_dashboard.html")
SET1 = "fd809333"
CHOICES = (("featherlm", "FeatherLM (O3c)", "var(--c1)"), ("same", "About the same", "var(--muted-bar)"),
           ("claude", "Claude Opus 5.5, strong prompt", "var(--c2)"))
SOURCES = {"public": "public page", "local": "venue device", "store": "Claude page", "code": "vote code",
           "telegram": "Telegram page"}


def choice(r: dict) -> str:
    w = r.get("winner")
    return "same" if w is None else "featherlm" if w.startswith("O3c") else "claude"


def summarise(rows: list[dict]) -> dict:
    s1 = [r for r in rows if str(r.get("version", "")).startswith(SET1)]
    c = Counter(choice(r) for r in s1)
    f, cl = c["featherlm"], c["claude"]
    share, lo, hi = rate_ci(f, f + cl) if f + cl else (0.0, 0.0, 0.0)
    pairs, readers = defaultdict(Counter), defaultdict(Counter)
    for r in s1:
        pairs[(r["pid"], r["id"])][choice(r)] += 1
        readers[r["ballot"]][choice(r)] += 1
    src = defaultdict(lambda: [set(), 0])
    for r in s1:
        src[r["source"]][0].add(r["ballot"]); src[r["source"]][1] += 1
    return {"picks": len(s1), "readers": len(readers), "counts": c, "share": share, "lo": lo, "hi": hi,
            "p": judge_sign_test(f, cl) if f + cl else None, "decisive": f + cl,
            "phones": sum(1 for b in {r["ballot"] for r in s1}
                          if any((x.get("vw") or 9999) < 768 for x in s1 if x["ballot"] == b)),
            "pairs": sorted(pairs.items()), "readers_rows": list(readers.items()),
            "reasons": [r for r in s1 if (r.get("reason") or "").strip()],
            "sources": {k: (len(v[0]), v[1]) for k, v in src.items()},
            "other_sets": Counter(r["version"][:8] for r in rows if not str(r.get("version", "")).startswith(SET1))}


def bar(c: Counter, scale: int) -> str:
    segs = "".join(f'<i style="flex:{c[k]};background:{col}" title="{name} {c[k]}"></i>'
                   for k, name, col in CHOICES if c[k])
    return f'<div class="bar" style="width:{100 * sum(c.values()) / scale:.1f}%">{segs}</div>'


def render(s: dict) -> str:
    e = html.escape
    pct = lambda x: f"{100 * x:.1f}%"
    c = s["counts"]
    lead = "FeatherLM" if c["featherlm"] > c["claude"] else "Claude Opus 5.5" if c["claude"] > c["featherlm"] else "each side"
    lead_share = max(c["featherlm"], c["claude"]) / s["decisive"] if s["decisive"] else 0
    chance = ("That gap is unlikely to be chance." if s["p"] is not None and s["p"] < 0.05
              else "That gap could still be chance.")
    p = "—" if s["p"] is None else "<0.001" if s["p"] < 0.001 else f"{s['p']:.2f}"
    legend = "".join(f'<span><i style="background:{col}"></i>{name}</span>' for _, name, col in CHOICES)
    split = " · ".join(f"{name} {c[k]} ({pct(c[k] / s['picks'])})" for k, name, _ in CHOICES) if s["picks"] else ""
    mx = max((sum(v.values()) for _, v in s["pairs"]), default=1)
    pair_rows = "".join(
        f'<tr><td class="id">{e(i)}</td><td class="viz">{bar(v, mx)}</td><td class="num">{v["featherlm"]}</td>'
        f'<td class="num">{v["same"]}</td><td class="num">{v["claude"]}</td></tr>' for (pid, i), v in s["pairs"])
    reader_rows = "".join(
        f'<tr><td class="num">{n}</td><td class="num">{sum(v.values())}</td><td class="num">{v["featherlm"]}</td>'
        f'<td class="num">{v["same"]}</td><td class="num">{v["claude"]}</td></tr>'
        for n, (_, v) in enumerate(s["readers_rows"], 1))
    said = {"featherlm": "picked FeatherLM", "claude": "picked Claude", "same": "said about the same"}
    reasons = "".join(f'<li><q>{e(r["reason"].strip())}</q><div class="m">{e(r["id"])} · {said[choice(r)]}</div></li>'
                      for r in s["reasons"]) or '<li class="m">No notes yet.</li>'
    sources = ", ".join(f"{SOURCES.get(k, k)}: {n} readers, {m} picks" for k, (n, m) in sorted(s["sources"].items()))
    other = ", ".join(f"{v} ({n} picks)" for v, n in sorted(s["other_sets"].items())) or "none"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FeatherLM Human Votes</title>
<style>
:root{{--bg:#f7f6f2;--panel:#fffefb;--fg:#1f1e1b;--muted:#6b6862;--line:#e3e0d8;--c1:#2f6f5e;--c2:#8a5a2b;--muted-bar:#c9c5bb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#191917;--panel:#22221f;--fg:#ecebe6;--muted:#a3a098;--line:#3a3934;--c1:#5fb59b;--c2:#d39a5f;--muted-bar:#5a5852}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:32px 16px 64px;display:grid;gap:20px}}
h1{{font:400 30px/1.2 Georgia,"Iowan Old Style",serif;margin:0}}h2{{font-size:16px;font-weight:600;margin:0}}
.lede{{margin:8px 0 0;max-width:70ch}}.src,.note,.m{{color:var(--muted);font-size:13px}}.src{{max-width:80ch;margin:6px 0 0}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:12px}}
.tile,.card{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px;min-width:0}}
.card{{padding:20px;overflow-x:auto}}.k{{color:var(--muted);font-size:13px}}.v{{font:400 30px/1.2 Georgia,serif;margin-top:4px;font-variant-numeric:tabular-nums}}
.s{{color:var(--muted);font-size:13px;margin-top:4px;font-variant-numeric:tabular-nums}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:12px}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:var(--muted);margin:10px 0}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}.legend i{{width:11px;height:11px;border-radius:2px;display:inline-block}}
.bar{{display:flex;gap:2px;height:100%;min-height:14px;border-radius:4px;overflow:hidden}}.bar i{{display:block}}
.big .bar{{width:100%!important;height:32px}}.big p{{margin:10px 0 0;font-variant-numeric:tabular-nums}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}th{{text-align:left;color:var(--muted);font-size:12px;font-weight:600}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line)}}.num{{text-align:right;width:3.5em}}.id{{white-space:nowrap;width:6em}}
td.viz{{height:26px;min-width:120px}}.box{{max-height:420px;overflow:auto}}
ul{{list-style:none;margin:0;padding:0;display:grid;gap:14px}}q{{font-family:Georgia,serif}}
</style></head><body><main>
<header><h1>FeatherLM human votes</h1>
<p class="lede">Readers chose <b>{e(lead)}</b> in <b>{pct(lead_share)}</b> of the pairs where they picked a side. {chance}</p>
<p class="src">Blind A/B test, set 1: FeatherLM (O3c) against Claude Opus 5.5 with the strong prompt. Each reader gets 5 of 20
pairs in random order and never sees which system wrote which. Latest pick per reader and pair. Sources: {e(sources)}.
Other pair sets in the file: {e(other)}. Built from hackathon/report/human_ab.jsonl by build_human_dashboard.py.</p></header>
<section class="tiles">
<div class="tile"><div class="k">Readers</div><div class="v">{s['readers']}</div><div class="s">{s['phones']} on a phone</div></div>
<div class="tile"><div class="k">Picks</div><div class="v">{s['picks']}</div><div class="s">{len(s['reasons'])} with a written reason</div></div>
<div class="tile"><div class="k">FeatherLM share of decisive picks</div><div class="v">{pct(s['share'])}</div>
<div class="s">95% CI {pct(s['lo'])} to {pct(s['hi'])}, of {s['decisive']} picks</div></div>
<div class="tile"><div class="k">Sign test p</div><div class="v">{p}</div><div class="s">Two-sided, "about the same" left out</div></div>
</section>
<section class="card big"><h2>Every pick</h2><div class="legend">{legend}</div>{bar(c, max(1, s['picks']))}<p>{e(split)}</p></section>
<div class="grid">
<section class="card"><h2>By passage</h2><p class="note">Picks for each eval item. Readers see 5 of the 20, so bars differ in length.</p>
<div class="legend">{legend}</div><table><thead><tr><th>Item</th><th></th><th class="num">FeatherLM</th><th class="num">Same</th><th class="num">Claude</th></tr></thead>
<tbody>{pair_rows}</tbody></table></section>
<section class="card"><h2>What readers wrote</h2><p class="note">Optional notes left with a pick, as typed.</p><ul>{reasons}</ul></section>
</div>
<section class="card"><h2>Readers</h2><p class="note">One row per anonymous reader.</p><div class="box"><table>
<thead><tr><th class="num">Reader</th><th class="num">Answered</th><th class="num">FeatherLM</th><th class="num">Same</th><th class="num">Claude</th></tr></thead>
<tbody>{reader_rows}</tbody></table></div></section>
</main></body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="src", default=SRC)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    rows = [json.loads(l) for l in open(a.src, encoding="utf-8") if l.strip()]
    s = summarise(rows)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(s))
    c = s["counts"]
    print(f"set 1: {s['readers']} readers, {s['picks']} picks, FeatherLM {c['featherlm']} / same {c['same']} / "
          f"Claude {c['claude']}, share {s['share']:.3f} [{s['lo']:.3f}, {s['hi']:.3f}] p={s['p']} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
