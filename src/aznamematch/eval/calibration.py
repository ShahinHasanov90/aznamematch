"""Calibration (reliability) — ONLY for matchers that emit a true probability.

A raw cosine or fuzz-ratio is NOT a calibrated probability, so we apply this only to matchers
flagged probabilistic (RegressionV1). We bin predicted scores, compare bin mean-prediction to
the empirical match rate, and report Expected Calibration Error (ECE), sliced cross-script vs
same-script (the divergence we most expect to be mis-calibrated).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def reliability(labels: np.ndarray, scores: np.ndarray, n_bins: int = 10) -> dict:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(scores, bins) - 1, 0, n_bins - 1)
    rows = []
    ece = 0.0
    n = len(labels)
    for b in range(n_bins):
        sel = idx == b
        cnt = int(sel.sum())
        if cnt == 0:
            continue
        conf = float(np.mean(scores[sel]))
        acc = float(np.mean(labels[sel]))
        ece += (cnt / n) * abs(conf - acc)
        rows.append({"bin": b, "count": cnt, "mean_pred": conf, "empirical": acc})
    return {"bins": rows, "ece": float(ece)}


def calibration(df: pd.DataFrame, scores: np.ndarray) -> dict:
    """Overall + cross-script vs same-script reliability slices."""
    labels = df["label"].to_numpy()
    cross = (df["script_pair"] != "same").to_numpy()
    out = {"overall": reliability(labels, scores)}
    if cross.sum() > 0:
        out["cross_script"] = reliability(labels[cross], scores[cross])
    if (~cross).sum() > 0:
        out["same_script"] = reliability(labels[~cross], scores[~cross])
    return out
