"""Phase 0: config loading + dotted access."""

from __future__ import annotations

import pytest

from aznamematch.config import DEFAULT_CONFIG, get, load_config


def test_default_config_loads():
    cfg = load_config()
    assert isinstance(cfg, dict)
    assert "seed" in cfg


def test_default_config_path_exists():
    assert DEFAULT_CONFIG.exists()


def test_get_dotted_access():
    cfg = load_config()
    assert get(cfg, "identities.count") == cfg["identities"]["count"]


def test_get_missing_raises():
    cfg = load_config()
    with pytest.raises(KeyError):
        get(cfg, "does.not.exist")


def test_get_missing_returns_default():
    cfg = load_config()
    assert get(cfg, "does.not.exist", default=None) is None
    assert get(cfg, "does.not.exist", default=42) == 42


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")
