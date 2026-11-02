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


CLAIM_UNAVAILABLE = "(claim check unavailable"


def claim_check(draft, out, a):
    """Open-model claim verifier (GLM-5.3). Returns (added_claims, pt, ct).
    [] only when the check ran clean or --claim-check is off. If both attempts fail it returns a NON-empty
    placeholder starting with CLAIM_UNAVAILABLE, so an unchecked rewrite never counts as clean."""
    if not a.claim_check:
        return [], 0, 0
    dec = decoding("fireworks", a.claim_check, "low"); dec["temperature"] = 0.0
    msg = [{"role": "user", "content": f"{CLAIM_ASK}\n\nDRAFT:\n{draft}\n\nREWRITE:\n{out}"}]
    for attempt in range(2):   # retry once; an unchecked rewrite must not count as clean
        try:
            r, p, c = chat("fireworks", a.claim_check, "You are a strict fact checker.", msg, dec)
            mt = re.search(r"\{.*\}", clean(r), re.S)
            if not mt:
                continue
            added = json.loads(mt.group(0)).get("added", [])
            return [x for x in added if isinstance(x, str) and x.strip()][:6], p, c
        except Exception:
            continue
    return [CLAIM_UNAVAILABLE + ": re-verify this rewrite against the draft and remove anything not in it)"], 0, 0


# --style-round lint (O3q): deterministic, located style feedback after the basic style round.
# Patterns are generic copy patterns seen in the drafts and our own outputs. Disclosure: they were found while reading
# eval-judge reasons, but no judge score is used here; dev selection is GLM-5.3 only.
LINT_MAX, LINT_ROUNDS = 6, 2
LINT_SLOGANS = [r"\bis everything\b", r"\byou asked,? we\b", r"\b(?:it is|it's) that simple\b", r"\bhere we are\b",
                r"\bcould be next\b", r"\bthe future (?:of \w+ )?is here\b", r"\? (?:Absolutely|100%)"]
LINT_SPLIT = r"\b(is not|isn't|not just)\b[^.?!]{0,50}[.]\s*(It|This|That)(?:'s| is)\b"
LINT_VALUES = r"\b(believ\w*|priorit\w*|mission\w*|passion\w*|excit\w*|humbl\w*|journey\w*|working hard)\b"
LINT_VAGUE = r"\b(helps? you|handles? the rest|stands? out|takes? care of|more than ever)\b"
LINT_LABEL = r"^\s*([A-Z][A-Za-z0-9&/'-]*(?: [A-Za-z0-9&/'-]+){0,2}):\s"
LINT_STOP = set("a an the and or but of to in on for with at by from is are was were be been it its it's this that "
                "these those we our you your they their i my he she his her as so if then than not no do does did "
                "have has had will would can could just very".split())


def _lint_norm(t):
    """Lowercase alphanumeric words; em/en dashes, '!' and curly quotes do not block a match."""
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(re.findall(r"[a-z0-9$%']+", t.lower().replace("—", " ").replace("–", " ").replace("!", " ")))


def _lint_sents(text):
    """[(line_index, sentence)] for every sentence that ends in . ? or ! (sign-offs and names are not sentences)."""
    out = []
    for i, line in enumerate(text.splitlines()):
        for s in re.split(r"(?<=[.?!])\s+", line.strip()):
            s = s.strip()
            if s and s[-1] in ".?!":
                out.append((i, s))
    return out


def _lint_toks(s):
    return [w for w in re.findall(r"[a-z0-9$%']+", s.lower().replace("’", "'"))]


def _lint_span(text, ms, me):
    """Expand a match to the sentence(s) it touches."""
    left = max(text.rfind(c, 0, ms) for c in ".?!\n") + 1
    rights = [j for j in (text.find(c, me) for c in ".?!\n") if j != -1]
    right = min(rights) + 1 if rights else len(text)
    return " ".join(text[left:right].split())


def safe_trim(text):
    """Deterministic trim that only deletes repeats: (a) a sentence of <= 4 words ending in '.' whose numbers and
    content words all appear in the sentence before it ('Six minutes.'); (b) a run of 2+ words repeated twice in a row."""
    def content(s):
        return {w for w in _lint_toks(s) if w not in LINT_STOP}
    lines = text.split("\n"); prev = None; out_lines = []
    for line in lines:
        parts = re.split(r"(?<=[.?!])(\s+)", line)
        keep = []
        for k in range(0, len(parts), 2):
            s = parts[k]; sep = parts[k + 1] if k + 1 < len(parts) else ""
            st = s.strip()
            if not st:
                keep.append(s + sep); continue
            c = content(st)
            if (prev is not None and st.endswith(".") and len(st.split()) <= 4 and c and c <= content(prev)):
                continue
            keep.append(s + sep); prev = st
        new = "".join(keep).rstrip()
        if line.strip() and not new.strip():
            continue   # the whole line was a dropped repeat
        out_lines.append(new if line.strip() else line)
    t = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
    return re.sub(r"\b(\w+(?: \w+){1,5}) \1\b", r"\1", t, flags=re.I)


def style_lint(draft, out, cap=LINT_MAX):
    """Located style problems in `out` (pure, no network). Never changes gates. Returns problem lines, capped at `cap`
    (cap=None returns all; the accept rule counts all)."""
    d_norm = _lint_norm(draft)
    in_draft = lambda s: bool(_lint_norm(s)) and _lint_norm(s) in d_norm
    o = out.replace("’", "'").replace("‘", "'")
    hits = []
    for pat in LINT_SLOGANS + [LINT_SPLIT]:
        for mt in re.finditer(pat, o, re.I):
            hits.append(f"Replace this tagline with the plain claim: {_lint_span(o, mt.start(), mt.end())}")
    lines = o.splitlines()
    nonempty = [i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("#")]
    last = nonempty[-1] if nonempty and len(lines[nonempty[-1]].split()) <= 15 else -1   # a short final line is the CTA
    excluded = lambda i: (re.match(LINT_LABEL, lines[i]) or lines[i].strip().startswith("#") or i == last)
    sents = _lint_sents(o)
    run = []
    for i, s in sents + [(-1, "")]:
        if s and not excluded(i) and len(s.split()) <= 6 and not in_draft(s):
            run.append(s); continue
        if len(run) >= 2:
            hits.append(f"Join these into one complete sentence: {' '.join(run)}")
        run = []
    body = [(i, s) for i, s in sents if not lines[i].strip().startswith("#")]
    for n, (i, s) in enumerate(body):
        q = re.sub(LINT_LABEL, "", s) if n == 0 else s
        if s.endswith("?") and (n == 0 or len(s.split()) <= 8) and not in_draft(re.sub(LINT_LABEL, "", s)):
            hits.append(f"Make this a plain statement, or keep the draft's own question: {q.strip()}")
    d_vals = [s for _, s in _lint_sents(draft) if re.search(LINT_VALUES, s, re.I) and not re.search(r"\d", s)]
    for _, s in sents:
        ot = set(_lint_toks(s))
        if ot and any(len(ot & set(_lint_toks(d))) / len(ot) > 0.6 for d in d_vals):
            hits.append(f"Cut or restate as a fact: {s}")
    for mt in re.finditer(LINT_VAGUE, o, re.I):
        hits.append(f"Say what it actually does, using only the draft's facts, instead of '{mt.group(0)}': "
                    f"{_lint_span(o, mt.start(), mt.end())}")
    d_labels = [m_.group(1) for l in draft.splitlines() if (m_ := re.match(LINT_LABEL, l))]
    o_labels = [m_.group(1) for l in lines if (m_ := re.match(LINT_LABEL, l))]
    if d_labels:
        it = iter(o_labels)
        if not all(any(x == y for y in it) for x in d_labels):   # draft labels must appear as a subsequence
            hits.append("Keep the draft's field labels, in the draft's order: " + ", ".join(x + ":" for x in d_labels))
    o_tags = {t.lower() for t in re.findall(r"#\w+", o)}
    miss = [t for t in dict.fromkeys(re.findall(r"#\w+", draft)) if t.lower() not in o_tags]
    if miss:
        hits.append("Put back these hashtags from the draft: " + " ".join(miss))
    o_norm = _lint_norm(o)
    for q in re.findall(r"\"([^\"\n]{15,})\"|“([^”\n]{15,})”", draft):
        q = q[0] or q[1]
        if _lint_norm(q) not in o_norm:
            hits.append(f'Restore this quote word for word as the draft has it: "{q}"')
    hits = list(dict.fromkeys(hits))
    return hits if cap is None else hits[:cap]


def lint_round(draft, out, g, cp, a, log):
    """Safe trim, then up to LINT_ROUNDS located-feedback revisions. A revision is kept only if the gates pass, the
    claim check (if on) is clean and the lint hit count strictly drops; otherwise the previous text stays."""
    pt = ct = 0
    t = safe_trim(out)
    log["lint_trim"] = False
    if t != out:
        gt = gates.check(draft, t)
        if gt["pass"]:
            out, g, cp = t, gt, copy_overlap(draft, t); log["lint_trim"] = True
    hits = style_lint(draft, out, cap=None)
    log.update(lint_before=len(hits), lint_rounds=0, lint_kept=0)
    for _ in range(LINT_ROUNDS):
        if not hits:
            break
        msgs = [{"role": "user", "content": draft}, {"role": "assistant", "content": out},
                {"role": "user", "content": "Revise your rewrite. Fix only these problems and change nothing else:\n- "
                 + "\n- ".join(hits[:LINT_MAX]) + "\nReply with the full revised text only."}]
        text, p, c = chat(a.provider, a.model, a.system_prompt, msgs, a.dec)
        pt += p; ct += c; log["lint_rounds"] += 1
        out2 = clean(text); g2 = gates.check(draft, out2); cp2 = copy_overlap(draft, out2)
        hits2 = style_lint(draft, out2, cap=None)
        ok = g2["pass"] and not (a.anti_copy and cp2 > COPY_MAX) and len(hits2) < len(hits)
        if ok and a.claim_check:
            added2, p, c = claim_check(draft, out2, a); pt += p; ct += c
            ok = not added2
        if ok:
            out, g, cp, hits = out2, g2, cp2, hits2; log["lint_kept"] += 1
    log["lint_after"] = len(hits)
    return out, g, cp, pt, ct


def one_pass(draft, a, log=None):
    """Draft -> verify -> targeted revise (max a.loops) -> optional style round.
    Returns (out, gates, loop, pt, ct, copy, added): `added` is the last claim-check result for the returned text."""
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
        cand = (g["n_fail"] + int(near) + int(bool(added)), -loop, out, g, loop, cp, added)   # fewer failures wins; ties go to the later revision
        best = cand if best is None or cand[:2] < best[:2] else best
        if (g["pass"] and not near and not added) or loop == a.loops:
            break
        problems = g["problems"] + ([COPY_ASK] if near else []) + (
            ["You added content that is not in the draft: " + "; ".join(f'"{x}"' for x in added) + ". Remove it."] if added else [])
        msgs += [{"role": "assistant", "content": out},
                 {"role": "user", "content": "Revise your rewrite. Fix only these problems and change nothing else:\n- "
                  + "\n- ".join(problems) + "\nReply with the full revised text only."}]
    _, _, out, g, loop, cp, added = best
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
            out, g, loop, cp, added = out2, g2, loop + 1, cp2, []
    if a.style_round == "lint" and g["pass"]:
        # O3q: after the unchanged basic style round, safe trim + located lint revisions; falls back to gate-passing text.
        out, g, cp, p, c = lint_round(draft, out, g, cp, a, log if log is not None else {})
        pt += p; ct += c
    return out, g, loop, pt, ct, cp, added


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


PAIR_ASK = ("Which rewrite reads more like a calm, skilled human copywriter wrote it, while saying exactly what the "
            "DRAFT says? Answer 1 or 2.")


def check_select_judge(model):
    """The selection judge must never be the eval judge (Kimi K3), or selection would tune to the scorer."""
    if "kimi" in model.lower():
        raise SystemExit(f"--select-judge-model {model} is the eval judge family (Kimi); use GLM-5.3")


def parse_pair(text):
    """Strict verdict: the cleaned answer must start with 1 or 2 (and not 12, 21, ...). Else None (no verdict)."""
    mt = re.match(r"^\s*([12])(?![0-9])", clean(text))
    return int(mt.group(1)) if mt else None


def pair_pick(a_text, b_text, draft, a):
    """One ordered pairwise call on the selection judge. Returns (1|2|None, pt, ct)."""
    dec = decoding("fireworks", a.select_judge_model, "low")
    dec["temperature"] = 0.0; dec["max_tokens"] = a.pair_max_tokens; dec.pop("top_p", None)
    msg = [{"role": "user", "content": f"{PAIR_ASK}\n\nDRAFT:\n{draft}\n\nREWRITE 1:\n{a_text}\n\nREWRITE 2:\n{b_text}"
            "\n\nAnswer with the single digit 1 or 2 and nothing else."}]
    try:
        r, p, c = chat("fireworks", a.select_judge_model, "You are a strict senior copy editor.", msg, dec)
    except Exception:
        return None, 0, 0
    return parse_pair(r), p, c


def _sent_len(t):
    s = gates.m.sentences(t)
    return len(gates.m.words(t)) / max(len(s), 1)


def knockout(ok, cands, draft, a):
    """Single-elimination over eligible candidates, both orders per match. Agreeing verdicts decide ('judge');
    disagreement or a missing verdict is a tie broken by lower copy_overlap, then lower index ('copy').
    rhythm() (idea 1) is not built, so copy_overlap is the only tie-break. Odd rounds: the bye goes to the
    lowest copy_overlap candidate (a fixed rule, not judge quality), so the others meet on the judge's verdict
    first; it would win any tie anyway. Bracket order is by candidate index. Returns (winner, log)."""
    idx = lambda x: cands.index(x)
    tb = lambda x: (x["copy"], idx(x))
    log = {"matches": [], "bye": None, "no_verdict": 0, "pt": 0, "ct": 0}
    alive = sorted(ok, key=idx)
    stage = None
    while len(alive) > 1:
        nxt = []
        if len(alive) % 2:
            bye = min(alive, key=tb); alive = [x for x in alive if x is not bye]
            log["bye"] = idx(bye) if log["bye"] is None else log["bye"]
            nxt.append(bye)
        for x, y in zip(alive[::2], alive[1::2]):
            v1, p1, c1 = pair_pick(x["out"], y["out"], draft, a)
            v2, p2, c2 = pair_pick(y["out"], x["out"], draft, a)
            log["pt"] += p1 + p2; log["ct"] += c1 + c2
            log["no_verdict"] += (v1 is None) + (v2 is None)
            if v1 == 1 and v2 == 2:
                w, stage = x, "judge"
            elif v1 == 2 and v2 == 1:
                w, stage = y, "judge"
            else:
                w, stage = min((x, y), key=tb), "copy"
            log["matches"].append({"pair": [idx(x), idx(y)], "v_ab": v1, "v_ba": v2, "winner": idx(w),
                                   "by": stage, "flip": stage != "judge"})
            nxt.append(w)
        alive = sorted(nxt, key=idx)
    log["decided_by"] = stage
    return alive[0], log


def rewrite(item, a):
    draft = item["ai_draft"]
    t0 = time.time(); pt = ct = 0
    cands = []
    for _ in range(a.best_of):
        lint_log = {}
        out, g, loop, p, c, cp, added = one_pass(draft, a, lint_log) if a.style_round == "lint" else one_pass(draft, a)
        pt += p; ct += c
        cands.append({"out": out, "g": g, "loop": loop, "copy": cp, "added": added, "lint": lint_log})
    sel = {}
    if a.best_of > 1:
        strict = getattr(a, "strict_claims", False)
        mode = getattr(a, "select", "absolute")
        # --strict-claims (off by default so O3k rows reproduce): a candidate whose last claim check flagged
        # added content, or could not run, is not eligible.
        ok = [x for x in cands if x["g"]["pass"] and not (a.anti_copy and x["copy"] > COPY_MAX)
              and not (strict and x["added"])]
        jpt = jct = 0
        sel = {}
        if mode == "pairwise":
            if len(ok) >= 2:
                pick, kl = knockout(ok, cands, draft, a)
                jpt, jct = kl["pt"], kl["ct"]
                flips = sum(m["flip"] for m in kl["matches"])
                sel = {"select": "pairwise", "matches": kl["matches"], "bye": kl["bye"], "flips": flips,
                       "flip_rate": round(flips / len(kl["matches"]), 4), "no_verdict": kl["no_verdict"],
                       "decided_by": kl["decided_by"], "tiebreak": "copy_overlap (rhythm() not built)"}
            elif ok:
                pick = ok[0]
                sel = {"select": "pairwise", "matches": [], "bye": None, "flips": 0, "flip_rate": None,
                       "no_verdict": 0, "decided_by": "only_eligible"}
            else:
                pick = None
                sel = {"select": "pairwise", "matches": [], "bye": None, "flips": 0, "flip_rate": None,
                       "no_verdict": 0, "decided_by": "fallback"}
        else:
            for x in ok:
                x["score"], p, c = judge_score(x["out"], a)
                jpt += p; jct += c
            pick = max(ok, key=lambda x: (x["score"] or 0, -x["copy"])) if ok else None
            sel = {"scores": [x.get("score") for x in cands]}
        if pick is None:
            pick = min(cands, key=lambda x: (x["g"]["n_fail"] + int(a.anti_copy and x["copy"] > COPY_MAX)
                                             + int(strict and bool(x["added"])), x["copy"]))
        sel = {"candidates": len(cands), "eligible": len(ok), **sel,
               "picked": cands.index(pick), "judge_model": a.select_judge_model,
               "judge_prompt_tokens": jpt, "judge_completion_tokens": jct,
               "judge_cost_usd": round(jpt * a.judge_in_price / 1e6 + jct * a.judge_out_price / 1e6, 6)}
        if strict or mode == "pairwise":
            un = [x for x in cands if x is not pick]
            mean = lambda xs, f: round(sum(f(x["out"]) for x in xs) / len(xs), 2) if xs else None
            nw = lambda t: len(gates.m.words(t))
            sel.update({"strict_claims": strict,
                        "claim_flagged": sum(bool(x["added"]) and not x["added"][0].startswith(CLAIM_UNAVAILABLE) for x in cands),
                        "claim_unavailable": sum(bool(x["added"]) and x["added"][0].startswith(CLAIM_UNAVAILABLE) for x in cands),
                        "picked_words": nw(pick["out"]), "unpicked_mean_words": mean(un, nw),
                        "picked_sent_len": round(_sent_len(pick["out"]), 2), "unpicked_mean_sent_len": mean(un, _sent_len)})
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
    if a.style_round == "lint":
        lg = pick.get("lint") or {}
        row.update({"lint_before": lg.get("lint_before"), "lint_after": lg.get("lint_after"),
                    "lint_rounds": lg.get("lint_rounds", 0), "lint_kept": lg.get("lint_kept", 0),
                    "lint_trim": lg.get("lint_trim", False)})
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
    ap.add_argument("--select", default="absolute", choices=["absolute", "pairwise"],
                    help="best-of-N picker: absolute 1-10 score (default, O3j/O3k) or pairwise knockout, both orders")
    ap.add_argument("--pair-max-tokens", type=int, default=256, help="max tokens per pairwise call (reasoning included)")
    ap.add_argument("--strict-claims", action="store_true",
                    help="best-of-N: drop candidates whose last claim check flagged added content (off = O3k behaviour)")
    ap.add_argument("--judge-in-price", type=float, default=0.0); ap.add_argument("--judge-out-price", type=float, default=0.0)
    ap.add_argument("--style-round", nargs="?", const="basic", default=None, choices=["basic", "cliche", "calm", "lint"],
                    help="after the gates pass, one copywriter style edit (basic or cliche), kept only if gates still pass; "
                         "lint = basic, then safe trim + up to 2 located style-lint revisions (kept only if gates pass "
                         "and lint hits drop)")
    a = ap.parse_args()
    check_select_judge(a.select_judge_model)
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
                "select": a.select if a.best_of > 1 else None, "strict_claims": a.strict_claims,
                "judge_prices_usd_per_m": [a.judge_in_price, a.judge_out_price],
                "prices_usd_per_m": [a.in_price, a.out_price], "eval": a.eval, "rows": len(rows),
                "pass_rate": sum(r["gates"]["pass"] for r in rows) / len(rows), "empty_outputs": [r["id"] for r in rows if not r["output"]], "commit": commit,
                "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    if a.style_round == "lint":
        lr = [r for r in rows if r.get("lint_before") is not None]
        mean = lambda k: round(sum(r[k] for r in lr) / len(lr), 3) if lr else None
        manifest["lint"] = {"rows_linted": len(lr), "mean_lint_before": mean("lint_before"),
                            "mean_lint_after": mean("lint_after"), "rows_lint_kept": sum(r["lint_kept"] > 0 for r in lr),
                            "rows_trim_kept": sum(bool(r.get("lint_trim")) for r in lr),
                            "lint_rounds_total": sum(r["lint_rounds"] for r in lr), "max_rounds": LINT_ROUNDS,
                            "max_hits_sent": LINT_MAX}
    base = os.path.basename(a.eval)
    suffix = "_heldout" if "heldout" in base else "_real" if "real" in base else ""
    json.dump(manifest, open(os.path.join(ROOT, f"hackathon/runs/{re.sub(r'[^A-Za-z0-9_.-]', '_', a.system_name)}{suffix}.json"), "w"), indent=1)
    print("DONE", json.dumps(manifest))


if __name__ == "__main__":
    main()
