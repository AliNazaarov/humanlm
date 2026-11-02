#!/usr/bin/env python3
"""Independent audit: is the harness just gaming its own metric?

The harness (hackathon/harness/harness.py) revises each draft against the exact gates we score (G1-G4 in
hackathon/harness/gates.py). This script scores every run file in evals/runs/hack_*.jsonl with signals the harness
never sees, and writes hackathon/audit/AUDIT.md (+ audit.json). Numbers in AUDIT.md come only from this script.

  python3 hackathon/audit/audit.py            # re-runs everything, picks up new run files by glob

Signals (none are used by the harness):
  a) reference similarity on the held-out pairs (chrF, word-overlap F1 vs the human original; the AI draft as floor)
  b) hold-out tells not in the gates (hedge, tricolon, paragraph-opener repeat, one-line paragraphs, burstiness,
     MATTR) vs the human band in evals/runs/band_v0.json
  c) gaming checks: near-copies of the draft, deleted sentences, label/markdown changes, artefacts, loops used
  d) paired bootstrap 95% CIs (1000 resamples, seed 0) harness vs the frontier rows
  e) gate forensics: how many official G1/G2 fails are metric artefacts (a numeral spelled out, "Kenyan" -> "Kenya",
     a capitalised word after a bullet) and the pass rate once those are corrected ("lenient" gates)
Stdlib + pipeline/metrics.py only. Read-only on everything outside hackathon/audit/.
"""
from __future__ import annotations

import collections, difflib, glob, json, math, os, random, re, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import metrics as m  # noqa: E402

BAND = json.load(open(os.path.join(ROOT, "evals/runs/band_v0.json"), encoding="utf-8"))["metrics"]
GATE_TELLS = ("stock_rate", "em_dash_rate", "not_x_but_y_rate", "emoji_rate", "exclaim_share")   # what gates.py checks
HOLDOUT_TELLS = ("hedge_rate", "tricolon_rate", "para_opener_repeat", "one_line_para_share", "burstiness", "mattr")
LEN_LO, LEN_HI, NAMES_MIN = 0.7, 1.3, 0.9          # same constants as gates.py
N_BOOT, SEED = 1000, 0
MIN_ROWS = 30          # a run with fewer rows is still in progress: listed, but kept out of every table and test
HARNESS_HINT = re.compile(r"harness|O3|F1H|O5|N3", re.I)
FRONTIER_HINT = re.compile(r"F2|claude|gpt|gemini|opus|frontier", re.I)

WORDNUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
           "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
           "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30", "zero": "0",
           "forty": "40", "fifty": "50", "sixty": "60", "hundred": "100", "thousand": "1000", "million": "1000000",
           "half": "0.5", "dozen": "12", "first": "1", "second": "2", "third": "3"}
LABEL = re.compile(r"(?mi)^\s*(headline(?: \d)?|subhead|subject|cta|tagline|description(?: \d)?|first comment|body|p\.?s\.?)\s*:")
MD = re.compile(r"(?m)\*\*|^#{1,6}\s|^\s*[-*]\s")
META = re.compile(r"(?i)(^|\n)\s*\*?\s*(note:|one thing to check|i've kept|i have kept|here is the|here's the|"
                  r"rewritten version|let me know|i'd rather not|i can't|i cannot|as an ai|this text is|"
                  r"i'd be happy to|would you like me)")
TRAILING_NUMS = re.compile(r"(?:\b\d[\d.,]*\b[\s,;]*){4,}\s*$")


# ---------------------------------------------------------------- io
def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def load_items():
    items = {}
    for f in ("evals/eval_all.jsonl", "evals/heldout_pairs.jsonl"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            for r in read_jsonl(p):
                items[r["id"]] = r
    return items


def split_of(i):
    return "heldout" if i.startswith("ho-") else "trick" if i.startswith("trick") else "dev"


def discover(items):
    """Every evals/runs/hack_*.jsonl (side files like X.jsonl.failures.jsonl skipped), grouped by `system` label."""
    systems = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "evals/runs/hack_*.jsonl"))):
        if ".jsonl." in os.path.basename(p):
            continue
        rows = read_jsonl(p)
        if not rows:
            continue
        label = rows[0].get("system") or os.path.basename(p)
        s = systems.setdefault(label, {"label": label, "files": [], "rows": {}, "model": rows[0].get("model")})
        s["files"].append(rel(p))
        for r in rows:
            if r["id"] in items and (r.get("output") or "").strip() and r["id"] not in s["rows"]:
                s["rows"][r["id"]] = r
    for s in systems.values():
        ran = {split_of(i) for i in s["rows"]}
        expected = [i for i in items if split_of(i) in ran]
        s["expected"] = len(expected)
        s["missing"] = sorted(i for i in expected if i not in s["rows"])
        s["complete"] = not s["missing"]
        s["kind"] = ("harness" if HARNESS_HINT.search(s["label"]) else
                     "frontier" if FRONTIER_HINT.search(s["label"]) else "open")
    return systems


# ---------------------------------------------------------------- text helpers
def toks(t):
    return [w.lower() for w in m.words(t)]


def bag_f1(a, b):
    """F1 between two multisets of tokens."""
    if not a or not b:
        return 0.0
    ca, cb = collections.Counter(a), collections.Counter(b)
    inter = sum((ca & cb).values())
    if not inter:
        return 0.0
    p, r = inter / len(b), inter / len(a)
    return 2 * p * r / (p + r)


def ngrams(seq, n):
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]


def chrf(hyp, ref, max_n=6, beta=2.0):
    """chrF (Popovic 2015): char n-gram P/R averaged over n=1..6, F-beta with beta=2, whitespace removed."""
    h, r = re.sub(r"\s+", "", hyp), re.sub(r"\s+", "", ref)
    ps, rs = [], []
    for n in range(1, max_n + 1):
        hg, rg = collections.Counter(ngrams(h, n)), collections.Counter(ngrams(r, n))
        if not hg or not rg:
            continue
        inter = sum((hg & rg).values())
        ps.append(inter / sum(hg.values()))
        rs.append(inter / sum(rg.values()))
    if not ps:
        return 0.0
    p, r = statistics.fmean(ps), statistics.fmean(rs)
    if p + r == 0:
        return 0.0
    return (1 + beta ** 2) * p * r / (beta ** 2 * p + r)


def content_words(t):
    return [w for w in toks(t) if len(w) > 3]


FORMAT_NOISE = re.compile(r"\*\*|__|^#{1,6}\s+|^\s*[-*•✓✔▸►]\s+|[\U0001F300-\U0001FAFF\U0001F1E6-\U0001F1FF☀-➿⭐⭕️]", re.M)


def names_lenient(text):
    """metrics._names after stripping markdown/emoji/bullets, and also skipping Title Case *segments* (bold labels such
    as '**The Weak Monsters**:' or 'Headline: Close Your Books Faster'), where capitalisation says nothing about names."""
    out = set()
    text = re.sub(r"\s*[—–]\s*|\s+-\s+", ". ", FORMAT_NOISE.sub("", m._norm(text)))   # a dash pause starts a new clause
    for line in text.splitlines():
        ws = m.words(line)
        if len(ws) >= 3 and sum(w[:1].isupper() for w in ws) / len(ws) >= 0.6:
            continue
        for seg in re.split(r":\s+", line):
            sw = m.words(seg)
            if len(sw) >= 2 and sum(w[:1].isupper() for w in sw) / len(sw) >= 0.6:
                continue
            for s in m.sentences(seg):
                for w in m.words(s)[1:]:
                    w = re.sub(r"'s$", "", w)
                    if w[0].isupper() and w.lower() not in m.PRONOUN_I and not (len(w) > 1 and w.isupper()):
                        out.add(w.lower())   # ALL-CAPS shouting ("HERE!") is not a name
    return out


def derived(token, text_low):
    """'kenya' from 'Kenyan', 'february' from 'Feb', 'baltic' from 'Baltics': the token or its 4-letter stem is in the text."""
    if token in text_low:
        return True
    stem = token[:4] if len(token) >= 4 else token
    return len(stem) >= 4 and re.search(r"\b" + re.escape(stem), text_low) is not None


# ---------------------------------------------------------------- gates (same rule as gates.py) + forensics
def gate_check(draft, out):
    f = m.faithfulness(draft, out)
    tm = m.text_metrics(out)
    ratio = tm["n_words"] / max(len(m.words(draft)), 1)
    bad_tells = [k for k in GATE_TELLS if tm[k] > BAND[k][1] + 1e-9]
    g1 = not f["hard_fail"]
    g2 = not f["numbers_dropped"] and f["names_kept"] >= NAMES_MIN
    g3 = not bad_tells
    g4 = LEN_LO <= ratio <= LEN_HI
    # --- forensics: which fails are artefacts of the cheap regex checks?
    out_low, draft_low = out.lower(), draft.lower()
    nums_added_real = [x for x in f["numbers_added"]]
    src_words = {re.sub(r"'s$", "", w.lower()) for w in m.words(draft)}
    out_words = {re.sub(r"'s$", "", w.lower()) for w in m.words(out)}
    src_names_len, out_names_len = names_lenient(draft), names_lenient(out)
    common = lambda n, t: n.endswith("ly") or re.search(r"(?<![A-Za-z])" + re.escape(n) + r"(?![A-Za-z])", t) is not None  # adverb, or used in lower case
    names_added_real = sorted(n for n in out_names_len if n not in src_words and not derived(n, draft_low) and not common(n, draft + " " + out))
    names_added_artefact = [n for n in f["names_added"] if n not in names_added_real]
    quote_reworded = bool(f["quotes_added"]) and bool(m.attributions(draft)["quotes"])
    quote_new = bool(f["quotes_added"]) and not m.attributions(draft)["quotes"]
    nums_dropped_spelled = [x for x in f["numbers_dropped"]
                           if any(re.search(r"\b" + w + r"\b", out_low) for w, n in WORDNUM.items() if n == x)]
    nums_dropped_real = [x for x in f["numbers_dropped"] if x not in nums_dropped_spelled]
    names_dropped_real = sorted(n for n in src_names_len if n not in out_words and not derived(n, out_low) and not common(n, draft))
    names_kept_lenient = 1.0 if not src_names_len else 1 - len(names_dropped_real) / len(src_names_len)
    g1_real = not (nums_added_real or names_added_real or quote_new)
    g2_real = not nums_dropped_real and names_kept_lenient >= NAMES_MIN
    reasons = {
        "g1_numbers_added": bool(nums_added_real), "g1_names_added_real": bool(names_added_real),
        "g1_names_added_artefact": bool(names_added_artefact), "g1_quote_new": quote_new,
        "g1_quote_reworded": quote_reworded, "g1_attribution_verb": bool(f["attribution_added"]),
        "g2_numbers_dropped_real": bool(nums_dropped_real), "g2_numbers_spelled_out": bool(nums_dropped_spelled),
        "g2_names_dropped_real": names_kept_lenient < NAMES_MIN,
        "g2_names_dropped_artefact": (f["names_kept"] < NAMES_MIN) and names_kept_lenient >= NAMES_MIN,
    }
    return {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "pass": g1 and g2 and g3 and g4,
            "G1_lenient": g1_real, "G2_lenient": g2_real, "pass_lenient": g1_real and g2_real and g3 and g4,
            "len_ratio": ratio, "bad_tells": bad_tells, "reasons": reasons, "tm": tm, "faith": f,
            "detail": {"nums_added": nums_added_real, "names_added_real": names_added_real,
                       "names_added_artefact": names_added_artefact, "nums_dropped_real": nums_dropped_real,
                       "nums_dropped_spelled": nums_dropped_spelled, "names_dropped_real": names_dropped_real,
                       "quotes_added": f["quotes_added"][:1], "quote_reworded": quote_reworded,
                       "attribution_verb_added": bool(f["attribution_added"]), "bad_tells": bad_tells,
                       "len_ratio": round(ratio, 2)}}


# ---------------------------------------------------------------- per-row signals the harness never sees
def row_signals(item, out, loops_used=None):
    draft = item["ai_draft"]
    g = gate_check(draft, out)
    tm = g["tm"]
    dt, ot = toks(draft), toks(out)
    sig = {
        "pass": int(g["pass"]), "pass_lenient": int(g["pass_lenient"]),
        "G1": int(g["G1"]), "G2": int(g["G2"]), "G3": int(g["G3"]), "G4": int(g["G4"]),
        "G1_lenient": int(g["G1_lenient"]), "G2_lenient": int(g["G2_lenient"]),
        "len_ratio": g["len_ratio"],
        # b) hold-out tells
        **{f"inband_{k}": int(BAND[k][0] - 1e-9 <= tm[k] <= BAND[k][1] + 1e-9) for k in HOLDOUT_TELLS},
        # c) gaming checks
        "copy_uni_f1": bag_f1(dt, ot), "copy_bi_f1": bag_f1(ngrams(dt, 2), ngrams(ot, 2)),
        "identical": int(out.strip() == draft.strip()),
        "label_stripped": int(bool(LABEL.search(draft)) and not LABEL.search(out)),
        "markdown_added": int(bool(MD.search(out)) and not MD.search(draft)),
        "markdown_stripped": int(bool(MD.search(draft)) and not MD.search(out)),
        "meta_note": int(bool(META.search(out))),
        "trailing_numbers": int(bool(TRAILING_NUMS.search(out.strip()))),
        "loops_used": loops_used,
    }
    sig["inband_holdout_all"] = int(all(sig[f"inband_{k}"] for k in HOLDOUT_TELLS))
    sig["inband_holdout_share"] = statistics.fmean(sig[f"inband_{k}"] for k in HOLDOUT_TELLS)
    sig["near_copy"] = int(sig["copy_bi_f1"] > 0.9)
    # deleted sentences: a draft sentence (>= 5 words) whose content words are < 40% recalled anywhere in the output
    out_cw = collections.Counter(content_words(out))
    dsents = [s for s in m.sentences(draft) if len(m.words(s)) >= 5]
    deleted = 0
    for s in dsents:
        cw = content_words(s)
        if cw and sum(w in out_cw for w in cw) / len(cw) < 0.4:
            deleted += 1
    sig["deleted_sent_rate"] = deleted / len(dsents) if dsents else 0.0
    sig["any_sent_deleted"] = int(deleted > 0)
    # repeated sentence (>= 6 words) inside the output
    osents = [" ".join(toks(s)) for s in m.sentences(out) if len(m.words(s)) >= 6]
    sig["repeated_sentence"] = int(len(osents) != len(set(osents)))
    sig["artefact_any"] = int(sig["meta_note"] or sig["trailing_numbers"] or sig["repeated_sentence"] or sig["identical"])
    # a) reference similarity (held-out only)
    if item.get("human"):
        sig["chrf_ref"] = chrf(out, item["human"])
        sig["wordf1_ref"] = bag_f1(ot, toks(item["human"]))
        sig["chrf_draft_floor"] = chrf(draft, item["human"])
        sig["closer_than_draft"] = int(sig["chrf_ref"] > sig["chrf_draft_floor"])
    for k, v in g["reasons"].items():
        sig["r_" + k] = int(v)
    sig["_detail"] = g["detail"]
    return sig


# ---------------------------------------------------------------- stats
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def paired_bootstrap(a, b, n_boot=N_BOOT, seed=SEED):
    """Mean(a-b) with a percentile 95% CI over resampled items; p = two-sided share of resamples crossing 0."""
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    if n == 0:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        means.append(statistics.fmean(d[rng.randrange(n)] for _ in range(n)))
    means.sort()
    lo, hi = means[int(0.025 * n_boot)], means[min(n_boot - 1, int(0.975 * n_boot))]
    obs = statistics.fmean(d)
    p = 2 * min(sum(x <= 0 for x in means), sum(x >= 0 for x in means)) / n_boot
    return {"mean": obs, "lo": lo, "hi": hi, "p": min(1.0, p), "n": n}


def mean_of(per, key, ids=None):
    vals = [per[i][key] for i in (ids or per) if i in per and per[i].get(key) is not None]
    return statistics.fmean(vals) if vals else None


def rate_str(per, key, ids=None):
    vals = [per[i][key] for i in (ids or per) if i in per and per[i].get(key) is not None]
    if not vals:
        return "n/a"
    p, lo, hi = wilson(sum(vals), len(vals))
    return f"{100 * p:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]"


def pct(x, nd=0):
    return "n/a" if x is None else f"{100 * x:.{nd}f}%"


def num(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    items = load_items()
    systems = discover(items)
    if not systems:
        raise SystemExit("no evals/runs/hack_*.jsonl files found")
    in_progress = {k: s for k, s in systems.items() if len(s["rows"]) < MIN_ROWS}
    systems = {k: s for k, s in systems.items() if k not in in_progress}
    if not systems:
        raise SystemExit("every run file has fewer than MIN_ROWS rows")
    # score every row with the out-of-gate signals
    for s in systems.values():
        s["per"] = {i: row_signals(items[i], r["output"], r.get("loops_used")) for i, r in s["rows"].items()}
        # score_all counts a missing row (refusal/failed call) as an empty rewrite that fails; we mirror that only for
        # the official pass-rate block so the leaderboard numbers match, and skip gaps everywhere else.
        s["pass_with_gaps"] = {i: s["per"][i]["pass"] for i in s["per"]} | {i: 0 for i in s["missing"]}
    # calibration row: the held-out human originals themselves, scored as if they were outputs
    human = {}
    for i, it in items.items():
        if it.get("human"):
            human[i] = row_signals(it, it["human"])
    # the AI drafts scored as outputs (floor for the tells)
    draft_rows = {i: row_signals(it, it["ai_draft"]) for i, it in items.items()}

    order = sorted(systems, key=lambda k: -statistics.fmean(systems[k]["pass_with_gaps"].values()))
    ho_ids = [i for i in items if split_of(i) == "heldout"]
    main_ids = [i for i in items if split_of(i) != "heldout"]
    harness_labels = [k for k in order if systems[k]["kind"] == "harness"]
    primary = next((k for k in order if k.startswith("O3_")), harness_labels[0] if harness_labels else order[0])
    frontier_labels = [k for k in order if systems[k]["kind"] == "frontier" and k != primary]

    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "n_items": len(items), "band": rel(os.path.join(ROOT, "evals/runs/band_v0.json")),
           "systems": {}, "paired": {}, "examples": [], "leaderboard": {}}
    L = []
    w = L.append
    w("# Audit: is the harness gaming its own metric?")
    w("")
    w(f"_Generated by `hackathon/audit/audit.py` on {out['generated']} from every `evals/runs/hack_*.jsonl` present "
      f"({len(systems)} systems, {len(items)} eval items). Re-run the script to refresh; do not edit numbers by hand._")
    w("")
    w("**The question.** `hackathon/harness/harness.py` drafts, checks the draft against the exact four gates we score "
      "(`hackathon/harness/gates.py`: G1 nothing invented, G2 nothing lost, G3 no AI tells, G4 length 0.7-1.3x), asks the "
      "model to fix the listed problems, and keeps the best of up to 4 candidates. A system that optimises the metric it is "
      "scored on can win the metric without writing better text. This audit scores every system with signals the harness "
      "never sees, and also checks whether the official gates themselves are fair (section E).")
    w("")
    w("**Short answer.** See the verdict table in section F; every number there is computed below.")
    w("")

    # ---- systems table
    w("## Systems found")
    w("")
    w("| System | Kind | Model | Rows | Expected | Complete | Files |")
    w("|---|---|---|---|---|---|---|")
    for k in order:
        s = systems[k]
        w(f"| `{k}` | {s['kind']} | `{s['model']}` | {len(s['rows'])} | {s['expected']} | "
          f"{'yes' if s['complete'] else 'NO (' + str(len(s['missing'])) + ' missing, counted as fails in the official rate)'} | "
          f"{', '.join('`' + f + '`' for f in s['files'])} |")
    w("")
    for k, s in in_progress.items():
        w(f"- `{k}`: {len(s['rows'])} rows so far ({', '.join('`' + f + '`' for f in s['files'])}); fewer than {MIN_ROWS}, so it is in progress and left out of every table below.")
    if in_progress:
        w("")
    w(f"Primary harness row for the paired tests: `{primary}`. Frontier rows: {', '.join('`' + f + '`' for f in frontier_labels) or 'none'}.")
    w("")

    # ---- leaderboard (official gates) for the deck
    w("## Official headline metric (for reference; same rule as `gates.py`, missing rows count as fails)")
    w("")
    w("| System | All items | Main (dev+trick) | Held-out | G1 | G2 | G3 | G4 |")
    w("|---|---|---|---|---|---|---|---|")
    for k in order:
        s = systems[k]
        pw = s["pass_with_gaps"]
        blocks = {}
        for name, ids in (("all", list(items)), ("main", main_ids), ("heldout", ho_ids)):
            vals = [pw[i] for i in ids if i in pw]
            blocks[name] = wilson(sum(vals), len(vals)) + (len(vals),) if vals else None
        out["leaderboard"][k] = {b: (None if v is None else {"rate": v[0], "lo": v[1], "hi": v[2], "n": v[3]}) for b, v in blocks.items()}
        out["leaderboard"][k]["gates"] = {g: mean_of(s["per"], g) for g in ("G1", "G2", "G3", "G4")}
        cell = lambda b: "n/a" if blocks[b] is None else f"{100 * blocks[b][0]:.0f}% [{100 * blocks[b][1]:.0f}, {100 * blocks[b][2]:.0f}] n={blocks[b][3]}"
        w(f"| `{k}` | {cell('all')} | {cell('main')} | {cell('heldout')} | " + " | ".join(pct(mean_of(s['per'], g)) for g in ("G1", "G2", "G3", "G4")) + " |")
    w("")
    w("Wilson 95% intervals. `hackathon/report/results.json` is the official source for the leaderboard; this table exists so the audit's other numbers can be read next to it.")
    w("")

    # ---- E) gate forensics
    w("## E. Are the official gates fair? (gate forensics)")
    w("")
    w("G1 and G2 use cheap regex checks from `pipeline/metrics.py`: a 'name' is any capitalised word that is not sentence-initial, a "
      "'number' is any digit string. That produces false fails that have nothing to do with facts: `Kenyan freelancers` -> `freelancers in Kenya` "
      "counts as an invented name; `5 months` -> `five months` counts as a dropped number; a capitalised word after a markdown bullet counts as a name; "
      "`We added support` counts as an added attribution verb. The columns below split every G1/G2 fail into real and artefact, and recompute the pass "
      "rate with the artefacts forgiven (**lenient**). A reworded quotation is kept as a real fail (someone's words were changed) but shown separately.")
    w("")
    w("| System | Official pass | Lenient pass | G1 fails: real invented number | real new name | new quote | reworded quote | name artefact only | attribution verb only | G2 fails: real dropped number | numeral spelled out | real dropped name | name artefact only |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in order:
        s = systems[k]; per = s["per"]
        cnt = lambda key: sum(p[key] for p in per.values())
        only_name_art = sum(1 for p in per.values() if not p["G1"] and p["r_g1_names_added_artefact"] and not (p["r_g1_numbers_added"] or p["r_g1_names_added_real"] or p["r_g1_quote_new"] or p["r_g1_quote_reworded"] or p["r_g1_attribution_verb"]))
        only_attr = sum(1 for p in per.values() if not p["G1"] and p["r_g1_attribution_verb"] and not (p["r_g1_numbers_added"] or p["r_g1_names_added_real"] or p["r_g1_quote_new"] or p["r_g1_quote_reworded"] or p["r_g1_names_added_artefact"]))
        only_spelled = sum(1 for p in per.values() if not p["G2"] and p["r_g2_numbers_spelled_out"] and not (p["r_g2_numbers_dropped_real"] or p["r_g2_names_dropped_real"]))
        only_name_drop_art = sum(1 for p in per.values() if not p["G2"] and p["r_g2_names_dropped_artefact"] and not (p["r_g2_numbers_dropped_real"] or p["r_g2_names_dropped_real"] or p["r_g2_numbers_spelled_out"]))
        out["systems"].setdefault(k, {})["forensics"] = {
            "official_pass": mean_of(per, "pass"), "lenient_pass": mean_of(per, "pass_lenient"),
            "g1_numbers_added": cnt("r_g1_numbers_added"), "g1_names_added_real": cnt("r_g1_names_added_real"),
            "g1_quote_new": cnt("r_g1_quote_new"), "g1_quote_reworded": cnt("r_g1_quote_reworded"),
            "g1_only_name_artefact": only_name_art, "g1_only_attribution_verb": only_attr,
            "g2_numbers_dropped_real": cnt("r_g2_numbers_dropped_real"), "g2_only_spelled_out": only_spelled,
            "g2_names_dropped_real": cnt("r_g2_names_dropped_real"), "g2_only_name_artefact": only_name_drop_art, "n": len(per)}
        w(f"| `{k}` | {rate_str(per, 'pass')} | {rate_str(per, 'pass_lenient')} | {cnt('r_g1_numbers_added')} | {cnt('r_g1_names_added_real')} | "
          f"{cnt('r_g1_quote_new')} | {cnt('r_g1_quote_reworded')} | {only_name_art} | {only_attr} | {cnt('r_g2_numbers_dropped_real')} | "
          f"{only_spelled} | {cnt('r_g2_names_dropped_real')} | {only_name_drop_art} |")
    w("")
    w("Counts are rows (out of each system's rows, gaps excluded). 'only' columns: the row failed that gate for that artefact and nothing else. "
      "Note the 'real new name' column is still a regex guess: inspect `audit.json` -> `detail` before quoting any single item as an invention.")
    w("")

    # ---- a) reference similarity
    w("## A. Reference similarity on the held-out pairs (120 items with a human original)")
    w("")
    w("chrF (character n-grams 1-6, beta=2) and bag-of-words F1 between the system output and the human original the AI draft was made from. "
      "The AI draft itself is the floor: a system that just copies the draft scores the floor exactly. 'Closer than draft' is the share of items where "
      "the output's chrF to the human is above the draft's. The harness never sees the human text.")
    w("")
    w("| System | n | chrF vs human | word-F1 vs human | closer than draft | chrF vs draft (copy) |")
    w("|---|---|---|---|---|---|")
    floor_chrf = statistics.fmean(draft_rows[i]["chrf_draft_floor"] for i in ho_ids)
    floor_f1 = statistics.fmean(bag_f1(toks(items[i]["ai_draft"]), toks(items[i]["human"])) for i in ho_ids)
    w(f"| _AI draft (floor)_ | {len(ho_ids)} | {num(floor_chrf)} | {num(floor_f1)} | 0% | 1.000 |")
    for k in order:
        s = systems[k]; per = s["per"]
        if not any(i in per for i in ho_ids):
            continue
        c = mean_of(per, "chrf_ref", ho_ids); f1 = mean_of(per, "wordf1_ref", ho_ids)
        cd = statistics.fmean(chrf(s["rows"][i]["output"], items[i]["ai_draft"]) for i in ho_ids if i in per)
        out["systems"].setdefault(k, {})["ref"] = {"chrf": c, "wordf1": f1, "closer_than_draft": mean_of(per, "closer_than_draft", ho_ids), "chrf_vs_draft": cd,
                                                   "n": sum(i in per for i in ho_ids)}
        w(f"| `{k}` | {sum(i in per for i in ho_ids)} | {num(c)} | {num(f1)} | {rate_str(per, 'closer_than_draft', ho_ids)} | {num(cd)} |")
    out["floor"] = {"chrf": floor_chrf, "wordf1": floor_f1}
    w("")
    w("Reading it: every rewrite drifts away from the human original (the draft is already a close paraphrase of it), so absolute values sit below the floor. "
      "What matters is the ordering and the gap: a harness that only gamed the gates would sit at the floor on chrF-vs-draft (near 1.0) and show no movement toward the human.")
    w("")

    # ---- b) hold-out tells
    w("## B. Hold-out tells the gates never check")
    w("")
    w("Six per-text tells from `pipeline/metrics.py` that are **not** in G3, each checked against the 10th-90th percentile human band "
      "(`evals/runs/band_v0.json`, 909 human texts). The harness is never told about these. The held-out human originals are scored the same way as a calibration row: "
      "two of the band's metrics (`para_opener_repeat`, `one_line_para_share`) have a zero-width band, so even real human text fails them often, "
      "and short social posts with one-line paragraphs fail `one_line_para_share` by construction.")
    w("")
    w("| System | n | " + " | ".join(HOLDOUT_TELLS) + " | all 6 in band | mean in-band share |")
    w("|---|---|" + "---|" * (len(HOLDOUT_TELLS) + 2))
    for label, per, ids in (("_held-out human originals (calibration)_", human, ho_ids), ("_AI drafts (floor)_", draft_rows, list(items))):
        w(f"| {label} | {len(per)} | " + " | ".join(pct(mean_of(per, f'inband_{k}', ids)) for k in HOLDOUT_TELLS)
          + f" | {pct(mean_of(per, 'inband_holdout_all', ids))} | {pct(mean_of(per, 'inband_holdout_share', ids), 1)} |")
    out["calibration"] = {"human": {k: mean_of(human, f"inband_{k}") for k in HOLDOUT_TELLS} | {"all": mean_of(human, "inband_holdout_all"), "share": mean_of(human, "inband_holdout_share")},
                          "draft": {k: mean_of(draft_rows, f"inband_{k}") for k in HOLDOUT_TELLS} | {"all": mean_of(draft_rows, "inband_holdout_all"), "share": mean_of(draft_rows, "inband_holdout_share")}}
    for k in order:
        per = systems[k]["per"]
        out["systems"].setdefault(k, {})["tells"] = {t: mean_of(per, f"inband_{t}") for t in HOLDOUT_TELLS} | {"all": mean_of(per, "inband_holdout_all"), "share": mean_of(per, "inband_holdout_share")}
        w(f"| `{k}` | {len(per)} | " + " | ".join(pct(mean_of(per, f'inband_{t}')) for t in HOLDOUT_TELLS)
          + f" | {pct(mean_of(per, 'inband_holdout_all'))} | {pct(mean_of(per, 'inband_holdout_share'), 1)} |")
    w("")

    # ---- c) gaming checks
    w("## C. Gaming checks (all systems; the harness rows are the ones under suspicion)")
    w("")
    w("- **near-copy**: word-bigram F1 between output and draft > 0.9 (the model barely rewrote); **identical**: output == draft.")
    w("- **deleted sentences**: share of draft sentences (5+ words) whose content words are less than 40% recalled anywhere in the output; "
      "'any deleted' is the share of items with at least one such sentence. The gates only check length and numbers/names, so a system could pass G2/G4 while dropping claims.")
    w("- **label stripped**: the draft had `Headline:`/`CTA:`-style labels and the output has none; **markdown added/stripped**: `**`, `#`, bullets appear/disappear.")
    w("- **artefacts**: a meta note in the output ('Note:', 'I've kept', 'let me know'...), a trailing list of numbers, a repeated sentence, or an echo of the draft.")
    w("")
    w("| System | n | copy bigram-F1 (mean) | near-copy | identical | deleted sentences (mean) | any deleted | label stripped | markdown added | markdown stripped | meta note | trailing numbers | repeated sentence |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in order:
        per = systems[k]["per"]
        out["systems"].setdefault(k, {})["gaming"] = {key: mean_of(per, key) for key in ("copy_bi_f1", "near_copy", "identical", "deleted_sent_rate", "any_sent_deleted", "label_stripped", "markdown_added", "markdown_stripped", "meta_note", "trailing_numbers", "repeated_sentence", "artefact_any")}
        w(f"| `{k}` | {len(per)} | {num(mean_of(per, 'copy_bi_f1'))} | {pct(mean_of(per, 'near_copy'))} | {pct(mean_of(per, 'identical'))} | "
          f"{pct(mean_of(per, 'deleted_sent_rate'), 1)} | {pct(mean_of(per, 'any_sent_deleted'))} | {pct(mean_of(per, 'label_stripped'))} | "
          f"{pct(mean_of(per, 'markdown_added'))} | {pct(mean_of(per, 'markdown_stripped'))} | {pct(mean_of(per, 'meta_note'))} | "
          f"{pct(mean_of(per, 'trailing_numbers'))} | {pct(mean_of(per, 'repeated_sentence'))} |")
    w("")
    w("### Loops used by the harness rows")
    w("")
    w("`loops_used` is the index of the candidate the harness kept (0 = the first draft already passed or was the best). 'First-draft pass' is the share of items whose very "
      "first draft passed all gates, which is what the same model scores without the loop; the gap to the final pass rate is what the loop added.")
    w("")
    w("| System | n | loops 0 / 1 / 2 / 3 | first-draft pass | final pass (official) | final pass (lenient) | rows revised that still fail |")
    w("|---|---|---|---|---|---|---|")
    for k in order:
        per = systems[k]["per"]
        if all(p["loops_used"] is None for p in per.values()):
            continue
        hist = collections.Counter(p["loops_used"] for p in per.values())
        first = statistics.fmean(int(p["loops_used"] == 0 and p["pass"]) for p in per.values())
        still = sum(1 for p in per.values() if (p["loops_used"] or 0) > 0 and not p["pass"])
        out["systems"].setdefault(k, {})["loops"] = {"hist": {str(i): hist.get(i, 0) for i in range(4)}, "first_draft_pass": first, "revised_still_fail": still}
        w(f"| `{k}` | {len(per)} | {hist.get(0, 0)} / {hist.get(1, 0)} / {hist.get(2, 0)} / {hist.get(3, 0)} | {pct(first)} | {pct(mean_of(per, 'pass'))} | {pct(mean_of(per, 'pass_lenient'))} | {still} |")
    w("")

    # ---- d) paired comparisons
    w("## D. Paired comparisons, harness vs frontier (paired bootstrap, 1000 resamples, seed 0)")
    w("")
    w(f"Each row is mean(`{primary}` - other) over the items both systems completed, with a 95% percentile interval and a two-sided bootstrap p. "
      "Positive = the harness is higher. For 'copy bigram-F1' and 'deleted sentences' lower is better, so a negative difference favours the harness.")
    w("")
    PAIR_KEYS = [("chrf_ref", "chrF vs human (held-out)", "higher"), ("wordf1_ref", "word-F1 vs human (held-out)", "higher"),
                 ("inband_holdout_share", "hold-out tells in band (share of 6)", "higher"), ("inband_holdout_all", "all 6 hold-out tells in band", "higher"),
                 ("pass", "official gate pass", "higher"), ("pass_lenient", "lenient gate pass", "higher"),
                 ("copy_bi_f1", "copy bigram-F1 vs draft", "lower"), ("deleted_sent_rate", "deleted sentences", "lower"),
                 ("any_sent_deleted", "any sentence deleted", "lower"), ("artefact_any", "artefact present", "lower")]
    w("| vs | signal | better is | n paired | diff | 95% CI | p | reads as |")
    w("|---|---|---|---|---|---|---|---|")
    others = frontier_labels + [k for k in order if k not in frontier_labels and k != primary and systems[k]["kind"] != "harness" and k.startswith("O")]
    for other in others:
        a, b = systems[primary]["per"], systems[other]["per"]
        out["paired"][other] = {}
        for key, name, better in PAIR_KEYS:
            ids = [i for i in items if i in a and i in b and a[i].get(key) is not None and b[i].get(key) is not None]
            res = paired_bootstrap([a[i][key] for i in ids], [b[i][key] for i in ids])
            if not res:
                continue
            out["paired"][other][key] = res
            good = (res["mean"] > 0) == (better == "higher")
            sig = res["lo"] > 0 or res["hi"] < 0
            verdict = ("harness better" if good else "harness worse") + (", significant" if sig else ", n.s.")
            if not sig and abs(res["mean"]) < 0.02:
                verdict = "tie"
            scale = 100 if key not in ("chrf_ref", "wordf1_ref", "copy_bi_f1") else 1
            unit = "pp" if scale == 100 else ""
            w(f"| `{other}` | {name} | {better} | {res['n']} | {scale * res['mean']:+.2f}{unit} | [{scale * res['lo']:+.2f}, {scale * res['hi']:+.2f}] | {res['p']:.3f} | {verdict} |")
    w("")

    # ---- verdicts
    w("## F. Verdict per signal")
    w("")
    verdicts = []
    s0 = out["systems"][primary]
    f2 = next((k for k in frontier_labels if k.startswith("F2")), frontier_labels[0] if frontier_labels else None)
    def vrow(signal, verdict, evidence):
        verdicts.append((signal, verdict, evidence)); w(f"| {signal} | **{verdict}** | {evidence} |")
    w("| Signal | Verdict | Evidence (this run) |")
    w("|---|---|---|")
    # gate fairness
    off, len_ = s0["forensics"]["official_pass"], s0["forensics"]["lenient_pass"]
    fr = {k: out["systems"][k]["forensics"] for k in frontier_labels}
    best_fr_len = max((v["lenient_pass"] for v in fr.values()), default=None)
    best_fr_off = max((v["official_pass"] for v in fr.values()), default=None)
    gap_off = None if best_fr_off is None else off - best_fr_off
    gap_len = None if best_fr_len is None else len_ - best_fr_len
    if gap_len is None:
        vrow("Gate fairness (E)", "n/a", "no frontier row present")
    elif gap_len > 0.05:
        vrow("Gate fairness (E)", "harness wins", f"official gap to the best frontier row {100 * gap_off:+.0f} pp; after forgiving regex artefacts (spelled-out numerals, demonyms, bullet capitals) the gap is still {100 * gap_len:+.0f} pp ({pct(len_)} vs {pct(best_fr_len)})")
    elif gap_len > 0:
        vrow("Gate fairness (E)", "partly gaming", f"official gap {100 * gap_off:+.0f} pp shrinks to {100 * gap_len:+.0f} pp once artefacts are forgiven: a good part of the headline gap is metric noise, not facts")
    else:
        vrow("Gate fairness (E)", "loses", f"with artefacts forgiven the best frontier row is at or above the harness ({pct(best_fr_len)} vs {pct(len_)})")
    def across(key, better, scale, unit):
        """Verdict for one paired signal across every frontier row: wins/loses/tie per row, then an overall call."""
        parts, calls = [], []
        for k in frontier_labels:
            r = out["paired"].get(k, {}).get(key)
            if not r:
                continue
            sig = r["lo"] > 0 or r["hi"] < 0
            good = (r["mean"] > 0) == (better == "higher")
            call = "tie" if not sig else ("better" if good else "worse")
            calls.append(call)
            parts.append(f"vs `{k}` {scale * r['mean']:+.2f}{unit} [{scale * r['lo']:+.2f}, {scale * r['hi']:+.2f}] ({call})")
        if not calls:
            return "n/a", "no frontier row"
        if all(c == "better" for c in calls):
            v = "harness wins"
        elif all(c == "worse" for c in calls):
            v = "loses"
        elif "worse" in calls:
            v = "mixed"
        else:
            v = "harness wins vs some, tie vs the rest" if "better" in calls else "tie"
        return v, "; ".join(parts)
    # a) reference similarity
    v, ev = across("chrf_ref", "higher", 1, " chrF")
    vrow("A. Closeness to the human original (chrF, held-out)", v, ev + f". Harness chrF-vs-draft {num(s0['ref']['chrf_vs_draft'])} (1.0 = pure copy). Caveat: chrF favours staying close to the draft wording, so the most conservative rewriter scores highest here")
    # b) tells
    v, ev = across("inband_holdout_share", "higher", 100, "pp")
    vrow("B. Hold-out tells not in the gates", v, f"harness mean in-band share {pct(s0['tells']['share'], 1)}; " + ev + f"; human originals {pct(out['calibration']['human']['share'], 1)}, AI drafts {pct(out['calibration']['draft']['share'], 1)}")
    # c) gaming
    g = s0["gaming"]
    fr_copy = {k: out["systems"][k]["gaming"]["near_copy"] for k in frontier_labels}
    base = next((k for k in order if k.startswith("O1")), None)
    base_copy = out["systems"][base]["gaming"]["near_copy"] if base else None
    worst_fr = max(fr_copy.values(), default=0)
    copy_v = ("harness wins" if g["near_copy"] <= worst_fr + 0.02 else
              "partly gaming" if g["near_copy"] <= 0.2 else "loses")
    vrow("C1. Copying the draft", copy_v, f"near-copies {pct(g['near_copy'])}, identical {pct(g['identical'])}, mean bigram-F1 vs draft {num(g['copy_bi_f1'])}; frontier rows: " + ", ".join(f"`{k}` near-copy {pct(fr_copy[k])}, mean {num(out['systems'][k]['gaming']['copy_bi_f1'])}" for k in frontier_labels) + (f"; same model without the loop (`{base}`) near-copy {pct(base_copy)}" if base else ""))
    v, ev = across("deleted_sent_rate", "lower", 100, "pp")
    vrow("C2. Dropping sentences (content loss the gates miss)", v, f"harness deleted-sentence rate {pct(g['deleted_sent_rate'], 1)}, any-deleted {pct(g['any_sent_deleted'])}; " + ev)
    art_v = "harness wins" if g["artefact_any"] <= 0.03 else "partly gaming" if g["artefact_any"] <= 0.1 else "loses"
    vrow("C3. Artefacts (meta notes, trailing numbers, repeats, echoes)", art_v, f"artefact share {pct(g['artefact_any'])} (meta note {pct(g['meta_note'])}, trailing numbers {pct(g['trailing_numbers'])}, repeated sentence {pct(g['repeated_sentence'])}, identical {pct(g['identical'])}); label stripped {pct(g['label_stripped'])}, markdown added {pct(g['markdown_added'])}")
    if "loops" in s0:
        lp = s0["loops"]
        vrow("C4. What the loop adds", "disclosed", f"first-draft pass {pct(lp['first_draft_pass'])} -> final {pct(s0['forensics']['official_pass'])}; loops 0/1/2/3 = {lp['hist']['0']}/{lp['hist']['1']}/{lp['hist']['2']}/{lp['hist']['3']}; {lp['revised_still_fail']} revised rows still fail")
    w("")
    w("How to read 'partly gaming': the harness does what it says (its outputs pass the gates honestly, with no copying or artefacts), but part of the "
      "headline margin over the frontier comes from the gates' regex checks penalising harmless edits the frontier makes. The fair number to quote is the lenient one.")
    w("")

    # ---- examples
    w("## G. The five most telling example pairs")
    w("")
    w(f"Chosen by rule, not by hand: items where a frontier row fails a *real* G1/G2 reason (not an artefact) and `{primary}` passes, ranked by severity "
      "(numbers, then names, then quotes, then content dropped); then one item where the harness still fails, and one with the harness's highest copy score (its weakest-looking rewrite).")
    w("")
    examples = []
    if f2:
        a, b = systems[primary], systems[f2]
        for i in items:
            if i not in a["per"] or i not in b["per"]:
                continue
            pa = a["per"][i]
            if not (pa["pass"] and pa["pass_lenient"]):
                continue
            whys, severity = [], 0
            for k in frontier_labels:
                pb = systems[k]["per"].get(i)
                if not pb:
                    continue
                d = pb["_detail"]
                bits = []
                if d["nums_added"]: bits.append(f"added number(s) {d['nums_added']}")
                if d["names_added_real"]: bits.append(f"added name(s) {d['names_added_real']}")
                if d["nums_dropped_real"]: bits.append(f"dropped number(s) {d['nums_dropped_real']}")
                if d["names_dropped_real"]: bits.append(f"dropped name(s) {d['names_dropped_real']}")
                if d["quotes_added"]: bits.append("changed the wording inside a quotation")
                if bits:
                    whys.append(f"`{k}` " + ", ".join(bits))
                    severity += 3 * bool(d["nums_added"] or d["nums_dropped_real"]) + 2 * bool(d["names_added_real"] or d["names_dropped_real"]) + bool(d["quotes_added"]) + pb["deleted_sent_rate"]
            if whys:
                examples.append((severity, i, "; ".join(whys) + f"; harness passed, deleted-sentence rate {pct(pa['deleted_sent_rate'])}"))
        examples.sort(key=lambda x: -x[0])
        picked = [(i, why) for _, i, why in examples[:3]]
        fails = [(a["per"][i]["deleted_sent_rate"], i) for i in a["per"] if not a["per"][i]["pass"] and i in b["per"]]
        if fails:
            fails.sort(key=lambda x: -x[0]); i = fails[0][1]
            d = a["per"][i]["_detail"]
            picked.append((i, f"harness FAILS here (gates: G1={a['per'][i]['G1']} G2={a['per'][i]['G2']} G3={a['per'][i]['G3']} G4={a['per'][i]['G4']}; detail {json.dumps({k: v for k, v in d.items() if v})}); frontier pass={b['per'][i]['pass']}"))
        copies = sorted(((a["per"][i]["copy_bi_f1"], i) for i in a["per"] if i in b["per"] and i not in {p[0] for p in picked}
                         and len(m.words(items[i]["ai_draft"])) >= 40), reverse=True)
        if copies:
            i = copies[0][1]
            picked.append((i, f"harness's highest copy score on a 40+ word draft (bigram-F1 vs draft {num(copies[0][0])}): its least-changed rewrite; frontier bigram-F1 {num(b['per'][i]['copy_bi_f1'])}"))
        strong = next((k for k in frontier_labels if "strong" in k), None)
        def snip(t, n=260):
            t = re.sub(r"\s+", " ", t.strip())
            return (t[:n] + "...") if len(t) > n else t
        for i, why in picked[:5]:
            w(f"### `{i}` ({split_of(i)})")
            w("")
            w(f"Why it is here: {why}.")
            w("")
            w(f"- **draft**: {snip(items[i]['ai_draft'])}")
            w(f"- **`{f2}`**: {snip(b['rows'][i]['output'])}")
            if strong and i in systems[strong]["rows"]:
                w(f"- **`{strong}`** (pass={systems[strong]['per'][i]['pass']}): {snip(systems[strong]['rows'][i]['output'])}")
            w(f"- **`{primary}`**: {snip(a['rows'][i]['output'])}")
            if items[i].get("human"):
                w(f"- **human original**: {snip(items[i]['human'])}")
            w("")
            out["examples"].append({"id": i, "why": why, "draft": items[i]["ai_draft"], "frontier": b["rows"][i]["output"],
                                    "claude_strong": systems[strong]["rows"][i]["output"] if strong and i in systems[strong]["rows"] else None,
                                    "harness": a["rows"][i]["output"], "human": items[i].get("human")})
        # frontier fact changes worth quoting on a slide: real invented numbers/names or real dropped numbers by any frontier row
        w("### Frontier rows: every real (non-artefact) number/name change, for the deck")
        w("")
        w("| system | id | what changed | harness pass |")
        w("|---|---|---|---|")
        for k in frontier_labels:
            for i, p in systems[k]["per"].items():
                d = p["_detail"]
                bits = []
                if d["nums_added"]: bits.append(f"added number(s) {d['nums_added']}")
                if d["names_added_real"]: bits.append(f"added name(s) {d['names_added_real']}")
                if d["nums_dropped_real"]: bits.append(f"dropped number(s) {d['nums_dropped_real']}")
                if bits:
                    out.setdefault("frontier_fact_changes", []).append({"system": k, "id": i, "what": "; ".join(bits)})
                    w(f"| `{k}` | `{i}` | {'; '.join(bits)} | {a['per'][i]['pass'] if i in a['per'] else 'n/a'} |")
        w("")
    else:
        w("_No frontier row found, no examples._")
        w("")

    # ---- caveats
    w("## H. Caveats the team should say out loud")
    w("")
    w("- G1/G2 are regex proxies, not fact checkers. Section E shows how many fails are artefacts; quote the lenient rate when a judge pushes.")
    w("- The human band's `para_opener_repeat` and `one_line_para_share` ranges are [0, 0], so marketing formats with `Headline:`/`CTA:` lines fail them by construction; "
      "that is why even the held-out human originals do not score 100% on the hold-out tells.")
    w("- chrF to the human original rewards staying close to the source wording; a pure copy of the draft scores the floor, a good rewrite can legitimately move away. Read A together with C1.")
    w("- The dev/trick drafts were written by Claude Opus 5.5; the Claude rows are rewriting their own family's text. The held-out split (real human originals, drafts by an open model) does not have that bias.")
    w("- Nothing here is a human preference judgement. The pairwise judge and the blind human test in `hackathon/report/` are the only humanness evidence.")
    w("")
    w(f"_Runtime {time.time() - t0:.1f}s. Raw numbers: `hackathon/audit/audit.json`._")

    # strip per-item detail from json systems dump (keep sizes sane) but keep examples
    json.dump(out, open(os.path.join(HERE, "audit.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(HERE, "AUDIT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(f"{s}: {v} :: {e}" for s, v, e in verdicts))
    print(f"wrote {rel(os.path.join(HERE, 'AUDIT.md'))} and audit.json in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
