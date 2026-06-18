"""Phase 6: lexical matchers."""

from __future__ import annotations

import pytest

from aznamematch.matchers.lexical import LexicalMatcher


@pytest.mark.parametrize("strategy", ["token_set", "wratio", "jaro_winkler"])
def test_range_and_identical(strategy):
    m = LexicalMatcher(strategy)
    assert m.score("Əli Hüseynov", "Əli Hüseynov") == pytest.approx(1.0)
    assert 0.0 <= m.score("Əli", "Murad") <= 1.0


def test_unrelated_low():
    m = LexicalMatcher("token_set")
    assert m.score("Əli Hüseynov", "Murad Quliyev") < 0.5


def test_token_set_is_order_insensitive():
    m = LexicalMatcher("token_set")
    assert m.score("Əli Vəli oğlu", "Vəli Əli oğlu") == pytest.approx(1.0)


def test_token_swap_is_hard_for_lexical():
    # The token_swap hard negative is *meant* to fool lexical matchers (high score, label 0).
    m = LexicalMatcher("token_set")
    assert m.score("Bəxtiyar Elgün oğlu", "Elgün Bəxtiyar oğlu") > 0.9


def test_invalid_strategy_raises():
    with pytest.raises(ValueError):
        LexicalMatcher("bogus").score("a", "b")
