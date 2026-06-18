"""Matcher abstract base + registry.

A matcher scores how likely two surface strings denote the same entity, in ``[0, 1]``.
Some matchers need training (RegressionV1); the default ``fit`` is a no-op. ``scores`` is a
batch hook matchers can override for efficiency (e.g. the semantic encoder).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

_REGISTRY: dict[str, type[Matcher]] = {}


class Matcher(ABC):
    name: str = "base"
    requires_training: bool = False

    @abstractmethod
    def score(self, a: str, b: str) -> float:
        """Similarity in [0, 1]: 1 = same entity, 0 = unrelated."""

    def scores(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [self.score(a, b) for a, b in pairs]

    def fit(self, pairs: list[tuple[str, str]], labels: list[int]) -> None:
        """Train the matcher (no-op for unsupervised matchers)."""
        return None


def register(cls: type[Matcher]) -> type[Matcher]:
    _REGISTRY[cls.name] = cls
    return cls


def available() -> list[str]:
    return sorted(_REGISTRY)


def get_matcher(name: str, **kwargs) -> Matcher:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown matcher {name!r}; available: {available()}")
    return _REGISTRY[name](**kwargs)
