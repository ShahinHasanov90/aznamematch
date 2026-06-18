"""Phase 4 (part 1): surface-form construction.

For each canonical identity we materialize the set of *surface forms* it can appear as:
the canonical AZ-Latin name, its cross-script transliterations (Phase 2), the same-entity
suffix-matrix renderings (Phase 1) and their transliterations, and corrupted twins of those
(Phase 3). Every surface carries the full provenance schema (see docs/dataset_schema.md), so
pair construction and later evaluation can slice without regenerating data.

Homoglyph (Phase 3b) surfaces are NOT created here — they belong to the separate frozen
adversarial set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from aznamematch.config import get
from aznamematch.generate import noise
from aznamematch.generate.canonical import Identity
from aznamematch.generate.translit import generate_variants
from aznamematch.generate.translit.base import CYRL, LATN_AZ, NONE


@dataclass(frozen=True)
class SurfaceForm:
    """One observed rendering of an identity, with full provenance."""

    canonical_id: str
    entity_type: str
    surface: str
    script: str
    translit_standard: str
    corruption_types: tuple[str, ...]
    suffix_transform: str
    name_origin_group: str
    given: str = ""
    patronymic: str = ""
    family: str = ""
    org_tokens: tuple[str, ...] = ()
    is_homoglyph: bool = False
    homoglyph_codepoints: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "entity_type": self.entity_type,
            "surface": self.surface,
            "script": self.script,
            "translit_standard": self.translit_standard,
            "corruption_types": ";".join(self.corruption_types),
            "suffix_transform": self.suffix_transform,
            "name_origin_group": self.name_origin_group,
            "given": self.given,
            "patronymic": self.patronymic,
            "family": self.family,
            "org_tokens": " ".join(self.org_tokens),
            "is_homoglyph": self.is_homoglyph,
            "homoglyph_codepoints": self.homoglyph_codepoints,
        }


def _join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _base_renderings(ident: Identity) -> list[tuple[str, str, str, str, str]]:
    """List of (full_text, suffix_transform, given, patronymic, family) for an identity."""
    if ident.entity_type == "org":
        return [(ident.canonical, "none", "", "", "")]

    out: list[tuple[str, str, str, str, str]] = [
        (ident.canonical, "none", ident.given, ident.patronymic, ident.family)
    ]
    for fv in ident.family_variants:
        text = _join([ident.given, ident.patronymic, fv.text])
        out.append((text, fv.suffix_transform, ident.given, ident.patronymic, fv.text))
    if ident.russified_patronymic:
        text = _join([ident.given, ident.russified_patronymic, ident.family])
        out.append((text, "patronymic", ident.given, ident.russified_patronymic, ident.family))
    return out


def _patronymic_indices(patronymic: str) -> list[int] | None:
    """Token positions of the patronymic in a ``given [patronymic] family`` rendering."""
    if not patronymic:
        return None
    return list(range(1, 1 + len(patronymic.split())))


def build_surfaces(ident: Identity, cfg: dict[str, Any],
                   rng: np.random.Generator) -> list[SurfaceForm]:
    """All clean + corrupted surface forms for one identity, deduped by (script, surface)."""
    surfaces: list[SurfaceForm] = []
    seen: set[tuple[str, str]] = set()
    is_person = ident.entity_type == "person"

    def add(text: str, script: str, standard: str, stf: str,
            corruption: tuple[str, ...], g: str, p: str, f: str) -> None:
        key = (script, text)
        if not text or key in seen:
            return
        seen.add(key)
        surfaces.append(SurfaceForm(
            canonical_id=ident.canonical_id, entity_type=ident.entity_type, surface=text,
            script=script, translit_standard=standard, corruption_types=corruption,
            suffix_transform=stf, name_origin_group=ident.name_origin_group,
            given=g, patronymic=p, family=f, org_tokens=ident.org_tokens,
        ))

    for text, stf, g, p, f in _base_renderings(ident):
        add(text, LATN_AZ, NONE, stf, (), g, p, f)
        for v in generate_variants(text, produce_russian=is_person, cfg=cfg, rng=rng):
            add(v.text, v.script, v.standard, stf, (), g, p, f)

    clean = list(surfaces)  # snapshot before any corruption is appended

    def corrupt_once(sf: SurfaceForm) -> None:
        droppable = _patronymic_indices(sf.patronymic) if sf.script == LATN_AZ else None
        ctext, ctypes = noise.corrupt(
            sf.surface, sf.script, rng, cfg, droppable_indices=droppable
        )
        if ctypes and ctext != sf.surface:
            add(ctext, sf.script, sf.translit_standard, sf.suffix_transform,
                tuple(ctypes), sf.given, sf.patronymic, sf.family)

    # Standard corruption pass: a corrupted twin for a fraction of all clean surfaces.
    p_corrupt = float(get(cfg, "noise.p_surface_corrupted", 0.5))
    for sf in clean:
        if rng.random() < p_corrupt:
            corrupt_once(sf)

    # Cyrillic emphasis: extra corrupted twins for each clean Cyrillic surface, so AZ-RU pairs
    # can be drawn with diversity (Cyrillic is otherwise outnumbered by Latin romanizations).
    extra_cyr = int(get(cfg, "noise.cyrillic_extra_corrupted", 0))
    for sf in clean:
        if sf.script == CYRL:
            for _ in range(extra_cyr):
                corrupt_once(sf)

    return surfaces
