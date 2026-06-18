"""Azerbaijani Latin <-> Cyrillic, plus AZ-Latin -> Latin romanization profiles.

Three jobs:

1. ``to_cyrillic`` / ``to_latin`` — the **Soviet Azerbaijani Cyrillic alphabet** (1958-1991),
   a bijective script mapping (round-trippable; ``docs/transliteration.md``). This yields the
   national ``cyrl`` surface (``Əliyev`` -> ``Әлијев``).
2. ``az_to_russian_cyrillic`` — the **Russified** Russian-Cyrillic rendering used in
   Soviet/Russian documents (``Əliyev`` -> ``Алиев``, ``Hüseyn`` -> ``Гусейн``). Lossy,
   many-to-one. Tagged ``cyrl``.
3. ``romanize`` — AZ Latin -> plain-ASCII Latin under competing **BGN/PCGN** and **ALA-LC**
   profiles. The salient divergences (``ə`` -> ``e``/``a``; ``ğ`` -> ``gh``/``g``) are what
   make matching hard. Tagged ``latn-translit``.
"""

from __future__ import annotations

from aznamematch.generate.translit.base import (
    ALA_LC,
    BGN_PCGN,
    apply_ordered,
)

# --- Soviet Azerbaijani Cyrillic alphabet (bijective) ----------------------------------
# Lowercase Latin -> Cyrillic. The dotted/dotless I pair (i/ı/İ/I) is handled explicitly in
# the conversion functions to avoid Python's locale-independent casing of U+0130/U+0131.
_AZ_LAT_TO_CYR: dict[str, str] = {
    "a": "а", "b": "б", "c": "ҹ", "ç": "ч", "d": "д", "e": "е", "ə": "ә", "f": "ф",
    "g": "ҝ", "ğ": "ғ", "h": "һ", "x": "х", "j": "ж", "k": "к", "q": "г", "l": "л",
    "m": "м", "n": "н", "o": "о", "ö": "ө", "p": "п", "r": "р", "s": "с", "ş": "ш",
    "t": "т", "u": "у", "ü": "ү", "v": "в", "y": "ј", "z": "з", "i": "и", "ı": "ы",
}
_AZ_CYR_TO_LAT: dict[str, str] = {c: latin for latin, c in _AZ_LAT_TO_CYR.items()}

# Explicit I-family overrides (both directions).
_I_LAT_TO_CYR = {"İ": "И", "I": "Ы", "i": "и", "ı": "ы"}
_I_CYR_TO_LAT = {"И": "İ", "Ы": "I", "и": "i", "ы": "ı"}


def to_cyrillic(name: str) -> str:
    """AZ Latin -> Soviet Azerbaijani Cyrillic (national ``cyrl`` surface)."""
    out: list[str] = []
    for ch in name:
        if ch in _I_LAT_TO_CYR:
            out.append(_I_LAT_TO_CYR[ch])
            continue
        low = ch.lower()
        if low in _AZ_LAT_TO_CYR:
            mapped = _AZ_LAT_TO_CYR[low]
            out.append(mapped.upper() if ch.isupper() else mapped)
        else:
            out.append(ch)
    return "".join(out)


def to_latin(cyr: str) -> str:
    """Soviet Azerbaijani Cyrillic -> AZ Latin (inverse of :func:`to_cyrillic`)."""
    out: list[str] = []
    for ch in cyr:
        if ch in _I_CYR_TO_LAT:
            out.append(_I_CYR_TO_LAT[ch])
            continue
        low = ch.lower()
        if low in _AZ_CYR_TO_LAT:
            mapped = _AZ_CYR_TO_LAT[low]
            out.append(mapped.upper() if ch.isupper() else mapped)
        else:
            out.append(ch)
    return "".join(out)


# --- AZ-safe lowercasing (dodge U+0130/U+0131 casing surprises) ------------------------
def az_lower(name: str) -> str:
    return name.replace("İ", "i").replace("I", "ı").lower()


def _titlecase_tokens(text: str) -> str:
    return " ".join(w[:1].upper() + w[1:] if w else w for w in text.split(" "))


# --- Russified Russian-Cyrillic rendering (lossy) --------------------------------------
# Ordered longest-first: y-clusters and AZ specials before base letters.
_RU_CYR_RULES: list[tuple[str, str]] = [
    ("iyeva", "иева"), ("iyev", "иев"), ("iya", "ия"),
    ("yeva", "ева"), ("yev", "ев"),
    ("ya", "я"), ("yu", "ю"), ("yo", "ё"), ("ye", "е"), ("y", "й"),
    ("ç", "ч"), ("ş", "ш"), ("c", "дж"), ("x", "х"), ("q", "г"), ("ğ", "г"),
    ("ö", "о"), ("ü", "у"), ("ə", "а"), ("ı", "ы"), ("h", "г"),
    ("a", "а"), ("b", "б"), ("d", "д"), ("e", "е"), ("f", "ф"), ("g", "г"),
    ("i", "и"), ("j", "ж"), ("k", "к"), ("l", "л"), ("m", "м"), ("n", "н"),
    ("o", "о"), ("p", "п"), ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"),
    ("v", "в"), ("z", "з"),
]


def az_to_russian_cyrillic(name: str) -> str:
    """AZ Latin -> Russified Russian Cyrillic (e.g. ``Əliyev`` -> ``Алиев``)."""
    return _titlecase_tokens(apply_ordered(az_lower(name), _RU_CYR_RULES))


# --- AZ Latin -> ASCII Latin romanization profiles ------------------------------------
# Only the AZ special letters need rewriting; plain ASCII letters pass through. The profiles
# deliberately diverge on the schwa (ə) and ğ, which is the phenomenon under test.
_PROFILE_BGN_PCGN: dict[str, str] = {
    "ə": "e", "x": "kh", "q": "g", "c": "j", "ç": "ch", "ş": "sh", "ğ": "gh",
    "ö": "o", "ü": "u", "ı": "i", "j": "zh",
}
_PROFILE_ALA_LC: dict[str, str] = {
    "ə": "a", "x": "kh", "q": "g", "c": "j", "ç": "ch", "ş": "sh", "ğ": "g",
    "ö": "o", "ü": "u", "ı": "i", "j": "zh",
}
_PROFILES: dict[str, dict[str, str]] = {
    BGN_PCGN: _PROFILE_BGN_PCGN,
    ALA_LC: _PROFILE_ALA_LC,
}


def romanize(name: str, standard: str) -> str:
    """AZ Latin -> ASCII Latin under ``BGN_PCGN`` or ``ALA_LC`` (``latn-translit``)."""
    if standard not in _PROFILES:
        raise ValueError(f"Unsupported AZ romanization standard: {standard!r}")
    rules = sorted(_PROFILES[standard].items(), key=lambda kv: -len(kv[0]))
    return _titlecase_tokens(apply_ordered(az_lower(name), rules))
