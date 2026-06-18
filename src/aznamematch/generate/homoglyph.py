"""Phase 3b: adversarial homoglyph layer (a SEPARATE threat model).

Substitutes Latin letters with visually-identical Cyrillic code points (Unicode TR39
confusables) — the IDN-homograph / sanctions-evasion technique. This is *deliberate*
obfuscation, deliberately kept OUT of the core positive set (which models *incidental*
cross-script divergence); the attacked pairs are frozen into
``data/adversarial/homoglyph_v1/``.

Important nuance (documented in docs/homoglyphs.md): at the code-point level Cyrillic ``с`` ≠
Latin ``c``, so a raw lexical matcher fails catastrophically. **Plain `unidecode` does NOT
fix this** — it transliterates by *sound* (Cyrillic ``С`` -> ``s``, ``Х`` -> ``kh``), not by
*shape*. The correct repair is the **TR39 confusable skeleton** (:func:`confusable_fold`),
which maps each confusable back to its Latin shape. So this slice is essentially a binary
capability check: "does the matcher apply TR39 confusable folding?" — not graded difficulty.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

# Latin -> Cyrillic visual confusables (Unicode TR39). Shape-identical, different code point.
HOMOGLYPHS: dict[str, str] = {
    # uppercase
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "I": "І", "J": "Ј", "K": "К",
    "M": "М", "O": "О", "P": "Р", "S": "Ѕ", "T": "Т", "X": "Х", "Y": "У",
    # lowercase
    "a": "а", "c": "с", "e": "е", "h": "һ", "i": "і", "j": "ј", "k": "к", "m": "м",
    "o": "о", "p": "р", "s": "ѕ", "x": "х", "y": "у",
}

# Inverse: Cyrillic confusable -> Latin shape (lowercased). The TR39 "skeleton" fold.
_CONFUSABLE_TO_LATIN: dict[str, str] = {}
for _lat, _cyr in HOMOGLYPHS.items():
    _CONFUSABLE_TO_LATIN[_cyr] = _lat.lower()

# AZ Latin special letters -> ASCII (for the optional diacritic-strip step).
_AZ_STRIP = {"ə": "e", "ğ": "g", "ç": "c", "ş": "s", "ö": "o", "ü": "u", "ı": "i"}

_WS = re.compile(r"\s+")


def confusable_fold(text: str) -> str:
    """TR39-skeleton fold: map Cyrillic confusables back to Latin shape, then casefold.

    This is the preprocessing that defeats the homoglyph attack (and which plain `unidecode`
    does not provide). ``confusable_fold(attacked) == confusable_fold(clean)``.
    """
    folded = "".join(_CONFUSABLE_TO_LATIN.get(ch, ch) for ch in text)
    return _WS.sub(" ", folded).strip().casefold()


def strip_az_diacritics(text: str) -> str:
    out = []
    for ch in text:
        rep = _AZ_STRIP.get(ch.lower())
        if rep is None:
            out.append(ch)
        else:
            out.append(rep.upper() if ch.isupper() else rep)
    return "".join(out)


@dataclass(frozen=True)
class HomoglyphAttack:
    """A clean Latin surface and its homoglyph-obfuscated twin."""

    clean: str
    attacked: str
    swapped_codepoints: tuple[str, ...]  # e.g. ("a->U+0430", "e->U+0435")
    diacritics_stripped: bool

    @property
    def is_attack(self) -> bool:
        return bool(self.swapped_codepoints)


def attack(name: str, rng: np.random.Generator, *, p_char_swap: float,
           p_diacritic_strip: float) -> HomoglyphAttack:
    """Build a homoglyph attack on ``name`` (an AZ/Latin surface), deterministically.

    With probability ``p_diacritic_strip`` the AZ diacritics are removed first (a common
    real obfuscation), then each eligible Latin letter is swapped to its Cyrillic confusable
    with probability ``p_char_swap``. At least one swap is forced when any letter is eligible.
    """
    stripped = rng.random() < p_diacritic_strip
    clean = strip_az_diacritics(name) if stripped else name

    eligible = [i for i, ch in enumerate(clean) if ch in HOMOGLYPHS]
    chars = list(clean)
    swaps: list[str] = []

    if eligible:
        chosen = [i for i in eligible if rng.random() < p_char_swap]
        if not chosen:  # guarantee the attack actually obfuscates something
            chosen = [eligible[int(rng.integers(0, len(eligible)))]]
        for i in chosen:
            cyr = HOMOGLYPHS[chars[i]]
            swaps.append(f"{chars[i]}->U+{ord(cyr):04X}")
            chars[i] = cyr

    return HomoglyphAttack(
        clean=clean,
        attacked="".join(chars),
        swapped_codepoints=tuple(swaps),
        diacritics_stripped=stripped,
    )
