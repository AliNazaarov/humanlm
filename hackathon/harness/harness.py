"""Agentic rewrite harness: draft -> verify with gates.py -> targeted revision (max N loops) -> keep the best.

Works with any OpenAI-compatible chat endpoint (Fireworks by default, OpenAI, Gemini) or Anthropic.
Keys: ~/.config/humanlm/keys.env (or $HUMANLM_KEYS), then repo .env.
  python3 hackathon/harness/harness.py EVAL.jsonl OUT.jsonl --model MODEL --system-name NAME
      [--provider fireworks|anthropic|openai|gemini|fwsampler] [--loops 3] [--prompt-file P] [--in-price USD_PER_M] [--out-price USD_PER_M]
      [--concurrency 4] [--limit N]
--loops 0 is a single plain call (the non-harness row for the same model).
Writes the shared run schema plus `loops_used` and `gates`, and a manifest in hackathon/runs/<system>.json.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, random, re, ssl, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import gates  # noqa: E402

ROOT = gates.ROOT
SYSTEM = ("Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, "
          "correct grammar. Keep every fact, name and number. Add nothing.")
TEMP, TOP_P, MAX_TOK = 0.7, 0.9, 400
STYLE_ASK = ("Now edit it the way a senior copywriter would: make it sound like one specific person talking to "
             "one reader. Vary sentence length, cut filler and generic words, prefer concrete verbs. Keep every fact, "
             "name and number exactly, add nothing, keep about the same length. Reply with the full text only.")
STYLE_ASK_CALM = ("Now edit it the way a senior copywriter would. Write in calm, complete sentences. Remove dramatic "
                  "fragments, one-word sentences, repeated phrases used for effect, staccato lists and punchy one-line "
                  "closers. Remove marketing cliches and hype. Make it sound like one thoughtful person writing to one "
                  "reader. Keep every fact, name and number exactly, add nothing, keep about the same length. Reply with "
                  "the full text only.")
STYLE_ASK_CLICHE = ("Now edit it the way a senior copywriter would. Remove every marketing cliche and hype phrase, even if "
                    "it was in the draft (for example: unlock, seamless, elevate, empower, game-changer, take it to the next "
                    "level, we can't wait, mission is simple, say goodbye to, ditch the). Say the plain thing instead. Make it "
                    "sound like one specific person talking to one reader. Keep every fact, name and number exactly, add "
                    "nothing, keep about the same length. Reply with the full text only.")


def load_env():
    """Keys from HUMANLM_KEYS (default ~/.config/humanlm/keys.env, outside the repo), then repo .env. Empty values are skipped."""
    for p in (os.environ.get("HUMANLM_KEYS", os.path.expanduser("~/.config/humanlm/keys.env")),
              os.path.expanduser("~/.config/humanlm/gemini.env"), os.path.join(ROOT, ".env")):
        if os.path.exists(p):
            for line in open(p):
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    if v:
                        os.environ.setdefault(k, v)


def _ssl_ctx():
    """Python.org builds on macOS ship without root certs; fall back to certifi or the system bundle."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem") if os.path.exists("/etc/ssl/cert.pem") else None


CTX = _ssl_ctx()


def post(url, headers, body, tries=10):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), {**headers, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504, 529) and i < tries - 1:
                time.sleep(min(60, 2 ** i) + random.random() * 3); continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError):
            if i < tries - 1:
                time.sleep(2 ** i); continue
            raise


_FWS = {}
_FWS_LOCK = __import__("threading").Lock()


def _fw_sampler(model):
    """Fireworks serverless-training sampler bound to a saved LoRA snapshot (no deployment).
    Needs the fireworks-ai[training] SDK + fw-ai/cookbook renderers, so run the harness with that venv."""
    with _FWS_LOCK:
        if model not in _FWS:
            from fireworks.training.sdk import FiretitanServiceClient
            from training.renderer import get_renderer
            from training.renderer.model_info import get_recommended_renderer_name
            from training.renderer.tokenizer import get_tokenizer
            tok_name = os.environ.get("HL_TOKENIZER", "zai-org/GLM-5.3-Flash")
            tok = get_tokenizer(tok_name)
            rname = os.environ.get("HL_RENDERER") or ("glm53_flash" if "GLM-5.3-Flash" in tok_name else get_recommended_renderer_name(tok_name))
            renderer = get_renderer(rname, tok)   # same renderer the SFT recipe trained with
            service = FiretitanServiceClient(api_key=os.environ["FIREWORKS_API_KEY"],
                                             base_url="https://api.fireworks.ai/training/v1/serverless")
            kw = {"base_model": model} if model.startswith("accounts/fireworks/models/") else {"model_path": model}
            _FWS[model] = (service.create_sampling_client(tokenizer=tok, **kw), renderer)
        return _FWS[model]


def sampler_tokenizer_decode(renderer, toks):
    return renderer.tokenizer.decode(toks)


def decoding(provider, model, effort):
    """What each provider accepts. Recorded in every row and the manifest; differences are disclosed in the README."""
    if provider == "anthropic" and model.startswith("claude-opus-5"):
        # Opus 5.x rejects temperature/top_p and disabling thinking (400): send none, adaptive thinking, low effort.
        return {"max_tokens": 1500, "thinking": {"type": "adaptive"}, "output_config": {"effort": "low"}}
    if provider == "anthropic":
        return {"max_tokens": MAX_TOK, "temperature": TEMP}
    if provider == "openai":
        # GPT-6.x reasoning models accept only the default temperature.
        return {"max_completion_tokens": 1500, "reasoning_effort": effort}
    if provider == "fwsampler":
        return {"max_tokens": 1500, "temperature": TEMP, "top_p": TOP_P}
    if provider == "gemini":
        return {"max_tokens": 4096, "temperature": TEMP, "top_p": TOP_P, "reasoning_effort": effort}
    d = {"max_tokens": 1500, "temperature": TEMP, "top_p": TOP_P}
    if effort != "omit":
        d["reasoning_effort"] = effort   # GLM-5.3 is thinking-only; "low" keeps it fast and leaves room for the answer
    return d


def chat(provider, model, system, msgs, dec):
    """One call. Returns (text, prompt_tokens, completion_tokens)."""
    if provider == "anthropic":
        r = post("https://api.anthropic.com/v1/messages",
                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                 {"model": model, "system": system, "messages": msgs, **dec})
        text = "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text")
        return text, r["usage"]["input_tokens"], r["usage"]["output_tokens"]
    if provider == "fwsampler":
        from fireworks.training.sdk import SamplingParams
        from training.renderer import get_text_content
        sampler, renderer = _fw_sampler(model)
        # Prefill "</think>": GLM-5.3 non-thinking mode, the same "<think></think>{answer}" shape the SFT data trained on.
        prompt = renderer.build_generation_prompt([{"role": "system", "content": system}] + msgs, prefill="</think>")
        res = sampler.sample(prompt=prompt, num_samples=1, sampling_params=SamplingParams(
            max_tokens=dec["max_tokens"], temperature=dec["temperature"], top_p=dec["top_p"],
            stop=renderer.get_stop_sequences())).result()
        toks = list(res.sequences[0].tokens)
        text = __import__("re").sub(r"<\|[a-z_]+\|>", "", sampler_tokenizer_decode(renderer, toks))
        return text.split("</think>")[-1].strip(), prompt.length, len(toks)
    url, key = {"fireworks": ("https://api.fireworks.ai/inference/v1/chat/completions", "FIREWORKS_API_KEY"),
                "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
                "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY")}[provider]
    body = {"model": model, "messages": [{"role": "system", "content": system}] + msgs, **dec}
    if provider == "gemini" and os.environ.get("GEMINI_PAID_API_KEY"):
        key = "GEMINI_PAID_API_KEY"   # billing-enabled key for Gemini 4 Argon; the free key has no quota for it
    r = post(url, {"Authorization": f"Bearer {os.environ[key]}"}, body)
    text = r["choices"][0]["message"].get("content") or ""
    u = r.get("usage", {})
    return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


_RETR = None


def retrieve(draft, k):
    """k most similar TRAINING pairs (TF-IDF cosine on the AI draft) as few-shot examples. Never eval items."""
    global _RETR
    import math, collections
    tok = lambda t: re.findall(r"[a-z']+", t.lower())
    if _RETR is None:
        rows = [json.loads(l)["messages"] for l in open(os.path.join(ROOT, "hackathon/data/train.jsonl"))]
        docs = [(m[1]["content"], m[2]["content"]) for m in rows if 40 <= len(m[2]["content"].split()) <= 160]
        df = collections.Counter(w for d, _ in docs for w in set(tok(d)))
        n = len(docs)
        idf = {w: math.log(n / c) for w, c in df.items()}
        vecs = []
        for d, _ in docs:
            tf = collections.Counter(tok(d)); v = {w: c * idf[w] for w, c in tf.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            vecs.append({w: x / norm for w, x in v.items()})
        _RETR = (docs, vecs, idf)
    docs, vecs, idf = _RETR
    tf = collections.Counter(tok(draft)); q = {w: c * idf.get(w, 0.0) for w, c in tf.items()}
    qn = math.sqrt(sum(x * x for x in q.values())) or 1.0
    scores = sorted(((sum(q[w] * v.get(w, 0.0) for w in q) / qn, i) for i, v in enumerate(vecs)), reverse=True)[:k]
    return [docs[i] for _, i in scores]


def clean(t):
    return re.sub(r"<think>.*?</think>", "", t, flags=re.S).strip()


COPY_MAX = 0.9
COPY_ASK = ("This is almost a copy of the draft. Actually rewrite it in a human voice: change sentence structure "
            "and wording, keep every fact.")
JUDGE_ASK = ("Rate how much this marketing text sounds like a skilled human copywriter wrote it, not an AI. "
             "1 = obviously AI, 10 = indistinguishable from a skilled human. Judge voice, rhythm and word choice only. "
             "Reply with one integer from 1 to 10 and nothing else.\n\nTEXT:\n")


def copy_overlap(draft, out):
    """Word-bigram F1 between draft and output, the audit's near-copy measure (hackathon/audit/audit.py)."""
    import collections
    def bi(t):
        w = [x.lower() for x in gates.m.words(t)]
        return [tuple(w[i:i + 2]) for i in range(len(w) - 1)]
    da, ob = bi(draft), bi(out)
    if not da or not ob:
        return 0.0
    inter = sum((collections.Counter(da) & collections.Counter(ob)).values())
    if not inter:
        return 0.0
    p, r = inter / len(ob), inter / len(da)
    return 2 * p * r / (p + r)


CLAIM_ASK = ("You check rewrites for invented content. Compare the REWRITE with the DRAFT. List every claim, detail, "
             "example, reason, scenario or statement of fact in the REWRITE that is not stated in the DRAFT and not a "
             "direct restatement of it. Ignore pure wording and tone changes. Reply with JSON only: {\"added\": [\"short quote\", ...]}"
             " and an empty list if nothing was added.")


def claim_check(draft, out, a):
    """Open-model claim verifier (GLM-5.3). Returns (added_claims, pt, ct). Errors count as 'unchecked' (empty list)."""
    if not a.claim_check:
        return [], 0, 0
    dec = decoding("fireworks", a.claim_check, "low"); dec["temperature"] = 0.0
    msg = [{"role": "user", "content": f"{CLAIM_ASK}\n\nDRAFT:\n{draft}\n\nREWRITE:\n{out}"}]
    try:
        r, p, c = chat("fireworks", a.claim_check, "You are a strict fact checker.", msg, dec)
        mt = re.search(r"\{.*\}", clean(r), re.S)
        added = json.loads(mt.group(0)).get("added", []) if mt else []
        return [x for x in added if isinstance(x, str) and x.strip()][:6], p, c
    except Exception:
        return [], 0, 0


def one_pass(draft, a):
    """Draft -> verify -> targeted revise (max a.loops) -> optional style round. Returns (out, gates, loop, pt, ct, copy)."""
    shots = []
    for d, hm in (retrieve(draft, a.retrieve) if a.retrieve else []):
        shots += [{"role": "user", "content": d}, {"role": "assistant", "content": hm}]
    msgs = shots + [{"role": "user", "content": draft}]
    pt = ct = 0; best = None
    for loop in range(a.loops + 1):
        text, p, c = chat(a.provider, a.model, a.system_prompt, msgs, a.dec)
        pt += p; ct += c
        out = clean(text)
        g = gates.check(draft, out)
        cp = copy_overlap(draft, out)
        near = a.anti_copy and cp > COPY_MAX
        added = []
        if g["pass"] and not near:
            added, p, c = claim_check(draft, out, a); pt += p; ct += c
        cand = (g["n_fail"] + int(near) + int(bool(added)), -loop, out, g, loop, cp)   # fewer failures wins; ties go to the later revision
        best = cand if best is None or cand[:2] < best[:2] else best
        if (g["pass"] and not near and not added) or loop == a.loops:
            break
        problems = g["problems"] + ([COPY_ASK] if near else []) + (
            ["You added content that is not in the draft: " + "; ".join(f'"{x}"' for x in added) + ". Remove it."] if added else [])
        msgs += [{"role": "assistant", "content": out},
                 {"role": "user", "content": "Revise your rewrite. Fix only these problems and change nothing else:\n- "
                  + "\n- ".join(problems) + "\nReply with the full revised text only."}]
    _, _, out, g, loop, cp = best
    if a.style_round and g["pass"]:
        # One style pass: a skilled copywriter's edit for voice and rhythm. Kept only if every gate still passes.
        msgs2 = [{"role": "user", "content": draft}, {"role": "assistant", "content": out},
                 {"role": "user", "content": {"cliche": STYLE_ASK_CLICHE, "calm": STYLE_ASK_CALM}.get(a.style_round, STYLE_ASK)}]
        text, p, c = chat(a.provider, a.model, a.system_prompt, msgs2, a.dec)
        pt += p; ct += c
        out2 = clean(text); g2 = gates.check(draft, out2); cp2 = copy_overlap(draft, out2)
        added2 = []
        if g2["pass"] and not (a.anti_copy and cp2 > COPY_MAX):
            added2, p, c = claim_check(draft, out2, a); pt += p; ct += c
        if g2["pass"] and not (a.anti_copy and cp2 > COPY_MAX) and not added2:
            out, g, loop, cp = out2, g2, loop + 1, cp2
    return out, g, loop, pt, ct, cp


def judge_score(text, a):
    """Selection judge (GLM-5.3 by default, a different model from the eval judge). Returns (score, pt, ct)."""
    dec = decoding("fireworks", a.select_judge_model, "low")
    dec["temperature"] = 0.0
    msg = [{"role": "user", "content": JUDGE_ASK + text}]
    try:
        r, p, c = chat("fireworks", a.select_judge_model, "You are a strict senior copy editor.", msg, dec)
    except Exception:
        return None, 0, 0
    mt = re.search(r"\b(10|[1-9])\b", clean(r))
    return (int(mt.group(1)) if mt else None), p, c


def rewrite(item, a):
    draft = item["ai_draft"]
    t0 = time.time(); pt = ct = 0
    cands = []
    for _ in range(a.best_of):
        out, g, loop, p, c, cp = one_pass(draft, a)
        pt += p; ct += c
        cands.append({"out": out, "g": g, "loop": loop, "copy": cp})
    sel = {}
    if a.best_of > 1:
        ok = [x for x in cands if x["g"]["pass"] and not (a.anti_copy and x["copy"] > COPY_MAX)]
        jpt = jct = 0
        for x in ok:
            x["score"], p, c = judge_score(x["out"], a)
            jpt += p; jct += c
        if ok:
            pick = max(ok, key=lambda x: (x["score"] or 0, -x["copy"]))
        else:
            pick = min(cands, key=lambda x: (x["g"]["n_fail"] + int(a.anti_copy and x["copy"] > COPY_MAX), x["copy"]))
        sel = {"candidates": len(cands), "eligible": len(ok), "scores": [x.get("score") for x in cands],
               "picked": cands.index(pick), "judge_model": a.select_judge_model,
               "judge_prompt_tokens": jpt, "judge_completion_tokens": jct,
               "judge_cost_usd": round(jpt * a.judge_in_price / 1e6 + jct * a.judge_out_price / 1e6, 6)}
    else:
        pick = cands[0]
    out, g, loop, cp = pick["out"], pick["g"], pick["loop"], pick["copy"]
    row = {"id": item["id"], "system": a.system_name, "output": out,
           "latency_ms": round((time.time() - t0) * 1000), "prompt_tokens": pt, "completion_tokens": ct,
           "cost_usd": round(pt * a.in_price / 1e6 + ct * a.out_price / 1e6 + sel.get("judge_cost_usd", 0), 6),
           "model": a.model, "decoding": a.dec, "loops_used": loop,
           "gates": {k: v for k, v in g.items() if k != "problems"}}
    if a.anti_copy or a.best_of > 1:
        row["copy_overlap"] = round(cp, 4)
    if sel:
        row["selection"] = sel
    return row


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("eval"); ap.add_argument("out")
    ap.add_argument("--model", required=True); ap.add_argument("--system-name", required=True)
    ap.add_argument("--provider", default="fireworks", choices=["fireworks", "anthropic", "openai", "gemini", "fwsampler"])
    ap.add_argument("--loops", type=int, default=3); ap.add_argument("--prompt-file")
    ap.add_argument("--in-price", type=float, default=0.0); ap.add_argument("--out-price", type=float, default=0.0)
    ap.add_argument("--concurrency", type=int, default=4); ap.add_argument("--limit", type=int)
    ap.add_argument("--reasoning-effort", default="low", help="low|medium|high, or omit (not sent)")
    ap.add_argument("--claim-check", default=None, help="open model id that lists claims added vs the draft; non-empty -> revise")
    ap.add_argument("--retrieve", type=int, default=0, help="add k most similar training pairs (AI draft -> human original) as few-shot examples")
    ap.add_argument("--anti-copy", action="store_true", help="revise near-copies of the draft (word-bigram F1 > 0.9)")
    ap.add_argument("--best-of", type=int, default=1, help="run the whole pipeline N times, pick by --select-judge-model")
    ap.add_argument("--select-judge-model", default="accounts/fireworks/models/glm-5p3")
    ap.add_argument("--judge-in-price", type=float, default=0.0); ap.add_argument("--judge-out-price", type=float, default=0.0)
    ap.add_argument("--style-round", nargs="?", const="basic", default=None, choices=["basic", "cliche", "calm"],
                    help="after the gates pass, one copywriter style edit (basic or cliche), kept only if gates still pass")
    a = ap.parse_args()
    a.dec = decoding(a.provider, a.model, a.reasoning_effort)
    a.system_prompt = open(a.prompt_file).read().strip() if a.prompt_file else SYSTEM
    items = [json.loads(l) for l in open(a.eval)][: a.limit]
    done = {json.loads(l)["id"] for l in open(a.out)} if os.path.exists(a.out) else set()
    todo = [it for it in items if it["id"] not in done]
    with open(a.out, "a") as o, cf.ThreadPoolExecutor(a.concurrency) as ex:
        for fut in cf.as_completed([ex.submit(rewrite, it, a) for it in todo]):
            try:
                row = fut.result()
            except Exception as e:   # one item failing (e.g. rate limit) must not kill the run; re-run to resume it
                print(f"ITEM_FAILED {str(e)[:200]}", flush=True)
                continue
            o.write(json.dumps(row) + "\n"); o.flush()
            print(f"{row['id']} pass={row['gates']['pass']} loops={row['loops_used']} {row['latency_ms']}ms", flush=True)
    rows = [json.loads(l) for l in open(a.out)]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == len(items), f"rows {len(ids)}, unique {len(set(ids))}, expected {len(items)}"
    empty = [r["id"] for r in rows if not r["output"]]
    if empty:   # refusals/failures stay in the file and count as fails in scoring; the manifest records them
        print(f"WARNING: {len(empty)} empty outputs: {empty[:10]}", flush=True)
    os.makedirs(os.path.join(ROOT, "hackathon/runs"), exist_ok=True)
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    manifest = {"system": a.system_name, "provider": a.provider, "model": a.model, "loops": a.loops,
                "prompt_sha256": hashlib.sha256(a.system_prompt.encode()).hexdigest()[:16],
                "prompt_file": a.prompt_file, "decoding": a.dec, "style_round": a.style_round, "retrieve": a.retrieve, "claim_check": a.claim_check, "anti_copy": a.anti_copy, "best_of": a.best_of,
                "select_judge_model": a.select_judge_model if a.best_of > 1 else None,
                "prices_usd_per_m": [a.in_price, a.out_price], "eval": a.eval, "rows": len(rows),
                "pass_rate": sum(r["gates"]["pass"] for r in rows) / len(rows), "empty_outputs": [r["id"] for r in rows if not r["output"]], "commit": commit,
                "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    base = os.path.basename(a.eval)
    suffix = "_heldout" if "heldout" in base else "_real" if "real" in base else ""
    json.dump(manifest, open(os.path.join(ROOT, f"hackathon/runs/{re.sub(r'[^A-Za-z0-9_.-]', '_', a.system_name)}{suffix}.json"), "w"), indent=1)
    print("DONE", json.dumps(manifest))


if __name__ == "__main__":
    main()
