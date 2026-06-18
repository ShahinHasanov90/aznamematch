"""RegressionV1 — a nomenklatura-style logistic-regression baseline (name-centric subset).

OpenSanctions' production ``RegressionV1`` is an 18-feature logistic regression over name,
date, identifier and demographic similarity. Our labeled pairs carry only surface strings
(no DOB/ID at the pair level), so we replicate the **name-centric feature subset**: token
overlap, edit similarity, Jaro-Winkler, a cross-script phonetic-match signal, normalized-token
overlap, length ratio, and first/last-token agreement. Trained on a synthetic train split.
"""

from __future__ import annotations

import numpy as np
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from aznamematch.matchers.base import Matcher, register
from aznamematch.matchers.normalize import normalize_name
from aznamematch.matchers.phonetic import PhoneticMatcher

FEATURE_NAMES = (
    "token_set_ratio", "wratio", "jaro_winkler", "phonetic_jaccard",
    "norm_token_jaccard", "length_ratio", "first_token_eq", "last_token_eq",
)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


_PHON = PhoneticMatcher(normalize=True)


def features(a: str, b: str) -> list[float]:
    """The name-centric feature vector for a surface pair."""
    na, nb = normalize_name(a), normalize_name(b)
    set_a, set_b = set(na), set(nb)
    la, lb = len(a), len(b)
    return [
        fuzz.token_set_ratio(a, b) / 100.0,
        fuzz.WRatio(a, b) / 100.0,
        float(JaroWinkler.similarity(a, b)),
        _PHON.score(a, b),
        _jaccard(set_a, set_b),
        (min(la, lb) / max(la, lb)) if max(la, lb) else 1.0,
        float(bool(na) and bool(nb) and na[0] == nb[0]),
        float(bool(na) and bool(nb) and na[-1] == nb[-1]),
    ]


@register
class RegressionV1Matcher(Matcher):
    """Logistic regression over :func:`features`. Must be ``fit`` before scoring."""

    name = "regression_v1"
    requires_training = True

    def __init__(self) -> None:
        self._model = None

    def fit(self, pairs: list[tuple[str, str]], labels: list[int]) -> None:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        x = np.array([features(a, b) for a, b in pairs], dtype=float)
        y = np.array(labels, dtype=int)
        self._model = make_pipeline(
            StandardScaler(),
            LogisticRegression(random_state=0, max_iter=1000),
        )
        self._model.fit(x, y)

    def _check(self):
        if self._model is None:
            raise RuntimeError("RegressionV1Matcher must be fit() before scoring.")

    def score(self, a: str, b: str) -> float:
        self._check()
        x = np.array([features(a, b)], dtype=float)
        return float(self._model.predict_proba(x)[0, 1])

    def scores(self, pairs: list[tuple[str, str]]) -> list[float]:
        self._check()
        x = np.array([features(a, b) for a, b in pairs], dtype=float)
        return [float(p) for p in self._model.predict_proba(x)[:, 1]]
