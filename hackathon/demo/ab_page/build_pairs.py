"""Public pairs for the blind A/B page. Usage: build_pairs.py [AB_PAIRS.json] [OUT.json]
Reads hackathon/demo/ab_pairs.json (from make_ab_pairs.py) and writes ab_page/pairs.json with every
system name removed. Each side gets an opaque group X or Y, assigned by a coin flip that is not stored,
so the page can tally without anyone decoding names. reveal_map(ab, pub) recovers {X: system, Y: system}
by comparing the two files. meta.version = sha256 of the pairs' text, stored with every ballot so
export_votes.py can refuse votes cast on a different set of pairs.
"""
import hashlib, json, os, random, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, "../../.."))
SRC = os.path.join(root, "hackathon/demo/ab_pairs.json")
OUT = os.path.join(here, "pairs.json")


def version(ab: dict) -> str:
    """sha256 over (pid, draft, a, b) of every pair, first 16 hex chars."""
    body = json.dumps([[p["pid"], p["draft"], p["a"], p["b"]] for p in ab["pairs"]], ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def systems(ab: dict) -> list[str]:
    s = sorted({x for p in ab["pairs"] for x in (p["a_system"], p["b_system"])})
    if len(s) != 2 or any(p["a_system"] == p["b_system"] for p in ab["pairs"]):
        raise ValueError(f"need two distinct systems in every pair, got {s}")
    return s


def public(ab: dict, flip: bool | None = None) -> dict:
    s = systems(ab)
    if flip is None:
        flip = random.SystemRandom().random() < 0.5
    g = {s[0]: "Y" if flip else "X", s[1]: "X" if flip else "Y"}
    pairs = [{"pid": p["pid"], "id": p["id"], "draft": p["draft"], "a": p["a"], "b": p["b"],
              "a_group": g[p["a_system"]], "b_group": g[p["b_system"]]} for p in ab["pairs"]]
    return {"meta": {"n": len(pairs), "version": version(ab)}, "pairs": pairs}


def reveal_map(ab: dict, pub: dict) -> dict:
    """{'X': system, 'Y': system}, read off any pair; checks every pair agrees."""
    by_pid = {p["pid"]: p for p in ab["pairs"]}
    out = {}
    for q in pub["pairs"]:
        p = by_pid[q["pid"]]
        for side in ("a", "b"):
            if out.setdefault(q[side + "_group"], p[side + "_system"]) != p[side + "_system"]:
                raise ValueError(f"pair {q['pid']}: group {q[side + '_group']} maps to two systems")
    return out


def main(argv=None):
    a = list(argv if argv is not None else sys.argv[1:]) + [None, None]
    src, out = a[0] or SRC, a[1] or OUT
    ab = json.load(open(src, encoding="utf-8"))
    pub = public(ab)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, indent=1)
    print(f"{pub['meta']['n']} pairs, version {pub['meta']['version']} -> {os.path.relpath(out, root)}")


if __name__ == "__main__":
    main()
