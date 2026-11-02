"""Do the LLM judges' style verdicts agree with human readers? Item-level check on the blind A/B pairs.
Usage: judge_human_agreement.py  -> hackathon/report/judge_human_agreement.json (score_all shows it)

Human side: hackathon/report/human_ab.jsonl rows for a pairs version, majority per item (ties skipped).
Judge side: the committed pairwise judge files for the same two systems; the style sub-verdict, both orders,
a side counts only when both orders agree (else tie, skipped). Small n: read as a calibration warning, not a rate.
"""
from __future__ import annotations

import collections, json, os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
SETS = [{"version": "fd809333d5320427", "ours": "O3c_glm_prompt_harness_style",
         "judges": {"kimi-k3": "judge", "qwen3p8-max": "judge2qwen"}}]


def human_majority(version: str, ours: str) -> dict[str, str]:
    votes = collections.defaultdict(lambda: [0, 0])
    for line in open(os.path.join(ROOT, "hackathon/report/human_ab.jsonl"), encoding="utf-8"):
        r = json.loads(line) if line.strip() else {}
        if r.get("version") == version and r.get("winner"):
            votes[r["id"]][0 if ours in r["winner"] else 1] += 1
    return {i: ("ours" if o > c else "ref") for i, (o, c) in votes.items() if o != c}


def judge_style(path: str) -> dict[str, str]:
    by = collections.defaultdict(dict)
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("verdict") is not None:
            by[d["id"]][d["order"]] = d.get("style") or d["verdict"]
    out = {}
    for i, o in by.items():
        ab = {"1": "ours", "2": "ref"}.get(o.get("AB"))
        ba = {"2": "ours", "1": "ref"}.get(o.get("BA"))
        if ab and ab == ba:
            out[i] = ab
    return out


def main() -> int:
    res = {"sets": []}
    for s in SETS:
        hum = human_majority(s["version"], s["ours"])
        entry = {"version": s["version"], "ours": s["ours"], "human_decided_items": len(hum), "judges": {}}
        for model, prefix in s["judges"].items():
            p = os.path.join(ROOT, f"hackathon/report/{prefix}_hack_{s['ours']}_vs_hack_strong_claude-opus-5-5.jsonl")
            if not os.path.exists(p):
                continue
            j = judge_style(p)
            both = [i for i in hum if i in j]
            agree = sum(j[i] == hum[i] for i in both)
            entry["judges"][model] = {"agree": agree, "disagree": len(both) - agree, "n_compared": len(both)}
        res["sets"].append(entry)
    with open(os.path.join(ROOT, "hackathon/report/judge_human_agreement.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res["sets"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
