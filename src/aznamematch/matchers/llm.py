"""Optional LLM matcher (gated). Few-shot "same real-world entity? yes/no + confidence".

Gated behind ``--with-llm`` + ``LLM_API_KEY``. It is NON-deterministic, so it is kept
OUT of the committed reference results (the harness records it separately if enabled). If the
key/SDK is absent, :meth:`available` is False and the harness skips it with a clear log line
rather than crashing.
"""

from __future__ import annotations

import os

from aznamematch.matchers.base import Matcher

_SYSTEM = (
    "You decide whether two name strings refer to the SAME real-world person or "
    "organization, accounting for cross-script transliteration (Azerbaijani Latin, Russian "
    "Cyrillic, English) and spelling variation. Reply with only a number in [0,1]: the "
    "probability they are the same entity."
)


class LLMMatcher(Matcher):
    name = "llm"

    def __init__(self, model: str = "configured-model") -> None:
        self.model = model
        self._client = None

    @staticmethod
    def available() -> bool:
        if not os.environ.get("LLM_API_KEY"):
            return False
        try:
            import llm  # noqa: F401
        except ImportError:
            return False
        return True

    def _ensure(self):
        if self._client is None:
            import llm

            self._client = llm.llm()
        return self._client

    def score(self, a: str, b: str) -> float:
        if not self.available():
            raise RuntimeError("LLMMatcher unavailable (need LLM_API_KEY + llm).")
        client = self._ensure()
        msg = client.messages.create(
            model=self.model,
            max_tokens=8,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Name A: {a}\nName B: {b}\nProbability:"}],
        )
        text = "".join(getattr(b_, "text", "") for b_ in msg.content).strip()
        try:
            return max(0.0, min(1.0, float(text.split()[0])))
        except (ValueError, IndexError):
            return 0.5
