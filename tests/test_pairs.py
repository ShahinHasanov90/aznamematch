"""Phase 4: surface forms + labeled pair construction."""

from __future__ import annotations

import copy

import pytest

from aznamematch.config import load_config
from aznamematch.generate.canonical import generate_identities
from aznamematch.generate.pairs import HARD_TYPES, _script_pair, build_pairs
from aznamematch.generate.surface import build_surfaces
from aznamematch.generate.translit.base import CYRL, LATN_AZ, LATN_TRANSLIT
from aznamematch.seeds import record_rng, stage_seeds


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@pytest.fixture(scope="module")
def small():
    cfg = copy.deepcopy(load_config())
    cfg["identities"]["count"] = 60
    seeds = stage_seeds(cfg["seed"])
    identities = generate_identities(cfg, seeds)
    surf_seq = seeds.seq("surface")
    by_id = {
        ident.canonical_id: build_surfaces(ident, cfg, record_rng(surf_seq, i))
        for i, ident in enumerate(identities)
    }
    pairs = build_pairs(identities, by_id, cfg, seeds)
    return cfg, identities, by_id, pairs


def test_script_pair_derivation():
    assert _script_pair(LATN_AZ, CYRL) == "AZ-RU"
    assert _script_pair(LATN_AZ, LATN_TRANSLIT) == "AZ-EN"
    assert _script_pair(CYRL, LATN_TRANSLIT) == "RU-EN"
    assert _script_pair(LATN_AZ, LATN_AZ) == "same"


def test_surfaces_have_cross_script_for_person(small):
    _, identities, by_id, _ = small
    person = next(i for i in identities if i.entity_type == "person")
    scripts = {s.script for s in by_id[person.canonical_id]}
    assert {LATN_AZ, CYRL, LATN_TRANSLIT} <= scripts


def test_label_balance_matches_config(small):
    cfg, _, _, pairs = small
    pos = [p for p in pairs if p.label == 1]
    neg = [p for p in pairs if p.label == 0]
    hard = [p for p in pairs if p.hardness == "hard"]
    assert len(neg) == round(len(pos) * cfg["pairs"]["neg_per_pos"])
    assert len(hard) == round(len(neg) * cfg["pairs"]["hard_negative_fraction"])
    assert all(p.hardness == "hard" for p in pairs if p.hard_negative_type != "none")


def test_no_trivial_exact_string_positives(small):
    _, _, _, pairs = small
    assert all(p.surface1 != p.surface2 for p in pairs if p.label == 1)


def test_no_duplicate_pairs(small):
    # Exact (surface1, surface2, label) duplicates are removed so a pair can't straddle the
    # entity-disjoint eval split.
    _, _, _, pairs = small
    keys = [(p.surface1, p.surface2, p.label) for p in pairs]
    assert len(keys) == len(set(keys))


def test_metadata_complete(small):
    _, _, _, pairs = small
    for p in pairs:
        assert p.script_pair in {"AZ-RU", "AZ-EN", "RU-EN", "same"}
        assert p.hardness in {"easy", "hard"}
        assert p.hard_negative_type in ("none", *HARD_TYPES)
        assert p.scripts and p.standards and p.name_origin_groups
        assert p.is_homoglyph is False  # core set carries no homoglyphs


def test_each_hard_negative_type_valid(small):
    _, _, _, pairs = small
    by_type = {t: [p for p in pairs if p.hard_negative_type == t] for t in HARD_TYPES}
    for t in HARD_TYPES:
        assert by_type[t], f"no {t} hard negatives generated"

    ts = by_type["token_swap"][0]
    assert sorted(ts.surface1.split()) == sorted(ts.surface2.split())
    assert ts.surface1 != ts.surface2

    gc = by_type["generation_collision"][0]
    # The son's surface (the longer one) contains "oğlu" and repeats a father token.
    longer, shorter = sorted([gc.surface1, gc.surface2], key=len, reverse=True)
    assert "oğlu" in longer
    assert set(shorter.split()) & set(longer.split())

    sc = by_type["surname_collision"][0]
    assert sc.surface1.split()[-1] == sc.surface2.split()[-1]
    assert sc.surface1.split()[0] != sc.surface2.split()[0]

    oe = by_type["one_edit"][0]
    fam1, fam2 = oe.surface1.split()[-1], oe.surface2.split()[-1]
    assert fam1 != fam2 and _levenshtein(fam1, fam2) <= 2


def test_determinism(small):
    cfg, identities, by_id, pairs = small
    seeds = stage_seeds(cfg["seed"])
    pairs2 = build_pairs(identities, by_id, cfg, seeds)
    assert [p.to_row() for p in pairs] == [p.to_row() for p in pairs2]


def test_reproducible_regardless_of_target_key_order(small):
    # The dataset must depend on target VALUES, not the incidental key order in the config
    # (a re-serialization that sorts keys must not change the output).
    cfg, identities, by_id, pairs = small
    reordered = copy.deepcopy(cfg)
    t = reordered["pairs"]["script_pair_targets"]
    reordered["pairs"]["script_pair_targets"] = {k: t[k] for k in reversed(list(t))}
    pairs2 = build_pairs(identities, by_id, reordered, stage_seeds(cfg["seed"]))
    assert [p.to_row() for p in pairs] == [p.to_row() for p in pairs2]


def test_positives_are_cross_script_majority(small):
    # Stratified sampling should make most positives genuinely cross-script.
    _, _, _, pairs = small
    pos = [p for p in pairs if p.label == 1]
    cross = [p for p in pos if p.script_pair != "same"]
    assert len(cross) > len(pos) * 0.5


def test_az_ru_positives_well_represented(small):
    # The AZ-RU cell must be a major, comparable cross-script cell (the whole point of the
    # cyrl emphasis + stratified targeting), not a thin sliver.
    from collections import Counter

    _, _, _, pairs = small
    cells = Counter(p.script_pair for p in pairs if p.label == 1)
    cross = {c: cells.get(c, 0) for c in ("AZ-RU", "AZ-EN", "RU-EN")}
    assert cross["AZ-RU"] >= 0.6 * max(cross.values())
    assert cross["AZ-RU"] >= cells.get("same", 0)


def test_cross_script_cells_are_label_balanced(small):
    # Each cross-script cell needs BOTH labels to be individually evaluable later.
    _, _, _, pairs = small
    for c in ("AZ-RU", "AZ-EN", "RU-EN"):
        labels = {p.label for p in pairs if p.script_pair == c}
        assert labels == {0, 1}, f"cell {c} missing a label: {labels}"


def test_cyrillic_emphasis_increases_cyrl_surfaces():
    from aznamematch.generate.surface import build_surfaces
    from aznamematch.generate.translit.base import CYRL

    base = copy.deepcopy(load_config())
    base["noise"]["p_surface_corrupted"] = 0.0  # isolate the extra-cyrillic pass
    cfg0 = copy.deepcopy(base)
    cfg0["noise"]["cyrillic_extra_corrupted"] = 0
    cfgn = copy.deepcopy(base)
    cfgn["noise"]["cyrillic_extra_corrupted"] = 3

    seeds = stage_seeds(base["seed"])
    person = next(i for i in generate_identities(base, seeds) if i.entity_type == "person")
    seq = seeds.seq("surface")
    n0 = sum(1 for s in build_surfaces(person, cfg0, record_rng(seq, 0)) if s.script == CYRL)
    nn = sum(1 for s in build_surfaces(person, cfgn, record_rng(seq, 0)) if s.script == CYRL)
    assert nn > n0
