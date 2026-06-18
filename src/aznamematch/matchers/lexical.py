"""Lexical matchers: rapidfuzz string-similarity strategies + Jaro-Winkler."""

from __future__ import annotations

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from aznamematch.matchers.base import Matcher, register


@register
class LexicalMatcher(Matcher):
    """Edit/token-based string similarity. ``strategy`` selects the rapidfuzz scorer.

    - ``token_set`` (default): order- and duplicate-insensitive token ratio.
    - ``wratio``: rapidfuzz's weighted composite ratio.
    - ``jaro_winkler``: prefix-weighted edit similarity.
    """

    name = "lexical"

    def __init__(self, strategy: str = "token_set") -> None:
        self.strategy = strategy
        self.name = "lexical" if strategy == "token_set" else f"lexical_{strategy}"

    def score(self, a: str, b: str) -> float:
        if self.strategy == "token_set":
            return fuzz.token_set_ratio(a, b) / 100.0
        if self.strategy == "wratio":
            return fuzz.WRatio(a, b) / 100.0
        if self.strategy == "jaro_winkler":
            return float(JaroWinkler.similarity(a, b))
        raise ValueError(f"Unknown lexical strategy: {self.strategy!r}")
