"""Unknown-Standard protocol + Cross-Standard Robustness Score.

Real compliance data rarely tells you which transliteration standard produced a name. We
simulate that: tune each matcher's decision threshold on pairs from the *named* standards
(ICAO / GOST / BGN-PCGN / ALA-LC), then evaluate on the *ad-hoc* standardless pairs (the
realistic unknown case). The Cross-Standard Robustness Score = F1(ad-hoc) / F1(named) at that
fixed threshold — how much performance is retained under standard shift (1.0 = no loss).

We also report per-standard recall at a global threshold, to expose which producing standard
a matcher is weakest on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aznamematch.eval.metrics import best_f1, prf1_at

NAMED_STANDARDS = ("ICAO", "GOST", "BGN_PCGN", "ALA_LC")
AD_HOC = "ad_hoc"


def _involves_any(standards_field: str, wanted: tuple[str, ...]) -> bool:
    present = set(str(standards_field).split(";"))
    return any(w in present for w in wanted)


def cross_standard_score(df: pd.DataFrame, scores: np.ndarray) -> dict:
    labels = df["label"].to_numpy()
    # Strictly disjoint slices: tune on pairs involving ONLY named standards, evaluate on pairs
    # involving ONLY ad-hoc (a pair tagged e.g. "ICAO;ad_hoc" belongs to neither, so the
    # tune/eval sets never overlap).
    named = df["standards"].apply(lambda v: _involves_any(v, NAMED_STANDARDS))
    adhoc = df["standards"].apply(lambda v: _involves_any(v, (AD_HOC,)))
    named_mask = (named & ~adhoc).to_numpy()
    adhoc_mask = (adhoc & ~named).to_numpy()

    result: dict = {"n_named": int(named_mask.sum()), "n_adhoc": int(adhoc_mask.sum())}
    if named_mask.sum() == 0 or adhoc_mask.sum() == 0 \
            or len(np.unique(labels[named_mask])) < 2:
        result["robustness"] = float("nan")
        return result

    tuned = best_f1(labels[named_mask], scores[named_mask])
    thr = tuned["threshold"]
    f1_named = tuned["f1"]
    f1_adhoc = prf1_at(labels[adhoc_mask], scores[adhoc_mask], thr)["f1"]
    result.update({
        "tuned_threshold": float(thr),
        "f1_named": float(f1_named),
        "f1_adhoc": float(f1_adhoc),
        "robustness": float(f1_adhoc / f1_named) if f1_named else float("nan"),
    })
    return result


def per_standard_recall(df: pd.DataFrame, scores: np.ndarray, threshold: float) -> dict:
    """Recall on positives bucketed by each translit standard present (at a fixed threshold)."""
    labels = df["label"].to_numpy()
    pred = scores >= threshold
    out: dict[str, dict] = {}
    for std in (*NAMED_STANDARDS, AD_HOC):
        mask = df["standards"].apply(lambda v, s=std: s in str(v).split(";")).to_numpy()
        pos = mask & (labels == 1)
        n_pos = int(pos.sum())
        if n_pos < 20:
            continue
        recall = float(np.sum(pred & pos) / n_pos)
        out[std] = {"n_pos": n_pos, "recall": recall}
    recalls = [v["recall"] for v in out.values()]
    spread = (max(recalls) - min(recalls)) if len(recalls) >= 2 else 0.0
    return {"threshold": float(threshold), "by_standard": out, "recall_spread": float(spread)}
