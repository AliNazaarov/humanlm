"""Deterministic cleanup of the 'punchy' tell readers named (no model calls; can only delete repetition).

Per paragraph:
  (a) drop a sentence of <= 4 words whose content words / numbers all already appear in the previous sentence
      ("In testing, it culled 3,000 photos in 6 minutes. Six minutes." -> drops "Six minutes.");
  (b) drop a sentence that repeats the previous one (case/punctuation-insensitive): "Click, compare, delete." x2.
The edit is kept only if hackathon/harness/gates.check still passes; otherwise the original output is kept.
  python3 hackathon/harness/dedupe_fragments.py EVAL.jsonl IN_RUN.jsonl OUT_RUN.jsonl --name NAME
"""
import argparse, json, os, re, sys, time

sys.path.insert(0, os.path.dirname(__file__))
import gates  # noqa: E402

NUMW = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10", "twelve": "12", "twenty": "20", "hundred": "100"}
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "it", "its", "it's", "is", "are", "was", "just",
        "that", "this", "with", "you", "your", "we", "our", "all", "so", "now", "no", "not", "more", "less"}
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“])")


def toks(s):
    out = set()
    for w in re.findall(r"[A-Za-z0-9$€£%,.']+", s.lower()):
        w = w.strip(".,'")
        w = NUMW.get(w, w).replace(",", "")
        if w and w not in STOP:
            out.add(w)
    return out


def clean_para(p):
    sents = SPLIT.split(p.strip())
    kept, dropped = [], []
    for s in sents:
        prev = kept[-1] if kept else None
        norm = re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
        if prev is not None:
            pnorm = re.sub(r"[^a-z0-9 ]", "", prev.lower()).strip()
            words = re.findall(r"\w+", s)
            if norm and norm == pnorm:
                dropped.append(s); continue
            if len(words) <= 4 and toks(s) and toks(s) <= toks(prev):
                dropped.append(s); continue
        kept.append(s)
    return " ".join(kept), dropped


def clean(text):
    paras = re.split(r"(\n\s*\n)", text)
    out, dropped = [], []
    for chunk in paras:
        if chunk.strip() and not re.fullmatch(r"\n\s*\n", chunk):
            c, d = clean_para(chunk); out.append(c); dropped += d
        else:
            out.append(chunk)
    return "".join(out), dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eval"); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--name", required=True)
    a = ap.parse_args()
    drafts = {json.loads(l)["id"]: json.loads(l)["ai_draft"] for l in open(a.eval)}
    rows, edited, reverted = [], 0, 0
    for l in open(a.inp):
        r = json.loads(l); d = drafts.get(r["id"], ""); new, dropped = clean(r.get("output") or "")
        if dropped:
            g = gates.check(d, new)
            if g["pass"] or not r["gates"]["pass"]:
                r = {**r, "output": new, "gates": {k: v for k, v in g.items() if k != "problems"}}; edited += 1
            else:
                reverted += 1; dropped = []
        r = {**r, "system": a.name, "post_edit": {"rule": "dedupe_fragments", "dropped": dropped}}
        rows.append(r)
    with open(a.out, "w") as o:
        for r in rows:
            o.write(json.dumps(r) + "\n")
    suffix = "_heldout" if "heldout" in os.path.basename(a.eval) else "_real" if "real" in os.path.basename(a.eval) else ""
    man = {"system": a.name, "provider": "post-edit", "source_run": a.inp, "rule": __doc__.splitlines()[0], "rows": len(rows),
           "edited": edited, "reverted_gate_fail": reverted, "pass_rate": sum(r["gates"]["pass"] for r in rows) / len(rows),
           "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    json.dump(man, open(os.path.join(gates.ROOT, f"hackathon/runs/{a.name}{suffix}.json"), "w"), indent=1)
    print(json.dumps(man))


if __name__ == "__main__":
    main()
