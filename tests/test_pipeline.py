"""Phase 4: end-to-end pipeline + byte-level determinism of written artifacts."""

from __future__ import annotations

import copy

import pandas as pd
import pytest
import yaml

from aznamematch.config import load_config
from aznamematch.generate.pipeline import run_generation


def _write_cfg(tmp_path, outdir):
    cfg = copy.deepcopy(load_config())
    cfg["identities"]["count"] = 40
    cfg["homoglyph"]["n_identities"] = 20
    cfg["output"] = {
        "full_dir": str(outdir / "full"),
        "sample_dir": str(outdir / "sample"),
        "sample_rows": 25,
        "adversarial_dir": str(outdir / "adversarial"),
    }
    path = tmp_path / f"{outdir.name}.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("gen")
    out1 = tmp / "run1"
    cfg_path = _write_cfg(tmp, out1)
    summary = run_generation(str(cfg_path))
    return tmp, out1, summary


def test_summary_counts_consistent(generated):
    _, _, s = generated
    assert s["pairs"] == s["positives"] + s["negatives"]
    assert s["identities"] == 40
    assert s["homoglyph_attacks"] <= 20


def test_artifacts_written(generated):
    _, out1, _ = generated
    assert (out1 / "full" / "pairs.parquet").exists()
    assert (out1 / "full" / "surfaces.parquet").exists()
    for name in ("identities_sample.csv", "surfaces_sample.csv", "pairs_sample.csv"):
        assert (out1 / "sample" / name).exists()
    assert (out1 / "adversarial" / "homoglyph_v1" / "homoglyphs.parquet").exists()


def test_homoglyphs_fold_equal(generated):
    _, out1, _ = generated
    hg = pd.read_parquet(out1 / "adversarial" / "homoglyph_v1" / "homoglyphs.parquet")
    assert len(hg) > 0
    assert (hg["fold_clean"] == hg["fold_attacked"]).all()
    assert (hg["clean"] != hg["attacked"]).all()  # differ at code-point level


def test_full_reproducibility(generated, tmp_path):
    # A second run with the same seed must produce an identical pairs table.
    tmp, out1, _ = generated
    out2 = tmp / "run2"
    cfg_path = _write_cfg(tmp, out2)
    run_generation(str(cfg_path))

    a = pd.read_parquet(out1 / "full" / "pairs.parquet")
    b = pd.read_parquet(out2 / "full" / "pairs.parquet")
    assert a.equals(b)

    sa = pd.read_parquet(out1 / "full" / "surfaces.parquet")
    sb = pd.read_parquet(out2 / "full" / "surfaces.parquet")
    assert sa.equals(sb)
