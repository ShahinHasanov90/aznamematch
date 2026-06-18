"""Error-by-root-cause taxonomy: attribute every FP / FN to a category from pair metadata.

Categories: ``script_divergence`` (competing scripts/standards), ``phonetic_orthographic``
(within-script ə/e, suffix-morphology, …), ``lexical`` (typo/abbrev/reorder corruption),
``hard_negative_collision`` (token_swap / generation_collision / surname / one_edit), and
``homoglyph`` (adversarial). This is what powers "WHERE does each matcher fail".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORIES = (
    "script_divergence", "phonetic_orthographic", "lexical",
    "hard_negative_collision", "homoglyph", "other",
)


def _fn_category(row: pd.Series) -> str:
    """Root cause for a missed positive (false negative)."""
    if bool(row.get("is_homoglyph", False)):
        return "homoglyph"
    if row.get("script_pair", "same") != "same":
        return "script_divergence"
    if str(row.get("corruption_types", "")):
        return "lexical"
    # same-script, no corruption -> orthographic/morphological (e.g. suffix transition).
    return "phonetic_orthographic"


def _fp_category(row: pd.Series) -> str:
    """Root cause for a spurious match (false positive)."""
    if str(row.get("hard_negative_type", "none")) not in ("none", "", "nan"):
        return "hard_negative_collision"
    if bool(row.get("is_homoglyph", False)):
        return "homoglyph"
    return "other"


def breakdown(df: pd.DataFrame, scores: np.ndarray, threshold: float) -> dict[str, dict]:
    """Per-category FP/FN counts (+ rates) for one matcher at ``threshold``."""
    pred = scores >= threshold
    labels = df["label"].to_numpy()
    is_fn = (~pred) & (labels == 1)
    is_fp = pred & (labels == 0)

    counts = {c: {"fp": 0, "fn": 0} for c in CATEGORIES}
    for idx in np.where(is_fn)[0]:
        counts[_fn_category(df.iloc[idx])]["fn"] += 1
    for idx in np.where(is_fp)[0]:
        counts[_fp_category(df.iloc[idx])]["fp"] += 1

    total_fn = int(is_fn.sum())
    total_fp = int(is_fp.sum())
    out: dict[str, dict] = {"threshold": float(threshold),
                            "total_fp": total_fp, "total_fn": total_fn, "by_category": {}}
    for c in CATEGORIES:
        fp, fn = counts[c]["fp"], counts[c]["fn"]
        out["by_category"][c] = {
            "fp": fp, "fn": fn,
            "fp_rate": (fp / total_fp) if total_fp else 0.0,
            "fn_rate": (fn / total_fn) if total_fn else 0.0,
        }
    return out
