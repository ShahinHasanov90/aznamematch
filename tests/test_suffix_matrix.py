"""Phase 1: post-Soviet suffix transition matrix."""

from __future__ import annotations

import numpy as np
import pytest

from aznamematch.generate import suffix_matrix as sm


def test_russified_vowel_vs_consonant_ending():
    # Vowel-ending root -> -yev/-yeva; consonant-ending -> -ov/-ova.
    assert sm.render_family("Əli", "m", sm.RUSSIFIED) == "Əliyev"
    assert sm.render_family("Əli", "f", sm.RUSSIFIED) == "Əliyeva"
    assert sm.render_family("Məmməd", "m", sm.RUSSIFIED) == "Məmmədov"
    assert sm.render_family("Məmməd", "f", sm.RUSSIFIED) == "Məmmədova"


def test_national_zade_and_soy_are_gender_invariant():
    assert sm.render_family("Əli", "m", "zade") == "Əlizadə"
    assert sm.render_family("Əli", "f", "zade") == "Əlizadə"
    assert sm.render_family("Əli", "m", "soy") == "Əlisoy"


@pytest.mark.parametrize(
    ("root", "expected"),
    [
        ("Murad", "Muradlı"),   # last vowel a -> back unrounded -> lı
        ("Davud", "Davudlu"),   # last vowel u -> back rounded   -> lu
        ("Vəli", "Vəlili"),     # last vowel i -> front unrounded -> li
        ("Mövsüm", "Mövsümlü"),  # last vowel ü -> front rounded  -> lü
    ],
)
def test_li_vowel_harmony(root, expected):
    assert sm.render_family(root, "m", "li") == expected


def test_unknown_style_raises():
    with pytest.raises(ValueError):
        sm.render_family("Əli", "m", "bogus")


def test_patronymics():
    assert sm.az_patronymic("Vaqif", "m") == "Vaqif oğlu"
    assert sm.az_patronymic("Vaqif", "f") == "Vaqif qızı"
    assert sm.russified_patronymic("Vaqif", "m") == "Vaqifoviç"
    assert sm.russified_patronymic("Vaqif", "f") == "Vaqifovna"


def test_choose_canonical_style_is_valid_and_deterministic():
    a = sm.choose_canonical_style(np.random.default_rng(0))
    b = sm.choose_canonical_style(np.random.default_rng(0))
    assert a == b
    assert a in sm.ALL_STYLES


def test_family_variants_tags_national_and_assimilation():
    # Force both branches from a national canonical style.
    variants = sm.family_variants(
        "Əli", "m", "zade", p_national_alt=1.0, p_russified=1.0,
        rng=np.random.default_rng(3),
    )
    transforms = {v.suffix_transform for v in variants}
    assert sm.T_NATIONAL in transforms
    assert sm.T_ASSIMILATION in transforms
    # National alt uses a national style != canonical.
    nat = next(v for v in variants if v.suffix_transform == sm.T_NATIONAL)
    assert nat.style in sm.NATIONAL_STYLES and nat.style != "zade"


def test_family_variants_no_assimilation_when_canonical_russified():
    variants = sm.family_variants(
        "Əli", "m", sm.RUSSIFIED, p_national_alt=1.0, p_russified=1.0,
        rng=np.random.default_rng(3),
    )
    assert all(v.suffix_transform != sm.T_ASSIMILATION for v in variants)


def test_family_variants_deterministic():
    kw = dict(p_national_alt=0.5, p_russified=0.6)
    a = sm.family_variants("Murad", "m", "soy", rng=np.random.default_rng(11), **kw)
    b = sm.family_variants("Murad", "m", "soy", rng=np.random.default_rng(11), **kw)
    assert [(v.text, v.style, v.suffix_transform) for v in a] == [
        (v.text, v.style, v.suffix_transform) for v in b
    ]
