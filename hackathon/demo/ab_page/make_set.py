"""A further A/B pair set on fresh items. Usage: make_set.py RUN_X.jsonl RUN_Y.jsonl OUT.json --n 8 [--seed 1] [--exclude AB.json ...]
Like make_ab_pairs.py (same output format, eval_all items, dev/trick in proportion, sides shuffled per pair), but never
reuses an item already in an --exclude pair file, so a second human test reads text nobody has judged yet.
"""
import argparse, json, os, random

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, "../../.."))


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path, encoding="utf-8")) if r.get("output", "x").strip()}


def make(ev: dict, x: dict, y: dict, n: int, seed: int, exclude: set) -> list[dict]:
    ids = sorted((set(ev) & set(x) & set(y)) - exclude)
    rng = random.Random(seed)
    trick = [i for i in ids if i.startswith("trick")]; dev = [i for i in ids if not i.startswith("trick")]
    k = round(n * len(trick) / len(ids)) if ids else 0
    chosen = rng.sample(dev, n - k) + rng.sample(trick, k)
    rng.shuffle(chosen)
    pairs = []
    for pid, i in enumerate(chosen, 1):
        sides = [x[i], y[i]]; rng.shuffle(sides)
        pairs.append({"pid": pid, "id": i, "draft": ev[i]["ai_draft"], "a": sides[0]["output"], "b": sides[1]["output"],
                      "a_system": sides[0]["system"], "b_system": sides[1]["system"]})
    return pairs


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("x"); p.add_argument("y"); p.add_argument("out")
    p.add_argument("--n", type=int, default=8); p.add_argument("--seed", type=int, default=1)
    p.add_argument("--exclude", action="append", default=[])
    a = p.parse_args(argv)
    ev = load(os.path.join(root, "evals/eval_all.jsonl"))
    excl = {q["id"] for f in a.exclude for q in json.load(open(f, encoding="utf-8"))["pairs"]}
    pairs = make(ev, load(a.x), load(a.y), a.n, a.seed, excl)
    rel = lambda q: os.path.relpath(q, root).replace(os.sep, "/")
    meta = {"x": rel(a.x), "y": rel(a.y), "seed": a.seed, "n": len(pairs), "excluded": sorted(excl)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "pairs": pairs}, f, ensure_ascii=False, indent=1)
    print(f"{len(pairs)} pairs ({sum(q['id'].startswith('trick') for q in pairs)} trick), {len(excl)} ids excluded -> {rel(a.out)}")


if __name__ == "__main__":
    main()
