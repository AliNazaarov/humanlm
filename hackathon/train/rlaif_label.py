"""RLAIF preference labels for DPO: GLM-5.3 judges cand1 vs cand2 on TRAINING prompts only (tr-*).

Both orders are asked; a pair is kept only if both orders pick the same rewrite and both candidates pass
the headline gates (hackathon/harness/gates.py). Ali's own labels (labels.jsonl) override the AI label for
their ids, and AI-vs-Ali agreement on the overlap is reported.
Judge: accounts/fireworks/models/glm-5p3 (reasoning low). Not the eval judge (Kimi K3).
  python3 hackathon/train/rlaif_label.py
"""
import concurrent.futures as cf, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HR = ROOT / "hackathon/train/human_rl"
sys.path.insert(0, str(ROOT / "hackathon/harness"))
import gates, harness  # noqa: E402

JUDGE = "accounts/fireworks/models/glm-5p3"
ASK = """You are a senior copywriter. Below is an AI-written DRAFT and two rewrites of it.
Which rewrite would a skilled copywriter actually send to a client, given that it must keep every fact,
number, name and claim of the draft and add nothing? Prefer the one that reads like a real person wrote it:
plain, specific, natural rhythm, no AI cliches.

DRAFT:
{draft}

REWRITE A:
{a}

REWRITE B:
{b}

Reply with exactly one letter, A or B, and nothing else."""


def ask(draft, a, b):
    dec = harness.decoding("fireworks", JUDGE, "low")
    text, _, _ = harness.chat("fireworks", JUDGE, "You judge copy. Answer A or B.",
                              [{"role": "user", "content": ASK.format(draft=draft, a=a, b=b)}], dec)
    t = harness.clean(text).strip().strip("*").strip()
    m = re.match(r"^(?:Rewrite\s+)?([AB])\b", t) or re.search(r"\b(?:Rewrite|Answer:?)\s*\**([AB])\b", t)
    if not m:
        last = re.findall(r"\b([AB])\b", t.splitlines()[-1]) if t else []
        return last[-1] if last else None
    return m.group(1)


def label(item):
    pid, draft, c1, c2 = item
    g1, g2 = gates.check(draft, c1), gates.check(draft, c2)
    if not (g1["pass"] and g2["pass"]):
        return {"id": pid, "kept": False, "why": "gate_fail", "g1": g1["pass"], "g2": g2["pass"]}
    first = ask(draft, c1, c2)          # A = cand1
    second = ask(draft, c2, c1)         # A = cand2
    w1 = {"A": "cand1", "B": "cand2"}.get(first)
    w2 = {"A": "cand2", "B": "cand1"}.get(second)
    agree = w1 is not None and w1 == w2
    row = {"id": pid, "judge": JUDGE, "agree": agree, "order1": w1, "order2": w2}
    if agree:
        row.update(kept=True, chosen=c1 if w1 == "cand1" else c2, rejected=c2 if w1 == "cand1" else c1, winner=w1)
    else:
        row.update(kept=False, why="orders_disagree")
    return row


def main():
    harness.load_env()
    prompts = {json.loads(l)["id"]: json.loads(l)["ai_draft"] for l in open(HR / "pref_prompts.jsonl")}
    c1 = {json.loads(l)["id"]: json.loads(l)["output"] for l in open(HR / "cand1.jsonl")}
    c2 = {json.loads(l)["id"]: json.loads(l)["output"] for l in open(HR / "cand2.jsonl")}
    items = [(i, prompts[i], c1[i], c2[i]) for i in sorted(prompts) if i.startswith("tr-") and i in c1 and i in c2]
    with cf.ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(label, items))
    ali = {}
    if (HR / "labels.jsonl").exists():
        for l in open(HR / "labels.jsonl"):
            r = json.loads(l)
            if r.get("chosen") and r.get("rejected"):
                ali[r["id"]] = r
    overlap = [r for r in rows if r["id"] in ali and r.get("kept")]
    agree_ali = sum(1 for r in overlap if r["chosen"].strip() == ali[r["id"]]["chosen"].strip()
                    or r["rejected"].strip() == ali[r["id"]]["rejected"].strip()) if overlap else 0
    out = []
    for r in rows:
        if r["id"] in ali:
            a = ali[r["id"]]
            out.append({"id": r["id"], "chosen": a["chosen"], "rejected": a["rejected"], "judge": "ali",
                        "agree": True, "edited": bool(a.get("edited"))})
        elif r.get("kept"):
            out.append({k: r[k] for k in ("id", "chosen", "rejected", "judge", "agree")})
    with open(HR / "ai_labels.jsonl", "w") as o:
        for r in out:
            o.write(json.dumps(r) + "\n")
    with open(HR / "ai_labels_audit.jsonl", "w") as o:
        for r in rows:
            o.write(json.dumps({k: v for k, v in r.items() if k not in ("chosen", "rejected")}) + "\n")
    why = {}
    for r in rows:
        why[r.get("why", "kept")] = why.get(r.get("why", "kept"), 0) + 1
    summary = {"candidates": len(items), "breakdown": why, "ai_kept": sum(r.get("kept", False) for r in rows),
               "ali_labels": len(ali), "ali_ai_overlap": len(overlap),
               "ali_ai_agreement": (agree_ali / len(overlap)) if overlap else None, "final_pairs": len(out)}
    json.dump(summary, open(HR / "ai_labels_summary.json", "w"), indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
