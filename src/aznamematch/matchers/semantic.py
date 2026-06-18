"""Semantic matcher: multilingual sentence-embedding cosine similarity.

Uses a multilingual sentence-transformer (default ``paraphrase-multilingual-MiniLM-L12-v2``)
that embeds names across scripts into a shared space; the score is cosine similarity mapped
to [0, 1]. The model is loaded lazily and cached; the first run downloads weights (CPU is
fine, no GPU required). This module is imported on demand (it pulls in torch).
"""

from __future__ import annotations

import numpy as np

from aznamematch.matchers.base import Matcher

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SemanticMatcher(Matcher):
    name = "semantic"

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None

    def _ensure(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _embed(self, texts: list[str]) -> np.ndarray:
        model = self._ensure()
        emb = model.encode(texts, normalize_embeddings=True, show_progress_bar=False,
                           convert_to_numpy=True)
        return np.asarray(emb, dtype=np.float32)

    def score(self, a: str, b: str) -> float:
        emb = self._embed([a, b])
        return self._cos(emb[0], emb[1])

    def scores(self, pairs: list[tuple[str, str]]) -> list[float]:
        # Encode each unique surface once, then look up per pair.
        uniq = sorted({s for p in pairs for s in p})
        index = {s: i for i, s in enumerate(uniq)}
        emb = self._embed(uniq)
        return [self._cos(emb[index[a]], emb[index[b]]) for a, b in pairs]

    @staticmethod
    def _cos(u: np.ndarray, v: np.ndarray) -> float:
        # Embeddings are L2-normalized, so the dot product IS cosine. We clamp negatives to 0
        # rather than rescaling [-1,1]->[0,1]: rescaling would compress everything into a
        # misleadingly high band. The raw cosine honestly reflects that this multilingual
        # model only weakly separates short names (the threshold sweep handles the operating
        # point; AUC is invariant to this monotone choice).
        return float(max(0.0, min(1.0, float(np.dot(u, v)))))
