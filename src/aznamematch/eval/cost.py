"""Parametric Expected-Cost ranking (ECT).

``ECT = P(FP)·c_FP + P(FN)·c_FN``. The cost ratio ``c_FN : c_FP`` is a CONFIGURABLE input
(e.g. 1:1, 10:1, 100:1) — we NEVER invent absolute monetary costs. For each ratio we pick the
cost-optimal threshold per matcher (min ECT over the sweep) and rank matchers. This shows how
the ranking shifts as missing a sanctioned entity (FN) is weighted far above a false alarm
(FP).
"""

from __future__ import annotations

import numpy as np


def ect_at(labels: np.ndarray, scores: np.ndarray, threshold: float,
           c_fp: float, c_fn: float) -> float:
    pred = scores >= threshold
    n = len(labels)
    fp = int(np.sum(pred & (labels == 0)))
    fn = int(np.sum(~pred & (labels == 1)))
    return (fp / n) * c_fp + (fn / n) * c_fn


def min_ect(labels: np.ndarray, scores: np.ndarray, c_fp: float, c_fn: float,
            grid: np.ndarray | None = None) -> dict[str, float]:
    """Cost-optimal operating point: the threshold minimizing ECT for this cost ratio."""
    if grid is None:
        grid = np.round(np.linspace(0.0, 1.0, 101), 4)
    best = min(((ect_at(labels, scores, float(t), c_fp, c_fn), float(t)) for t in grid),
               key=lambda x: x[0])
    return {"ect": best[0], "threshold": best[1]}


def rank_matchers(matcher_scores: dict[str, tuple[np.ndarray, np.ndarray]],
                  cost_ratios: list[tuple[float, float]]) -> dict[str, list[dict]]:
    """For each (c_fp, c_fn) ratio, rank matchers by minimum ECT (lower is better).

    ``matcher_scores`` maps matcher name -> (labels, scores).
    """
    out: dict[str, list[dict]] = {}
    for c_fp, c_fn in cost_ratios:
        key = f"c_fn:c_fp={c_fn:g}:{c_fp:g}"
        rows = []
        for name, (labels, scores) in matcher_scores.items():
            r = min_ect(labels, scores, c_fp, c_fn)
            rows.append({"matcher": name, "ect": r["ect"], "threshold": r["threshold"]})
        rows.sort(key=lambda r: r["ect"])
        for rank, r in enumerate(rows, 1):
            r["rank"] = rank
        out[key] = rows
    return out
