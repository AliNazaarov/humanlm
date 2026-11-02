"""Row checks for O3c / O3m / O3n vs Claude strong (verify pass 2 fails: gate floor, F10 frame loss).

Reads only committed run files and the eval inputs; writes hackathon/runs/dev/row_checks.json.
Run from the repo root:  python3 hackathon/runs/dev/row_checks.py
Numbers in hackathon/runs/dev/README.md ("Pass 3" section) come from the JSON this writes.
"""
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "evals" / "runs"
OUT = Path(__file__).with_name("row_checks.json")

SYSTEMS = {
    "O3c_glm_prompt_harness_style": "hack_O3c_glm_prompt_harness_style",
    "O3m_glm_plainclaim": "hack_O3m_glm_plainclaim",
    "O3n_glm_frame": "hack_O3n_glm_frame",
    "frontier-strong:claude-opus-5-5": "hack_strong_claude-opus-5-5",
}
SPLITS = {"eval_all": "", "heldout": "_heldout", "real": "_real"}
GATE_FLOOR = 0.95

# Two hashtag definitions, so the count does not hinge on one regex:
#   loose  = any '#' followed by word chars (also matches '#1')   -> the verify pass 2 count
#   strict = '#' + letter, not preceded by a word char or '&'      -> real hashtags only
HASHTAG = {
    "loose": re.compile(r"#\w+"),
    "strict": re.compile(r"(?<![\w&])#[A-Za-z]\w*"),
}
SUBJECT = re.compile(r"^\s*Subject:", re.M)


def load(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


def main():
    evals = load(ROOT / "evals" / "eval_all.jsonl")
    out = {"gate_floor": GATE_FLOOR, "gates": {}, "frame_loss_eval_all": {}}
    for label, stem in SYSTEMS.items():
        g = {}
        for split, suf in SPLITS.items():
            p = RUNS / f"{stem}{suf}.jsonl"
            if not p.exists():
                continue
            rows = load(p)
            if not all("gates" in r for r in rows.values()):
                continue  # frontier runs are gated by score_all, not in-row
            n_pass = sum(1 for r in rows.values() if r["gates"]["pass"])
            g[split] = {
                "pass": n_pass,
                "n": len(rows),
                "rate": round(n_pass / len(rows), 4),
                "meets_floor": n_pass / len(rows) >= GATE_FLOOR,
                "fail_ids": sorted(i for i, r in rows.items() if not r["gates"]["pass"]),
                "file": str(p.relative_to(ROOT)),
            }
        if g:
            out["gates"][label] = g

        rows = load(RUNS / f"{stem}.jsonl")
        fl = {"file": f"evals/runs/{stem}.jsonl"}
        for name, rx in HASHTAG.items():
            have = [i for i, e in evals.items() if rx.search(e["ai_draft"])]
            dropped = [i for i in have if not rx.search(rows[i]["output"])]
            fl[f"hashtag_{name}"] = {"drafts_with": len(have), "output_drops_all": len(dropped), "ids": dropped}
        have = [i for i, e in evals.items() if SUBJECT.search(e["ai_draft"])]
        dropped = [i for i in have if not SUBJECT.search(rows[i]["output"])]
        fl["subject_line"] = {"drafts_with": len(have), "output_drops": len(dropped), "ids": dropped}
        ratios = [len(rows[i]["output"].split()) / max(1, len(e["ai_draft"].split())) for i, e in evals.items()]
        fl["median_output_to_draft_word_ratio"] = round(statistics.median(ratios), 3)
        out["frame_loss_eval_all"][label] = fl

    # Verify pass 3, ruling 2: are the eval-judge facts losses the hashtag-drop items?
    # Uses only the per-item FACTS field of the committed judge files (no reason text, no score fed back).
    out["facts_loss_vs_hashtag_drop"] = facts_loss_check(out["frame_loss_eval_all"])

    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for label, g in out["gates"].items():
        print(label, {s: f"{v['pass']}/{v['n']}{'' if v['meets_floor'] else ' BELOW FLOOR'}" for s, v in g.items()})
    for label, fl in out["frame_loss_eval_all"].items():
        print(label, "hashtags loose", fl["hashtag_loose"]["output_drops_all"], "/", fl["hashtag_loose"]["drafts_with"],
              "strict", fl["hashtag_strict"]["output_drops_all"], "/", fl["hashtag_strict"]["drafts_with"],
              "subject", fl["subject_line"]["output_drops"], "/", fl["subject_line"]["drafts_with"],
              "ratio", fl["median_output_to_draft_word_ratio"])
    for key, v in out["facts_loss_vs_hashtag_drop"].items():
        print(key, "facts", f"{v['facts']['win']}/{v['facts']['loss']}/{v['facts']['tie']}",
              "matches summary" if v["matches_summary"] else "MISMATCH",
              "losses on hashtag-drop items", f"{v['losses_on_hashtag_drop_items']}/{v['facts']['loss']}")


JUDGE_FILES = {"kimi_k3": "judge_hack_{}_vs_hack_strong_claude-opus-5-5",
               "qwen_3p8_max": "judge2qwen_hack_{}_vs_hack_strong_claude-opus-5-5"}


def facts_loss_check(frame_loss):
    """Per committed eval-judge file (A = our system, B = Claude strong): facts W/L/T recomputed with the judge's
    own aggregate rule (hackathon/eval/judge.py), and how many facts losses are items where our output drops
    every hashtag (loose definition, the verify pass 2 count). Reads FACTS verdicts only, never REASON text."""
    import sys
    sys.path.insert(0, str(ROOT))
    from hackathon.eval.judge import aggregate

    report = ROOT / "hackathon" / "report"
    res = {}
    for label in ("O3c_glm_prompt_harness_style", "O3m_glm_plainclaim"):
        drop = set(frame_loss[label]["hashtag_loose"]["ids"])
        for judge, pat in JUDGE_FILES.items():
            stem = pat.format(label)
            per_item, summary = report / f"{stem}.jsonl", report / f"{stem}.summary.json"
            if not per_item.exists():
                continue
            rows = [json.loads(l) for l in per_item.read_text(encoding="utf-8").splitlines() if l.strip()]
            per_id, block = aggregate(rows, "facts")
            loss_ids = sorted(i for i, p in per_id.items() if p["final"] == "B")
            summ = json.loads(summary.read_text(encoding="utf-8"))
            sf = summ.get("facts") or summ.get("summary", {}).get("facts") or {}
            res[f"{label}|{judge}"] = {
                "file": str(per_item.relative_to(ROOT)),
                "facts": {k: block[k] for k in ("win", "loss", "tie", "n")},
                "summary_facts": {k: sf.get(k) for k in ("win", "loss", "tie")},
                "matches_summary": all(sf.get(k) == block[k] for k in ("win", "loss", "tie")),
                "facts_loss_ids": loss_ids,
                "hashtag_drop_items": len(drop),
                "losses_on_hashtag_drop_items": len(drop & set(loss_ids)),
                "loss_ids_on_hashtag_drop_items": sorted(drop & set(loss_ids)),
            }
    return res


if __name__ == "__main__":
    main()
