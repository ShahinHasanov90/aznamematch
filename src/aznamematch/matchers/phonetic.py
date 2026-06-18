"""Phonetic matcher: jellyfish phonetic coding preceded by the AZ-RU normalization layer.

This is where the cross-script normalization (``matchers/normalize.py``) pays off: vanilla
Soundex/Metaphone of ``Əliyev`` and ``Aliyev`` diverge (and choke on the non-ASCII schwa),
but after normalization both reduce to the same skeleton and hence the same phonetic code.

Score = Jaccard overlap of the two names' per-token phonetic-code sets, so it is robust to
token reordering and to a dropped patronymic.
"""

from __future__ import annotations

import jellyfish

from aznamematch.matchers.base import Matcher, register
from aznamematch.matchers.normalize import normalize_name

_ALGOS = {
    "soundex": jellyfish.soundex,
    "metaphone": jellyfish.metaphone,
    "nysiis": jellyfish.nysiis,
}


@register
class PhoneticMatcher(Matcher):
    """``algo`` in {soundex, metaphone, nysiis}; ``normalize`` toggles the AZ-RU layer."""

    name = "phonetic"

    def __init__(self, algo: str = "metaphone", normalize: bool = True) -> None:
        if algo not in _ALGOS:
            raise ValueError(f"Unknown phonetic algo: {algo!r}")
        self.algo = algo
        self.normalize = normalize
        self.name = "phonetic" if normalize else "phonetic_vanilla"

    def _codes(self, name: str) -> set[str]:
        tokens = normalize_name(name) if self.normalize else name.split()
        fn = _ALGOS[self.algo]
        codes: set[str] = set()
        for tok in tokens:
            try:
                code = fn(tok)
            except (UnicodeDecodeError, UnicodeEncodeError, ValueError):
                code = tok.lower()  # non-ASCII token vanilla coders can't handle
            if code:
                codes.add(code)
        return codes

    def score(self, a: str, b: str) -> float:
        ca, cb = self._codes(a), self._codes(b)
        if not ca or not cb:
            return 0.0
        return len(ca & cb) / len(ca | cb)
