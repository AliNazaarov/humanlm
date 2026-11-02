"""E1: per-item pick across committed FeatherLM runs (routing across open-model systems).

For each eval item: take every candidate output from the listed runs, keep those that pass all four gates AND an
open-model claim check (GLM-5.3: nothing added that isn't in the draft), then pick the one the selection judge
(GLM-5.3 absolute 1-10 "sounds like a skilled human copywriter"; the same scorer as O3j) rates highest.
Ties go to the incumbent order (O3c first). No eligible candidate -> O3c's output.
The eval judges (Kimi K3, Qwen 3.8 Max) are never used here.

  python3 hackathon/harness/ensemble.py EVAL.jsonl OUT.jsonl RUN1.jsonl RUN2.jsonl ... [--name E1_ensemble]
Cost per row = sum of the candidate rows' cost_usd + claim-check and judge calls (priced from --in/--out prices).
"""
import argparse, concurrent.futures as cf, json, os, subprocess, sys, time, types

sys.path.insert(0, os.path.dirname(__file__))
import harness as H  # noqa: E402

J = "accounts/fireworks/models/glm-5p3"


def main():
    H.load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("eval"); ap.add_argument("out"); ap.add_argument("runs", nargs="+")
    ap.add_argument("--name", default="E1_ensemble")
    ap.add_argument("--in-price", type=float, default=0.0); ap.add_argument("--out-price", type=float, default=0.0)
    ap.add_argument("--concurrency", type=int, default=12)
    a = ap.parse_args()
    cfg = types.SimpleNamespace(claim_check=J, select_judge_model=J)
    items = {json.loads(l)["id"]: json.loads(l) for l in open(a.eval)}
    runs = []
    for p in a.runs:
        rows = {json.loads(l)["id"]: json.loads(l) for l in open(p)}
        runs.append((os.path.basename(p).replace("hack_", "").replace(".jsonl", ""), rows))

    def pick(iid):
        draft = items[iid]["ai_draft"]; t0 = time.time(); pt = ct = 0; cands = []
        for name, rows in runs:
            r = rows.get(iid)
            if not r or not r.get("output"):
                continue
            g = H.gates.check(draft, r["output"])
            c = {"run": name, "out": r["output"], "gates": g, "src_cost": r.get("cost_usd", 0) or 0}
            if g["pass"]:
                added, p, q = H.claim_check(draft, r["output"], cfg); pt += p; ct += q
                c["added"] = added
                if not added:
                    c["score"], p, q = H.judge_score(r["output"], cfg); pt += p; ct += q
            cands.append(c)
        ok = [c for c in cands if "score" in c]
        best = max(ok, key=lambda c: ((c["score"] or 0), -ok.index(c))) if ok else next((c for c in cands if c["run"].startswith("O3c")), cands[0])
        g = {k: v for k, v in best["gates"].items() if k != "problems"}
        return {"id": iid, "system": a.name, "output": best["out"], "latency_ms": round((time.time() - t0) * 1000),
                "prompt_tokens": pt, "completion_tokens": ct,
                "cost_usd": round(sum(c["src_cost"] for c in cands) + pt * a.in_price / 1e6 + ct * a.out_price / 1e6, 6),
                "model": "ensemble:" + ",".join(n for n, _ in runs), "decoding": {"selector": J, "rule": "gates + claim check, max 1-10 score"},
                "loops_used": 0, "gates": g,
                "selection": {"picked_run": best["run"], "eligible": len(ok), "candidates": len(cands),
                              "scores": {c["run"]: c.get("score") for c in cands}, "flagged_added": {c["run"]: c["added"] for c in cands if c.get("added")}}}

    done = {json.loads(l)["id"] for l in open(a.out)} if os.path.exists(a.out) else set()
    with open(a.out, "a") as o, cf.ThreadPoolExecutor(a.concurrency) as ex:
        for f in cf.as_completed([ex.submit(pick, i) for i in items if i not in done]):
            try:
                r = f.result()
            except Exception as e:
                print("ITEM_FAILED", e, flush=True); continue
            o.write(json.dumps(r) + "\n"); o.flush()
            print(r["id"], r["selection"]["picked_run"], r["gates"]["pass"], flush=True)
    rows = [json.loads(l) for l in open(a.out)]
    picked = {}
    for r in rows:
        picked[r["selection"]["picked_run"]] = picked.get(r["selection"]["picked_run"], 0) + 1
    base = os.path.basename(a.eval); suffix = "_heldout" if "heldout" in base else "_real" if "real" in base else ""
    commit = subprocess.run(["git", "-C", H.ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = {"system": a.name, "provider": "ensemble", "model": J, "runs": a.runs, "eval": a.eval, "rows": len(rows),
           "pass_rate": sum(r["gates"]["pass"] for r in rows) / max(len(rows), 1), "picked": picked, "commit": commit,
           "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    json.dump(man, open(os.path.join(H.ROOT, f"hackathon/runs/{a.name}{suffix}.json"), "w"), indent=1)
    print("DONE", json.dumps(man))


if __name__ == "__main__":
    main()
