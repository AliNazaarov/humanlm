r"""Held-out ids that share 8+ consecutive words with the SFT train/valid data (evals/README rule, \w+ tokens).
Usage: heldout_overlap.py  -> hackathon/report/heldout_train_overlap.json
make_split.py keeps held-out and train apart by pid and exact text hash only, so near-duplicates (template text,
licence footers, reused sentences, generator wrappers) can appear in both. score_all reports a "heldout_clean"
block without these ids, which matters for any model trained on train.jsonl (the SFT rows).
"""
from __future__ import annotations

import json, os, re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
N = 8


def grams(text: str) -> set[tuple]:
    w = re.findall(r"\w+", text.lower())
    return {tuple(w[i:i + N]) for i in range(len(w) - N + 1)}


def main() -> int:
    train = set()
    for f in ("hackathon/data/train.jsonl", "hackathon/data/valid.jsonl"):
        for line in open(os.path.join(ROOT, f), encoding="utf-8"):
            for msg in json.loads(line)["messages"][1:]:
                train |= grams(msg["content"])
    rows = []
    for line in open(os.path.join(ROOT, "evals/heldout_pairs.jsonl"), encoding="utf-8"):
        d = json.loads(line)
        hg, ag = grams(d["human"]), grams(d["ai_draft"])
        h, a = len(hg & train), len(ag & train)
        if h or a:
            rows.append({"id": d["id"], "human_shared": h, "human_total": len(hg), "draft_shared": a, "draft_total": len(ag)})
    out = {"rule": f"{N}+ consecutive \\w+ tokens shared with hackathon/data/train.jsonl or valid.jsonl",
           "n_heldout_overlapping": len(rows), "ids": [r["id"] for r in rows], "rows": rows}
    path = os.path.join(ROOT, "hackathon/report/heldout_train_overlap.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(f"{len(rows)} held-out ids overlap train/valid -> hackathon/report/heldout_train_overlap.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
