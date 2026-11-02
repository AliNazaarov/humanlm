"""Probe (evidence for the name-proxy fix): how much does the name proxy move the headline? Patched _names treats each line start and the word
after ':' as sentence-initial, and skips Title Case lines (>= 60% capitalised words, e.g. headlines)."""
import json, re, sys
Usage: python hackathon/eval/names_probe.py <repo root> RUN.jsonl [RUN.jsonl ...]
ROOT = sys.argv[1]
sys.path[:0] = [ROOT + "/pipeline", ROOT + "/hackathon/harness", ROOT + "/hackathon/eval"]
import metrics as m, gates as gt, score_all as sa
orig = m._names

def fixed(text):
    out = set()
    for line in text.splitlines():
        ws = m.words(line)
        caps = [w for w in ws if w[:1].isupper()]
        if len(ws) >= 3 and len(caps) / len(ws) >= 0.6:
            continue  # Title Case line (headline): capitalisation says nothing about names
        for seg in re.split(r":\s*", line):
            for s in m.sentences(seg):
                for w in m.words(s)[1:]:
                    w = re.sub(r"'s$", "", w)
                    if w[0].isupper() and w.lower() not in m.PRONOUN_I:
                        out.add(w.lower())
    return out

items = sa.all_items()
for run in sys.argv[2:]:
    rows = [r for r in sa.read_jsonl(run) if r["id"] in items]
    res = {}
    for name, fn in (("current", orig), ("fixed", fixed)):
        m._names = fn
        g = [gt.check(items[r["id"]]["ai_draft"], r["output"]) for r in rows]
        res[name] = {k: sum(x[k] for x in g) for k in ("g1_nothing_invented", "g2_nothing_lost", "pass")}
    m._names = orig
    print(sa.rel(run), len(rows), res)
