"""Pairs for the blind human A/B test. Usage: make_ab_pairs.py RUN_X.jsonl RUN_Y.jsonl [OUT] [--n 20] [--seed 0]
Picks n eval ids at random (seeded), keeps dev and trick items in proportion, and shuffles which system
shows as A per pair. Writes {meta, pairs[{pid, id, draft, a, b, a_system, b_system}]}; the page hides *_system.
"""
import argparse, json, os, random

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path, encoding="utf-8"))}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("x"); p.add_argument("y")
    p.add_argument("out", nargs="?", default=os.path.join(root, "hackathon/demo/ab_pairs.json"))
    p.add_argument("--n", type=int, default=20); p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    ev, x, y = load(os.path.join(root, "evals/eval_all.jsonl")), load(a.x), load(a.y)
    ids = sorted(set(ev) & set(x) & set(y))
    rng = random.Random(a.seed)
    trick = [i for i in ids if i.startswith("trick")]; dev = [i for i in ids if not i.startswith("trick")]
    k_trick = round(a.n * len(trick) / len(ids))
    chosen = rng.sample(dev, a.n - k_trick) + rng.sample(trick, k_trick)
    rng.shuffle(chosen)
    pairs = []
    for n, i in enumerate(chosen, 1):
        sides = [x[i], y[i]]; rng.shuffle(sides)
        pairs.append({"pid": n, "id": i, "draft": ev[i]["ai_draft"], "a": sides[0]["output"], "b": sides[1]["output"],
                      "a_system": sides[0]["system"], "b_system": sides[1]["system"]})
    rel = lambda q: os.path.relpath(q, root).replace(os.sep, "/")
    meta = {"x": rel(a.x), "y": rel(a.y), "seed": a.seed, "n": len(pairs)}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"meta": meta, "pairs": pairs}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(pairs)} pairs ({k_trick} trick) -> {os.path.relpath(a.out, root)}")


if __name__ == "__main__":
    main()
