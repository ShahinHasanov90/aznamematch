"""Phase 6: hybrid matcher (blend + cascade)."""

from __future__ import annotations

import pytest

from aznamematch.matchers.hybrid import HybridMatcher
from aznamematch.matchers.lexical import LexicalMatcher
from aznamematch.matchers.phonetic import PhoneticMatcher


def test_blend_in_range_and_between_components():
    lex, phon = LexicalMatcher("token_set"), PhoneticMatcher(normalize=True)
    h = HybridMatcher([(lex, 0.5), (phon, 0.5)], mode="blend")
    a, b = "Əliyev", "Алиев"
    s = h.score(a, b)
    lo, hi = sorted([lex.score(a, b), phon.score(a, b)])
    assert lo - 1e-9 <= s <= hi + 1e-9


def test_cascade_rescues_cross_script():
    # Lexical scores Əliyev~Алиев near 0; the phonetic confirmer should rescue it.
    lex, phon = LexicalMatcher("token_set"), PhoneticMatcher(normalize=True)
    assert lex.score("Əliyev", "Алиев") < 0.4
    h = HybridMatcher([(lex, 1.0), (phon, 1.0)], mode="cascade", gate=0.4)
    assert h.score("Əliyev", "Алиев") > 0.9


def test_cascade_accepts_confident_cheap():
    lex, phon = LexicalMatcher("token_set"), PhoneticMatcher(normalize=True)
    h = HybridMatcher([(lex, 1.0), (phon, 1.0)], mode="cascade", gate=0.4)
    assert h.score("Əli Hüseynov", "Əli Hüseynov") == pytest.approx(1.0)


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        HybridMatcher(mode="bogus").score("a", "b")
