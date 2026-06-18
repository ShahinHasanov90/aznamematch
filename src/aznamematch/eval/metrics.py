"""Core matching metrics: P/R/F1, PR-AUC, ROC-AUC, threshold sweep + sensitivity.

All metrics are computed from (labels, scores) produced by a real matcher run — never
hardcoded (see docs/rules/zero-fabricated-numbers.md).
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

SENSITIVITY_THRESHOLDS = (0.55, 0.60, 0.65)


def prf1_at(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    pred = scores >= threshold
    tp = int(np.sum(pred & (labels == 1)))
    fp = int(np.sum(pred & (labels == 0)))
    fn = int(np.sum(~pred & (labels == 1)))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"threshold": float(threshold), "precision": precision, "recall": recall, "f1": f1}


def threshold_sweep(labels: np.ndarray, scores: np.ndarray,
                    grid: np.ndarray | None = None) -> list[dict[str, float]]:
    if grid is None:
        grid = np.round(np.linspace(0.0, 1.0, 101), 4)
    return [prf1_at(labels, scores, float(t)) for t in grid]


def best_f1(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    sweep = threshold_sweep(labels, scores)
    return max(sweep, key=lambda r: r["f1"])


def threshold_sensitivity(labels: np.ndarray, scores: np.ndarray,
                          thresholds: tuple[float, ...] = SENSITIVITY_THRESHOLDS) -> float:
    """L2 drift of F1 across adjacent thresholds (lower = more threshold-stable)."""
    f1s = [prf1_at(labels, scores, t)["f1"] for t in thresholds]
    diffs = np.diff(f1s)
    return float(np.sqrt(np.sum(diffs ** 2)))


def auc_scores(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    # AUCs require both classes present.
    if len(np.unique(labels)) < 2:
        return {"pr_auc": float("nan"), "roc_auc": float("nan")}
    return {
        "pr_auc": float(average_precision_score(labels, scores)),
        "roc_auc": float(roc_auc_score(labels, scores)),
    }


def summarize(labels: np.ndarray, scores: np.ndarray,
              chosen_threshold: float = 0.5) -> dict[str, float]:
    """Full metric summary for one matcher on one (labels, scores) set."""
    chosen = prf1_at(labels, scores, chosen_threshold)
    best = best_f1(labels, scores)
    aucs = auc_scores(labels, scores)
    return {
        "n": int(len(labels)),
        "n_pos": int(np.sum(labels == 1)),
        "f1_at_chosen": chosen["f1"],
        "precision_at_chosen": chosen["precision"],
        "recall_at_chosen": chosen["recall"],
        "chosen_threshold": float(chosen_threshold),
        "best_f1": best["f1"],
        "best_f1_threshold": best["threshold"],
        "best_f1_precision": best["precision"],
        "best_f1_recall": best["recall"],
        "pr_auc": aucs["pr_auc"],
        "roc_auc": aucs["roc_auc"],
        "threshold_sensitivity": threshold_sensitivity(labels, scores),
    }
