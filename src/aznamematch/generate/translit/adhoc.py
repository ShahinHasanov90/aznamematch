"""Ad-hoc, standardless Latin transliteration — the common real-world case.

No consistent standard: a person's name is romanized however a clerk/typist rendered it,
producing competing spellings (``Алиев`` -> ``Aliyev | Aliev | Alyev | Alijev``;
``Юрий`` -> ``Yuri | Yury | Juri | Iurii``). We model this by sampling, per AZ special
letter / cluster, from a set of attested competing renderings. Output is tagged ``ad_hoc``.
"""

from __future__ import annotations

import numpy as np

from aznamematch.generate.translit.az_cyrl import az_lower

# Per-letter competing ASCII renderings (lowercased AZ Latin -> options).
_CHOICES: dict[str, list[str]] = {
    "ə": ["e", "a"],
    "x": ["kh", "h"],
    "q": ["g", "q"],
    "c": ["j", "dj"],
    "ç": ["ch"],
    "ş": ["sh"],
    "ğ": ["gh", ""],
    "ö": ["o", "oe"],
    "ü": ["u", "ue"],
    "ı": ["i"],
    "j": ["zh", "j"],
}

# The -iy- cluster drives the canonical Aliyev/Aliev/Alyev/Alijev divergence.
_IY_CLUSTER = ["iy", "i", "ij", "y"]


def _one_variant(low_name: str, rng: np.random.Generator) -> str:
    out: list[str] = []
    i = 0
    n = len(low_name)
    while i < n:
        if low_name.startswith("iy", i):
            out.append(str(rng.choice(_IY_CLUSTER)))
            i += 2
            continue
        ch = low_name[i]
        if ch in _CHOICES:
            out.append(str(rng.choice(_CHOICES[ch])))
        else:
            out.append(ch)
        i += 1
    text = "".join(out)
    return " ".join(w[:1].upper() + w[1:] if w else w for w in text.split(" "))


def variants(name: str, rng: np.random.Generator, max_variants: int = 3) -> list[str]:
    """Up to ``max_variants`` distinct ad-hoc romanizations of ``name`` (deterministic)."""
    low = az_lower(name)
    seen: list[str] = []
    # Sample more attempts than needed to survive collisions, then keep first distinct ones.
    for _ in range(max_variants * 4):
        v = _one_variant(low, rng)
        if v not in seen:
            seen.append(v)
        if len(seen) >= max_variants:
            break
    return seen
