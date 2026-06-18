"""Phase 5: blocking (candidate generation) with RR / PQ / PC metrics.

Entity resolution = blocking -> matching. Blocking cheaply prunes the O(N^2) pair space to a
candidate set; matching then scores candidates. We report the three standard blocking metrics
on a record set (two records "match" iff they share a ``canonical_id``):

- **Reduction Ratio (RR)** = 1 - candidates / all-pairs  (how much work was saved)
- **Pair Completeness (PC)** = true matches kept / all true matches  (recall — the one that hurts)
- **Pair Quality (PQ)** = true matches kept / candidates  (precision of the candidate set)

Key demonstration: a *naive* blocker keyed on raw tokens / script puts the AZ-Latin and the
Cyrillic surface of the same person in different blocks, so it silently drops every
cross-script true match (low PC) — exactly the failure mode this benchmark exists to expose.
A fold/phonetic-key blocker bridges scripts and recovers them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations

from aznamematch.textnorm import fold_ascii

_VOWELS_Y = set("aeiouy")


@dataclass(frozen=True)
class Record:
    """A blockable record: ground-truth id + observed surface + script."""

    id: str
    surface: str
    script: str


@dataclass(frozen=True)
class BlockingMetrics:
    reduction_ratio: float
    pair_completeness: float
    pair_quality: float
    n_candidates: int
    n_true: int
    n_true_in_candidates: int


def _skeleton(token: str) -> str:
    """A cross-script-bridging phonetic key: ASCII-fold, drop vowels+y, dedupe runs.

    ``Aliyev``, ``Aliev`` and Cyrillic ``Алиев`` all reduce to ``lv``.
    """
    folded = fold_ascii(token)
    out: list[str] = []
    for ch in folded:
        if ch.isalnum() and ch not in _VOWELS_Y:
            if not out or out[-1] != ch:
                out.append(ch)
    return "".join(out)


class Blocker(ABC):
    name: str

    @abstractmethod
    def keys(self, record: Record) -> set[str]:
        """Blocking keys for a record; two records are candidates iff they share a key."""

    def candidate_pairs(self, records: list[Record]) -> set[frozenset[int]]:
        inverted: dict[str, list[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            for key in self.keys(rec):
                inverted[key].append(idx)
        cands: set[frozenset[int]] = set()
        for idxs in inverted.values():
            if len(idxs) > 1:
                for a, b in combinations(idxs, 2):
                    cands.add(frozenset((a, b)))
        return cands

    def evaluate(self, records: list[Record]) -> BlockingMetrics:
        n = len(records)
        total_pairs = n * (n - 1) // 2
        id_counts = Counter(r.id for r in records)
        n_true = sum(c * (c - 1) // 2 for c in id_counts.values())

        cands = self.candidate_pairs(records)
        true_in_cand = sum(1 for p in cands if _same_id(p, records))

        rr = 1 - len(cands) / total_pairs if total_pairs else 0.0
        pc = true_in_cand / n_true if n_true else 0.0
        pq = true_in_cand / len(cands) if cands else 0.0
        return BlockingMetrics(rr, pc, pq, len(cands), n_true, true_in_cand)


def _same_id(pair: frozenset[int], records: list[Record]) -> bool:
    a, b = tuple(pair)
    return records[a].id == records[b].id


class ExactTokenBlocker(Blocker):
    """Keys = raw lowercased whole tokens. Naive: cross-script tokens never match."""

    name = "exact_token"

    def keys(self, record: Record) -> set[str]:
        return {t.lower() for t in record.surface.split() if t}


class QGramBlocker(Blocker):
    """Keys = raw character q-grams (default 3). Also script-bound (no cross-script fold)."""

    name = "qgram"

    def __init__(self, q: int = 3) -> None:
        self.q = q
        self.name = f"qgram{q}"

    def keys(self, record: Record) -> set[str]:
        s = record.surface.lower().replace(" ", "")
        if len(s) <= self.q:
            return {s} if s else set()
        return {s[i:i + self.q] for i in range(len(s) - self.q + 1)}


class PhoneticKeyBlocker(Blocker):
    """Keys = cross-script phonetic skeleton per token (bridges AZ-Latin / Cyrillic / Latin)."""

    name = "phonetic_key"

    def keys(self, record: Record) -> set[str]:
        return {k for t in record.surface.split() if (k := _skeleton(t))}


class ScriptBlocker(Blocker):
    """Naive script-based blocker: keys = (script, first folded letter).

    Demonstrates the cross-script failure: same person in two scripts shares no key, so every
    cross-script true match is dropped. Included as a cautionary baseline.
    """

    name = "naive_script"

    def keys(self, record: Record) -> set[str]:
        folded = fold_ascii(record.surface)
        first = folded[0] if folded else "?"
        return {f"{record.script}:{first}"}


def default_blockers() -> list[Blocker]:
    return [ExactTokenBlocker(), QGramBlocker(3), PhoneticKeyBlocker(), ScriptBlocker()]


def compare_blockers(records: list[Record],
                     blockers: list[Blocker] | None = None) -> dict[str, BlockingMetrics]:
    blockers = blockers or default_blockers()
    return {b.name: b.evaluate(records) for b in blockers}


def records_from_surface_rows(rows: list[dict], per_identity_cap: int | None = None,
                              ) -> list[Record]:
    """Build a record set from surface rows (dicts with canonical_id/surface/script).

    ``per_identity_cap`` keeps at most that many surfaces per identity (input order), to keep
    the all-pairs space tractable for a blocking demo.
    """
    seen: Counter = Counter()
    out: list[Record] = []
    for r in rows:
        cid = r["canonical_id"]
        if per_identity_cap is not None and seen[cid] >= per_identity_cap:
            continue
        seen[cid] += 1
        out.append(Record(id=cid, surface=r["surface"], script=r["script"]))
    return out
