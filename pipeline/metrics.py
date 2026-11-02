"""HumanLM tell metrics. Each tell is its own number. There is no combined slop score (PLAN_30D §2,
EVALS_AND_RL_PLAN §2.3): targets are the human reference band, not zero.

Per text:  text_metrics(text) -> dict of floats; stock_hits(text) -> matched phrases (evidence).
Per set:   distinct_n(texts, n), self_bleu_lite(texts).
Gates:     faithfulness(source, output) (new number or name = hard fail); grammar(text) (None if no LanguageTool).
Bands:     human_band(corpus_jsonl, field) -> 10th-90th percentile per metric; in_band(metrics, band).
CLI:       python3 metrics.py score FILE.jsonl --field X [--source-field S] [--band band.json] [--grammar]
           python3 metrics.py band FILE.jsonl --field human
Stdlib only; language_tool_python is optional.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHRASES_PATH = os.path.join(HERE, "slop_phrases.txt")

WORD = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)*")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F1E6-\U0001F1FF☀-➿⭐⭕]")
TRICOLON = re.compile(
    r"\b([A-Za-z'-]+(?: [A-Za-z'-]+)?), ([A-Za-z'-]+(?: [A-Za-z'-]+)?),? (?:and|or) ([A-Za-z'-]+)\b", re.I)
_SECOND = r"(?:but|it's|it is|this is|that's|they're|we're|you're|it was|instead)\b"
NOT_X_BUT_Y = re.compile(
    r"\b(?:not|isn't|aren't|wasn't|weren't|don't|doesn't)\b[^.!?;:\n]{1,60}?(?:,|;|—|–|\s-\s)\s*" + _SECOND
    + r"|\bnot\s+(?:just\s+|only\s+)?\w+\s+but\b", re.I)
HEDGES = ("might", "may", "perhaps", "possibly", "arguably", "somewhat", "likely", "seems", "seem",
          "generally", "typically", "often", "can be", "could be", "tend to", "tends to",
          "in many ways", "to some extent", "it seems", "sort of", "kind of")
HEDGE_RE = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(h) for h in sorted(HEDGES, key=len, reverse=True))
                      + r")(?!\w)", re.I)
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
PRONOUN_I = {"i", "i'm", "i've", "i'll", "i'd"}


def _norm(text: str) -> str:
    return (text or "").replace("’", "'").replace("‘", "'")


def words(text: str) -> list[str]:
    return WORD.findall(_norm(text))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT.split(_norm(text)) if s.strip() and WORD.search(s)]


def paragraphs(text: str) -> list[str]:
    """Any non-empty line is a paragraph (social posts use single line breaks)."""
    return [p.strip() for p in _norm(text).split("\n") if WORD.search(p)]


def _per100(count: int, n_words: int) -> float:
    return 100.0 * count / n_words if n_words else 0.0


# ---------- stock phrases ----------
def load_phrases(path: str = PHRASES_PATH) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]


def _phrase_regex(phrases: list[str]) -> re.Pattern:
    parts = []
    for p in sorted(set(x.lower() for x in phrases), key=len, reverse=True):
        prefix = p.endswith("*")
        body = re.escape(p.rstrip("*")).replace(r"\-", "[- ]?").replace(r"\ ", r"\s+")
        parts.append(body + (r"\w*" if prefix else ""))
    return re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)", re.I)


_PHRASE_RE: re.Pattern | None = None


def stock_hits(text: str) -> list[str]:
    """Non-overlapping stock-phrase matches, longest phrase wins."""
    global _PHRASE_RE
    if _PHRASE_RE is None:
        _PHRASE_RE = _phrase_regex(load_phrases())
    return [m.group(0).lower() for m in _PHRASE_RE.finditer(_norm(text))]


# ---------- single tells ----------
def tricolon_count(text: str) -> int:
    return len(TRICOLON.findall(_norm(text)))


def not_x_but_y_count(text: str) -> int:
    return len(NOT_X_BUT_Y.findall(_norm(text)))


def mattr(tokens: list[str], window: int = 50) -> float:
    """Moving-average type-token ratio (length-robust lexical diversity)."""
    if not tokens:
        return 0.0
    if len(tokens) <= window:
        return len(set(tokens)) / len(tokens)
    counts: dict[str, int] = {}
    for t in tokens[:window]:
        counts[t] = counts.get(t, 0) + 1
    total = len(counts)
    for i in range(window, len(tokens)):
        out, inn = tokens[i - window], tokens[i]
        counts[out] -= 1
        if counts[out] == 0:
            del counts[out]
        counts[inn] = counts.get(inn, 0) + 1
        total += len(counts)
    return total / window / (len(tokens) - window + 1)


def text_metrics(text: str) -> dict[str, float]:
    """All per-text tells, each a separate number. Rates are per 100 words; *_share are per sentence/paragraph."""
    text = _norm(text)
    toks = words(text)
    n = len(toks)
    sents = sentences(text)
    lens = [len(words(s)) for s in sents]
    mean = statistics.fmean(lens) if lens else 0.0
    std = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    paras = paragraphs(text)
    openers = [words(p)[0].lower() for p in paras]
    return {
        "n_words": n,
        "stock_rate": _per100(len(stock_hits(text)), n),
        "em_dash_rate": _per100(text.count("—") + len(re.findall(r"\w--\w|\s--\s", text)), n),
        "tricolon_rate": _per100(tricolon_count(text), n),
        "not_x_but_y_rate": _per100(not_x_but_y_count(text), n),
        "question_share": sum(s.rstrip().rstrip('"\')').endswith("?") for s in sents) / len(sents) if sents else 0.0,
        "exclaim_share": sum(s.rstrip().rstrip('"\')').endswith("!") for s in sents) / len(sents) if sents else 0.0,
        "emoji_rate": _per100(len(EMOJI.findall(text)), n),
        "hedge_rate": _per100(len(HEDGE_RE.findall(text)), n),
        "sent_len_mean": mean,
        "sent_len_std": std,
        "burstiness": std / mean if mean else 0.0,
        "mattr": mattr([t.lower() for t in toks]),
        "avg_word_len": statistics.fmean(len(t) for t in toks) if toks else 0.0,
        "para_opener_repeat": 1 - len(set(openers)) / len(openers) if len(openers) > 1 else 0.0,
        "one_line_para_share": sum(len(sentences(p)) == 1 for p in paras) / len(paras) if paras else 0.0,
    }


# ---------- set metrics ----------
def _ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def distinct_n(texts: list[str], n: int) -> float:
    grams = [g for t in texts for g in _ngrams([w.lower() for w in words(t)], n)]
    return len(set(grams)) / len(grams) if grams else 0.0


def self_bleu_lite(texts: list[str], max_n: int = 4) -> float:
    """Mean share of each sample's 1..4-grams found in any other sample. 1 = all samples alike."""
    toks = [[w.lower() for w in words(t)] for t in texts]
    if len(toks) < 2:
        return 0.0
    scores = []
    for i, mine in enumerate(toks):
        per_n = []
        for n in range(1, max_n + 1):
            grams = _ngrams(mine, n)
            if not grams:
                continue
            ref = {g for j, other in enumerate(toks) if j != i for g in _ngrams(other, n)}
            per_n.append(sum(g in ref for g in grams) / len(grams))
        if per_n:
            scores.append(statistics.fmean(per_n))
    return statistics.fmean(scores) if scores else 0.0


# ---------- gates ----------
def _numbers(text: str) -> set[str]:
    return {x.replace(",", "") for x in NUMBER.findall(text)}


def _names(text: str) -> set[str]:
    """Capitalised words that are not sentence-initial (cheap proper-noun proxy)."""
    out = set()
    for s in sentences(text):
        for w in words(s)[1:]:
            w = re.sub(r"'s$", "", w)
            if w[0].isupper() and w.lower() not in PRONOUN_I:
                out.add(w.lower())
    return out


ATTRIB = re.compile(r"\b(said|says|told|according to|explained|added|noted|recalled|stated)\b", re.I)
QUOTE = re.compile(r"[\"\u201c]([^\"\u201d]{12,})[\"\u201d]")


def attributions(text: str) -> dict:
    """Reported speech: speech verbs and quoted spans of 4+ words."""
    text = _norm(text)
    quotes = [q.strip().lower() for q in QUOTE.findall(text) if len(q.split()) >= 4]
    return {"verbs": len(ATTRIB.findall(text)), "quotes": quotes}


def faithfulness(source: str, output: str) -> dict:
    """Kept vs added numbers and names. Any added number or name = hard fail (invented fact)."""
    source, output = _norm(source), _norm(output)
    src_nums, out_nums = _numbers(source), _numbers(output)
    src_words = {re.sub(r"'s$", "", w.lower()) for w in words(source)}
    src_names, out_names = _names(source), _names(output)
    out_words = {re.sub(r"'s$", "", w.lower()) for w in words(output)}
    nums_added = sorted(out_nums - src_nums)
    names_added = sorted(n for n in out_names if n not in src_words)
    sa, oa = attributions(source), attributions(output)
    src_low = source.lower()
    quotes_added = [q for q in oa["quotes"] if q not in src_low]
    attribution_added = oa["verbs"] > sa["verbs"]
    return {
        "numbers_kept": len(src_nums & out_nums) / len(src_nums) if src_nums else 1.0,
        "names_kept": len(src_names & out_words) / len(src_names) if src_names else 1.0,
        "numbers_dropped": sorted(src_nums - out_nums),
        "names_dropped": sorted(src_names - out_words),
        "numbers_added": nums_added,
        "names_added": names_added,
        "quotes_added": quotes_added,
        "attribution_added": attribution_added,
        "hard_fail": bool(nums_added or names_added or quotes_added or attribution_added),
    }


_LT = None


def _lt_tool():
    """LanguageTool instance, or None if the package / Java server is missing."""
    global _LT
    if _LT is None:
        try:
            import language_tool_python  # type: ignore
            _LT = language_tool_python.LanguageTool("en-US")
        except Exception:  # missing package, Java, or download: grammar is optional
            _LT = False
    return _LT or None


def grammar(text: str) -> float | None:
    """LanguageTool matches per 100 words, or None when LanguageTool is unavailable."""
    tool = _lt_tool()
    if tool is None:
        return None
    return _per100(len(tool.check(text)), len(words(text)))


# ---------- human band ----------
def percentile(values: list[float], pct: float) -> float:
    vals = sorted(values)
    if not vals:
        raise ValueError("percentile of empty list")
    k = (len(vals) - 1) * pct / 100
    lo = int(k)
    hi = min(lo + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)


def read_field(path: str, field: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if line.strip():
                row = json.loads(line)
                if isinstance(row.get(field), str) and row[field].strip():
                    rows.append(row | {"_line": i})
    return rows


def band_from_metrics(ms: list[dict], lo: float = 10, hi: float = 90) -> dict:
    keys = ms[0].keys() if ms else []
    return {"_n": len(ms), "pct": [lo, hi],
            "metrics": {k: [percentile([m[k] for m in ms], lo), percentile([m[k] for m in ms], hi)] for k in keys}}


def human_band(corpus_jsonl: str, field: str = "human", lo: float = 10, hi: float = 90) -> dict:
    """10th-90th percentile of every per-text metric over a human reference set."""
    band = band_from_metrics([text_metrics(r[field]) for r in read_field(corpus_jsonl, field)], lo, hi)
    return band | {"field": field, "source": os.path.basename(corpus_jsonl)}


def in_band(metrics: dict, band: dict) -> dict:
    """Per metric: value, lo, hi, ok, side ('low' / 'high' / None). No combined verdict on purpose."""
    out = {}
    for k, (lo, hi) in band["metrics"].items():
        v = metrics.get(k)
        if v is None:
            continue
        side = "low" if v < lo else "high" if v > hi else None
        out[k] = {"value": v, "lo": lo, "hi": hi, "ok": side is None, "side": side}
    return out


# ---------- CLI ----------
def score_file(path: str, field: str, source_field: str | None = None,
               band: dict | None = None, use_grammar: bool = False) -> dict:
    rows = read_field(path, field)
    texts = [r[field] for r in rows]
    out_rows = []
    for r, t in zip(rows, texts):
        row = {"line": r["_line"], "metrics": text_metrics(t), "stock_hits": stock_hits(t)}
        if source_field and isinstance(r.get(source_field), str):
            row["faithfulness"] = faithfulness(r[source_field], t)
        if use_grammar:
            row["grammar"] = grammar(t)
        if band:
            row["in_band"] = {k: v["ok"] for k, v in in_band(row["metrics"], band).items()}
        out_rows.append(row)
    ms = [r["metrics"] for r in out_rows]
    summary = {
        "n": len(out_rows),
        "mean": {k: statistics.fmean(m[k] for m in ms) for k in ms[0]} if ms else {},
        "distinct_1": distinct_n(texts, 1),
        "distinct_2": distinct_n(texts, 2),
        "self_bleu_lite": self_bleu_lite(texts),
    }
    if source_field:
        summary["faith_hard_fails"] = sum(r.get("faithfulness", {}).get("hard_fail", False) for r in out_rows)
    if band and out_rows:
        summary["in_band_share"] = {k: statistics.fmean(r["in_band"][k] for r in out_rows)
                                    for k in out_rows[0]["in_band"]}
    return {"field": field, "rows": out_rows, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="HumanLM tell metrics")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score", help="per-row metrics + summary JSON")
    s.add_argument("file")
    s.add_argument("--field", required=True)
    s.add_argument("--source-field", help="compare against this field for faithfulness")
    s.add_argument("--band", help="band JSON from the band command")
    s.add_argument("--grammar", action="store_true", help="run LanguageTool if installed (slow)")
    b = sub.add_parser("band", help="human reference band JSON")
    b.add_argument("file")
    b.add_argument("--field", default="human")
    b.add_argument("--lo", type=float, default=10)
    b.add_argument("--hi", type=float, default=90)
    a = ap.parse_args(argv)
    if a.cmd == "band":
        res = human_band(a.file, a.field, a.lo, a.hi)
    else:
        band = json.load(open(a.band, encoding="utf-8")) if a.band else None
        res = score_file(a.file, a.field, a.source_field, band, a.grammar)
    json.dump(res, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
