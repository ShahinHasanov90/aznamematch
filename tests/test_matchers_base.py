"""Phase 6: matcher base + registry."""

from __future__ import annotations

import pytest

import aznamematch.matchers  # noqa: F401  (triggers registration)
from aznamematch.matchers.base import Matcher, available, get_matcher


def test_registry_has_core_matchers():
    names = available()
    assert "lexical" in names
    assert "phonetic" in names


def test_get_matcher_returns_instance():
    m = get_matcher("lexical")
    assert isinstance(m, Matcher)
    assert 0.0 <= m.score("Əli", "Əli") <= 1.0


def test_unknown_matcher_raises():
    with pytest.raises(KeyError):
        get_matcher("does_not_exist")


def test_scores_batch_matches_score():
    m = get_matcher("phonetic")
    pairs = [("Əliyev", "Aliyev"), ("Murad", "Quliyev")]
    assert m.scores(pairs) == [m.score(*p) for p in pairs]


def test_fit_is_noop_for_unsupervised():
    m = get_matcher("lexical")
    assert m.fit([("a", "b")], [1]) is None
