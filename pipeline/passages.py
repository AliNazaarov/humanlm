"""Cut raw Common Pile docs into self-contained 80-300 word prose passages.

Modern = created before 2021-07-01 (pre GPT-3 text spreading on the web).
Old = public-domain books (Gutenberg). Output keeps source, licence, url, date for the data card.
"""
import glob, gzip, json, re, sys, random
from datetime import datetime

random.seed(7)
CUTOFF = datetime(2021, 7, 1)
OUT = sys.argv[1] if len(sys.argv) > 1 else "/data/passages"

def parse_date(s):
    if not s:
        return None
    s = str(s).replace("Published on ", "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(datetime.now().strftime(fmt))] if "%f" not in fmt else s, fmt)
        except ValueError:
            pass
    m = re.search(r"(19|20)\d\d", s)
    return datetime(int(m.group(0)), 1, 1) if m else None

def iter_docs(name):
    files = sorted(glob.glob(f"/data/raw/{name}/**/*.json.gz", recursive=True))
    files += sorted(glob.glob(f"/data/raw/{name}/**/*.jsonl.gz", recursive=True))
    if files:
        for f in files:
            with gzip.open(f, "rt", errors="ignore") as fh:
                for line in fh:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        return
    import pyarrow.parquet as pq
    for f in sorted(glob.glob(f"/data/raw/{name}/**/*.parquet", recursive=True)):
        for batch in pq.ParquetFile(f).iter_batches(batch_size=2000):
            yield from batch.to_pylist()

BAD = re.compile(r"(cookie|subscribe|click here|all rights reserved|copyright|login|sign up|terms of use|javascript|©|http|www\.|@|\|)", re.I)
SENT = re.compile(r"[^.!?]+[.!?]")

def good_para(p):
    w = p.split()
    if not 80 <= len(w) <= 300:
        return False
    if BAD.search(p):
        return False
    sents = SENT.findall(p)
    if len(sents) < 3:
        return False
    letters = sum(c.isalpha() for c in p)
    if letters / max(len(p), 1) < 0.72:
        return False
    if p.count("\n") > 2 or p.isupper():
        return False
    return True

STEP = re.compile(r"^(\d+[.)]?|step \d+|[-*•])\s", re.I)

def paras(text, kind="old"):
    if kind == "old":
        for block in re.split(r"\n\s*\n", text):
            block = re.sub(r"\s*\n\s*", " ", block).strip()
            if good_para(block):
                yield block
        return
    # web/news: keep only real prose lines (>= 12 words, not steps), then group neighbours into passages
    lines = [l.strip() for l in re.split(r"\n+", text)]
    group = []
    for l in lines + [""]:
        if len(l.split()) >= 12 and not STEP.match(l) and l[-1:] in ".!?\"'”’)":
            group.append(l)
            if len(" ".join(group).split()) >= 80:
                cand = " ".join(group)
                if good_para(cand):
                    yield cand
                group = []
        else:
            group = []

def meta(d):
    m = d.get("metadata")
    if isinstance(m, str):
        try:
            import ast
            m = ast.literal_eval(m)
        except Exception:
            m = {}
    return m or {}

def run(name, kind, cap, per_doc):
    out = open(f"{OUT}/{name}.jsonl", "w")
    n = docs = 0
    for d in iter_docs(name):
        m = meta(d)
        created = parse_date(d.get("created") or d.get("date"))
        if kind == "modern" and (created is None or created >= CUTOFF):
            continue
        docs += 1
        ps = list(paras(d.get("text", ""), kind))
        if kind == "old":  # skip front matter / licence boilerplate in books
            ps = ps[3:-3]
        random.shuffle(ps)
        for p in ps[:per_doc]:
            out.write(json.dumps({"text": p, "source": name, "kind": kind,
                                  "licence": m.get("license", "Public Domain" if kind == "old" else "see source"),
                                  "url": m.get("url", ""), "title": m.get("title", ""),
                                  "created": created.isoformat() if created else None,
                                  "doc_id": d.get("id")}) + "\n")
            n += 1
        if n >= cap:
            break
    out.close()
    print(name, "docs", docs, "passages", n, flush=True)

if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    plan = [("news_filtered", "modern", 40000, 6), ("foodista_filtered", "modern", 20000, 3),
            ("public_domain_review_filtered", "modern", 5000, 6), ("cccc_filtered", "modern", 80000, 3),
            ("project_gutenberg_filtered", "old", 60000, 8)]
    only = set(sys.argv[2:])
    for name, kind, cap, per in plan:
        if only and name not in only:
            continue
        run(name, kind, cap, per)
