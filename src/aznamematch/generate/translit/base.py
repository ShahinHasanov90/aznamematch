"""Shared types + case-aware substitution helpers for the transliteration modules."""

from __future__ import annotations

from dataclasses import dataclass

# script tags (see docs/dataset_schema.md)
LATN_AZ = "latn-az"
CYRL = "cyrl"
LATN_TRANSLIT = "latn-translit"

# translit_standard tags
ICAO = "ICAO"
GOST = "GOST"
ISO9 = "ISO9"
BGN_PCGN = "BGN_PCGN"
ALA_LC = "ALA_LC"
AD_HOC = "ad_hoc"
NONE = "none"


@dataclass(frozen=True)
class Variant:
    """A cross-script surface rendering of a name, with provenance."""

    text: str
    script: str
    standard: str


def _recase(src_char: str, mapped: str) -> str:
    """Apply the source character's case to its (possibly multi-char) mapping.

    Upper source -> Title-case the mapping (``Х`` -> ``Kh``, not ``KH``); lower -> as-is.
    """
    if src_char.isupper() and mapped:
        return mapped[0].upper() + mapped[1:]
    return mapped


def map_chars(text: str, lower_map: dict[str, str]) -> str:
    """Per-character substitution using a lowercase mapping, preserving source case.

    Characters absent from the map pass through unchanged.
    """
    out: list[str] = []
    for ch in text:
        low = ch.lower()
        if low in lower_map:
            out.append(_recase(ch, lower_map[low]))
        else:
            out.append(ch)
    return "".join(out)


def apply_ordered(text: str, rules: list[tuple[str, str]]) -> str:
    """Greedy left-to-right longest-match substitution over a lowercased copy of ``text``.

    Rules are matched against the lowercased text; the replacement is title-cased when the
    matched source span started with an uppercase character. ``rules`` should be ordered
    longest-source-first so multi-char clusters win over single chars.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    low = text.lower()
    while i < n:
        for src, dst in rules:
            if src and low.startswith(src, i):
                started_upper = text[i].isupper()
                out.append(dst[0].upper() + dst[1:] if (started_upper and dst) else dst)
                i += len(src)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)
