"""Phase 1: seeded canonical identities (persons + organizations).

Each identity has a stable ``canonical_id``, a canonical AZ-Latin surface form, separated
structured components, optional DOB + synthetic ID number (features for the later
RegressionV1 matcher), a ``name_origin_group`` for fairness slicing, and the same-entity
family / patronymic variants produced by the suffix matrix.

A denylist guard re-draws any identity whose canonical full name folds to a well-known real
full name (see ``docs/rules/no-real-persons.md``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from aznamematch import components
from aznamematch.config import get
from aznamematch.generate import suffix_matrix as sm
from aznamematch.seeds import StageSeeds, record_rng
from aznamematch.textnorm import fold_ascii

_STYLE_TO_GROUP = {
    sm.RUSSIFIED: "russified",
    "zade": "national_zade",
    "soy": "national_soy",
    "li": "national_li",
}


@dataclass(frozen=True)
class Identity:
    """A canonical synthetic entity (ground truth)."""

    canonical_id: str
    entity_type: str  # "person" | "org"
    name_origin_group: str
    canonical: str  # canonical AZ-Latin full surface form
    # Person components ("" / None when not applicable):
    gender: str = ""  # "m" | "f" | ""
    given: str = ""
    patronymic: str = ""  # AZ canonical patronymic, e.g. "Vaqif oğlu"
    family: str = ""
    family_root: str = ""
    patronymic_father: str = ""
    canonical_style: str = ""  # family style for persons
    # Org components:
    org_tokens: tuple[str, ...] = ()
    # Optional identity attributes:
    dob: str | None = None
    id_number: str | None = None
    # Same-entity suffix-matrix variants (Phase 1):
    family_variants: tuple[sm.FamilyVariant, ...] = ()
    russified_patronymic: str | None = None

    def to_row(self) -> dict[str, Any]:
        """Flat dict for serialization (variants serialized compactly)."""
        return {
            "canonical_id": self.canonical_id,
            "entity_type": self.entity_type,
            "name_origin_group": self.name_origin_group,
            "canonical": self.canonical,
            "gender": self.gender,
            "given": self.given,
            "patronymic": self.patronymic,
            "family": self.family,
            "family_root": self.family_root,
            "patronymic_father": self.patronymic_father,
            "canonical_style": self.canonical_style,
            "org_tokens": " ".join(self.org_tokens),
            "dob": self.dob or "",
            "id_number": self.id_number or "",
            "family_variants": ";".join(
                f"{v.text}|{v.style}|{v.suffix_transform}" for v in self.family_variants
            ),
            "russified_patronymic": self.russified_patronymic or "",
        }


def _make_dob(rng: np.random.Generator, min_year: int, max_year: int) -> str:
    year = int(rng.integers(min_year, max_year + 1))
    month = int(rng.integers(1, 13))
    day = int(rng.integers(1, 29))  # 1..28 avoids month-length edge cases
    return f"{year:04d}-{month:02d}-{day:02d}"


def _make_id_number(rng: np.random.Generator, length: int) -> str:
    return "".join(str(int(d)) for d in rng.integers(0, 10, size=length))


def _build_person(idx: int, rng: np.random.Generator, suffix_rng: np.random.Generator,
                  cfg: dict[str, Any]) -> Identity:
    given_by_gender = components.given_names()
    roots = components.family_roots()
    fathers = components.patronymic_fathers()

    gender = "m" if rng.random() < 0.5 else "f"
    given = str(rng.choice(given_by_gender[gender]))
    family_root = str(rng.choice(roots))
    canonical_style = sm.choose_canonical_style(rng)
    family = sm.render_family(family_root, gender, canonical_style)

    patronymic = ""
    patronymic_father = ""
    russified_pat = None
    if rng.random() < float(get(cfg, "identities.patronymic_fraction", 0.7)):
        patronymic_father = str(rng.choice(fathers))
        patronymic = sm.az_patronymic(patronymic_father, gender)
        russified_pat = sm.russified_patronymic(patronymic_father, gender)

    # Canonical full surface: Given [Patronymic] Family.
    parts = [given]
    if patronymic:
        parts.append(patronymic)
    parts.append(family)
    canonical = " ".join(parts)

    dob = None
    if rng.random() < float(get(cfg, "identities.dob.fraction", 0.8)):
        dob = _make_dob(rng, int(get(cfg, "identities.dob.min_year")),
                        int(get(cfg, "identities.dob.max_year")))

    id_number = None
    if rng.random() < float(get(cfg, "identities.id_number.fraction", 0.6)):
        id_number = _make_id_number(rng, int(get(cfg, "identities.id_number.length", 7)))

    fam_variants: tuple[sm.FamilyVariant, ...] = ()
    if bool(get(cfg, "suffix_matrix.enabled", True)):
        fam_variants = tuple(
            sm.family_variants(
                family_root, gender, canonical_style,
                p_national_alt=float(get(cfg, "suffix_matrix.p_national_alt", 0.5)),
                p_russified=float(get(cfg, "suffix_matrix.p_russified", 0.6)),
                rng=suffix_rng,
            )
        )

    return Identity(
        canonical_id=f"E{idx:06d}",
        entity_type="person",
        name_origin_group=_STYLE_TO_GROUP[canonical_style],
        canonical=canonical,
        gender=gender,
        given=given,
        patronymic=patronymic,
        family=family,
        family_root=family_root,
        patronymic_father=patronymic_father,
        canonical_style=canonical_style,
        dob=dob,
        id_number=id_number,
        family_variants=fam_variants,
        russified_patronymic=russified_pat,
    )


def _build_org(idx: int, rng: np.random.Generator, cfg: dict[str, Any]) -> Identity:
    tok = components.org_tokens()
    brand = str(rng.choice(tok["brand"]))
    parts = [brand]
    if rng.random() < 0.7 and tok["industry"]:
        parts.append(str(rng.choice(tok["industry"])))
    parts.append(str(rng.choice(tok["legal"])))

    id_number = None
    if rng.random() < float(get(cfg, "identities.id_number.fraction", 0.6)):
        id_number = _make_id_number(rng, int(get(cfg, "identities.id_number.length", 7)))

    return Identity(
        canonical_id=f"E{idx:06d}",
        entity_type="org",
        name_origin_group="organization",
        canonical=" ".join(parts),
        org_tokens=tuple(parts),
        id_number=id_number,
    )


def generate_identities(cfg: dict[str, Any], seeds: StageSeeds) -> list[Identity]:
    """Generate the configured number of canonical identities, deterministically."""
    n = int(get(cfg, "identities.count"))
    org_fraction = float(get(cfg, "identities.org_fraction", 0.15))
    rng = seeds.rng("canonical")
    suffix_seq = seeds.seq("suffix_matrix")
    denylist = components.denylist_folded()

    identities: list[Identity] = []
    for idx in range(n):
        is_org = rng.random() < org_fraction
        # Re-draw on the rare denylist collision; deterministic given the seed.
        for _ in range(8):
            if is_org:
                ident = _build_org(idx, rng, cfg)
            else:
                ident = _build_person(idx, rng, record_rng(suffix_seq, idx), cfg)
            if fold_ascii(ident.canonical) not in denylist:
                break
        identities.append(ident)
    return identities
