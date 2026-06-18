"""Hybrid matcher: weighted blend and cheap-filter -> expensive-confirm cascade."""

from __future__ import annotations

from aznamematch.matchers.base import Matcher, register
from aznamematch.matchers.lexical import LexicalMatcher
from aznamematch.matchers.phonetic import PhoneticMatcher


@register
class HybridMatcher(Matcher):
    """Combine component matchers.

    - ``mode="blend"``: weighted average of component scores.
    - ``mode="cascade"``: a cheap matcher gates; only above ``gate`` do we pay for the
      expensive confirmer, and the final score is their max (cheap evidence alone can't
      confirm, but the confirmer can rescue a cross-script pair the cheap one missed).

    Defaults use lexical + normalized-phonetic so the hybrid needs no training or model
    download; callers may inject any components (e.g. add a semantic matcher).
    """

    name = "hybrid"

    def __init__(self, components: list[tuple[Matcher, float]] | None = None,
                 mode: str = "blend", gate: float = 0.4) -> None:
        if components is None:
            components = [(LexicalMatcher("token_set"), 0.5),
                         (PhoneticMatcher(normalize=True), 0.5)]
        self.components = components
        self.mode = mode
        self.gate = gate
        self.name = f"hybrid_{mode}"

    def score(self, a: str, b: str) -> float:
        if self.mode == "blend":
            total = sum(w for _, w in self.components) or 1.0
            return sum(m.score(a, b) * w for m, w in self.components) / total
        if self.mode == "cascade":
            cheap, expensive = self.components[0][0], self.components[-1][0]
            cheap_s = cheap.score(a, b)
            if cheap_s >= self.gate:
                return cheap_s  # cheap matcher is confident; skip the expensive one
            # Low cheap score: consult the expensive confirmer to rescue cross-script pairs.
            return max(cheap_s, expensive.score(a, b))
        raise ValueError(f"Unknown hybrid mode: {self.mode!r}")
