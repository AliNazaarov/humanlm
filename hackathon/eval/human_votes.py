"""Blind human test: O3c (GLM + harness + style) vs Claude Opus 5.5 strong. Two sources, reported separately and pooled.
Usage: human_votes.py  -> hackathon/report/human_votes.json (score_all shows it under the leaderboard)

Telegram: hackathon/social/telegram/VOTES.md (per post: A | B | Both fine | Neither counts) + KEY.json (gitignored until
the polls close), mapping each post to the side that is O3c: {"1": "A"} or {"1": {"A": "<system>", "B": "<system>"}}.
Page: hackathon/report/human_ab.jsonl (export_votes.py), rows with version == PAIRS_VERSION; people counted by ballot.
Win rate counts only decisive votes; "both fine" and "neither" are reported, never folded in. Sign test on wins.
"""
from __future__ import annotations

import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path.insert(0, HERE)
import stats as st  # noqa: E402

PAIRS_VERSION = "fd809333d5320427"  # O3c vs frontier-strong:claude-opus-5-5 (hackathon/demo/ab_page/pairs.json)
OURS = re.compile(r"O3c", re.I)


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


def page_counts(rows: list[dict]) -> dict:
    rows = [r for r in rows if r.get("version") == PAIRS_VERSION]
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
    if os.path.exists(page):
        rows = [json.loads(l) for l in open(page, encoding="utf-8") if l.strip()]
        c = page_counts(rows)
        if c["votes"]:
            res["sources"]["page"] = summarise(c)
    if res["sources"]:
        pooled = {k: sum(s[k] for s in res["sources"].values()) for k in ("ours", "theirs", "both_fine", "neither")}
        res["pooled"] = summarise(pooled)
    with open(os.path.join(ROOT, "hackathon/report/human_votes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print("human votes:", {k: (v["ours"], v["theirs"]) for k, v in res["sources"].items()} or "none yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
