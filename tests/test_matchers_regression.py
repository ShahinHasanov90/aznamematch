"""Phase 6: RegressionV1 baseline."""

from __future__ import annotations

import pytest

from aznamematch.matchers.regression_v1 import FEATURE_NAMES, RegressionV1Matcher, features

# A tiny labeled train set: cross-script same-entity positives + unrelated negatives.
TRAIN = [
    ("Əli Hüseynov", "Ali Huseynov", 1),
    ("Əli Hüseynov", "Али Гусейнов", 1),
    ("Murad Quliyev", "Murad Guliev", 1),
    ("Murad Quliyev", "Мурад Гулиев", 1),
    ("Səbinə Məmmədova", "Sabina Mammadova", 1),
    ("Əli Hüseynov", "Murad Quliyev", 0),
    ("Murad Quliyev", "Səbinə Məmmədova", 0),
    ("Əli Hüseynov", "Səbinə Məmmədova", 0),
    ("Ali Huseynov", "Murad Guliev", 0),
    ("Sabina Mammadova", "Мурад Гулиев", 0),
]


def test_features_length_and_range():
    f = features("Əli Hüseynov", "Ali Huseynov")
    assert len(f) == len(FEATURE_NAMES)
    assert all(0.0 <= v <= 1.0 for v in f)


def test_requires_fit_before_score():
    m = RegressionV1Matcher()
    with pytest.raises(RuntimeError):
        m.score("a", "b")


def test_trains_and_separates_pos_from_neg():
    m = RegressionV1Matcher()
    pairs = [(a, b) for a, b, _ in TRAIN]
    labels = [y for _, _, y in TRAIN]
    m.fit(pairs, labels)
    pos = m.score("Əli Hüseynov", "Ali Huseynov")
    neg = m.score("Əli Hüseynov", "Murad Quliyev")
    assert 0.0 <= pos <= 1.0 and 0.0 <= neg <= 1.0
    assert pos > neg


def test_deterministic_training():
    pairs = [(a, b) for a, b, _ in TRAIN]
    labels = [y for _, _, y in TRAIN]
    m1 = RegressionV1Matcher()
    m1.fit(pairs, labels)
    m2 = RegressionV1Matcher()
    m2.fit(pairs, labels)
    probe = [("Əli Hüseynov", "Али Гусейнов"), ("Murad Quliyev", "Səbinə Məmmədova")]
    assert m1.scores(probe) == m2.scores(probe)
