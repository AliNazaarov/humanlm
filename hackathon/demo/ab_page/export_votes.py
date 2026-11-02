"""Turn the A/B page's vote store into hackathon/report/human_ab.jsonl.
Usage: export_votes.py VOTES_DUMP.json [AB_PAIRS.json] [OUT.jsonl]
VOTES_DUMP.json = the `votes` collection as a list of {id, data} (an ArtifactData list of the page),
or {"documents": [...]}. One row per answered pair:
  {voter, ballot, pid, id, vote: A|B|tie, a_system, b_system, first_shown: a|b, reason}
`vote` is relative to ab_pairs.json's a/b, so a_system/b_system name the winner. Blank picks are skipped.
`voter` is a claude.ai account id; one account can hold many readers ("Hand to the next person"),
so count people by `ballot`, never by `voter`. Ballots cast on a different pairs version are dropped.
"""
import importlib.util, json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, "../../.."))
AB = os.path.join(root, "hackathon/demo/ab_pairs.json")
OUT = os.path.join(root, "hackathon/report/human_ab.jsonl")
VOTE = {"a": "A", "b": "B", "tie": "tie"}


def docs(dump) -> list[dict]:
    if isinstance(dump, dict):
        dump = dump.get("documents") or dump.get("docs") or []
    return [{"id": d.get("id") or d.get("doc_id"), "data": d.get("data") or {}} for d in dump]


def _version(ab: dict) -> str:
    spec = importlib.util.spec_from_file_location("build_pairs", os.path.join(here, "build_pairs.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.version(ab)


def rows(dump, ab: dict, stale: list | None = None) -> list[dict]:
    """Answered picks as report rows; ballot ids cast on another pairs version go to `stale`."""
    pairs, ver = {p["pid"]: p for p in ab["pairs"]}, _version(ab)
    out = []
    for d in sorted(docs(dump), key=lambda d: str(d["id"])):
        for bid, ballot in sorted((d["data"].get("ballots") or {}).items()):
            if ballot.get("version") != ver:
                if stale is not None:
                    stale.append(bid)
                continue
            for pid, pk in sorted((ballot.get("picks") or {}).items(), key=lambda kv: int(kv[0])):
                p = pairs.get(int(pid))
                if p is None or pk.get("pick") not in VOTE:
                    continue
                out.append({"voter": d["id"], "ballot": bid, "pid": p["pid"], "id": p["id"],
                            "vote": VOTE[pk["pick"]], "a_system": p["a_system"], "b_system": p["b_system"],
                            "first_shown": pk.get("first"), "reason": (pk.get("reason") or "")[:300]})
    return out


def main(argv=None):
    a = list(argv if argv is not None else sys.argv[1:])
    if not a:
        print(__doc__); return 1
    dump = json.load(open(a[0], encoding="utf-8"))
    ab = json.load(open(a[1] if len(a) > 1 else AB, encoding="utf-8"))
    out = a[2] if len(a) > 2 else OUT
    stale = []
    rs = rows(dump, ab, stale)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rs)} votes from {len({r['ballot'] for r in rs})} ballots -> {os.path.relpath(out, root)}")
    if stale:
        print(f"dropped {len(stale)} ballots cast on a different pairs version", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
