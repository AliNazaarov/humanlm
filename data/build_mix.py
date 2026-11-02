"""Re-filter all pairs with the current gen_pairs.keep(), dedup, cap news share. Usage: build_mix.py OUT [news_cap]"""
import sys, json, glob, hashlib, collections, random, os
here = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]; CAP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
src = open(os.path.join(here, "../pipeline/gen_pairs.py")).read()
sys.argv = ["x", "/dev/null", "/dev/null"]
g = {}; exec(src[:src.index("done = set()")], g)
rows, seen, why = [], set(), collections.Counter()
for f in sorted(glob.glob(os.path.join(here, "pairs/*.jsonl"))):
    for l in open(f):
        try: d = json.loads(l)
        except Exception: continue
        k = hashlib.md5(d["human"].encode()).hexdigest()
        if k in seen: continue
        seen.add(k)
        ok, r = g["keep"](d["human"], d["ai_draft"])
        why[r] += 1
        if ok: rows.append(d)
random.seed(0); random.shuffle(rows)
news = [r for r in rows if r["source"].startswith("news")]; rest = [r for r in rows if not r["source"].startswith("news")]
news = news[:int(len(rest) * CAP / (1 - CAP))]
mix = rest + news; random.shuffle(mix)
with open(OUT, "w") as o:
    for r in mix: o.write(json.dumps(r) + "\n")
c = collections.Counter(r["source"] for r in mix)
print("filter:", dict(why)); print("mix:", len(mix), {k: f"{v} ({v/len(mix):.0%})" for k, v in c.most_common()})
