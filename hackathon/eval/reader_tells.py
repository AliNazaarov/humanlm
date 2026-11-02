"""Reader tells: the patterns people in the blind A/B test named when they picked the other rewrite.
Usage: reader_tells.py [--out hackathon/report/reader_tells.json] [--block eval|heldout|real]
Post-hoc and diagnostic, built from set 1 reader notes (hackathon/report/human_ab.jsonl). It never feeds the headline
gates (pipeline/metrics.py stays frozen) and it scores every system's run the same way.
  fragment_run   3+ sentences in a row of at most 5 words each ("9 years. 360 weddings. Countless Mondays.")
  echo           a sentence of at most 3 words that only repeats the one before ("...in 6 minutes. Six minutes.")
  hook           growth-post openers: "here's what", "secret weapon", "game-changer", "smart move", ...
  rhetorical_qa  a question of at most 5 words answered by the writer ("Our secret weapon? The App Store.")
  slogan         three short sentences on one opening word, or "less X. more Y." / "no X. just Y." pairs
  tagline        "everything you need, nothing you don't" and the same shape
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNS = os.path.join(ROOT, "evals", "runs")
OUT = os.path.join(ROOT, "hackathon", "report", "reader_tells.json")
KINDS = ("fragment_run", "echo", "hook", "rhetorical_qa", "slogan", "tagline")

WORD = re.compile(r"[A-Za-z0-9$%]+(?:'[A-Za-z]+)*")
SENT = re.compile(r"[^.!?\n]+[.!?]+[\"'”)]*")
LIST = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")
NUM_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}
HOOKS = re.compile(r"\b(?:here'?s (?:what|the thing|why|how)|but here'?s|secret weapon|game[- ]changer|"
                   r"smart move|let that sink in|well\. here we are|the best part\??|think what you'?d|"
                   r"spoiler|plot twist|the result\?|the catch\?|guess what)\b", re.I)
TAGLINE = re.compile(r"\b(?:everything|all) you need,? (?:and )?nothing you don'?t\b|"
                     r"\b(?:less|fewer) \w+(?: \w+)?[.,] (?:more|and more) \w+", re.I)
PAIR = re.compile(r"^(?:no|less|fewer)\b", re.I), re.compile(r"^(?:just|more|only)\b", re.I)


def _norm(t: str) -> str:
    return (t or "").replace("’", "'").replace("‘", "'")


def _words(s: str) -> list[str]:
    return [NUM_WORDS.get(w.lower(), w.lower()) for w in WORD.findall(s)]


def paragraphs(text: str) -> list[list[str]]:
    """Sentences per line; list lines and lines with no closing punctuation (a heading) are left out."""
    lines = [l for l in _norm(text).split("\n") if l.strip() and not LIST.match(l)]
    return [[s.strip() for s in SENT.findall(line)] for line in lines]


def tells(text: str) -> dict[str, int]:
    out = dict.fromkeys(KINDS, 0)
    flat = [s for p in paragraphs(text) for s in p if _words(s)]
    lens = [len(_words(s)) for s in flat]
    run = 0
    for n in lens + [99]:
        if n <= 5:
            run += 1
            continue
        out["fragment_run"] += run >= 3
        run = 0
    for prev, s in zip(flat, flat[1:]):
        w = _words(s)
        if 0 < len(w) <= 3 and not s.endswith("?") and set(w) <= set(_words(prev)):
            out["echo"] += 1
    for para in paragraphs(text):
        for q, nxt in zip(para, para[1:]):
            if q.rstrip("\"'”)").endswith("?") and len(_words(q)) <= 5 and not q.startswith(("\"", "“")):
                out["rhetorical_qa"] += 1
    for a, b, c in zip(flat, flat[1:], flat[2:]):
        ws = [_words(x) for x in (a, b, c)]
        if all(1 < len(w) <= 5 for w in ws) and ws[0][0] == ws[1][0] == ws[2][0]:
            out["slogan"] += 1
    for a, b in zip(flat, flat[1:]):
        if len(_words(a)) <= 6 and len(_words(b)) <= 8 and PAIR[0].match(a) and PAIR[1].match(b):
            out["slogan"] += 1
    t = _norm(text)
    out["hook"] = len(HOOKS.findall(t))
    out["tagline"] = len(TAGLINE.findall(t))
    return out


def score_run(path: str) -> dict:
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    per = [tells(r.get("output") or "") for r in rows]
    n = len(per)
    any_hit = sum(any(p.values()) for p in per)
    return {"n": n, "any_share": any_hit / n if n else 0.0,
            "per_100_outputs": {k: 100.0 * sum(p[k] for p in per) / n if n else 0.0 for k in KINDS},
            "ids_with_tells": sorted(r["id"] for r, p in zip(rows, per) if any(p.values()))}


def runs_for(block: str) -> dict[str, str]:
    """hack_<system>.jsonl is the 130-item eval run; _heldout / _real are the other blocks."""
    out = {}
    for p in sorted(glob.glob(os.path.join(RUNS, "hack_*.jsonl"))):
        if ".jsonl." in os.path.basename(p):  # side files such as *.jsonl.failures.jsonl
            continue
        name = os.path.basename(p)[5:-6]
        tail = next((t for t in ("_heldout", "_real") if name.endswith(t)), "")
        if (block == "eval" and not tail) or (tail == "_" + block):
            out[name[: len(name) - len(tail)] if tail else name] = p
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--block", action="append", choices=("eval", "heldout", "real"))
    a = ap.parse_args(argv)
    blocks = a.block or ["eval", "heldout"]
    res = {"note": "post-hoc diagnostic from set 1 reader notes; not a headline gate", "kinds": list(KINDS),
           "blocks": {b: {s: score_run(p) for s, p in runs_for(b).items()} for b in blocks}}
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    for b in blocks:
        print(f"== {b}")
        for s, r in sorted(res["blocks"][b].items(), key=lambda kv: kv[1]["any_share"]):
            k = " ".join(f"{x[:4]}={r['per_100_outputs'][x]:.0f}" for x in KINDS)
            print(f"{r['any_share']:6.1%}  n={r['n']:<4} {s:<45} {k}")
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
