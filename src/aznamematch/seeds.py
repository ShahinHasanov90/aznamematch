"""Deterministic seeding utilities.

Same master seed -> byte-identical dataset (see ``docs/rules/seeding.md``). Every
generation stage gets its own child ``SeedSequence`` so that changing one stage's number
of random draws does not shift another stage's stream.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Ordered names of the pipeline stages that consume randomness. The order is part of the
# reproducibility contract: appending a new stage is safe (SeedSequence.spawn is incremental,
# so existing children are unchanged), reordering is NOT.
STAGE_NAMES: tuple[str, ...] = (
    "canonical",
    "suffix_matrix",
    "translit",
    "noise",
    "homoglyph",
    "pairs",
    "surface",  # per-identity surface-form construction (translit + noise combined stream)
)


@dataclass(frozen=True)
class StageSeeds:
    """Per-stage child :class:`numpy.random.SeedSequence` objects, keyed by stage name."""

    master: int
    _by_stage: dict[str, np.random.SeedSequence]

    def seq(self, stage: str) -> np.random.SeedSequence:
        if stage not in self._by_stage:
            raise KeyError(f"Unknown stage {stage!r}; known: {tuple(self._by_stage)}")
        return self._by_stage[stage]

    def rng(self, stage: str) -> np.random.Generator:
        """A fresh, deterministic Generator for a whole stage."""
        return np.random.default_rng(self.seq(stage))


def stage_seeds(master_seed: int) -> StageSeeds:
    """Derive per-stage seeds from a single master seed."""
    children = np.random.SeedSequence(master_seed).spawn(len(STAGE_NAMES))
    by_stage = dict(zip(STAGE_NAMES, children, strict=True))
    return StageSeeds(master=master_seed, _by_stage=by_stage)


def record_rng(stage_seq: np.random.SeedSequence, key: int) -> np.random.Generator:
    """A reproducible per-record Generator independent of iteration order.

    Derives a child stream from the stage's entropy plus a stable integer ``key`` (e.g. a
    numeric form of ``canonical_id``), so record N always draws the same values regardless
    of how many records preceded it.
    """
    entropy = tuple(stage_seq.entropy) if isinstance(stage_seq.entropy, (list, tuple)) else (
        int(stage_seq.entropy),
    )
    child = np.random.SeedSequence(entropy=list(entropy) + [int(key)])
    return np.random.default_rng(child)
