"""Held-out split + Fireworks SFT data. Built during the hackathon (2026-11-02).

Reads every pair in data/pairs/, applies the same filter as data/build_mix.py (dedup, gen_pairs.keep()
with the attribution check, news <= 25%), removes anything that overlaps the eval sets by 8+ consecutive
words, holds out 120 pairs by a stable hash of pid, and writes:
  evals/heldout_pairs.jsonl          120 pairs with real human references, never trained on
  hackathon/data/train.jsonl         Fireworks chat JSONL (system, user = AI draft, assistant = human)
  hackathon/data/valid.jsonl         200 rows, also never trained on
  hackathon/data/SPLIT.md            counts, source mix, rules
Usage: python3 hackathon/data/make_split.py [max_train_rows]
"""
import collections, glob, hashlib, json, os, random, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MAX_TRAIN = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
NEWS_CAP, N_HELDOUT, N_VALID, NGRAM = 0.25, 120, 200, 8
SYSTEM = ("Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, "
          "correct grammar. Keep every fact, name and number. Add nothing.")

src = open(os.path.join(ROOT, "pipeline/gen_pairs.py")).read()
argv, sys.argv = sys.argv, ["x", "/dev/null", "/dev/null"]
g = {}; exec(src[:src.index("done = set()")], g)
sys.argv = argv
keep = g["keep"]

def grams(text):
    w = re.findall(r"\w+", text.lower())
    return {" ".join(w[i:i + NGRAM]) for i in range(len(w) - NGRAM + 1)}

eval_grams = set()
for f in ["evals/dev_set.jsonl", "evals/trick_set.jsonl", "evals/baseline_frontier.jsonl"]:
    for l in open(os.path.join(ROOT, f)):
        d = json.loads(l)
        for k in ("ai_draft", "output", "draft", "reference"):
            if isinstance(d.get(k), str):
                eval_grams |= grams(d[k])

rows, seen, why = [], set(), collections.Counter()
for f in sorted(glob.glob(os.path.join(ROOT, "data/pairs/*.jsonl"))):
    if " 2." in f:
        continue
    for l in open(f):
        try:
            d = json.loads(l)
        except Exception:
            why["bad_json"] += 1; continue
        k = hashlib.md5(d["human"].encode()).hexdigest()
        if k in seen:
            why["duplicate"] += 1; continue
        seen.add(k)
        ok, r = keep(d["human"], d["ai_draft"])
        if not ok:
            why[r.split()[0]] += 1; continue
        if grams(d["ai_draft"]) & eval_grams or grams(d["human"]) & eval_grams:
            why["eval_overlap"] += 1; continue
        rows.append(d)

rows.sort(key=lambda d: hashlib.md5(d["pid"].encode()).hexdigest())
heldout, rest = rows[:N_HELDOUT], rows[N_HELDOUT:]
valid, pool = rest[:N_VALID], rest[N_VALID:]
news = [r for r in pool if r["source"].startswith("news")]
other = [r for r in pool if not r["source"].startswith("news")]
news = news[:int(len(other) * NEWS_CAP / (1 - NEWS_CAP))]
train = other + news
random.seed(0); random.shuffle(train)
train = train[:MAX_TRAIN]

def chat(d):
    return {"messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": d["ai_draft"]},
                         {"role": "assistant", "content": d["human"]}]}

with open(os.path.join(ROOT, "evals/heldout_pairs.jsonl"), "w") as o:
    for i, d in enumerate(heldout, 1):
        o.write(json.dumps({"id": f"ho-{i:03d}", "pid": d["pid"], "ai_draft": d["ai_draft"], "human": d["human"],
                            "source": d["source"], "licence": d.get("licence"), "url": d.get("url")}) + "\n")
for name, part in (("train", train), ("valid", valid)):
    with open(os.path.join(ROOT, f"hackathon/data/{name}.jsonl"), "w") as o:
        for d in part:
            o.write(json.dumps(chat(d)) + "\n")

held_pids = {d["pid"] for d in heldout} | {d["pid"] for d in valid}
assert not held_pids & {d["pid"] for d in train}, "held-out pid leaked into train"
left = sum(1 for d in train + valid if (grams(d["ai_draft"]) | grams(d["human"])) & eval_grams)
assert left == 0, f"{left} train/valid rows still overlap the eval sets"

mix = collections.Counter(d["source"] for d in train)
lines = ["# Split (built 2026-11-02 during the hackathon)", "",
         f"- Raw pairs read: {sum(why.values()) + len(rows)}; kept after filters: {len(rows)}",
         f"- Dropped: {dict(why)}",
         f"- Eval-overlap rule: drop a pair if its AI draft or human text shares {NGRAM}+ consecutive words with dev/trick/frontier eval files",
         f"- Held out: {len(heldout)} (`evals/heldout_pairs.jsonl`), the first {N_HELDOUT} pairs by md5(pid)",
         f"- Valid: {len(valid)}; Train: {len(train)} (news capped at {NEWS_CAP:.0%}, max {MAX_TRAIN})",
         "- Train source mix: " + ", ".join(f"{k} {v} ({v/len(train):.0%})" for k, v in mix.most_common()),
         f"- Remaining eval overlap in train/valid: {left}",
         "- Licence: Common Pile filtered subsets (openly licensed / public domain). No frontier-model text in training.",
         f"- System prompt (same as pipeline/infer.py and every eval run): {SYSTEM}"]
open(os.path.join(ROOT, "hackathon/data/SPLIT.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
