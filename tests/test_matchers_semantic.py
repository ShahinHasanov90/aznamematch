"""Phase 6: semantic matcher (guarded — skips if the model can't be loaded offline)."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def matcher():
    st = pytest.importorskip("sentence_transformers")  # noqa: F841
    from aznamematch.matchers.semantic import SemanticMatcher

    m = SemanticMatcher()
    try:
        m._ensure()  # load (downloads weights on first run)
    except Exception as exc:  # pragma: no cover - network/offline
        pytest.skip(f"semantic model unavailable: {exc}")
    return m


def test_scores_in_range_and_rank(matcher):
    pairs = [("Əliyev", "Алиев"), ("Əli Hüseynov", "Murad Quliyev")]
    s = matcher.scores(pairs)
    assert all(0.0 <= x <= 1.0 for x in s)
    # Same entity across scripts should rank above an unrelated pair.
    assert s[0] > s[1]


def test_batch_matches_single(matcher):
    a, b = "Səbinə Məmmədova", "Sabina Mammadova"
    assert matcher.scores([(a, b)])[0] == pytest.approx(matcher.score(a, b), abs=1e-5)
