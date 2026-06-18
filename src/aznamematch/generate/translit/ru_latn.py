"""Russian Cyrillic -> Latin under competing standards.

Standards (see docs/transliteration.md for citations):

- **ICAO Doc 9303** (machine-readable passports): ``ц→ts``, ``х→kh``, ``ъ→ie``, ``ю→iu``,
  ``я→ia``, ``й→i``.
- **GOST 7.79-2000 / ISO 9** (System B): univocal and **reversible** (``х→x``, ``ц→cz``,
  ``щ→shh``, soft/hard signs as backtick markers). :func:`gost_encode` / :func:`gost_decode`
  round-trip.
- **BGN/PCGN 1947**: ``е→ye`` initially and after a vowel; ``х→kh``; ``й→y``; ``я→ya``.
- **ALA-LC 1997**: scholarly, ``я→ia``, ``ю→iu``, ``й→ĭ``, ``э→ė``.

The *divergence between these* is the phenomenon under test (``х`` -> ``kh`` vs ``h``;
``я`` -> ``ia`` vs ``ya``; ``ъ`` -> ``ie`` vs a marker).
"""

from __future__ import annotations

from aznamematch.generate.translit.base import (
    ALA_LC,
    BGN_PCGN,
    GOST,
    ICAO,
    apply_ordered,
    map_chars,
)

_CYR_VOWELS = set("аеёиоуыэюя")

_ICAO: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "ie", "ы": "y", "ь": "", "э": "e",
    "ю": "iu", "я": "ia",
}

_ALA_LC: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "ë", "ж": "zh",
    "з": "z", "и": "i", "й": "ĭ", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "ʺ", "ы": "y", "ь": "ʹ", "э": "ė",
    "ю": "iu", "я": "ia",
}

# GOST 7.79-2000 System B (reversible). Multi-char codes are uniquely decodable when matched
# longest-first; soft/hard signs use backtick markers.
_GOST: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh",
    "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "cz",
    "ч": "ch", "ш": "sh", "щ": "shh", "ъ": "``", "ы": "y`", "ь": "`", "э": "e`",
    "ю": "yu", "я": "ya",
}

# BGN/PCGN 1947 base map (the е->ye context rule is applied separately).
_BGN: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya",
}


def _bgn_e_context(cyr: str) -> str:
    """Apply BGN/PCGN ``е -> ye`` initially and after a vowel; ``е -> e`` otherwise."""
    out: list[str] = []
    for idx, ch in enumerate(cyr):
        if ch in ("е", "Е"):
            prev = cyr[idx - 1].lower() if idx > 0 else ""
            ye = (idx == 0) or (prev in _CYR_VOWELS) or (not prev.isalpha())
            rep = "ye" if ye else "e"
            out.append(rep[0].upper() + rep[1:] if ch.isupper() else rep)
        else:
            out.append(ch)
    return "".join(out)


def romanize(cyr: str, standard: str) -> str:
    """Russian Cyrillic -> Latin under the given standard."""
    if standard == ICAO:
        return map_chars(cyr, _ICAO)
    if standard == ALA_LC:
        return map_chars(cyr, _ALA_LC)
    if standard == GOST:
        return gost_encode(cyr)
    if standard == BGN_PCGN:
        return map_chars(_bgn_e_context(cyr), {k: v for k, v in _BGN.items() if k != "е"})
    raise ValueError(f"Unsupported RU romanization standard: {standard!r}")


def gost_encode(cyr: str) -> str:
    """Russian Cyrillic -> GOST 7.79 System B Latin (reversible)."""
    return map_chars(cyr, _GOST)


def gost_decode(latin: str) -> str:
    """Inverse of :func:`gost_encode` (greedy longest-match), for round-trip verification."""
    rules = sorted(((v, k) for k, v in _GOST.items()), key=lambda kv: -len(kv[0]))
    return apply_ordered(latin, rules)
