"""Reverse distillation: turn a human passage into the 'AI-polished' version a user would paste.

Pair = (ai_draft -> human). The model learns to undo AI polish. An open Apache-2.0 model
(Qwen3.5) writes the AI side, so no frontier-API terms apply. Pairs that drop a fact are thrown out,
so the model never learns to add facts that were not in its input.
Usage: python3 gen_pairs.py SHARD.jsonl OUT.jsonl [server_url] [model_tag]
"""
import json, re, sys, os, hashlib, time, random
import requests

SHARD, OUT = sys.argv[1], sys.argv[2]
URL = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8080"
TAG = sys.argv[4] if len(sys.argv) > 4 else "qwen3.5"

TEMPLATES = {
    "polish": "Rewrite the following text so it reads as polished, professional and engaging. Keep every fact, name and number.",
    "linkedin": "Turn the following text into an engaging LinkedIn post. Keep every fact, name and number.",
    "marketing": "Rewrite the following text as compelling marketing copy for a website. Keep every fact, name and number.",
    "blog": "Rewrite the following text as a clear, well-structured blog paragraph. Keep every fact, name and number.",
    "email": "Rewrite the following text as a friendly, professional email to a customer. Keep every fact, name and number.",
}
NUM = re.compile(r"\b\d[\d,.:%]*\b")
NAME = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b")

def facts(t):
    return set(NUM.findall(t)) | set(NAME.findall(t))

ATTRIB = re.compile(r"\b(said|says|told|according to|explained|added|noted|recalled|stated)\b", re.I)
QUOTE = re.compile(r"[\"\u201c]([^\"\u201d]{12,})[\"\u201d]")

def attribution_problem(human, ai):
    """Reporter voice teaches the model to invent quotes: skip heavy reported speech,
    and any pair whose human side has speech or quotes the AI side lacks."""
    hv, av = len(ATTRIB.findall(human)), len(ATTRIB.findall(ai))
    if hv >= 2:
        return "reported_speech"
    if hv > av:
        return "attribution_lost"
    ai_low = ai.lower()
    if any(len(q.split()) >= 4 and q.strip().lower() not in ai_low for q in QUOTE.findall(human)):
        return "quote_lost"
    return None

def keep(human, ai):
    if not ai or ai.lower().startswith(("here is", "here's", "sure", "certainly")):
        return False, "preamble"
    r = len(ai.split()) / max(len(human.split()), 1)
    if not 0.6 <= r <= 1.8:
        return False, f"len_ratio {r:.2f}"
    nums = set(NUM.findall(human))
    if any(n not in ai for n in nums):
        return False, "number_lost"
    if set(NUM.findall(ai)) - nums:
        return False, "number_added"
    names = set(NAME.findall(human))
    if names:
        kept = sum(1 for x in names if x in ai) / len(names)
        if kept < 0.75:
            return False, f"names_kept {kept:.2f}"
    a = attribution_problem(human, ai)
    if a:
        return False, a
    return True, "ok"

UNITS = re.compile(r"\b(cups?|tbsp|tsp|teaspoons?|tablespoons?|grams?|oz|ounces?|ml|lbs?|pounds?|diced|chopped|minced)\b", re.I)

def skip_passage(t):
    w = t.split()
    if len(UNITS.findall(t)) >= 4:
        return "recipe_list"
    if sum(c.isdigit() or c in "¼½¾⅓⅔" for c in t) / max(len(w), 1) > 0.15:
        return "numeric_list"
    return None

def gen(text, tmpl):
    body = {"messages": [{"role": "user", "content": f"{TEMPLATES[tmpl]} Output only the rewritten text.\n\n{text}"}],
            "temperature": 0.7, "top_p": 0.9, "max_tokens": 700,
            "chat_template_kwargs": {"enable_thinking": False}}
    r = requests.post(f"{URL}/v1/chat/completions", json=body, timeout=600)
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()

done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        done.add(json.loads(l)["pid"])
stats = {"kept": 0, "dropped": 0}
rej = open(OUT + ".rejected", "a")
with open(OUT, "a") as out:
    for i, line in enumerate(open(SHARD)):
        p = json.loads(line)
        pid = hashlib.md5(p["text"].encode()).hexdigest()[:12]
        if pid in done:
            continue
        if skip_passage(p["text"]):
            continue
        tmpl = random.Random(pid).choice(list(TEMPLATES))
        t0 = time.time()
        try:
            ai = gen(p["text"], tmpl)
        except Exception as e:
            print("err", e, flush=True); time.sleep(5); continue
        ok, why = keep(p["text"], ai)
        rec = {"pid": pid, "ai_draft": ai, "human": p["text"], "template": tmpl, "gen_model": TAG,
               "source": p["source"], "kind": p["kind"], "licence": p["licence"], "url": p.get("url", ""),
               "created": p.get("created"), "secs": round(time.time() - t0, 1)}
        if ok:
            out.write(json.dumps(rec) + "\n"); out.flush(); stats["kept"] += 1
        else:
            rec["why"] = why; rej.write(json.dumps(rec) + "\n"); rej.flush(); stats["dropped"] += 1
        if (stats["kept"] + stats["dropped"]) % 25 == 0:
            print(i, stats, f"{time.time()-t0:.1f}s/last", flush=True)
print("FINISHED", stats, flush=True)
