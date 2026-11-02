"""Merge every human A/B vote into hackathon/report/human_ab.jsonl.
Usage: export_votes.py [--store DUMP.json] [--public ROWS.json] [--local LOCALSTORAGE.json ...] [--codes CODES.txt ...]
                       [--telegram VOTES.json ...]
                       [--rev GITREV ...] [--out OUT.jsonl]

Pair sets: the current hackathon/demo/ab_pairs.json + ab_page/pairs.json, plus the same two files at each --rev
(older pair versions, e.g. --rev fdb8bfc). A vote is mapped through the set whose version it was cast on, so
versions never mix; votes for an unknown version are counted and dropped.
Sources:
  --store     the page's `votes` collection (ArtifactData list: [{id, data: {ballots: {bid: {version, picks}}}}])
  --local     the page's localStorage from one device (all ballots ever cast on it, e.g. a hand-around laptop):
              in that browser's console run  copy(localStorage.getItem("ab-read-v1"))  and paste into a .json file
  --public    the public page's Supabase table `ab_votes` as a JSON list of rows (select * … order by id); one row
              per pick event, the latest per (ballot, pid) counts
  --codes     any text holding codes from the page's done screen: FLM1:<version 8>:<ballot 6>:<a|b|t|- per pid>
  --telegram  Ali's hosted page: a JSON list (or {"votes": [...]}) of {pid, choice: X|Y|tie|both_bad, version,
              voter|voter_hash, ballot?}; X/Y are the opaque groups in that version's pairs.json
One row per answered pair:
  {source, version, ballot, voter, pid, id, vote: A|B|tie|both_bad, winner, a_system, b_system, first_shown, reason,
   ui, vw, ts}   ui = page version (1 = before the 2026-11-02 design pass, 2 = after; null for codes/telegram), vw = viewport
   px, ts = when the pick was made (ISO UTC from the reader's device; null for codes/telegram)
`vote` is relative to ab_pairs.json's a/b; `winner` names the system (null for tie/both_bad).
Count people by `ballot` (one reader), never by `voter`: one account can collect many readers on one device.
"""
import argparse, importlib.util, json, os, re, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, "../../.."))
AB, PUB = "hackathon/demo/ab_pairs.json", "hackathon/demo/ab_page/pairs.json"
OUT = os.path.join(root, "hackathon/report/human_ab.jsonl")
PICK = {"a": "A", "b": "B", "tie": "tie", "t": "tie"}
CODE = re.compile(r"FLM1:([0-9a-f]{8}):([0-9a-z]{1,6}):([abt-]+)")

spec = importlib.util.spec_from_file_location("build_pairs", os.path.join(here, "build_pairs.py"))
bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)


def pair_set(ab: dict, pub: dict) -> dict:
    """{version, pairs: {pid: pair}, groups: {'X': system, 'Y': system}} for one version of the pairs."""
    ver = bp.version(ab)
    if pub.get("meta", {}).get("version") not in (None, ver):
        raise ValueError(f"pairs.json version {pub['meta']['version']} != ab_pairs version {ver}")
    return {"version": ver, "pairs": {p["pid"]: p for p in ab["pairs"]}, "groups": bp.reveal_map(ab, pub)}


def load_sets(revs: list[str], extra: list | tuple = ()) -> dict:
    """Pair sets by version: the current files, the same files at each git rev, and each extra (AB, PUB) path pair."""
    sets = {}
    def add(ab, pub):
        s = pair_set(ab, pub); sets[s["version"]] = s
    add(*(json.load(open(os.path.join(root, f), encoding="utf-8")) for f in (AB, PUB)))
    for ab_path, pub_path in extra:
        add(*(json.load(open(p, encoding="utf-8")) for p in (ab_path, pub_path)))
    for rev in revs:
        add(*(json.loads(subprocess.run(["git", "-C", root, "show", f"{rev}:{f}"], check=True,
                                        capture_output=True, text=True, encoding="utf-8").stdout) for f in (AB, PUB)))
    return sets


def find(sets: dict, version: str | None) -> dict | None:
    """The set whose version equals or starts with `version` (codes carry 8 hex chars)."""
    if not version:
        return None
    hits = [s for v, s in sets.items() if v.startswith(version)]
    return hits[0] if len(hits) == 1 else None


def row(source, s, ballot, voter, pid, vote, first=None, reason="", ui=None, vw=None, ts=None):
    p = s["pairs"][pid]
    winner = {"A": p["a_system"], "B": p["b_system"]}.get(vote)
    return {"source": source, "version": s["version"], "ballot": ballot, "voter": voter, "pid": pid, "id": p["id"],
            "vote": vote, "winner": winner, "a_system": p["a_system"], "b_system": p["b_system"],
            "first_shown": first, "reason": (reason or "")[:300], "ui": ui, "vw": vw, "ts": ts}


def from_store(dump, sets: dict, dropped: list) -> list[dict]:
    docs = (dump.get("documents") or dump.get("docs") or []) if isinstance(dump, dict) else dump
    out = []
    for d in sorted(docs, key=lambda d: str(d.get("id") or d.get("doc_id"))):
        uid = d.get("id") or d.get("doc_id")
        for bid, b in sorted(((d.get("data") or {}).get("ballots") or {}).items()):
            s = find(sets, b.get("version"))
            if s is None:
                dropped.append(("store", bid, b.get("version"))); continue
            for pid, pk in sorted((b.get("picks") or {}).items(), key=lambda kv: int(kv[0])):
                if int(pid) in s["pairs"] and pk.get("pick") in PICK:
                    out.append(row("page", s, bid, uid, int(pid), PICK[pk["pick"]], pk.get("first"), pk.get("reason"),
                                   b.get("ui", 1), b.get("vw"), pk.get("at")))  # ballots before the design pass carry no ui
    return out


def from_public(rows: list[dict], sets: dict, dropped: list) -> list[dict]:
    """The public table: later rows for the same (ballot, pid) replace earlier ones (a changed pick or reason)."""
    latest = {}
    for r in sorted(rows, key=lambda r: (r.get("id") or 0, str(r.get("at") or ""))):
        latest[(r.get("ballot"), r.get("pid"))] = r
    out = []
    for (bid, pid), r in sorted(latest.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
        s = find(sets, r.get("version"))
        if s is None or pid not in s["pairs"] or r.get("pick") not in PICK:
            dropped.append(("public", bid, r.get("version"))); continue
        out.append(row("public", s, f"pub:{bid}", None, pid, PICK[r["pick"]], r.get("first"), r.get("reason"),
                       r.get("ui"), r.get("vw"), r.get("at") or r.get("created_at")))
    return out


def from_local(saved: dict, sets: dict, dropped: list, device: str) -> list[dict]:
    """One device's localStorage value {ballot, local: {ballots}}: every ballot on it, source 'local'."""
    doc = {"id": f"device:{device}", "data": (saved or {}).get("local") or {}}
    rows = from_store([doc], sets, dropped)
    for r in rows:
        r["source"], r["ballot"] = "local", f"{device}:{r['ballot']}"
    return rows


def from_codes(text: str, sets: dict, dropped: list) -> list[dict]:
    out, seen = [], set()
    for ver, tail, seq in CODE.findall(text):
        s, bid = find(sets, ver), f"code:{ver}:{tail}"
        if s is None or len(seq) != len(s["pairs"]):
            dropped.append(("code", bid, ver)); continue
        if bid in seen:  # the same code pasted twice
            continue
        seen.add(bid)
        for pid, ch in zip(sorted(s["pairs"]), seq):
            if ch in PICK:
                out.append(row("code", s, bid, None, pid, PICK[ch]))
    return out


def from_telegram(votes, sets: dict, dropped: list) -> list[dict]:
    votes = votes.get("votes", []) if isinstance(votes, dict) else votes
    out, seen = [], set()
    for v in votes:
        s = find(sets, v.get("version"))
        voter = v.get("voter_hash") or v.get("voter")
        bid = f"tg:{v.get('ballot') or voter}"
        try:
            pid = int(v.get("pid"))
        except (TypeError, ValueError):
            pid = None
        choice = str(v.get("choice", "")).strip()
        if s is None or pid not in (s["pairs"] if s else {}):
            dropped.append(("telegram", bid, v.get("version"))); continue
        if choice in ("X", "Y"):
            p, sys_ = s["pairs"][pid], s["groups"][choice]
            vote = "A" if sys_ == p["a_system"] else "B"
        elif choice in ("tie", "both_bad"):
            vote = choice
        else:
            dropped.append(("telegram", bid, v.get("version"))); continue
        if (bid, s["version"], pid) in seen:  # keep the first vote per reader and pair
            continue
        seen.add((bid, s["version"], pid))
        out.append(row("telegram", s, bid, voter, pid, vote, reason=v.get("reason", "")))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store"); ap.add_argument("--public"); ap.add_argument("--local", action="append", default=[])
    ap.add_argument("--codes", action="append", default=[])
    ap.add_argument("--telegram", action="append", default=[]); ap.add_argument("--rev", action="append", default=[])
    ap.add_argument("--pairs", nargs=2, action="append", default=[], metavar=("AB_PAIRS", "PUBLIC_PAIRS"),
                    help="another pair set, e.g. hackathon/demo/ab_pairs_set2.json hackathon/demo/ab_page/set2/pairs.json")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if not (a.store or a.public or a.local or a.codes or a.telegram):
        ap.print_help(); return 1
    sets, dropped, rs = load_sets(a.rev, a.pairs), [], []
    if a.store:
        rs += from_store(json.load(open(a.store, encoding="utf-8")), sets, dropped)
    if a.public:
        raw = json.load(open(a.public, encoding="utf-8"))
        rs += from_public(raw.get("rows", raw) if isinstance(raw, dict) else raw, sets, dropped)
    for f in a.local:
        raw = json.load(open(f, encoding="utf-8"))
        rs += from_local(json.loads(raw) if isinstance(raw, str) else raw, sets, dropped,
                         os.path.splitext(os.path.basename(f))[0])
    # A code duplicates a local ballot from the same device (same version + ballot tail): keep the local copy.
    have = {(r["version"][:8], r["ballot"].rsplit(":", 1)[-1][-6:]) for r in rs if r["source"] == "local"}
    for f in a.codes:
        rs += [r for r in from_codes(open(f, encoding="utf-8").read(), sets, dropped)
               if (r["version"][:8], r["ballot"].rsplit(":", 1)[-1]) not in have]
    for f in a.telegram:
        rs += from_telegram(json.load(open(f, encoding="utf-8")), sets, dropped)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for ver in sorted({r["version"] for r in rs}):
        sub = [r for r in rs if r["version"] == ver]
        print(f"{ver}: {len(sub)} votes from {len({r['ballot'] for r in sub})} readers")
    print(f"-> {os.path.relpath(a.out, root)}")
    if dropped:
        print(f"dropped {len(dropped)} ballots/votes on unknown pair versions: {sorted({d[2] for d in dropped})}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
