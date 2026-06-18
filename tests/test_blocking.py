"""Phase 5: blocking metrics + the cross-script demonstration."""

from __future__ import annotations

import pytest

from aznamematch.blocking.blockers import (
    ExactTokenBlocker,
    PhoneticKeyBlocker,
    Record,
    ScriptBlocker,
    _skeleton,
    compare_blockers,
)

# Same person A in 3 surfaces (Latin, Cyrillic, Latin-variant); person B in 2 (Latin, Cyrillic).
FIXTURE = [
    Record("A", "Kanan Aliyev", "latn-translit"),
    Record("A", "Кянан Алиев", "cyrl"),
    Record("A", "Kanan Aliev", "latn-translit"),
    Record("B", "Murad Mammadov", "latn-translit"),
    Record("B", "Мурад Мамедов", "cyrl"),
]
# n=5 -> 10 all-pairs; true matches = C(3,2)+C(2,2)... = 3 (A) + 1 (B) = 4.


def test_skeleton_bridges_scripts():
    assert _skeleton("Aliyev") == _skeleton("Aliev") == _skeleton("Алиев")
    assert _skeleton("Mammadov") == _skeleton("Мамедов")


def test_exact_token_metrics_exact_values():
    m = ExactTokenBlocker().evaluate(FIXTURE)
    # Only (r0,r2) share a raw token ("kanan"); all cross-script matches missed.
    assert m.n_true == 4
    assert m.n_candidates == 1
    assert m.n_true_in_candidates == 1
    assert m.reduction_ratio == pytest.approx(0.9)
    assert m.pair_completeness == pytest.approx(0.25)
    assert m.pair_quality == pytest.approx(1.0)


def test_phonetic_key_recovers_cross_script():
    m = PhoneticKeyBlocker().evaluate(FIXTURE)
    assert m.pair_completeness == pytest.approx(1.0)  # finds ALL, incl. cross-script
    assert m.n_true_in_candidates == 4
    assert 0.0 <= m.reduction_ratio <= 1.0


def test_naive_script_blocker_misses_cross_script():
    m = ScriptBlocker().evaluate(FIXTURE)
    assert m.pair_completeness < 1.0  # cross-script duplicates dropped


def test_phonetic_beats_naive_on_cross_script():
    metrics = compare_blockers(FIXTURE)
    assert metrics["phonetic_key"].pair_completeness > metrics["exact_token"].pair_completeness
    assert metrics["phonetic_key"].pair_completeness > metrics["naive_script"].pair_completeness


def test_metrics_bounds_and_determinism():
    a = compare_blockers(FIXTURE)
    b = compare_blockers(FIXTURE)
    for name, m in a.items():
        assert 0.0 <= m.reduction_ratio <= 1.0
        assert 0.0 <= m.pair_completeness <= 1.0
        assert 0.0 <= m.pair_quality <= 1.0
        assert (m.reduction_ratio, m.pair_completeness, m.pair_quality) == (
            b[name].reduction_ratio, b[name].pair_completeness, b[name].pair_quality)
