"""FeatherLM financial model. Every input is either measured (from a committed run file) or a labelled assumption.

Run: python market/fin_model.py   (writes market/fin_model.json, prints markdown tables)
"""
import json
import os

# Measured: hack_O3c_glm_prompt_harness_style.jsonl (130 rows), Fireworks GLM-5.3 Flash prices in hackathon/report/PRICES.md
MEASURED = {
    "avg_prompt_tokens": 4346,
    "avg_completion_tokens": 290,
    "price_in_per_m": 0.15,
    "price_out_per_m": 0.50,
    "price_cached_in_per_m": 0.03,
    "claude_strong_cost_per_1k": 9.11,  # README results table
    "claude_harness_cost_per_1k": 15.85,  # F1H_opus_harness, README results table
}

# Assumptions [E]: change these, rerun, and the tables follow.
A = {
    "cogs_buffer": 2.0,  # real customer drafts may be longer than eval drafts
    "cached_share_of_input": 0.8,  # system prompt + harness instructions repeat on every call
    "payment_fee": 0.035,
    "plans": {
        "solo": {"price": 19, "rewrites": 200},  # $19 entry from board/DECISIONS.md
        "team": {"price": 79, "rewrites": 1500},
    },
    "api_price_per_1k": 4.00,
    "free_users_per_paid": 10,
    "free_rewrites": 20,
    "cac": {"solo": 40, "team": 300},
    "monthly_churn": {"solo": 0.06, "team": 0.03},
    "fixed_cost": [250_000, 1_200_000, 3_000_000],  # year 1-3: people, infra, legal
    "dedicated_gpu_per_hour": 8.0,  # H100 on-demand, third-party reports $7-8/hr [?]
    # End-of-year paying customers; API = rewrites per month
    "scenarios": {
        "conservative": {"solo": [300, 1500, 5000], "team": [20, 100, 400], "api": [1e6, 10e6, 30e6]},
        "base": {"solo": [1000, 5000, 15000], "team": [60, 400, 1500], "api": [5e6, 30e6, 100e6]},
        "upside": {"solo": [3000, 15000, 50000], "team": [150, 1200, 5000], "api": [20e6, 150e6, 500e6]},
    },
}


def cost_per_rewrite(cached=False):
    m = MEASURED
    if cached:
        s = A["cached_share_of_input"]
        price_in = (1 - s) * m["price_in_per_m"] + s * m["price_cached_in_per_m"]
    else:
        price_in = m["price_in_per_m"]
    return (m["avg_prompt_tokens"] * price_in + m["avg_completion_tokens"] * m["price_out_per_m"]) / 1e6


def plan_unit(name, cogs):
    p = A["plans"][name]
    variable = p["rewrites"] * cogs + p["price"] * A["payment_fee"]
    gm = (p["price"] - variable) / p["price"]
    ltv = p["price"] * gm / A["monthly_churn"][name]
    return {"price": p["price"], "rewrites": p["rewrites"], "cogs_month": round(variable, 2),
            "gross_margin": round(gm, 3), "ltv": round(ltv), "cac": A["cac"][name],
            "ltv_cac": round(ltv / A["cac"][name], 1), "payback_months": round(A["cac"][name] / (p["price"] * gm), 1)}


def scenario(s, cogs):
    out = []
    for y in range(3):
        solo, team, api = s["solo"][y], s["team"][y], s["api"][y]
        rev = solo * 19 * 12 + team * 79 * 12 + api * 12 * A["api_price_per_1k"] / 1000
        rewrites_month = solo * A["plans"]["solo"]["rewrites"] + team * A["plans"]["team"]["rewrites"] + api
        free = (solo + team) * A["free_users_per_paid"] * A["free_rewrites"]
        compute = (rewrites_month + free) * 12 * cogs
        fees = (solo * 19 + team * 79) * 12 * A["payment_fee"]
        gp = rev - compute - fees
        out.append({"year": y + 1, "arr_exit": round(rev), "rewrites_per_month": int(rewrites_month + free),
                    "compute_cost": round(compute), "gross_margin": round(gp / rev, 3),
                    "fixed_cost": A["fixed_cost"][y], "run_rate_operating_result": round(gp - A["fixed_cost"][y])})
    return out


# Scale-up case: more data, more compute, funding. Measured inputs from hackathon/train/TRAIN_LOG.md (SFT v1:
# 5,000 rows, 1,856,167 train tokens, $8.89/M serverless GLM-5.3 Flash train rate). Everything else [E].
SCALE = {
    "train_tokens_per_row": 1_856_167 / 5000,
    "train_price_per_m": 8.89,
    "epochs": 3,
    "runs_per_stage": 20,  # sweeps and ablations, not one lucky run
    "dpo_cost_multiplier": 2,  # preference tuning costs about 2x SFT per token (Fireworks tier table, third-party)
    "expert_rate_hour": 60,  # freelance copywriter, $50-85/h experienced range
    "expert_pairs_per_hour": 6,
    "eval_round_cost": 600,  # one blind panel of paid copywriters (market/RISKS.md R15: $300-600)
    "eval_rounds_per_year": 24,
    "stages": [
        {"name": "Today's data size, full sweep", "sft_pairs": 5000, "expert_pairs": 0, "pref_pairs": 66},
        {"name": "Seed, months 0-12", "sft_pairs": 50_000, "expert_pairs": 5000, "pref_pairs": 20_000},
        {"name": "Series A, months 12-36", "sft_pairs": 500_000, "expert_pairs": 25_000, "pref_pairs": 500_000},
    ],
    # After a style fine-tune passes the gates first time, the harness needs fewer revise loops.
    "ft_tokens_per_rewrite": {"input": 1800, "output": 300},
    # Funded five-year case: end-of-year paying customers; API = rewrites per month
    "funded": {
        "solo": [2000, 12_000, 40_000, 90_000, 160_000],
        "team": [100, 1000, 4000, 10_000, 20_000],
        "api": [10e6, 80e6, 300e6, 800e6, 1.5e9],
        "api_price_per_1k": [4.0, 4.0, 3.0, 3.0, 2.5],  # price falls as volume grows
        "cogs_per_1k": [1.59, 0.80, 0.50, 0.42, 0.42],  # today's buffered cost → fine-tuned single pass
        "fixed_cost": [1_500_000, 4_000_000, 9_000_000, 16_000_000, 25_000_000],
        "raised": [3_000_000, 0, 12_000_000, 0, 0],  # seed now, Series A in year 3
        "monthly_churn": {"solo": 0.04, "team": 0.02},  # better product keeps users longer
    },
}


def stage_cost(st):
    s = SCALE
    tok = s["train_tokens_per_row"] * s["epochs"] * s["runs_per_stage"] * s["train_price_per_m"] / 1e6
    sft = st["sft_pairs"] * tok
    dpo = st["pref_pairs"] * 2 * tok * s["dpo_cost_multiplier"]  # two responses per preference pair
    expert = st["expert_pairs"] / s["expert_pairs_per_hour"] * s["expert_rate_hour"]
    evals = s["eval_round_cost"] * s["eval_rounds_per_year"]
    return {"stage": st["name"], "sft_pairs": st["sft_pairs"], "expert_pairs": st["expert_pairs"],
            "pref_pairs": st["pref_pairs"], "sft_compute": round(sft), "dpo_compute": round(dpo),
            "expert_data": round(expert), "human_evals": evals, "total": round(sft + dpo + expert + evals)}


def funded():
    f = SCALE["funded"]
    out, prev_arr, cash = [], 0, 0
    for y in range(5):
        solo, team, api = f["solo"][y], f["team"][y], f["api"][y]
        arr = solo * 19 * 12 + team * 79 * 12 + api * 12 * f["api_price_per_1k"][y] / 1000
        rewrites = solo * A["plans"]["solo"]["rewrites"] + team * A["plans"]["team"]["rewrites"] + api
        compute_run_rate = rewrites * 12 * f["cogs_per_1k"][y] / 1000
        fees = (solo * 19 + team * 79) * 12 * A["payment_fee"]
        gm = (arr - compute_run_rate - fees) / arr
        revenue = (prev_arr + arr) / 2  # in-year revenue ≈ average of start and end run-rate
        cash += f["raised"][y] + revenue * gm - f["fixed_cost"][y]
        out.append({"year": y + 1, "arr_exit": round(arr), "revenue_in_year": round(revenue),
                    "rewrites_per_month": int(rewrites), "gross_margin": round(gm, 3),
                    "fixed_cost": f["fixed_cost"][y], "raised": f["raised"][y], "cash_end": round(cash)})
        prev_arr = arr
    ltv = {n: round(A["plans"][n]["price"] * 0.95 / f["monthly_churn"][n]) for n in ("solo", "team")}
    return {"years": out, "ltv": ltv}


def main():
    raw = cost_per_rewrite()
    cogs = raw * A["cogs_buffer"]
    cached = cost_per_rewrite(cached=True)
    gpu_month = A["dedicated_gpu_per_hour"] * 730
    result = {
        "measured": MEASURED,
        "assumptions": A,
        "cost_per_1k_measured": round(raw * 1000, 3),
        "cost_per_1k_with_buffer": round(cogs * 1000, 3),
        "cost_per_1k_with_caching": round(cached * 1000, 3),
        "cheaper_than_claude_strong_x": round(MEASURED["claude_strong_cost_per_1k"] / (raw * 1000), 1),
        "cheaper_than_claude_harness_x": round(MEASURED["claude_harness_cost_per_1k"] / (raw * 1000), 1),
        "api_gross_margin": round(1 - cogs * 1000 / A["api_price_per_1k"], 3),
        "dedicated_breakeven_rewrites_month": round(gpu_month / cogs),
        "units": {n: plan_unit(n, cogs) for n in A["plans"]},
        "scenarios": {n: scenario(s, cogs) for n, s in A["scenarios"].items()},
    }
    ft = SCALE["ft_tokens_per_rewrite"]
    m = MEASURED
    ft_raw = (ft["input"] * m["price_in_per_m"] + ft["output"] * m["price_out_per_m"]) / 1e6
    s = A["cached_share_of_input"]
    ft_cached = (ft["input"] * ((1 - s) * m["price_in_per_m"] + s * m["price_cached_in_per_m"]) + ft["output"] * m["price_out_per_m"]) / 1e6
    result["scale"] = {
        "assumptions": SCALE,
        "stages": [stage_cost(st) for st in SCALE["stages"]],
        "ft_cost_per_1k": round(ft_raw * 1000, 3),
        "ft_cost_per_1k_cached": round(ft_cached * 1000, 3),
        "funded": funded(),
    }
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fin_model.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"cost/1k measured ${result['cost_per_1k_measured']}, buffered ${result['cost_per_1k_with_buffer']}, "
          f"cached ${result['cost_per_1k_with_caching']}; {result['cheaper_than_claude_strong_x']}x cheaper than Claude strong, "
          f"{result['cheaper_than_claude_harness_x']}x than Claude in the same harness; API GM {result['api_gross_margin']}; "
          f"dedicated GPU breakeven {result['dedicated_breakeven_rewrites_month']:,} rewrites/month")
    print("\n| Plan | Price | Rewrites/mo | Variable cost/mo | Gross margin | LTV | CAC | LTV/CAC | Payback (mo) |\n|---|---|---|---|---|---|---|---|---|")
    for n, u in result["units"].items():
        print(f"| {n} | ${u['price']} | {u['rewrites']} | ${u['cogs_month']} | {u['gross_margin']:.0%} | ${u['ltv']:,} | ${u['cac']} | {u['ltv_cac']} | {u['payback_months']} |")
    for n, rows in result["scenarios"].items():
        print(f"\n{n}\n| Year | Exit ARR | Rewrites/mo | Compute | Gross margin | Fixed cost | Run-rate operating result |\n|---|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['year']} | ${r['arr_exit']:,} | {r['rewrites_per_month']:,} | ${r['compute_cost']:,} | {r['gross_margin']:.0%} | ${r['fixed_cost']:,} | ${r['run_rate_operating_result']:,} |")
    sc = result["scale"]
    print(f"\nscale: fine-tuned cost/1k ${sc['ft_cost_per_1k']} (cached ${sc['ft_cost_per_1k_cached']})")
    print("| Stage | SFT pairs | Expert pairs | Preference pairs | SFT compute | DPO compute | Expert data | Human evals/yr | Total |\n|---|---|---|---|---|---|---|---|---|")
    for st in sc["stages"]:
        print(f"| {st['stage']} | {st['sft_pairs']:,} | {st['expert_pairs']:,} | {st['pref_pairs']:,} | ${st['sft_compute']:,} | ${st['dpo_compute']:,} | ${st['expert_data']:,} | ${st['human_evals']:,} | ${st['total']:,} |")
    print("\nfunded\n| Year | Exit ARR | In-year revenue | Rewrites/mo | Gross margin | Fixed cost | Raised | Cash at year end |\n|---|---|---|---|---|---|---|---|")
    for r in sc["funded"]["years"]:
        print(f"| {r['year']} | ${r['arr_exit']:,} | ${r['revenue_in_year']:,} | {r['rewrites_per_month']:,} | {r['gross_margin']:.0%} | ${r['fixed_cost']:,} | ${r['raised']:,} | ${r['cash_end']:,} |")
    print(f"LTV with lower churn: {sc['funded']['ltv']}")


if __name__ == "__main__":
    main()
