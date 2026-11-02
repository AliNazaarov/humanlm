"""Build local DPO pairs: chosen = real human original, rejected = our model's rewrite (O7 rows).
Drops empty rejected outputs and any pair sharing an 8-gram with an eval item (eval_all, heldout_pairs, real_readmes).
  python3 hackathon/train/mlx_local/make_dpo_pairs.py OUT_DIR [--max 150]
Writes OUT_DIR/train.jsonl + valid.jsonl ({"prompt","chosen","rejected","system"}) and prints counts as JSON.
"""
import json, os, re, sys, random

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SYSTEM = ("Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, "
          "correct grammar. Keep every fact, name and number. Add nothing.")
SRC = [("hackathon/train/ruslan/o7_drafts_ali.jsonl", "hackathon/train/ruslan/o7_rejected_ali.jsonl"),
       ("hackathon/train/ruslan/o7_drafts_ali2.jsonl", "hackathon/train/ruslan/o7_rejected_ali2.jsonl")]
EVALS = ["evals/eval_all.jsonl", "evals/heldout_pairs.jsonl", "evals/real_readmes.jsonl"]


def words(t):
    return re.findall(r"[a-z0-9']+", t.lower())


def grams(t, n=8):
    w = words(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def main():
    out_dir = sys.argv[1]
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 150
    eval_grams = set()
    for f in EVALS:
        for l in open(os.path.join(ROOT, f)):
            r = json.loads(l)
            for k in ("ai_draft", "human", "output"):
                if r.get(k):
                    eval_grams |= grams(r[k])
    pairs, n_empty, n_overlap, n_missing = [], 0, 0, 0
    for df, rf in SRC:
        drafts = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, df))}
        rej = {}
        for l in open(os.path.join(ROOT, rf)):
            r = json.loads(l); rej[r["id"]] = r.get("output") or ""
        for i, d in drafts.items():
            if i not in rej:
                n_missing += 1; continue
            if not rej[i].strip():
                n_empty += 1; continue
            if any(grams(t) & eval_grams for t in (d["ai_draft"], d["human"], rej[i])):
                n_overlap += 1; continue
            pairs.append({"id": i, "system": SYSTEM, "prompt": d["ai_draft"], "chosen": d["human"], "rejected": rej[i]})
    # Highest choppy-tell gap first: share of short sentences (<= 6 words) in the rejected rewrite minus the human original.
    def choppy(t):
        sents = [x for x in re.split(r"(?<=[.?!])\s+|\n+", t) if x.strip()]
        return sum(len(words(x)) <= 6 for x in sents) / max(len(sents), 1)
    for p in pairs:
        p["choppy_gap"] = round(choppy(p["rejected"]) - choppy(p["chosen"]), 4)
    pairs.sort(key=lambda p: -p["choppy_gap"])
    pairs = pairs[:mx]
    random.Random(0).shuffle(pairs)
    os.makedirs(out_dir, exist_ok=True)
    n_val = max(4, len(pairs) // 20)
    with open(os.path.join(out_dir, "valid.jsonl"), "w") as f:
        for p in pairs[:n_val]:
            f.write(json.dumps(p) + "\n")
    with open(os.path.join(out_dir, "train.jsonl"), "w") as f:
        for p in pairs[n_val:]:
            f.write(json.dumps(p) + "\n")
    print(json.dumps({"train": len(pairs) - n_val, "valid": n_val, "dropped_empty": n_empty,
                      "dropped_eval_8gram_overlap": n_overlap, "no_rejected_yet": n_missing}))


if __name__ == "__main__":
    main()
