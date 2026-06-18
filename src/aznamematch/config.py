"""Configuration loading.

The generation pipeline is driven entirely by ``configs/generation.yaml`` (see that file
for documented knobs). We keep the config as a plain nested dict and expose a tiny typed
accessor so callers get a clear error on a missing key instead of a silent ``None``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Repository root = three levels up from this file
# (src/aznamematch/config.py -> src/aznamematch -> src -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "generation.yaml"


class _Missing:
    """Sentinel so ``None`` is a valid explicit default for :func:`get`."""

    __slots__ = ()


_MISSING = _Missing()


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load a generation config YAML into a nested dict.

    Args:
        path: Path to the YAML file. Defaults to ``configs/generation.yaml``.
    """
    cfg_path = Path(path) if path is not None else DEFAULT_CONFIG
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping, got {type(data).__name__}")
    return data


def get(cfg: dict[str, Any], dotted: str, default: Any = _MISSING) -> Any:
    """Fetch ``cfg["a"]["b"]["c"]`` via ``get(cfg, "a.b.c")``.

    Raises ``KeyError`` if the path is absent and no ``default`` is given.
    """
    node: Any = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            if isinstance(default, _Missing):
                raise KeyError(f"Missing config key: {dotted!r}")
            return default
        node = node[part]
    return node
