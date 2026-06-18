"""Phase 1: canonical identity generation."""

from __future__ import annotations

import pytest

from aznamematch import components
from aznamematch.config import load_config
from aznamematch.generate.canonical import generate_identities
from aznamematch.seeds import stage_seeds
from aznamematch.textnorm import fold_ascii

AZ_LETTERS = set("əğçşüöıqxƏĞÇŞÜÖİQX")


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def ids(cfg):
    return generate_identities(cfg, stage_seeds(cfg["seed"]))


def test_count_matches_config(cfg, ids):
    assert len(ids) == cfg["identities"]["count"]


def test_ids_unique_and_nonempty(ids):
    assert len({i.canonical_id for i in ids}) == len(ids)
    assert all(i.canonical_id and i.canonical and i.name_origin_group for i in ids)


def test_determinism_same_seed(cfg):
    a = generate_identities(cfg, stage_seeds(cfg["seed"]))
    b = generate_identities(cfg, stage_seeds(cfg["seed"]))
    assert [i.to_row() for i in a] == [i.to_row() for i in b]


def test_different_seed_differs(cfg):
    a = generate_identities(cfg, stage_seeds(cfg["seed"]))
    b = generate_identities(cfg, stage_seeds(cfg["seed"] + 1))
    assert [i.canonical for i in a] != [i.canonical for i in b]


def test_az_letters_present(ids):
    # A meaningful share of canonical names must carry AZ-specific letters.
    with_az = sum(1 for i in ids if AZ_LETTERS & set(i.canonical))
    assert with_az > len(ids) // 2


def test_org_fraction_in_tolerance(cfg, ids):
    orgs = sum(1 for i in ids if i.entity_type == "org")
    target = cfg["identities"]["org_fraction"]
    assert abs(orgs / len(ids) - target) < 0.08


def test_person_and_org_components(ids):
    for i in ids:
        if i.entity_type == "person":
            assert i.given and i.family and i.gender in ("m", "f")
        else:
            assert i.org_tokens and i.canonical == " ".join(i.org_tokens)


def test_patronymic_fraction_in_tolerance(cfg, ids):
    persons = [i for i in ids if i.entity_type == "person"]
    with_pat = sum(1 for i in persons if i.patronymic)
    target = cfg["identities"]["patronymic_fraction"]
    assert abs(with_pat / len(persons) - target) < 0.1


def test_all_styles_present_russified_dominant(ids):
    from collections import Counter

    styles = Counter(i.canonical_style for i in ids if i.entity_type == "person")
    assert set(styles) == {"russified", "zade", "soy", "li"}
    assert styles["russified"] == max(styles.values())


def test_no_denylisted_names(ids):
    deny = components.denylist_folded()
    assert all(fold_ascii(i.canonical) not in deny for i in ids)


def test_patronymic_implies_russified_patronymic(ids):
    # If a person has an AZ patronymic, the russified-style alternate is also recorded.
    for i in ids:
        if i.entity_type == "person" and i.patronymic:
            assert i.russified_patronymic
