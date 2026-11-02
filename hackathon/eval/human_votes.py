"""Blind human test: O3c (GLM + harness + style) vs Claude Opus 5.5 strong. Two sources, reported separately and pooled.
Usage: human_votes.py  -> hackathon/report/human_votes.json (score_all shows it under the leaderboard)

Telegram: hackathon/social/telegram/VOTES.md (per post: A | B | Both fine | Neither counts) + KEY.json (gitignored until
the polls close), mapping each post to the side that is O3c: {"1": "A"} or {"1": {"A": "<system>", "B": "<system>"}}.
Page: hackathon/report/human_ab.jsonl (export_votes.py), rows with version == PAIRS_VERSION; people counted by ballot.
Venue: hackathon/social/human_ab_venue.json (one founder ballot, unblinded by hand; a check, not a gold rater).
Win rate counts only decisive votes; "both fine" and "neither" are reported, never folded in. Sign test on wins.
"""
from __future__ import annotations

import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path.insert(0, HERE)
import stats as st  # noqa: E402

PAIRS_VERSION = "fd809333d5320427"  # set 1: O3c vs frontier-strong:claude-opus-5-5 (hackathon/demo/ab_page/pairs.json)
SET2_VERSION = "dc49e2a1e1a1c15f"   # set 2: O3k vs frontier-strong:claude-opus-5-5, 8 fresh items (hackathon/demo/ab_page/set2/pairs.json)
OURS = re.compile(r"O3[ck]", re.I)  # FeatherLM side: O3c in set 1, O3k in set 2


def telegram_counts(votes_md: str, key: dict) -> list[dict]:
    """Per post: {post, ours, theirs, both_fine, neither}; posts without a key or without counts are skipped."""
    out = []
    for line in votes_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].isdigit() or not all(c.isdigit() for c in cells[1:]):
            continue
        post, a, b, both, neither = cells[0], *map(int, cells[1:])
        k = key.get(post)
        if k is None:
            continue
        ours_side = k if isinstance(k, str) else next(s for s, sysname in k.items() if OURS.search(sysname))
        ours, theirs = (a, b) if ours_side.upper() == "A" else (b, a)
        out.append({"post": int(post), "ours": ours, "theirs": theirs, "both_fine": both, "neither": neither})
    return out


def page_counts(rows: list[dict], version: str = PAIRS_VERSION) -> dict:
    rows = [r for r in rows if r.get("version") == version]
    ours = sum(1 for r in rows if r.get("winner") and OURS.search(r["winner"]))
    theirs = sum(1 for r in rows if r.get("winner") and not OURS.search(r["winner"]))
    return {"ours": ours, "theirs": theirs, "both_fine": sum(r.get("vote") == "tie" for r in rows),
            "neither": sum(r.get("vote") == "both_bad" for r in rows), "people": len({r["ballot"] for r in rows}),
            "votes": len(rows)}


def summarise(c: dict) -> dict:
    dec = c["ours"] + c["theirs"]
    out = dict(c)
    if dec:
        out["win_rate"], out["lo"], out["hi"] = st.rate_ci(c["ours"], dec)
    out["sign_test_p"] = st.judge_sign_test(c["ours"], c["theirs"])
    return out


def main() -> int:
    res = {"pairs": "O3c_glm_prompt_harness_style vs frontier-strong:claude-opus-5-5", "sources": {}}
    tg_md = os.path.join(ROOT, "hackathon/social/telegram/VOTES.md")
    tg_key = os.path.join(ROOT, "hackathon/social/telegram/KEY.json")
    if os.path.exists(tg_md) and os.path.exists(tg_key):
        posts = telegram_counts(open(tg_md, encoding="utf-8").read(), json.load(open(tg_key, encoding="utf-8")))
        if posts:
            tot = {k: sum(p[k] for p in posts) for k in ("ours", "theirs", "both_fine", "neither")}
            res["sources"]["telegram"] = {**summarise(tot), "posts": posts, "n_posts": len(posts),
                                          "votes": sum(tot.values())}
    page = os.path.join(ROOT, "hackathon/report/human_ab.jsonl")
    venue_in_page = False
    if os.path.exists(page):
        rows = [json.loads(l) for l in open(page, encoding="utf-8") if l.strip()]
        venue_in_page = any(r.get("source") == "local" and r.get("version") == PAIRS_VERSION for r in rows)
        c = page_counts(rows)
        if c["votes"]:
            res["sources"]["page"] = summarise(c)
        # Sensitivity (rule stated in advance of looking at the effect): drop ballots with 3+ picks where every pick
        # is the first-shown side (a position-only clicker). Reported next to the main count, never instead of it.
        by_ballot = {}
        for r in rows:
            if r.get("version") == PAIRS_VERSION:
                by_ballot.setdefault(r["ballot"], []).append(r)
        def first_shown_pick(r):
            fs = r.get("first_shown")
            return fs in ("a", "b") and r.get("vote", "").lower() == fs
        clickers = sorted(b for b, rs in by_ballot.items() if len(rs) >= 3 and all(first_shown_pick(r) for r in rs))
        # Reading-time floor (stated rule): a ballot with 3+ picks whose first-to-last pick span averages under
        # 6 s per pick (30 s for 5 pairs) is faster than reading; needs a per-row "ts" (ISO time) in the export.
        def too_fast(rs):
            ts = sorted(t for t in (r.get("ts") for r in rs) if t)
            if len(rs) < 3 or len(ts) < len(rs):
                return False
            from datetime import datetime
            span = (datetime.fromisoformat(ts[-1].replace("Z", "+00:00"))
                    - datetime.fromisoformat(ts[0].replace("Z", "+00:00"))).total_seconds()
            return span / len(rs) < 6
        speeders = sorted(b for b, rs in by_ballot.items() if too_fast(rs))
        dropped = sorted(set(clickers) | set(speeders))
        if dropped:
            cs = page_counts([r for r in rows if r.get("ballot") not in set(dropped)])
            res["sources"]["page"]["sensitivity_no_position_clickers"] = {
                **summarise(cs), "dropped_ballots": dropped, "position_only": clickers, "too_fast": speeders}
        c2 = page_counts(rows, SET2_VERSION)
        if c2["votes"]:
            res["sources"]["page_set2"] = {**summarise(c2), "pairs": "O3k_glm_calm_claimcheck_bo3 vs frontier-strong:claude-opus-5-5",
                                           "note": "set 2 compares O3k, not O3c: 'ours' = O3k"}
    venue = os.path.join(ROOT, "hackathon/social/human_ab_venue.json")
    if os.path.exists(venue):  # hand-unblinded ballot from Ali's laptop (founder: a check, not a gold rater)
        v = json.load(open(venue, encoding="utf-8"))
        meta = {"voter": v.get("voter"), "note": v.get("informal"), "pattern": v.get("pattern")}
        if venue_in_page:  # the same ballot is already in the export: keep only its caveats, never count it twice
            res["sources"]["page"].update({**meta, "voter": "includes one founder ballot (Ali, venue laptop: a check, "
                                                            "not a gold rater); the other readers are public-page visitors"})
        else:
            w = [p_["winner"] for p_ in v["picks"]]
            c = {"ours": w.count("ours"), "theirs": w.count("claude"), "both_fine": w.count("tie"), "neither": 0,
                 "people": 1, "votes": len(w)}
            res["sources"]["venue_founder"] = {**summarise(c), **meta}
    if res["sources"]:
        pooled = {k: sum(s[k] for s in res["sources"].values()) for k in ("ours", "theirs", "both_fine", "neither")}
        res["pooled"] = summarise(pooled)
    with open(os.path.join(ROOT, "hackathon/report/human_votes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print("human votes:", {k: (v["ours"], v["theirs"]) for k, v in res["sources"].items()} or "none yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
