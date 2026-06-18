"""Phase 6: phonetic matcher + the AZ-RU normalization contribution."""

from __future__ import annotations

import pytest

from aznamematch.matchers.normalize import normalize_token
from aznamematch.matchers.phonetic import PhoneticMatcher


@pytest.mark.parametrize("algo", ["soundex", "metaphone", "nysiis"])
def test_normalization_fixes_schwa_case_that_vanilla_misses(algo):
    """The documented ə/e case: passes after normalization, fails vanilla."""
    normalized = PhoneticMatcher(algo, normalize=True).score("Əliyev", "Aliyev")
    vanilla = PhoneticMatcher(algo, normalize=False).score("Əliyev", "Aliyev")
    assert normalized == pytest.approx(1.0)
    assert normalized > vanilla


def test_cross_script_phonetic_match():
    m = PhoneticMatcher(normalize=True)
    assert m.score("Əliyev", "Алиев") == pytest.approx(1.0)
    assert m.score("Hasanov", "Наѕаnоv") == pytest.approx(1.0)  # homoglyph folds too


def test_range_identical_unrelated():
    m = PhoneticMatcher(normalize=True)
    assert m.score("Əli Hüseynov", "Əli Hüseynov") == pytest.approx(1.0)
    assert 0.0 <= m.score("Əli Hüseynov", "Murad Quliyev") < 0.5


def test_token_order_invariance():
    # Set-based codes -> reordering tokens does not change the score.
    m = PhoneticMatcher(normalize=True)
    assert m.score("Əli Vəli oğlu", "Vəli Əli oğlu") == pytest.approx(1.0)


def test_normalize_token_convergence_and_separation():
    assert normalize_token("Əliyev") == normalize_token("Aliyev") == normalize_token("Алиев")
    assert normalize_token("Aliyev") != normalize_token("Mammadov")


def test_invalid_algo_raises():
    with pytest.raises(ValueError):
        PhoneticMatcher("bogus")
