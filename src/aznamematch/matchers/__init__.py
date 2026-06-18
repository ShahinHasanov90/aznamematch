"""Matchers (Phase 6). Each subclasses Matcher and exposes score(a, b) -> float in [0, 1].

Importing this package registers the lightweight matchers (lexical, phonetic, regression,
hybrid). The semantic (sentence-transformers/torch) and LLM (llm) matchers are
imported lazily by name via :func:`load_optional` to keep the default import cheap.
"""

from __future__ import annotations

from aznamematch.matchers import lexical, phonetic  # noqa: F401  (register on import)
from aznamematch.matchers.base import Matcher, available, get_matcher, register

__all__ = ["Matcher", "available", "get_matcher", "register", "load_optional"]


def load_optional(name: str):
    """Import a heavy matcher module on demand (``semantic`` / ``llm``) and return its class."""
    if name == "semantic":
        from aznamematch.matchers.semantic import SemanticMatcher
        return SemanticMatcher
    if name == "llm":
        from aznamematch.matchers.llm import LLMMatcher
        return LLMMatcher
    raise KeyError(f"No optional matcher {name!r}")
