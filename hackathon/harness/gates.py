"""The headline metric's gates (PLAN_V2_JUDGES.md): one definition shared by the harness and score_all.

A rewrite is a "fact-safe human rewrite" when all four gates pass:
  G1 nothing invented  - no new number, name, quote or attribution (metrics.faithfulness hard_fail)
  G2 nothing lost      - every number kept, >= 90% of names kept
  G3 no AI tells       - stock phrases, em dashes, not-X-but-Y, emoji, exclamations within the human band's upper bound
  G4 not gutted        - output length 0.7-1.3x the draft
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import metrics as m  # noqa: E402

BAND = json.load(open(os.path.join(ROOT, "evals/runs/band_v0.json")))["metrics"]
TELLS = {
    "stock_rate": "stock AI phrases",
    "em_dash_rate": "em dashes",
    "not_x_but_y_rate": "'not X but Y' contrasts",
    "emoji_rate": "emoji",
    "exclaim_share": "exclamation marks",
}
LEN_LO, LEN_HI, NAMES_MIN = 0.7, 1.3, 0.9


def check(draft: str, output: str) -> dict:
    """Return each gate's pass/fail plus plain-English problems a reviser can act on."""
    f = m.faithfulness(draft, output)
    tm = m.text_metrics(output)
    dn = max(len(m.words(draft)), 1)
    ratio = tm["n_words"] / dn
    problems = []
    if f["numbers_added"]:
        problems.append(f"You added numbers that are not in the draft: {', '.join(f['numbers_added'])}. Remove them.")
    if f["names_added"]:
        problems.append(f"You added names that are not in the draft: {', '.join(f['names_added'])}. Remove them.")
    if f.get("quotes_added") or f.get("attribution_added"):
        problems.append("You added a quote or a 'says/said' attribution that is not in the draft. Remove it.")
    if f["numbers_dropped"]:
        problems.append(f"You dropped these numbers from the draft: {', '.join(f['numbers_dropped'])}. Put each back exactly.")
    if f["names_kept"] < NAMES_MIN:
        problems.append(f"You dropped these names: {', '.join(f['names_dropped'])}. Put them back.")
    bad_tells = [label for k, label in TELLS.items() if tm[k] > BAND[k][1] + 1e-9]
    if bad_tells:
        hits = m.stock_hits(output)
        extra = f" Stock phrases found: {', '.join(sorted(set(hits))[:8])}." if hits else ""
        problems.append(f"Remove these AI tells: {', '.join(bad_tells)}.{extra}")
    if ratio < LEN_LO:
        problems.append(f"Your rewrite is too short ({ratio:.2f}x the draft). Keep all the content; aim for about the same length.")
    if ratio > LEN_HI:
        problems.append(f"Your rewrite is too long ({ratio:.2f}x the draft). Don't add content.")
    g1 = not f["hard_fail"]
    g2 = not f["numbers_dropped"] and f["names_kept"] >= NAMES_MIN
    g3 = not bad_tells
    g4 = LEN_LO <= ratio <= LEN_HI
    return {"g1_nothing_invented": g1, "g2_nothing_lost": g2, "g3_no_ai_tells": g3, "g4_not_gutted": g4,
            "pass": g1 and g2 and g3 and g4, "n_fail": 4 - sum((g1, g2, g3, g4)),
            "len_ratio": round(ratio, 3), "problems": problems}
