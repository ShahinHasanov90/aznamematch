"""Post-Soviet suffix transition matrix.

A single AZ name root is rendered across eras/styles: contemporary-national
(``Əli -> Əlizadə / Əlisoy / Əlli``), Soviet/Russified (``Əli -> Əliyev`` and onward to
Cyrillic ``Алиев`` in the transliteration phase), and patronymic (AZ ``Vaqif oğlu`` vs
Russified ``Vaqifoviç`` / Cyrillic ``Вагифович``).

MODELING ASSUMPTION (see docs/suffix_matrix.md): treating ``Əlizadə`` and ``Əliyev`` as the
SAME entity is a deliberate choice reflecting how a single family's surname has been
rendered differently across political eras. It is *not* a universal truth that every such
pair is the same person. The benchmark measures matching under this stated assumption.

All renderings here stay in AZ Latin (with AZ letters). Conversion to Cyrillic / other-Latin
transliterations happens in the Phase 2 ``translit`` package.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# AZ vowel sets for harmony.
_BACK_UNROUNDED = set("aı")
_BACK_ROUNDED = set("ou")
_FRONT_UNROUNDED = set("eəi")
_FRONT_ROUNDED = set("öü")
_VOWELS = _BACK_UNROUNDED | _BACK_ROUNDED | _FRONT_UNROUNDED | _FRONT_ROUNDED

# Family-name styles. "russified" is the Soviet -ov/-yev assimilation; the rest are
# contemporary-national forms.
RUSSIFIED = "russified"
NATIONAL_STYLES: tuple[str, ...] = ("zade", "soy", "li")
ALL_STYLES: tuple[str, ...] = (RUSSIFIED, *NATIONAL_STYLES)

# Suffix-transform tags (match docs/dataset_schema.md and provenance-metadata rule).
T_NONE = "none"
T_NATIONAL = "national"
T_ASSIMILATION = "assimilation"
T_PATRONYMIC = "patronymic"


@dataclass(frozen=True)
class FamilyVariant:
    """An alternative AZ-Latin family surface for the same root, vs the canonical form."""

    text: str
    style: str
    suffix_transform: str


def _last_vowel(root: str) -> str | None:
    for ch in reversed(root.casefold()):
        if ch in _VOWELS:
            return ch
    return None


def _li_suffix(root: str) -> str:
    """4-way vowel-harmony variant of the ``-lı/-li/-lu/-lü`` national suffix."""
    v = _last_vowel(root)
    if v in _BACK_UNROUNDED or v is None:
        return "lı"
    if v in _BACK_ROUNDED:
        return "lu"
    if v in _FRONT_ROUNDED:
        return "lü"
    return "li"  # front unrounded


def _ends_in_vowel(root: str) -> bool:
    return bool(root) and root.casefold()[-1] in _VOWELS


def render_family(root: str, gender: str, style: str) -> str:
    """Render ``root`` as a family name in the given ``style`` and ``gender`` (``m``/``f``)."""
    if style == RUSSIFIED:
        if _ends_in_vowel(root):
            return root + ("yev" if gender == "m" else "yeva")
        return root + ("ov" if gender == "m" else "ova")
    if style == "zade":
        return root + "zadə"
    if style == "soy":
        return root + "soy"
    if style == "li":
        return root + _li_suffix(root)
    raise ValueError(f"Unknown family style: {style!r}")


def choose_canonical_style(rng: np.random.Generator) -> str:
    """Pick the canonical family style. Russified forms dominate real AZ surnames today."""
    styles = [RUSSIFIED, "zade", "soy", "li"]
    weights = np.array([0.50, 0.20, 0.15, 0.15])
    return str(rng.choice(styles, p=weights))


def family_variants(
    root: str,
    gender: str,
    canonical_style: str,
    *,
    p_national_alt: float,
    p_russified: float,
    rng: np.random.Generator,
) -> list[FamilyVariant]:
    """Same-entity family renderings other than the canonical one.

    - With ``p_national_alt``: a *different* national style (tag ``national``).
    - With ``p_russified`` (only if canonical isn't already russified): the Soviet -ov/-yev
      form (tag ``assimilation``).
    """
    out: list[FamilyVariant] = []
    seen = {render_family(root, gender, canonical_style)}

    if rng.random() < p_national_alt:
        alts = [s for s in NATIONAL_STYLES if s != canonical_style]
        style = str(rng.choice(alts))
        text = render_family(root, gender, style)
        if text not in seen:
            out.append(FamilyVariant(text, style, T_NATIONAL))
            seen.add(text)

    if canonical_style != RUSSIFIED and rng.random() < p_russified:
        text = render_family(root, gender, RUSSIFIED)
        if text not in seen:
            out.append(FamilyVariant(text, RUSSIFIED, T_ASSIMILATION))
            seen.add(text)

    return out


def az_patronymic(father_root: str, gender: str) -> str:
    """AZ patronymic: ``<father> oğlu`` (son) / ``<father> qızı`` (daughter)."""
    return f"{father_root} oğlu" if gender == "m" else f"{father_root} qızı"


def russified_patronymic(father_root: str, gender: str) -> str:
    """Russified patronymic in AZ-Latin orthography: ``Vaqifoviç`` (m) / ``Vaqifovna`` (f).

    (``ç`` reads as ``ch``; the Cyrillic form ``Вагифович`` is produced by translit.)
    """
    return father_root + ("oviç" if gender == "m" else "ovna")
