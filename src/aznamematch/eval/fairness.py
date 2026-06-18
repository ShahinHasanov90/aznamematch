"""Group-aware fairness: per-``name_origin_group`` P/R/F1 and the max gap across groups.

A large gap means a matcher is systematically better/worse on some name-origin group — a
compliance-relevant disparity (e.g. higher false-positive rate on one group).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aznamematch.eval.metrics import prf1_at

DEFAULT_GROUPS = ("russified", "national_zade", "national_soy", "national_li", "organization")


def _involves(groups_field: str, group: str) -> bool:
    return group in str(groups_field).split(";")


def fairness(df: pd.DataFrame, scores: np.ndarray, threshold: float,
             groups: tuple[str, ...] = DEFAULT_GROUPS, min_pos: int = 20) -> dict:
    """F1/P/R per group (pairs whose name_origin_groups includes the group) + max F1 gap."""
    labels = df["label"].to_numpy()
    per_group: dict[str, dict] = {}
    for g in groups:
        mask = df["name_origin_groups"].apply(lambda v, g=g: _involves(v, g)).to_numpy()
        if mask.sum() == 0:
            continue
        gl, gs = labels[mask], scores[mask]
        n_pos = int(np.sum(gl == 1))
        if n_pos < min_pos:  # too few positives to be a stable slice
            continue
        m = prf1_at(gl, gs, threshold)
        per_group[g] = {"n": int(mask.sum()), "n_pos": n_pos,
                        "precision": m["precision"], "recall": m["recall"], "f1": m["f1"]}

    f1s = [v["f1"] for v in per_group.values()]
    max_gap = (max(f1s) - min(f1s)) if len(f1s) >= 2 else 0.0
    return {"threshold": float(threshold), "by_group": per_group, "max_f1_gap": float(max_gap)}
