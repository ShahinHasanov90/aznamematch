"""Phase 4 (part 2): labeled pair construction + full pair metadata.

Pairs are the benchmark's unit of evaluation:

- **Positives** — two distinct surface forms of the SAME identity (cross-script and/or
  corrupted and/or a suffix-matrix transition).
- **Easy negatives** — surfaces of two clearly different identities.
- **Hard negatives** (each tagged) — engineered to be lexically confusable yet different
  people: ``token_swap`` (same token multiset, swapped roles), ``generation_collision``
  (father vs son, patronymic repeats the father's given name), ``surname_collision`` (same
  family, different given), ``one_edit`` (surnames one edit apart).

Note: token reorder appears in BOTH positives (same person, reordered) and ``token_swap``
hard negatives (different people) — only the label differs. That ambiguity is intentional.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from aznamematch import components
from aznamematch.config import get
from aznamematch.generate import noise, suffix_matrix
from aznamematch.generate.canonical import Identity
from aznamematch.generate.surface import SurfaceForm
from aznamematch.generate.translit.base import CYRL, LATN_AZ, LATN_TRANSLIT, NONE
from aznamematch.seeds import StageSeeds

_CATEGORY = {LATN_AZ: "AZ", CYRL: "RU", LATN_TRANSLIT: "EN"}
_PAIR_LABEL = {
    frozenset({"AZ", "RU"}): "AZ-RU",
    frozenset({"AZ", "EN"}): "AZ-EN",
    frozenset({"RU", "EN"}): "RU-EN",
}
HARD_TYPES = ("token_swap", "generation_collision", "surname_collision", "one_edit")


@dataclass(frozen=True)
class Pair:
    """A labeled pair of surface forms with the union of both members' provenance."""

    pair_id: str
    id1: str
    id2: str
    surface1: str
    surface2: str
    label: int
    script_pair: str
    hardness: str
    hard_negative_type: str
    scripts: tuple[str, ...]
    standards: tuple[str, ...]
    corruption_types: tuple[str, ...]
    suffix_transforms: tuple[str, ...]
    name_origin_groups: tuple[str, ...]
    is_homoglyph: bool

    def to_row(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "id1": self.id1,
            "id2": self.id2,
            "surface1": self.surface1,
            "surface2": self.surface2,
            "label": self.label,
            "script_pair": self.script_pair,
            "hardness": self.hardness,
            "hard_negative_type": self.hard_negative_type,
            "scripts": ";".join(self.scripts),
            "standards": ";".join(self.standards),
            "corruption_types": ";".join(self.corruption_types),
            "suffix_transforms": ";".join(self.suffix_transforms),
            "name_origin_groups": ";".join(self.name_origin_groups),
            "is_homoglyph": self.is_homoglyph,
        }


def _script_pair(s1: str, s2: str) -> str:
    a, b = _CATEGORY[s1], _CATEGORY[s2]
    if a == b:
        return "same"
    return _PAIR_LABEL[frozenset({a, b})]


def _from_surfaces(pair_id: str, a: SurfaceForm, b: SurfaceForm, *, label: int,
                   hardness: str, hard_type: str) -> Pair:
    return Pair(
        pair_id=pair_id,
        id1=a.canonical_id, id2=b.canonical_id,
        surface1=a.surface, surface2=b.surface,
        label=label,
        script_pair=_script_pair(a.script, b.script),
        hardness=hardness,
        hard_negative_type=hard_type,
        scripts=tuple(sorted({a.script, b.script})),
        standards=tuple(sorted({a.translit_standard, b.translit_standard})),
        corruption_types=tuple(sorted(set(a.corruption_types) | set(b.corruption_types))),
        suffix_transforms=tuple(sorted({a.suffix_transform, b.suffix_transform})),
        name_origin_groups=tuple(sorted({a.name_origin_group, b.name_origin_group})),
        is_homoglyph=a.is_homoglyph or b.is_homoglyph,
    )


def _plain_surface(cid: str, text: str, group: str) -> SurfaceForm:
    """A bare AZ-Latin surface for synthesized hard-negative members."""
    return SurfaceForm(
        canonical_id=cid, entity_type="person", surface=text, script=LATN_AZ,
        translit_standard=NONE, corruption_types=(), suffix_transform="none",
        name_origin_group=group,
    )


# --- positives + easy negatives --------------------------------------------------------
def _build_positives(identities: list[Identity], by_id: dict[str, list[SurfaceForm]],
                     per_identity: int, rng: np.random.Generator,
                     cross_script_bias: float = 0.75) -> list[Pair]:
    """Sample positive pairs, biased toward cross-script pairs (the benchmark's focus)."""
    pos: list[Pair] = []
    counter = 0
    for ident in identities:
        sfs = by_id.get(ident.canonical_id, [])
        if len(sfs) < 2:
            continue
        used: set[frozenset[int]] = set()
        made = 0
        for _ in range(per_identity * 8):
            if made >= per_identity:
                break
            i = int(rng.integers(0, len(sfs)))
            cat_i = _CATEGORY[sfs[i].script]
            cross = rng.random() < cross_script_bias
            cands = [
                k for k in range(len(sfs))
                if k != i and sfs[k].surface != sfs[i].surface
                and (not cross or _CATEGORY[sfs[k].script] != cat_i)
            ]
            if not cands:  # fall back to any text-distinct partner
                cands = [k for k in range(len(sfs))
                         if k != i and sfs[k].surface != sfs[i].surface]
            if not cands:
                continue
            j = int(rng.choice(cands))
            key = frozenset({i, j})
            if key in used:
                continue
            used.add(key)
            counter += 1
            pos.append(_from_surfaces(f"P{counter:06d}", sfs[i], sfs[j],
                                      label=1, hardness="easy", hard_type="none"))
            made += 1
    return pos


def _build_easy_negatives(identities: list[Identity], by_id: dict[str, list[SurfaceForm]],
                          n: int, rng: np.random.Generator) -> list[Pair]:
    eligible = [i for i in identities if by_id.get(i.canonical_id)]
    out: list[Pair] = []
    seen: set[tuple[str, str]] = set()
    attempts = 0
    while len(out) < n and attempts < n * 20:
        attempts += 1
        a_id, b_id = (int(x) for x in rng.choice(len(eligible), size=2, replace=False))
        ia, ib = eligible[a_id], eligible[b_id]
        # "clearly different": different family root (persons) avoids accidental hardness.
        if ia.entity_type == "person" and ib.entity_type == "person" \
                and ia.family_root == ib.family_root:
            continue
        sa = by_id[ia.canonical_id][int(rng.integers(0, len(by_id[ia.canonical_id])))]
        sb = by_id[ib.canonical_id][int(rng.integers(0, len(by_id[ib.canonical_id])))]
        key = (sa.surface, sb.surface)
        if key in seen:
            continue
        seen.add(key)
        out.append(_from_surfaces(f"N{len(out) + 1:06d}", sa, sb,
                                  label=0, hardness="easy", hard_type="none"))
    return out


# --- hard-negative synthesizers --------------------------------------------------------
def _two_distinct(pool: list[str], rng: np.random.Generator) -> tuple[str, str]:
    i, j = (int(x) for x in rng.choice(len(pool), size=2, replace=False))
    return pool[i], pool[j]


def _synth_hard(kind: str, k: int, rng: np.random.Generator) -> Pair:
    males = components.given_names()["m"]
    roots = components.family_roots()
    pid = f"H{kind[:2].upper()}{k:05d}"
    a_id, b_id = f"{pid}a", f"{pid}b"

    if kind == "token_swap":
        g1, g2 = _two_distinct(males, rng)
        a = _plain_surface(a_id, f"{g1} {g2} oğlu", "hardneg_token_swap")
        b = _plain_surface(b_id, f"{g2} {g1} oğlu", "hardneg_token_swap")
    elif kind == "generation_collision":
        family = suffix_matrix.render_family(str(rng.choice(roots)), "m",
                                             suffix_matrix.RUSSIFIED)
        gf, gs = _two_distinct(males, rng)
        a = _plain_surface(a_id, f"{gf} {family}", "hardneg_generation")
        b = _plain_surface(b_id, f"{gs} {gf} oğlu {family}", "hardneg_generation")
    elif kind == "surname_collision":
        family = suffix_matrix.render_family(str(rng.choice(roots)), "m",
                                             suffix_matrix.RUSSIFIED)
        g1, g2 = _two_distinct(males, rng)
        a = _plain_surface(a_id, f"{g1} {family}", "hardneg_surname")
        b = _plain_surface(b_id, f"{g2} {family}", "hardneg_surname")
    else:  # one_edit
        family = suffix_matrix.render_family(str(rng.choice(roots)), "m",
                                             suffix_matrix.RUSSIFIED)
        edited = family
        for _ in range(6):
            cand, _ok = noise._char_edit(family, rng, "abcdefghijklmnopqrstuvwxyzəğçşöüı")
            if cand != family:
                edited = cand
                break
        g1, g2 = _two_distinct(males, rng)
        a = _plain_surface(a_id, f"{g1} {family}", "hardneg_one_edit")
        b = _plain_surface(b_id, f"{g2} {edited}", "hardneg_one_edit")

    return _from_surfaces(pid, a, b, label=0, hardness="hard", hard_type=kind)


def _build_hard_negatives(n: int, mix: dict[str, float],
                          rng: np.random.Generator) -> list[Pair]:
    kinds = [k for k in HARD_TYPES if float(mix.get(k, 0)) > 0]
    weights = np.array([float(mix[k]) for k in kinds])
    weights = weights / weights.sum()
    out: list[Pair] = []
    for k in range(n):
        kind = str(rng.choice(kinds, p=weights))
        out.append(_synth_hard(kind, k, rng))
    return out


def build_pairs(identities: list[Identity], by_id: dict[str, list[SurfaceForm]],
                cfg: dict[str, Any], seeds: StageSeeds) -> list[Pair]:
    """Construct the full labeled-pair set per the ``pairs.*`` config, deterministically."""
    rng = seeds.rng("pairs")
    per_identity = int(get(cfg, "pairs.positives_per_identity", 3))
    neg_per_pos = float(get(cfg, "pairs.neg_per_pos", 1.0))
    hard_frac = float(get(cfg, "pairs.hard_negative_fraction", 0.5))
    mix = dict(get(cfg, "pairs.hard_negative_mix", {}))

    positives = _build_positives(identities, by_id, per_identity, rng)
    n_neg = round(len(positives) * neg_per_pos)
    n_hard = round(n_neg * hard_frac)
    n_easy = n_neg - n_hard

    easy = _build_easy_negatives(identities, by_id, n_easy, rng)
    hard = _build_hard_negatives(n_hard, mix, rng)

    pairs = positives + easy + hard
    # Deterministic shuffle so positives/negatives interleave.
    order = rng.permutation(len(pairs))
    return [pairs[i] for i in order]
