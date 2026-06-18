"""Cross-script transliteration (AZ Latin<->Cyrillic, RU Cyrillic->Latin, ad-hoc).

``generate_variants`` ties the modules together: from one canonical AZ-Latin name it emits
the national Cyrillic surface, AZ->Latin romanizations (BGN/PCGN, ALA-LC), and — for persons,
who would also appear in Russian-language records — the Russified Russian-Cyrillic surface
plus its ICAO / GOST / BGN-PCGN / ALA-LC romanizations, and standardless ad-hoc spellings.
Each output is a :class:`Variant` carrying its script + standard provenance.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aznamematch.config import get
from aznamematch.generate.translit import adhoc, az_cyrl, ru_latn
from aznamematch.generate.translit.base import (
    AD_HOC,
    ALA_LC,
    BGN_PCGN,
    CYRL,
    GOST,
    ICAO,
    LATN_TRANSLIT,
    NONE,
    Variant,
)

__all__ = ["Variant", "generate_variants"]

# RU romanization standards in priority order (first to claim a given output text wins).
_RU_STANDARDS = (ICAO, GOST, BGN_PCGN, ALA_LC)
_AZ_LATIN_STANDARDS = (BGN_PCGN, ALA_LC)


def _enabled(cfg: dict[str, Any], dotted: str) -> bool:
    return bool(get(cfg, dotted, False))


def generate_variants(
    name: str,
    *,
    produce_russian: bool,
    cfg: dict[str, Any],
    rng: np.random.Generator,
) -> list[Variant]:
    """All cross-script renderings of ``name`` enabled by ``cfg``, deduplicated by surface.

    ``produce_russian`` gates the Russian-Cyrillic + RU-romanization branch (persons only).
    """
    out: list[Variant] = []
    seen: set[tuple[str, str]] = {(NONE, name)}  # never re-emit the source latn-az form

    def add(v: Variant) -> None:
        key = (v.script, v.text)
        if v.text and key not in seen:
            seen.add(key)
            out.append(v)

    # National Azerbaijani Cyrillic surface (reversible alphabet).
    add(Variant(az_cyrl.to_cyrillic(name), CYRL, NONE))

    # AZ Latin -> ASCII Latin romanizations.
    for std in _AZ_LATIN_STANDARDS:
        if _enabled(cfg, f"transliteration.az_cyrl.{std}"):
            add(Variant(az_cyrl.romanize(name, std), LATN_TRANSLIT, std))

    # Russified branch: Russian Cyrillic surface + its competing romanizations.
    if produce_russian:
        rus_cyr = az_cyrl.az_to_russian_cyrillic(name)
        add(Variant(rus_cyr, CYRL, NONE))
        for std in _RU_STANDARDS:
            if _enabled(cfg, f"transliteration.ru_latn.{std}"):
                add(Variant(ru_latn.romanize(rus_cyr, std), LATN_TRANSLIT, std))

    # Ad-hoc standardless spellings.
    if _enabled(cfg, "transliteration.adhoc.enabled"):
        max_v = int(get(cfg, "transliteration.adhoc.max_variants", 3))
        for text in adhoc.variants(name, rng, max_v):
            add(Variant(text, LATN_TRANSLIT, AD_HOC))

    return out
