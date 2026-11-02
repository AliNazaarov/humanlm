"""Build evals/real_readmes.jsonl: an EVAL-ONLY split of real product copy (README intros of permissively
licensed GitHub repos). Never training data.

Stages (each prints its count):
  collect  GitHub search API (token from `gh auth token`, never printed), repos created >= 2024-06-01,
           stars >= 20, one search per QUERIES term, licence checked from the API's license.spdx_id.
           README fetched via /repos/{o}/{r}/readme (base64 JSON, gives html_url). 1 request/second,
           waits on rate-limit headers. Raw API responses are cached in hackathon/eval/_cache_real/ so a
           re-run makes no network calls and gives the same file (--refresh refetches).
  extract  first prose section -> plain text (no badges, images, HTML, code, tables, links), 60-220 words,
           English, not list-only / install-only.
  enrich   pipeline/metrics text_metrics + stock_hits (no LLM); keep items with at least one AI tell.
  dedup    by normalised-text hash and by owner (one item per org/user).
  leakage  drop items sharing 8+ consecutive words with hackathon/data/train.jsonl or valid.jsonl.
  store    first TARGET items by (-stars, repo) -> ids rr-001.., sorted by id.

Usage: PYTHONUTF8=1 python hackathon/eval/collect_real.py [--refresh] [--target 80] [--max-candidates 400]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../.."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import metrics as m  # noqa: E402

OUT = os.path.join(ROOT, "evals", "real_readmes.jsonl")
CACHE = os.path.join(HERE, "_cache_real")
TRAIN_FILES = [os.path.join(ROOT, "hackathon", "data", f) for f in ("train.jsonl", "valid.jsonl")]

FETCHED = "2026-11-02"
CREATED_FROM = "2024-06-01"
MIN_STARS = 20
MIN_WORDS, MAX_WORDS = 60, 220
NGRAM = 8
ALLOWED = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC-BY-4.0", "CC0-1.0"}
# Exact search terms (each combined with f"created:>={CREATED_FROM} stars:>={MIN_STARS}").
QUERIES = [
    "topic:saas",
    "topic:productivity",
    "topic:startup",
    "topic:developer-tools",
    "topic:ai-tools",
    '"ai tool" in:description',
    '"developer tool" in:description',
    '"open source alternative" in:description',
]
PER_QUERY = 100  # one page of 100 per query; candidates capped at --max-candidates after union


# ---------------------------------------------------------------- HTTP (polite)
class GitHub:
    def __init__(self, refresh: bool = False):
        self.refresh = refresh
        self.token = None
        self.last = 0.0
        self.calls = 0

    def _token(self) -> str:
        if self.token is None:
            self.token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                                        check=True).stdout.strip()
        return self.token

    def get(self, path: str, cache_key: str):
        """GET api.github.com/path as JSON, cached on disk. Returns None on 404."""
        fn = os.path.join(CACHE, cache_key + ".json")
        if os.path.exists(fn) and not self.refresh:
            with open(fn, encoding="utf-8") as fh:
                return json.load(fh)
        import truststore
        truststore.inject_into_ssl()
        for attempt in range(5):
            wait = 1.0 - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.calls += 1
            req = urllib.request.Request("https://api.github.com/" + path, headers={
                "Authorization": "Bearer " + self._token(), "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "featherlm-eval-collector"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                    if r.headers.get("X-RateLimit-Remaining") == "0":
                        self._sleep_until(r.headers.get("X-RateLimit-Reset"))
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    data = None
                    break
                if e.code in (403, 429):
                    self._sleep_until(e.headers.get("X-RateLimit-Reset"), e.headers.get("Retry-After"))
                    continue
                if e.code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except urllib.error.URLError:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError("giving up on " + path)
        os.makedirs(CACHE, exist_ok=True)
        ign = os.path.join(CACHE, ".gitignore")
        if not os.path.exists(ign):
            with open(ign, "w", encoding="utf-8") as fh:
                fh.write("*\n")
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return data

    @staticmethod
    def _sleep_until(reset, retry_after=None):
        secs = int(retry_after) if retry_after else max(1, int(reset or 0) - int(time.time()) + 2)
        secs = min(secs, 120)
        print(f"  rate limit: sleeping {secs}s", file=sys.stderr)
        time.sleep(secs)


def collect(gh: GitHub, max_candidates: int) -> list[dict]:
    seen: dict[str, dict] = {}
    for i, q in enumerate(QUERIES):
        full = f"{q} created:>={CREATED_FROM} stars:>={MIN_STARS}"
        path = "search/repositories?" + urllib.parse.urlencode(
            {"q": full, "sort": "stars", "order": "desc", "per_page": PER_QUERY})
        res = gh.get(path, f"search_{i:02d}") or {}
        for it in res.get("items", []):
            seen.setdefault(it["full_name"], it)
    cands = sorted(seen.values(), key=lambda r: (-r["stargazers_count"], r["full_name"].lower()))
    return cands[:max_candidates]


# ---------------------------------------------------------------- extract / clean
FENCE = re.compile(r"^[ \t>]*(```|~~~).*?^[ \t>]*\1[^\n]*$", re.S | re.M)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
HTML_DROP = re.compile(r"<(script|style|picture|svg|table|details|pre|code)\b.*?</\1\s*>", re.S | re.I)
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
BADGE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)|\[([^\]]+)\]\[[^\]]*\]")
REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*\S+.*$", re.M)
URL = re.compile(r"<?https?://\S+>?")
INLINE_CODE = re.compile(r"`[^`\n]*`")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
SETEXT = re.compile(r"^\s*(=+|-+)\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$|^\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
NAV_ONLY = re.compile(r"^[\s|·•/\-–—,]*$")
EMPTY_LINK = re.compile(r"\[\]\[[^\]]*\]|\[\]\([^)]*\)|\[\]")
ALERT = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*", re.I)
SEPS = re.compile(r"\s[|·•]\s|\s[|·•]$|^[|·•]\s")
INTRO_NAMES = re.compile(r"^(about|overview|introduction|intro|what is|what's|why|description|summary)\b", re.I)
SKIP_SECTIONS = re.compile(r"(install|quick ?start|getting started|setup|usage|table of contents|contents|"
                           r"license|contribut|demo|screenshot|preview|sponsor|star history|features?)\b", re.I)
INSTALL_WORDS = re.compile(r"\b(npm|pnpm|yarn|pip|brew|docker|git clone|cargo|go install|npx)\b", re.I)
STOP = {"the", "and", "a", "to", "of", "is", "for", "in", "with", "your", "you", "it", "that", "on", "an", "or",
        "are", "this", "as", "be", "can", "from", "by", "we", "our"}


def _strip_inline(line: str) -> str:
    line = BADGE.sub("", line)
    line = IMAGE.sub("", line)
    # a line that is only links + separators is navigation ("Docs · Discord · Website"): drop it
    if LINK.search(line) and NAV_ONLY.match(LINK.sub("", line)):
        return ""
    line = LINK.sub(lambda mo: mo.group(1) or mo.group(2) or "", line)
    line = EMPTY_LINK.sub("", line)
    line = URL.sub("", line)
    line = INLINE_CODE.sub(lambda mo: mo.group(0).strip("`"), line)
    line = re.sub(r"(\*\*|__)(.+?)\1", r"\2", line)
    line = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", line)
    line = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", line)
    line = re.sub(r"^\s*>\s?", "", line)  # blockquote marker
    line = ALERT.sub("", re.sub(r"[ \t]+", " ", line).strip())
    return "" if _junk(line) else line


def _junk(line: str) -> bool:
    """Leftovers that are not copy: empty, nav rows, language pickers, dangling 'Website:' labels."""
    ws = m.words(line)
    if not ws:
        return True
    letters = [c for c in line if c.isalpha()]
    if letters and sum(not c.isascii() for c in letters) / len(letters) > 0.3:
        return True
    parts = [p for p in re.split(r"\s*[|·•]\s*", line) if p.strip()]
    if SEPS.search(line) and all(len(m.words(p)) <= 4 for p in parts) \
            and not LIST_ITEM.match(line):
        return True
    if "llms.txt" in line.lower():  # text addressed to crawlers/agents, not to readers
        return True
    return line.endswith(":") and len(ws) <= 5


def clean_markdown(md: str) -> list[tuple[int, str]]:
    """Markdown/HTML -> list of (heading_level or 0, plain line). Blank lines kept as (0, '')."""
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    md = HTML_COMMENT.sub("", md)
    md = FENCE.sub("", md)
    md = HTML_DROP.sub("", md)
    md = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1\s*>", lambda mo: "\n" + "#" * int(mo.group(1)) + " " + mo.group(2) + "\n",
                md, flags=re.S | re.I)
    md = re.sub(r"<br\s*/?>|</p\s*>|<p\b[^>]*>|</div\s*>|<div\b[^>]*>", "\n", md, flags=re.I)
    md = HTML_TAG.sub("", md)
    md = html.unescape(md)
    md = REF_DEF.sub("", md)
    out: list[tuple[int, str]] = []
    raw = md.split("\n")
    for i, line in enumerate(raw):
        if TABLE_ROW.match(line) or re.match(r"^( {4}|\t)\S", line) and (not out or out[-1][1] == ""):
            continue  # tables, indented code
        if SETEXT.match(line) and out and out[-1][1] and out[-1][0] == 0:
            lvl = 1 if line.strip().startswith("=") else 2
            out[-1] = (lvl, out[-1][1])
            continue
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append((0, ""))  # horizontal rule
            continue
        h = HEADING.match(line)
        if h:
            text = _strip_inline(h.group(2))
            if text:
                out.append((len(h.group(1)), text))
            continue
        out.append((0, _strip_inline(line)))
    return out


def _is_prose(line: str) -> bool:
    return len(m.words(line)) >= 8 and not LIST_ITEM.match(line)


def extract_intro(md: str, min_words: int = MIN_WORDS, max_words: int = MAX_WORDS) -> tuple[str | None, str]:
    """First prose section of a README as plain text, or (None, reason)."""
    lines = clean_markdown(md)
    # sections split at headings of level >= 2 (H1 is the title and stays with the intro)
    sections: list[tuple[str, list[str]]] = [("", [])]
    heads = {text for lvl, text in lines if lvl == 1}
    for lvl, text in lines:
        if lvl >= 2:
            sections.append((text, []))
        elif lvl == 1:
            sections[-1][1].append(text)
            sections[-1][1].append("")
        else:
            sections[-1][1].append(text)
    chosen = None
    for title, body in sections[:4]:  # the intro: pre-H2 text or one of the first few non-boilerplate sections
        if title and SKIP_SECTIONS.search(title) and not INTRO_NAMES.match(title):
            continue
        if any(_is_prose(b) for b in body):
            chosen = body
            break
    if chosen is None:
        head = [b for _, body in sections[:4] for b in body if b]
        if head and sum(bool(LIST_ITEM.match(b)) for b in head) / len(head) > 0.5:
            return None, "list_only"
        return None, "no_prose"
    # paragraphs: collapse runs of blank lines; keep line breaks for headings/taglines
    paras: list[str] = []
    cur: list[str] = []
    for b in chosen + [""]:
        if b and cur and not LIST_ITEM.match(b) and not LIST_ITEM.match(cur[-1]) and b not in heads \
                and cur[-1] not in heads:
            cur[-1] += " " + b
        elif b and cur and LIST_ITEM.match(cur[-1]) and not LIST_ITEM.match(b) and b not in heads:
            cur[-1] += " " + b  # continuation of a list item
        elif b:
            cur.append(b)
        elif cur:
            paras.append("\n".join(cur))
            cur = []
    lines_all = [ln for p in paras for ln in p.split("\n")]
    list_lines = sum(bool(LIST_ITEM.match(ln)) for ln in lines_all)
    if lines_all and list_lines / len(lines_all) > 0.5:
        return None, "list_only"
    prose = [ln for ln in lines_all if _is_prose(ln)]
    if len(prose) < 2 and sum(len(m.words(p)) for p in prose) < 30:
        return None, "no_prose"
    if INSTALL_WORDS.search(" ".join(lines_all)) and len(prose) < 2:
        return None, "install_only"
    # trim to max_words at a paragraph boundary
    keep, total, overflow = [], 0, False
    for p in paras:
        n = len(m.words(p))
        if total + n > max_words:
            overflow = True
            break
        keep.append(p)
        total += n
    text = "\n\n".join(keep).strip()
    n = len(m.words(text))
    if n < min_words:
        return None, "too_long" if overflow else "too_short"
    if n > max_words:
        return None, "too_long"
    if not is_english(text):
        return None, "non_english"
    return text, "ok"


def is_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isascii() for c in letters) / len(letters) < 0.95:
        return False
    toks = [t.lower() for t in m.words(text)]
    return bool(toks) and sum(t in STOP for t in toks) / len(toks) >= 0.12


# ---------------------------------------------------------------- enrich / dedup / leakage
def tells(text: str) -> dict:
    tm = m.text_metrics(text)
    return {"stock_rate": round(tm["stock_rate"], 3), "em_dash_rate": round(tm["em_dash_rate"], 3),
            "emoji_rate": round(tm["emoji_rate"], 3), "_any": (tm["stock_rate"] > 0 or tm["em_dash_rate"] > 0
            or tm["emoji_rate"] > 0 or tm["tricolon_rate"] > 0 or tm["not_x_but_y_rate"] > 0),
            "_stock_hits": m.stock_hits(text)}


def text_hash(text: str) -> str:
    return hashlib.sha1(" ".join(w.lower() for w in m.words(text)).encode()).hexdigest()


def ngrams(text: str, n: int = NGRAM) -> set[tuple]:
    t = [w.lower() for w in m.words(text)]
    return {tuple(t[i:i + n]) for i in range(len(t) - n + 1)}


def train_ngrams() -> set[tuple]:
    grams: set[tuple] = set()
    for fn in TRAIN_FILES:
        with open(fn, encoding="utf-8") as fh:
            for ln in fh:
                row = json.loads(ln)
                for msg in row.get("messages", []):
                    if msg.get("role") != "system":
                        grams |= ngrams(msg.get("content", ""))
    return grams


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and refetch")
    ap.add_argument("--target", type=int, default=80)
    ap.add_argument("--min", type=int, default=60)
    ap.add_argument("--max-candidates", type=int, default=400)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    gh = GitHub(refresh=a.refresh)
    counts: dict[str, int] = {}

    cands = collect(gh, a.max_candidates)
    counts["candidates"] = len(cands)
    cands = [r for r in cands if (r.get("license") or {}).get("spdx_id") in ALLOWED
             and r["created_at"][:10] >= CREATED_FROM and r["stargazers_count"] >= MIN_STARS
             and not r.get("fork") and not r.get("archived")]
    counts["licence_ok"] = len(cands)

    extracted, reasons = [], {}
    for r in cands:
        rd = gh.get(f"repos/{r['full_name']}/readme", "readme_" + r["full_name"].replace("/", "__"))
        if not rd or rd.get("encoding") != "base64":
            reasons["no_readme"] = reasons.get("no_readme", 0) + 1
            continue
        md = base64.b64decode(rd["content"]).decode("utf-8", errors="replace")
        text, why = extract_intro(md)
        reasons[why] = reasons.get(why, 0) + 1
        if text:
            extracted.append((r, rd, text))
    counts["readme_fetched"] = len(cands) - reasons.get("no_readme", 0)
    counts["extracted"] = len(extracted)

    enriched = []
    for r, rd, text in extracted:
        t = tells(text)
        if t["_any"]:
            enriched.append((r, rd, text, t))
    counts["has_tells"] = len(enriched)

    seen_h, seen_owner, dedup = set(), set(), []
    for item in enriched:
        r, _, text, _ = item
        h, owner = text_hash(text), r["owner"]["login"].lower()
        if h in seen_h or owner in seen_owner:
            continue
        seen_h.add(h)
        seen_owner.add(owner)
        dedup.append(item)
    counts["deduped"] = len(dedup)

    tg = train_ngrams()
    clean = [it for it in dedup if not (ngrams(it[2]) & tg)]
    counts["leakage_dropped"] = len(dedup) - len(clean)
    counts["leakage_clean"] = len(clean)

    chosen = clean[:a.target]
    rows = []
    for i, (r, rd, text, t) in enumerate(chosen, 1):
        rows.append({"id": f"rr-{i:03d}", "ai_draft": text, "source": "github_readme", "repo": r["full_name"],
                     "url": rd["html_url"], "licence": r["license"]["spdx_id"], "created_at": r["created_at"],
                     "stars": r["stargazers_count"], "fetched": FETCHED, "word_count": len(m.words(text)),
                     "tells": {k: t[k] for k in ("stock_rate", "em_dash_rate", "emoji_rate")}})
    rows.sort(key=lambda x: x["id"])
    # final leakage assert on what is written
    assert not any(ngrams(x["ai_draft"]) & tg for x in rows), "leakage in output"
    counts["stored"] = len(rows)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")

    lic: dict[str, int] = {}
    for x in rows:
        lic[x["licence"]] = lic.get(x["licence"], 0) + 1
    wc = [x["word_count"] for x in rows]
    print(json.dumps({"counts": counts, "extract_reasons": reasons, "licences": dict(sorted(lic.items())),
                      "word_count_range": [min(wc), max(wc)] if wc else None, "api_calls": gh.calls}, indent=1))
    if len(rows) < a.min:
        print(f"WARNING: only {len(rows)} items (< {a.min})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
