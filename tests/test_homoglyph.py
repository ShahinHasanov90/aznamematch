"""Phase 3b: adversarial homoglyph layer."""

from __future__ import annotations

import numpy as np
import pytest
from unidecode import unidecode

from aznamematch.generate import homoglyph as H


def _has_cyrillic(text: str) -> bool:
    return any(0x0400 <= ord(c) <= 0x04FF for c in text)


@pytest.mark.parametrize("name", ["Aliyev", "Hasanov", "Mammadov", "Pashayev", "Eliyev"])
def test_attack_differs_at_codepoint_but_folds_identically(name):
    a = H.attack(name, np.random.default_rng(0), p_char_swap=0.7, p_diacritic_strip=0.0)
    assert a.attacked != a.clean              # differs at code-point level
    assert _has_cyrillic(a.attacked)          # contains Cyrillic confusables
    assert H.confusable_fold(a.attacked) == H.confusable_fold(a.clean)  # TR39 fold equal


def test_at_least_one_swap_when_eligible():
    # p_char_swap=0 still forces one swap so the row is genuinely an attack.
    a = H.attack("Aliyev", np.random.default_rng(0), p_char_swap=0.0, p_diacritic_strip=0.0)
    assert a.is_attack
    assert len(a.swapped_codepoints) == 1


def test_swap_count_matches_cyrillic_introduced():
    a = H.attack("Mammadov", np.random.default_rng(1), p_char_swap=1.0, p_diacritic_strip=0.0)
    introduced = sum(1 for c in a.attacked if _has_cyrillic(c))
    assert introduced == len(a.swapped_codepoints)
    assert all(s.split("->")[1].startswith("U+") for s in a.swapped_codepoints)


def test_determinism():
    a = H.attack("Hasanov", np.random.default_rng(5), p_char_swap=0.6, p_diacritic_strip=0.5)
    b = H.attack("Hasanov", np.random.default_rng(5), p_char_swap=0.6, p_diacritic_strip=0.5)
    assert a == b


def test_unidecode_is_insufficient_tr39_works():
    # Swaps involving С/Н/Х/Р/у break under sound-based unidecode but survive TR39 folding.
    a = H.attack("Hasanov", np.random.default_rng(0), p_char_swap=1.0, p_diacritic_strip=0.0)
    assert unidecode(a.attacked).casefold() != a.clean.casefold()
    assert H.confusable_fold(a.attacked) == a.clean.casefold()


def test_diacritic_strip():
    assert H.strip_az_diacritics("Əliyev") == "Eliyev"
    assert H.strip_az_diacritics("Çinarə Şəfəq") == "Cinare Sefeq"


def test_diacritic_strip_flag_controls_clean_form():
    always = H.attack("Əliyev", np.random.default_rng(0), p_char_swap=0.5, p_diacritic_strip=1.0)
    never = H.attack("Əliyev", np.random.default_rng(0), p_char_swap=0.5, p_diacritic_strip=0.0)
    assert always.diacritics_stripped and "ə" not in always.clean.lower()
    assert not never.diacritics_stripped and "ə" in never.clean.lower()


def test_confusable_fold_maps_known_confusables():
    # Cyrillic С(U+0421) and Н(U+041D) fold to Latin shapes c and h.
    assert H.confusable_fold("СН") == "ch"
