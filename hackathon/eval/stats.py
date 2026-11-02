"""Uncertainty for the FeatherLM report. Seeded, so every number reproduces.

rate_ci(k, n)                              -> (rate, lo, hi), exact Clopper-Pearson 95%; use for fail/pass/win rates
bootstrap_ci(values, stat, n, seed)        -> (point, lo, hi), 95% percentile bootstrap; use for continuous metrics
paired_bootstrap_diff(a, b, stat, n, seed) -> (diff, lo, hi, p_two_sided); a[i], b[i] must be the same item
                                              (score_all aligns by id first)
judge_sign_test(wins, losses)              -> two-sided exact binomial p, ties excluded (report ties next to it)
percentiles(values, ps)                    -> {"p50": .., "p95": ..}, point values (latency)
cost_per_1k(costs)                         -> mean cost_usd x 1000
Percentile, not BCa: BCa breaks on degenerate samples such as an all-zero fail rate.
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
from scipy.stats import binomtest

Stat = Callable[[np.ndarray], float]
EPS = 1e-12  # differences closer to 0 than this count as ties


def _arr(values: Sequence[float]) -> np.ndarray:
    a = np.asarray(values, dtype=float)
    if a.size == 0:
        raise ValueError("empty sample")
    if not np.isfinite(a).all():
        raise ValueError("sample has NaN/inf (a missing row?)")
    return a


def rate_ci(k: int, n: int) -> tuple[float, float, float]:
    if not 0 <= k <= n or n == 0:
        raise ValueError(f"bad counts k={k} n={n}")
    ci = binomtest(k, n).proportion_ci(0.95, method="exact")
    return k / n, float(ci.low), float(ci.high)


def bootstrap_ci(values: Sequence[float], stat: Stat = np.mean, n: int = 10000,
                 seed: int = 0) -> tuple[float, float, float]:
    a = _arr(values)
    idx = np.random.default_rng(seed).integers(0, a.size, size=(n, a.size))
    reps = np.array([stat(a[i]) for i in idx])
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return float(stat(a)), float(lo), float(hi)


def paired_bootstrap_diff(a: Sequence[float], b: Sequence[float], stat: Stat = np.mean,
                          n: int = 10000, seed: int = 0) -> tuple[float, float, float, float]:
    """stat(a) - stat(b), resampling item indices once per replicate for both systems."""
    x, y = _arr(a), _arr(b)
    if x.size != y.size:
        raise ValueError(f"unaligned samples: {x.size} vs {y.size}")
    idx = np.random.default_rng(seed).integers(0, x.size, size=(n, x.size))
    reps = np.array([stat(x[i]) - stat(y[i]) for i in idx])
    lo, hi = np.percentile(reps, [2.5, 97.5])
    lt, gt = int(np.sum(reps < -EPS)), int(np.sum(reps > EPS))
    eq = n - lt - gt
    if eq == n:
        p = 1.0
    else:  # mid-p tail (ties split), +1 so p is never reported as 0
        p = min(1.0, (2 * min(lt + eq / 2, gt + eq / 2) + 1) / (n + 1))
    return float(stat(x) - stat(y)), float(lo), float(hi), float(p)


def judge_sign_test(wins: int, losses: int) -> float:
    if wins < 0 or losses < 0:
        raise ValueError(f"negative counts {wins}, {losses}")
    if wins + losses == 0:
        return 1.0
    return float(binomtest(wins, wins + losses, 0.5).pvalue)


def percentiles(values: Sequence[float], ps: Sequence[int] = (50, 95)) -> dict[str, float]:
    a = _arr(values)
    return {f"p{p}": float(np.percentile(a, p)) for p in ps}


def cost_per_1k(costs: Sequence[float]) -> float:
    return float(np.mean(_arr(costs)) * 1000)
