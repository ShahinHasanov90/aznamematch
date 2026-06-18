"""Phase 3: intra-script corruption."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from aznamematch.config import load_config
from aznamematch.generate import noise
from aznamematch.generate.translit.base import CYRL, LATN_AZ, LATN_TRANSLIT

AZ_SPECIALS = set("əğçşöüıƏĞÇŞÖÜI")
KNOWN_TYPES = {
    "char_edit", "ocr", "phonetic", "keyboard", "diacritic_loss", "abbreviation",
    "token_reorder", "patronymic_drop", "case", "whitespace_punct",
}


@pytest.fixture
def cfg():
    return load_config()


def _only(cfg, *, p_token=0.0, rates=None, reorder=0.0, drop=0.0, case=0.0, punct=0.0):
    """A config copy that isolates specific corruption paths."""
    c = copy.deepcopy(cfg)
    c["noise"]["p_corrupt_token"] = p_token
    c["noise"]["rates"] = rates or {}
    c["noise"]["record_level"] = {
        "p_token_reorder": reorder, "p_patronymic_drop": drop,
        "p_case_change": case, "p_punct_ws": punct,
    }
    return c


def test_determinism(cfg):
    a = noise.corrupt("Kənan Hüseynov", LATN_AZ, np.random.default_rng(9), cfg)
    b = noise.corrupt("Kənan Hüseynov", LATN_AZ, np.random.default_rng(9), cfg)
    assert a == b


def test_labels_are_known_types(cfg):
    rng = np.random.default_rng(1)
    for _ in range(200):
        _, types = noise.corrupt("Kənan Vaqif oğlu Hüseynov", LATN_AZ, rng, cfg)
        assert set(types) <= KNOWN_TYPES


def test_corruption_rate_in_tolerance(cfg):
    # Isolate per-token corruption (no record-level), single-token names: fraction with a
    # corruption should track p_corrupt_token.
    c = _only(cfg, p_token=0.5, rates={"char_edit": 1.0})
    rng = np.random.default_rng(4)
    hits = sum(1 for _ in range(2000)
               if noise.corrupt("Hüseynov", LATN_AZ, rng, c)[1])
    assert abs(hits / 2000 - 0.5) < 0.05


def test_token_reorder_is_permutation(cfg):
    c = _only(cfg, reorder=1.0)
    out, types = noise.corrupt("Kənan Vaqif Hüseynov", LATN_AZ, np.random.default_rng(2), c)
    assert types == ["token_reorder"]
    assert sorted(out.split()) == sorted("Kənan Vaqif Hüseynov".split())


def test_patronymic_drop_removes_tokens(cfg):
    c = _only(cfg, drop=1.0)
    out, types = noise.corrupt(
        "Kənan Vaqif oğlu Hüseynov", LATN_AZ, np.random.default_rng(0), c,
        droppable_indices=[1, 2],
    )
    assert "patronymic_drop" in types
    assert out.split() == ["Kənan", "Hüseynov"]


def test_diacritic_loss_strips_az_letters(cfg):
    c = _only(cfg, p_token=1.0, rates={"diacritic_loss": 1.0})
    out, types = noise.corrupt("Çinarə Şəfəq", LATN_AZ, np.random.default_rng(0), c)
    assert "diacritic_loss" in types
    assert not (AZ_SPECIALS & set(out))


def test_diacritic_loss_not_offered_for_cyrillic(cfg):
    # Cyrillic tokens have no AZ Latin specials; diacritic_loss must never be the label.
    c = _only(cfg, p_token=1.0, rates={"diacritic_loss": 1.0})
    rng = np.random.default_rng(3)
    for _ in range(50):
        _, types = noise.corrupt("Һүсејнов", CYRL, rng, c)
        assert "diacritic_loss" not in types


def test_abbreviation_makes_initial():
    assert noise._abbreviation("Vaqif", np.random.default_rng(0)) == ("V.", True)
    assert noise._abbreviation("V", np.random.default_rng(0)) == ("V", False)


def test_diacritic_applicator_direct():
    out, applied = noise._diacritic_loss("Hüseyn", np.random.default_rng(0))
    assert applied and out == "Huseyn"
    assert noise._diacritic_loss("Bob", np.random.default_rng(0)) == ("Bob", False)


def test_phonetic_only_on_latin(cfg):
    c = _only(cfg, p_token=1.0, rates={"phonetic": 1.0})
    # Latin token with a phonetic-eligible cluster gets a phonetic or fallback edit.
    _, types = noise.corrupt("Phil", LATN_TRANSLIT, np.random.default_rng(1), c)
    assert types and set(types) <= KNOWN_TYPES
