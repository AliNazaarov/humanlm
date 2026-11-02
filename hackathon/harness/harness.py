"""Agentic rewrite harness: draft -> verify with gates.py -> targeted revision (max N loops) -> keep the best.

Works with any OpenAI-compatible chat endpoint (Fireworks by default) or Anthropic.
  python3 hackathon/harness/harness.py EVAL.jsonl OUT.jsonl --model MODEL --system-name NAME
      [--provider fireworks|anthropic|openai] [--loops 3] [--prompt-file P] [--in-price USD_PER_M] [--out-price USD_PER_M]
      [--concurrency 4] [--limit N]
--loops 0 is a single plain call (the non-harness row for the same model).
Writes the shared run schema plus `loops_used` and `gates`, and a manifest in hackathon/runs/<system>.json.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import gates  # noqa: E402

ROOT = gates.ROOT
SYSTEM = ("Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, "
          "correct grammar. Keep every fact, name and number. Add nothing.")
TEMP, TOP_P, MAX_TOK = 0.7, 0.9, 400


def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def post(url, headers, body, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), {**headers, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504, 529) and i < tries - 1:
                time.sleep(2 ** i); continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 ** i); continue
            raise


def chat(provider, model, system, msgs):
    """One call. Returns (text, prompt_tokens, completion_tokens)."""
    if provider == "anthropic":
        r = post("https://api.anthropic.com/v1/messages",
                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                 {"model": model, "system": system, "messages": msgs, "max_tokens": MAX_TOK, "temperature": TEMP})
        text = "".join(b.get("text", "") for b in r["content"])
        return text, r["usage"]["input_tokens"], r["usage"]["output_tokens"]
    url, key = {"fireworks": ("https://api.fireworks.ai/inference/v1/chat/completions", "FIREWORKS_API_KEY"),
                "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY")}[provider]
    body = {"model": model, "messages": [{"role": "system", "content": system}] + msgs,
            "temperature": TEMP, "top_p": TOP_P, "max_tokens": MAX_TOK}
    if provider == "openai":
        body["max_completion_tokens"] = body.pop("max_tokens")
    r = post(url, {"Authorization": f"Bearer {os.environ[key]}"}, body)
    text = r["choices"][0]["message"]["content"] or ""
    u = r.get("usage", {})
    return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def clean(t):
    return re.sub(r"<think>.*?</think>", "", t, flags=re.S).strip()


def rewrite(item, a):
    draft = item["ai_draft"]
    msgs = [{"role": "user", "content": draft}]
    t0 = time.time(); pt = ct = 0; best = None
    for loop in range(a.loops + 1):
        text, p, c = chat(a.provider, a.model, a.system_prompt, msgs)
        pt += p; ct += c
        out = clean(text)
        g = gates.check(draft, out)
        cand = (g["n_fail"], -loop, out, g, loop)   # fewer failures wins; ties go to the later revision
        best = cand if best is None or cand[:2] < best[:2] else best
        if g["pass"] or loop == a.loops:
            break
        msgs += [{"role": "assistant", "content": out},
                 {"role": "user", "content": "Revise your rewrite. Fix only these problems and change nothing else:\n- "
                  + "\n- ".join(g["problems"]) + "\nReply with the full revised text only."}]
    _, _, out, g, loop = best
    return {"id": item["id"], "system": a.system_name, "output": out,
            "latency_ms": round((time.time() - t0) * 1000), "prompt_tokens": pt, "completion_tokens": ct,
            "cost_usd": round(pt * a.in_price / 1e6 + ct * a.out_price / 1e6, 6), "model": a.model,
            "loops_used": loop, "gates": {k: v for k, v in g.items() if k != "problems"}}


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("eval"); ap.add_argument("out")
    ap.add_argument("--model", required=True); ap.add_argument("--system-name", required=True)
    ap.add_argument("--provider", default="fireworks", choices=["fireworks", "anthropic", "openai"])
    ap.add_argument("--loops", type=int, default=3); ap.add_argument("--prompt-file")
    ap.add_argument("--in-price", type=float, default=0.0); ap.add_argument("--out-price", type=float, default=0.0)
    ap.add_argument("--concurrency", type=int, default=4); ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    a.system_prompt = open(a.prompt_file).read().strip() if a.prompt_file else SYSTEM
    items = [json.loads(l) for l in open(a.eval)][: a.limit]
    done = {json.loads(l)["id"] for l in open(a.out)} if os.path.exists(a.out) else set()
    todo = [it for it in items if it["id"] not in done]
    with open(a.out, "a") as o, cf.ThreadPoolExecutor(a.concurrency) as ex:
        for fut in cf.as_completed([ex.submit(rewrite, it, a) for it in todo]):
            row = fut.result()
            o.write(json.dumps(row) + "\n"); o.flush()
            print(f"{row['id']} pass={row['gates']['pass']} loops={row['loops_used']} {row['latency_ms']}ms", flush=True)
    rows = [json.loads(l) for l in open(a.out)]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(items), f"rows {len(ids)}, unique {len(set(ids))}, expected {len(items)}"
    assert all(r["output"] for r in rows), "empty output"
    os.makedirs(os.path.join(ROOT, "hackathon/runs"), exist_ok=True)
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    manifest = {"system": a.system_name, "provider": a.provider, "model": a.model, "loops": a.loops,
                "prompt_sha256": hashlib.sha256(a.system_prompt.encode()).hexdigest()[:16],
                "prompt_file": a.prompt_file, "temperature": TEMP, "top_p": TOP_P, "max_tokens": MAX_TOK,
                "prices_usd_per_m": [a.in_price, a.out_price], "eval": a.eval, "rows": len(rows),
                "pass_rate": sum(r["gates"]["pass"] for r in rows) / len(rows), "commit": commit,
                "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    json.dump(manifest, open(os.path.join(ROOT, f"hackathon/runs/{re.sub(r'[^A-Za-z0-9_.-]', '_', a.system_name)}.json"), "w"), indent=1)
    print("DONE", json.dumps(manifest))


if __name__ == "__main__":
    main()
