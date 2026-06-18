"""Phase 7: evaluation metrics on hand-checked fixtures + ECT cost-ranking behavior."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aznamematch.eval import breakdown, cost, fairness, metrics, robustness


def test_prf1_at_known_values():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([0.9, 0.8, 0.2, 0.6])
    m = metrics.prf1_at(labels, scores, 0.5)  # pred T,T,F,T -> tp2 fp1 fn0
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["recall"] == pytest.approx(1.0)
    assert m["f1"] == pytest.approx(0.8)


def test_best_f1_and_auc_perfect_separation_threshold():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([0.9, 0.8, 0.2, 0.6])
    assert metrics.best_f1(labels, scores)["f1"] == pytest.approx(1.0)  # thr in (0.6,0.8]
    assert metrics.auc_scores(labels, scores)["roc_auc"] == pytest.approx(1.0)


def test_threshold_sensitivity_l2():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([0.9, 0.8, 0.2, 0.6])
    # F1 at .55=.8, .60=.8, .65=1.0 -> diffs (0, .2) -> l2 = .2
    assert metrics.threshold_sensitivity(labels, scores) == pytest.approx(0.2)


def test_auc_single_class_is_nan():
    labels = np.array([1, 1, 1])
    out = metrics.auc_scores(labels, np.array([0.1, 0.5, 0.9]))
    assert out["roc_auc"] != out["roc_auc"]  # NaN


def test_cost_ranking_responds_to_ratio():
    labels = np.array([1] * 10 + [0] * 10)
    # recaller: 3 negatives are inseparable from positives -> 3 unavoidable FP (no FN possible)
    recaller = np.array([0.9] * 10 + [0.9] * 3 + [0.1] * 7)
    # precise: 3 positives are inseparable from negatives -> 3 unavoidable FN (no FP possible)
    precise = np.array([0.9] * 7 + [0.1] * 3 + [0.1] * 10)
    cache = {"recaller": (labels, recaller), "precise": (labels, precise)}
    ranking = cost.rank_matchers(cache, [(1, 100), (100, 1)])  # (c_fp, c_fn)
    fn_heavy = ranking["c_fn:c_fp=100:1"]   # FN penalized 100x -> recaller wins
    fp_heavy = ranking["c_fn:c_fp=1:100"]   # FP penalized 100x -> precise wins
    assert fn_heavy[0]["matcher"] == "recaller"
    assert fp_heavy[0]["matcher"] == "precise"


def _row(label, script_pair, hard, corr, group, std):
    return {"label": label, "script_pair": script_pair, "hard_negative_type": hard,
            "corruption_types": corr, "name_origin_groups": group, "standards": std,
            "is_homoglyph": False}


def _toy_df():
    return pd.DataFrame([
        _row(1, "AZ-RU", "none", "", "russified", "ICAO"),          # cross-script positive
        _row(1, "same", "none", "char_edit", "russified", "none"),  # same-script typo positive
        _row(0, "same", "token_swap", "", "hardneg_token_swap", "none"),  # hard negative
    ])


def test_breakdown_attributes_categories():
    df = _toy_df()
    # scores: miss the AZ-RU positive (FN, script_divergence); the same-script typo positive is
    # caught; the token_swap negative is wrongly matched (FP, hard_negative_collision).
    scores = np.array([0.1, 0.9, 0.9])
    b = breakdown.breakdown(df, scores, 0.5)
    assert b["by_category"]["script_divergence"]["fn"] == 1
    assert b["by_category"]["hard_negative_collision"]["fp"] == 1
    assert b["total_fn"] == 1 and b["total_fp"] == 1


def test_fairness_and_robustness_run():
    df = _toy_df()
    scores = np.array([0.6, 0.6, 0.4])
    fr = fairness.fairness(df, scores, 0.5, min_pos=1)
    assert "by_group" in fr and 0.0 <= fr["max_f1_gap"] <= 1.0
    cs = robustness.cross_standard_score(df, scores)
    assert "robustness" in cs  # may be NaN on a tiny fixture, but key must exist
