"""Phase 2: cross-script transliteration."""

from __future__ import annotations

import numpy as np
import pytest

from aznamematch.config import load_config
from aznamematch.generate.translit import adhoc as adhoc_mod
from aznamematch.generate.translit import az_cyrl, generate_variants, ru_latn
from aznamematch.generate.translit.base import CYRL, LATN_TRANSLIT


@pytest.mark.parametrize(
    "name",
    ["Əliyev", "Mövsümzadə", "İlqar Hüseynov", "Çinarə Şəfəq", "Quliyeva"],
)
def test_az_latin_cyrillic_roundtrip(name):
    # The reversible AZ alphabet mapping (the ISO-9-style reversibility property).
    assert az_cyrl.to_latin(az_cyrl.to_cyrillic(name)) == name


def test_schwa_maps_both_directions():
    # Spec requirement: Cyrillic Ә <-> Latin Ə.
    assert az_cyrl.to_cyrillic("Ə") == "Ә"
    assert az_cyrl.to_latin("Ә") == "Ə"


def test_russified_cyrillic_examples():
    assert az_cyrl.az_to_russian_cyrillic("Əliyev") == "Алиев"
    assert az_cyrl.az_to_russian_cyrillic("Hüseyn") == "Гусейн"


def test_az_romanization_schwa_divergence():
    # ə -> e (BGN/PCGN) vs ə -> a (ALA-LC); ğ -> gh vs g.
    assert az_cyrl.romanize("Əli", "BGN_PCGN") == "Eli"
    assert az_cyrl.romanize("Əli", "ALA_LC") == "Ali"
    # ğ -> gh (BGN/PCGN) vs ğ -> g (ALA-LC).
    assert az_cyrl.romanize("Çırağlı", "BGN_PCGN").lower().count("gh") == 1
    assert "gh" not in az_cyrl.romanize("Çırağlı", "ALA_LC").lower()


def test_az_romanize_invalid_standard():
    with pytest.raises(ValueError):
        az_cyrl.romanize("Əli", "ICAO")


def test_ru_standards_tricky_letters():
    # х -> kh (ICAO/BGN/ALA) vs x (GOST System B); ц -> ts; ъ -> ie (ICAO).
    assert ru_latn.romanize("Хан", "ICAO").startswith("Kh")
    assert ru_latn.romanize("Хан", "GOST").startswith("X")
    assert ru_latn.romanize("Цой", "ICAO").lower().startswith("ts")
    assert "ie" in ru_latn.romanize("Объезд", "ICAO").lower()  # ъ -> ie


def test_ru_ya_yu_divergence():
    # я -> ia (ICAO/ALA) vs ya (BGN); ю -> iu vs yu.
    assert ru_latn.romanize("Яна", "ICAO").lower().startswith("ia")
    assert ru_latn.romanize("Яна", "BGN_PCGN").lower().startswith("ya")


def test_x_renders_kh_and_h_in_adhoc():
    # AZ 'x' (/x/, same sound as Russian х) -> {kh, h}: both appear across ad-hoc spellings.
    variants = adhoc_mod.variants("Xəlilov", np.random.default_rng(0), 8)
    folded = " ".join(variants).lower()
    assert "kh" in folded and any(v.lower().startswith("h") for v in variants)


def test_gost_roundtrip():
    for s in ["алиев", "юрий", "щука", "объезд", "хижина", "цой"]:
        assert ru_latn.gost_decode(ru_latn.gost_encode(s)) == s


def test_generate_variants_structure_and_determinism():
    cfg = load_config()
    a = generate_variants("Əliyev", produce_russian=True, cfg=cfg, rng=np.random.default_rng(7))
    b = generate_variants("Əliyev", produce_russian=True, cfg=cfg, rng=np.random.default_rng(7))
    assert [(v.text, v.script, v.standard) for v in a] == [
        (v.text, v.script, v.standard) for v in b
    ]
    scripts = {v.script for v in a}
    assert CYRL in scripts and LATN_TRANSLIT in scripts
    # No duplicate (script, surface) pairs.
    keys = [(v.script, v.text) for v in a]
    assert len(keys) == len(set(keys))
    # The canonical source form is never re-emitted.
    assert all(v.text != "Əliyev" for v in a)


def test_orgs_skip_russian_branch():
    cfg = load_config()
    variants = generate_variants(
        "Xəzər Neft MMC", produce_russian=False, cfg=cfg, rng=np.random.default_rng(1)
    )
    # Only the national Cyrillic surface should appear (no Russified RU-romanization branch).
    cyr = [v for v in variants if v.script == CYRL]
    assert len(cyr) == 1
