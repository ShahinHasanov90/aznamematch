"""Text normalization helpers shared across the pipeline.

``fold_ascii`` is the canonical "are these the same string ignoring script/diacritics/case"
fold. It is used by the denylist guard (Phase 1) and by the homoglyph tests (Phase 3b),
where a Cyrillic-confusable attack must differ at the code-point level yet fold to the same
ASCII as its Latin source.
"""

from __future__ import annotations

import re

from unidecode import unidecode

_WS = re.compile(r"\s+")


def fold_ascii(text: str) -> str:
    """Casefold + transliterate-to-ASCII (unidecode) + collapse whitespace.

    This is intentionally lossy. Its key property for the homoglyph threat model: a Latin
    string and its Cyrillic-confusable attack fold identically — ``"Aliyev"`` and the
    homoglyph ``"Аliyev"`` (Cyrillic ``А``, U+0410) both fold to ``"aliyev"``. That models
    the confusable-folding preprocessing a robust matcher would apply.

    (Note: unidecode maps the AZ schwa ``ə`` to ``@``, so AZ-Latin forms do not necessarily
    fold to their plain-Latin transliterations — fold equality is used here only as the
    confusable-folding check, not as a name-equivalence oracle.)
    """
    return _WS.sub(" ", unidecode(text).casefold()).strip()
