"""Phase 0: deterministic seeding utilities."""

from __future__ import annotations

import numpy as np
import pytest

from aznamematch.seeds import STAGE_NAMES, record_rng, stage_seeds


def test_stage_seeds_cover_all_stages():
    ss = stage_seeds(123)
    for name in STAGE_NAMES:
        assert isinstance(ss.seq(name), np.random.SeedSequence)


def test_unknown_stage_raises():
    ss = stage_seeds(123)
    with pytest.raises(KeyError):
        ss.seq("not_a_stage")


def test_same_master_seed_is_reproducible():
    a = stage_seeds(2026).rng("noise").integers(0, 1_000_000, size=20)
    b = stage_seeds(2026).rng("noise").integers(0, 1_000_000, size=20)
    assert np.array_equal(a, b)


def test_different_master_seed_differs():
    a = stage_seeds(1).rng("noise").integers(0, 1_000_000, size=20)
    b = stage_seeds(2).rng("noise").integers(0, 1_000_000, size=20)
    assert not np.array_equal(a, b)


def test_stages_have_independent_streams():
    ss = stage_seeds(7)
    a = ss.rng("canonical").integers(0, 1_000_000, size=20)
    b = ss.rng("noise").integers(0, 1_000_000, size=20)
    assert not np.array_equal(a, b)


def test_record_rng_is_order_independent():
    seq = stage_seeds(99).seq("canonical")
    # Record keyed by 5 draws the same values whether or not other records preceded it.
    first = record_rng(seq, 5).random(10)
    second = record_rng(seq, 5).random(10)
    assert np.array_equal(first, second)
    other = record_rng(seq, 6).random(10)
    assert not np.array_equal(first, other)
