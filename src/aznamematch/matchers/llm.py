"""Optional LLM matcher (gated, provider-neutral).

Few-shot "same real-world entity? probability in [0,1]" against ANY OpenAI-compatible chat
endpoint (hosted or local). Configured purely by environment variables, so no specific
provider or SDK is baked in:

- ``LLM_API_KEY``   — bearer token for the endpoint.
- ``LLM_BASE_URL``  — base URL, e.g. ``https://api.example.com/v1`` (``/chat/completions`` is
  appended).
- ``LLM_MODEL``     — model identifier the endpoint expects.

It is NON-deterministic, so it is kept OUT of the committed reference results (the harness
records it separately if enabled). If the env vars are absent, :meth:`available` is False and
the harness skips it with a clear log line rather than crashing. Uses only the standard
library (no extra dependency).
"""

from __future__ import annotations

import json
import os
import urllib.request

from aznamematch.matchers.base import Matcher

_SYSTEM = (
    "You decide whether two name strings refer to the SAME real-world person or "
    "organization, accounting for cross-script transliteration (Azerbaijani Latin, Russian "
    "Cyrillic, English) and spelling variation. Reply with only a number in [0,1]: the "
    "probability they are the same entity."
)


class LLMMatcher(Matcher):
    name = "llm"

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.model = model or os.environ.get("LLM_MODEL", "")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "")).rstrip("/")

    @staticmethod
    def available() -> bool:
        return bool(os.environ.get("LLM_API_KEY")
                    and os.environ.get("LLM_BASE_URL")
                    and os.environ.get("LLM_MODEL"))

    def score(self, a: str, b: str) -> float:
        if not self.available():
            raise RuntimeError(
                "LLMMatcher unavailable (set LLM_API_KEY, LLM_BASE_URL, LLM_MODEL).")
        payload = {
            "model": self.model,
            "max_tokens": 8,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f"Name A: {a}\nName B: {b}\nProbability:"},
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (configured URL)
            data = json.load(resp)
        text = data["choices"][0]["message"]["content"].strip()
        try:
            return max(0.0, min(1.0, float(text.split()[0])))
        except (ValueError, IndexError):
            return 0.5
