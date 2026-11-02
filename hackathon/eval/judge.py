"""Pairwise LLM judge: system A vs system B on the same eval items, both orders, forced choice.

Protocol (EVALS_AND_RL_PLAN §2.6-2.7, plans/humanlm-role-b.md S3): per id the judge sees the facts that
must be kept, the draft, Rewrite 1 and Rewrite 2, and answers FACTS / STYLE / VERDICT, each `1|2|tie`,
plus a one-line REASON (held-out adds the human original and CLOSER). Each id runs in order "AB" (A is
Rewrite 1) and "BA" (B is Rewrite 1). A wins an id only when both orders favour A; B likewise; else tie.
flip_rate = share of complete ids whose two orders disagree. Rubric text lives in JUDGE_PROMPT.md.

Prompt:    load_prompts(path) -> {section: text}; build_messages(item, out1, out2, prompts, heldout).
Data:      read_jsonl; load_outputs(path) -> ({id: output}, dup_ids); load_items(eval, fact_files).
Family:    judge_family(model) -> 'qwen' | 'llama' | ...; a Claude judge is refused (frontier arm F1 is Claude).
Hashes:    cfg_hash(model, mock, heldout, prompts) on every row (mismatch -> exit unless --fresh);
           io_hash(item, a_out, b_out) on every row (mismatch -> row is stale and re-judged).
Parse:     parse_field(text, name) -> "1"|"2"|"tie"|None; parse_verdict(text) -> (verdict|None, reason).
Judge:     a judge is callable(messages, id, order) -> raw text; mock_judge(heldout); make_live_judge(model).
           Live calls raise Truncated on finish_reason "length" and EmptyOutput on empty content.
Aggregate: winner(verdict, order) -> "A"|"B"|"tie"; aggregate(rows, field) -> (per_id, summary block).
Run:       preflight(...) -> join report; run(...) -> summary dict (also <out>.summary.json,
           errors in <out>.errors.jsonl).
CLI:       python judge.py A.jsonl B.jsonl --model ID [--eval PATH] [--out PATH] [--mock] [--heldout]
                  [--concurrency 4] [--limit N] [--seed 0] [--fresh] [--allow-partial]
           Exit 0 when every expected pair is complete, 2 when some are not, 1 on a refused start.
Live calls use the OpenAI SDK against Fireworks (FIREWORKS_API_KEY from env, ~/.config/humanlm/keys.env or .env). Keys are never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable

Judge = Callable[[list, str, str], str]  # (messages, id, order) -> raw judge text

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROMPT_PATH = os.path.join(HERE, "JUDGE_PROMPT.md")
FACT_FILES = (os.path.join(ROOT, "evals", "dev_set.jsonl"), os.path.join(ROOT, "evals", "trick_set.jsonl"))
DEFAULT_EVAL = os.path.join(ROOT, "evals", "eval_all.jsonl")
HELDOUT_EVAL = os.path.join(ROOT, "evals", "heldout_pairs.jsonl")
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1"
TEMPERATURE = 0
MAX_TOKENS = 1024
ORDERS = ("AB", "BA")  # AB: A is Rewrite 1. BA: B is Rewrite 1.
SECTIONS = ("system", "criteria", "user", "user_heldout", "no_facts")

SECTION = re.compile(r"<!--\s*begin:(\w+)\s*-->\n?(.*?)\n?<!--\s*end:\1\s*-->", re.S)
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
THINK = re.compile(r"<think>.*?(?:</think>|$)", re.S | re.I)
ANSWER = re.compile(r"^(?:rewrite\s*|option\s*|#)?(1|2|tie|neither|draw|equal)\b\s*[.!]?$", re.I)
BARE = re.compile(r"^\s*(?:rewrite\s*)?([12])\s*$", re.I)


class Truncated(RuntimeError):
    """The judge hit max_tokens (finish_reason == "length")."""


class EmptyOutput(RuntimeError):
    """The judge returned no content."""


# ---------- prompt ----------

def load_prompts(path: str = PROMPT_PATH) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        sections = {name: body.strip() for name, body in SECTION.findall(f.read())}
    missing = set(SECTIONS) - sections.keys()
    if missing:
        raise ValueError(f"{path}: missing prompt sections {sorted(missing)}")
    return sections


def fill(template: str, values: dict[str, str]) -> str:
    """Single pass: filled values are never re-scanned. Unknown placeholders are an error."""
    def sub(m: re.Match) -> str:
        if m.group(1) not in values:
            raise KeyError(f"unknown placeholder {{{{{m.group(1)}}}}}")
        return values[m.group(1)] or ""
    return PLACEHOLDER.sub(sub, template)


def facts_text(item: dict, prompts: dict[str, str]) -> str:
    facts = item.get("facts") or []
    return "\n".join(f"- {x}" for x in facts) if facts else prompts["no_facts"]


def build_messages(item: dict, out1: str, out2: str, prompts: dict[str, str],
                   heldout: bool = False) -> list[dict]:
    user = fill(prompts["user_heldout" if heldout else "user"], {
        "FACTS": facts_text(item, prompts), "DRAFT": item.get("ai_draft", ""), "HUMAN": item.get("human", ""),
        "REWRITE_1": out1, "REWRITE_2": out2, "CRITERIA": prompts["criteria"]})
    return [{"role": "system", "content": prompts["system"]}, {"role": "user", "content": user}]


# ---------- data ----------

def read_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_outputs(path: str) -> tuple[dict[str, str], list[str]]:
    """({id: output}, duplicate ids). A duplicated id keeps its first output."""
    out: dict[str, str] = {}
    dups: list[str] = []
    for r in read_jsonl(path):
        if r["id"] in out:
            dups.append(r["id"])
        else:
            out[r["id"]] = r.get("output", "")
    return out, dups


def _mentions(text: str, token: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text) is not None


def item_facts(row: dict) -> list[str]:
    """brief.facts, then must_keep, then brief numbers/names not already mentioned (word boundary)."""
    brief = row.get("brief") or {}
    out: list[str] = []
    for x in list(brief.get("facts") or []) + list(row.get("must_keep") or []):
        if x and x not in out:
            out.append(x)
    joined = "\n".join(out)
    extra = [x for x in list(brief.get("numbers") or []) + list(brief.get("names") or [])
             if x and not _mentions(joined, x)]
    if extra:
        out.append("Numbers and names to keep exactly: " + ", ".join(extra))
    return out


def load_items(eval_path: str, fact_files: Iterable[str] = FACT_FILES) -> tuple[dict[str, dict], list[str]]:
    """(eval rows by id in file order, each with `facts` joined from fact_files by id; duplicate eval ids)."""
    facts: dict[str, list[str]] = {}
    for path in fact_files:
        if os.path.exists(path):
            for r in read_jsonl(path):
                facts[r["id"]] = item_facts(r)
    items: dict[str, dict] = {}
    dups: list[str] = []
    for r in read_jsonl(eval_path):
        if r["id"] in items:
            dups.append(r["id"])
            continue
        items[r["id"]] = {**r, "facts": item_facts(r) or facts.get(r["id"], [])}
    return items, dups


# ---------- hashes ----------

def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def cfg_hash(model: str, mock: bool, heldout: bool, prompts: dict[str, str]) -> str:
    return _hash({"model": model, "mock": mock, "heldout": heldout, "temperature": TEMPERATURE,
                  "max_tokens": MAX_TOKENS, "prompts": prompts})


def io_hash(item: dict, a_out: str, b_out: str) -> str:
    return _hash({"facts": item.get("facts") or [], "draft": item.get("ai_draft", ""),
                  "human": item.get("human", ""), "a": a_out, "b": b_out})


# ---------- parse ----------

def _strip(text: str) -> str:
    return THINK.sub("", text or "").strip()


def _field_values(text: str, name: str) -> list[str]:
    pat = re.compile(r"^[\s>*_#`-]*" + name + r"[\s*_`]*[:=\-][\s*_`]*(.*)$", re.I | re.M)
    return pat.findall(text)


def _answer(value: str) -> str | None:
    m = ANSWER.match(value.strip().strip("*_`'\"").strip())
    if not m:
        return None
    tok = m.group(1).lower()
    return tok if tok in ("1", "2") else "tie"


def parse_field(text: str, name: str) -> str | None:
    """Last NAME line wins; strict answer match ('1', 'Rewrite 2', 'tie', 'neither' -> tie). Else None."""
    values = _field_values(_strip(text), name)
    return _answer(values[-1]) if values else None


def parse_verdict(text: str) -> tuple[str | None, str]:
    """(verdict, reason). Falls back to a bare last line '1'/'Rewrite 2' only when there is no VERDICT
    line. Unparseable -> (None, 'unparsed')."""
    text = _strip(text)
    values = _field_values(text, "verdict")
    if values:
        verdict = _answer(values[-1])
    else:
        tail = [ln for ln in text.splitlines() if ln.strip()]
        m = BARE.match(tail[-1]) if tail else None
        verdict = m.group(1) if m else None
    if verdict is None:
        return None, "unparsed"
    reasons = _field_values(text, "reason")
    return verdict, (reasons[-1].strip().strip("*_`").strip() if reasons else "")


def parse_closer(text: str) -> str | None:
    return parse_field(text, "closer")


# ---------- judges ----------

def mock_verdict(item_id: str, order: str, heldout: bool = False) -> str:
    """Deterministic fake judge output from sha256(id|order), formatted like a real answer."""
    h = int(hashlib.sha256(f"{item_id}|{order}".encode()).hexdigest(), 16)
    pick = lambda k: ("1", "2", "tie")[(h // 3 ** k) % 3]  # noqa: E731
    closer = f"CLOSER: {pick(3)}\n" if heldout else ""
    return f"REASON: mock verdict for {item_id} {order}\nFACTS: {pick(1)}\nSTYLE: {pick(2)}\n{closer}VERDICT: {pick(0)}"


def mock_judge(heldout: bool = False) -> Judge:
    return lambda _messages, item_id, order: mock_verdict(item_id, order, heldout)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        # keys.env outside the repo first (CONTRACT with Ali), then repo .env; first value wins
        load_dotenv(os.environ.get("HUMANLM_KEYS", os.path.expanduser("~/.config/humanlm/keys.env")))
        load_dotenv(os.path.join(ROOT, ".env"))
    except ImportError:
        pass


def make_live_judge(model: str, client=None) -> Judge:
    if client is None:
        _load_env()
        if not os.environ.get("FIREWORKS_API_KEY"):
            sys.exit("FIREWORKS_API_KEY is not set (env, ~/.config/humanlm/keys.env or .env). Use --mock for an offline run.")
        from openai import OpenAI
        client = OpenAI(base_url=FIREWORKS_URL, api_key=os.environ["FIREWORKS_API_KEY"], max_retries=5)

    def call(messages: list[dict], _id: str = "", _order: str = "") -> str:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=TEMPERATURE,
                                              max_tokens=MAX_TOKENS)
        choice = resp.choices[0]
        if choice.finish_reason == "length":
            raise Truncated("finish_reason=length")
        content = choice.message.content or ""
        if not content.strip():
            raise EmptyOutput("empty content")
        return content
    return call


# ---------- aggregate ----------

def winner(verdict: str | None, order: str) -> str:
    """Map a positional verdict back to the system: '1' in order AB means A, in BA means B."""
    if verdict not in ("1", "2"):
        return "tie"
    first, second = ("A", "B") if order == "AB" else ("B", "A")
    return first if verdict == "1" else second


def aggregate(rows: Iterable[dict], field: str = "verdict") -> tuple[dict[str, dict], dict]:
    """Per id: A only if both orders favour A, B likewise, else tie. An id counts only when both orders
    have a parsed value for `field`. Later rows for the same (id, order) replace earlier ones.
    Returns (per_id, {win, loss, tie, n, flip_rate}) from A's side."""
    by_id: dict[str, dict[str, str | None]] = {}
    for r in rows:
        by_id.setdefault(r["id"], {})[r["order"]] = r.get(field)
    per_id: dict[str, dict] = {}
    for item_id, v in by_id.items():
        if all(v.get(o) is not None for o in ORDERS):
            ab, ba = winner(v["AB"], "AB"), winner(v["BA"], "BA")
            final = ab if ab == ba and ab != "tie" else "tie"
            per_id[item_id] = {"AB": ab, "BA": ba, "final": final, "flip": ab != ba}
    n = len(per_id)
    finals = [p["final"] for p in per_id.values()]
    block = {"win": finals.count("A"), "loss": finals.count("B"), "tie": finals.count("tie"), "n": n,
             "flip_rate": round(sum(p["flip"] for p in per_id.values()) / n, 4) if n else 0.0}
    return per_id, block


def pos1_rate(rows: Iterable[dict]) -> float:
    """Share of non-tie raw verdicts that pick Rewrite 1 (position bias check; 0.5 is unbiased)."""
    picks = [r["verdict"] for r in rows if r.get("verdict") in ("1", "2")]
    return round(picks.count("1") / len(picks), 4) if picks else 0.0


# ---------- judge family ----------

FAMILIES = ("claude", "anthropic", "gpt-oss", "gpt", "llama", "qwen", "deepseek", "mixtral", "mistral",
            "gemma", "kimi", "glm", "nemotron", "dbrx")
BANNED_FAMILIES = {"claude", "anthropic"}  # PLAN_V2_JUDGES: frontier arm F1 is Claude, so no Claude judge


def judge_family(model: str) -> str:
    """First known family name in the model id (e.g. 'accounts/fireworks/models/qwen3-235b' -> 'qwen')."""
    name = (model or "").lower().rsplit("/", 1)[-1]
    return next((f for f in FAMILIES if f in name), "unknown")


# ---------- run ----------

def _ids_report(ids: list[str]) -> dict:
    return {"count": len(ids), "first": ids[:3]}


def preflight(items: dict[str, dict], eval_dups: list[str], a: dict[str, str], a_dups: list[str],
              b: dict[str, str], b_dups: list[str], limit: int | None,
              seed: int) -> tuple[list[str], list[str], dict]:
    """(expected ids, ids to judge, join report). With --limit, expected is a seeded random sample."""
    expected = list(items)
    if limit and limit < len(expected):
        keep = set(random.Random(seed).sample(expected, limit))
        expected = [i for i in expected if i in keep]
    report = {"n_expected": len(expected),
              "missing_in_a": _ids_report([i for i in expected if i not in a]),
              "missing_in_b": _ids_report([i for i in expected if i not in b]),
              "not_in_eval": _ids_report(sorted((a.keys() | b.keys()) - items.keys())),
              "dup_ids": _ids_report(eval_dups + a_dups + b_dups)}
    return expected, [i for i in expected if i in a and i in b], report


def errors_path(out_path: str) -> str:
    return _base(out_path) + ".errors.jsonl"


def summary_path(out_path: str) -> str:
    return _base(out_path) + ".summary.json"


def _base(out_path: str) -> str:
    return out_path[:-len(".jsonl")] if out_path.endswith(".jsonl") else out_path


def judge_one(item: dict, a_out: str, b_out: str, order: str, prompts: dict[str, str], call: Judge,
              heldout: bool, cfg: str, io: str, mock: bool) -> dict:
    out1, out2 = (a_out, b_out) if order == "AB" else (b_out, a_out)
    raw = call(build_messages(item, out1, out2, prompts, heldout), item["id"], order)
    verdict, reason = parse_verdict(raw)
    row = {"id": item["id"], "order": order, "verdict": verdict, "facts": parse_field(raw, "facts"),
           "style": parse_field(raw, "style"), "reason": reason, "raw": raw, "cfg": cfg, "io": io, "mock": mock}
    if heldout:
        row["closer"] = parse_closer(raw)
    return row


def run(a_path: str, b_path: str, eval_path: str, out_path: str, call: Judge, *, model: str,
        mock: bool = False, heldout: bool = False, concurrency: int = 4, limit: int | None = None,
        seed: int = 0, fresh: bool = False, allow_partial: bool = False, prompt_path: str = PROMPT_PATH,
        fact_files: Iterable[str] = FACT_FILES) -> dict:
    prompts = load_prompts(prompt_path)
    items, eval_dups = load_items(eval_path, fact_files)
    (a, a_dups), (b, b_dups) = load_outputs(a_path), load_outputs(b_path)
    expected, ids, report = preflight(items, eval_dups, a, a_dups, b, b_dups, limit, seed)
    if report["dup_ids"]["count"]:
        sys.exit(f"duplicate ids: {json.dumps(report['dup_ids'])}")
    bad = {k: v for k, v in report.items() if k != "n_expected" and v["count"]}
    if bad and not allow_partial:
        sys.exit(f"inputs do not cover the eval set (pass --allow-partial to judge the overlap): {json.dumps(bad)}")

    if not mock and judge_family(model) in BANNED_FAMILIES:
        sys.exit(f"judge model family '{judge_family(model)}' is the frontier arm's family; use an open model.")
    cfg = cfg_hash(model, mock, heldout, prompts)
    if fresh and os.path.exists(out_path):
        os.remove(out_path)
    old = read_jsonl(out_path) if os.path.exists(out_path) else []
    foreign = [r for r in old if r.get("cfg") != cfg]
    if foreign:
        sys.exit(f"{out_path}: {len(foreign)} rows were made with a different judge config "
                 f"(model, mock, heldout, decoding or prompt). Use --fresh or a new --out.")
    io = {i: io_hash(items[i], a[i], b[i]) for i in ids}
    done = {(r["id"], r["order"]) for r in old if io.get(r["id"]) == r.get("io")}
    todo = [(i, o) for i in ids for o in ORDERS if (i, o) not in done]

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    lock, errors = threading.Lock(), []
    with open(out_path, "a", encoding="utf-8") as f, ThreadPoolExecutor(max(1, concurrency)) as pool:
        futs = {pool.submit(judge_one, items[i], a[i], b[i], o, prompts, call, heldout, cfg, io[i], mock): (i, o)
                for i, o in todo}
        for fut in as_completed(futs):
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001 - logged and retried on resume
                errors.append({"id": futs[fut][0], "order": futs[fut][1], "error": type(e).__name__})
                continue
            with lock:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
    with open(errors_path(out_path), "w", encoding="utf-8") as f:
        f.writelines(json.dumps(e) + "\n" for e in errors)

    rows = [r for r in read_jsonl(out_path) if r.get("cfg") == cfg and io.get(r["id"]) == r.get("io")]
    per_id, overall = aggregate(rows)
    incomplete = [i for i in expected if i not in per_id]
    summary = {"a": os.path.basename(a_path), "b": os.path.basename(b_path),
               "model": f"mock:{model}" if mock else model, "judge_family": judge_family(model),
               "mock": mock, "heldout": heldout,
               "eval": os.path.relpath(eval_path, ROOT).replace(os.sep, "/"), "cfg": cfg,
               **overall, "pos1_rate": pos1_rate(rows),
               "facts": aggregate(rows, "facts")[1], "style": aggregate(rows, "style")[1],
               **report, "n_complete": len(per_id), "incomplete_ids": _ids_report(incomplete),
               "empty_facts": sum(1 for i in ids if not items[i].get("facts")),
               "unparsed": sum(1 for r in rows if r.get("verdict") is None),
               "finish_length": sum(1 for e in errors if e["error"] == "Truncated"),
               "errors": len(errors), "skipped_resume": len(ids) * len(ORDERS) - len(todo),
               "limit": limit, "seed": seed}
    if heldout:
        summary["closer"] = aggregate(rows, "closer")[1]
    with open(summary_path(out_path), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def default_out(a_path: str, b_path: str, heldout: bool, mock: bool) -> str:
    name = f"judge_{stem(a_path)}_vs_{stem(b_path)}{'_heldout' if heldout else ''}{'_mock' if mock else ''}.jsonl"
    return os.path.join(ROOT, "hackathon", "report", name)


def force_mock_name(out_path: str) -> str:
    """--mock output always has 'mock' in its file name, so it can't pass for a real judge file."""
    if "mock" in os.path.basename(out_path).lower():
        return out_path
    return _base(out_path) + "_mock.jsonl"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pairwise judge, both orders.")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--eval", default=None, help="default evals/eval_all.jsonl (heldout_pairs.jsonl with --heldout)")
    ap.add_argument("--model", required=True, help="Fireworks model id (recorded in rows and summary)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mock", action="store_true", help="deterministic fake verdicts, no network")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None, help="judge a seeded random sample of N eval ids")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--heldout", action="store_true", help="add the human original and the CLOSER question")
    ap.add_argument("--fresh", action="store_true", help="delete existing rows in --out first")
    ap.add_argument("--allow-partial", action="store_true", help="judge the overlap when ids are missing")
    args = ap.parse_args(argv)
    eval_path = args.eval or (HELDOUT_EVAL if args.heldout else DEFAULT_EVAL)
    out = args.out or default_out(args.a, args.b, args.heldout, args.mock)
    if args.mock:
        out = force_mock_name(out)
    call = mock_judge(args.heldout) if args.mock else make_live_judge(args.model)
    summary = run(args.a, args.b, eval_path, out, call, model=args.model, mock=args.mock, heldout=args.heldout,
                  concurrency=args.concurrency, limit=args.limit, seed=args.seed, fresh=args.fresh,
                  allow_partial=args.allow_partial)
    print(json.dumps(summary, indent=2))
    print(f"rows: {out}\nsummary: {summary_path(out)}", file=sys.stderr)
    return 0 if summary["n_complete"] == summary["n_expected"] else 2


if __name__ == "__main__":
    sys.exit(main())
