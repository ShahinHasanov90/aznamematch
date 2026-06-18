"""Phase 3: intra-script corruption (FEBRL / GeCo / pseudopeople paradigm).

Seeded, per-token corruption applied to a surface form within its own script. Each call
records exactly which corruption types fired, so the pair-level error decomposition (Phase 7)
can attribute a false match/miss to a root cause. This layer models *incidental* noise (typos,
OCR, phonetic spelling, dropped patronymics) — it is distinct from the *deliberate* homoglyph
obfuscation in `homoglyph.py`.

Corruption taxonomy (per-token): ``char_edit`` (insert/delete/substitute/transpose),
``ocr``, ``phonetic``, ``keyboard`` (AZ-QWERTY adjacency), ``diacritic_loss`` (ə→e, ş→s, …),
``abbreviation`` (token→initial). Record-level: ``token_reorder``, ``patronymic_drop``,
``case``, ``whitespace_punct``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aznamematch.config import get
from aznamematch.generate.translit.base import CYRL, LATN_AZ, LATN_TRANSLIT

_LATIN_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
_AZ_EXTRA = "əğçşöüı"
_CYR_ALPHABET = "абвгдежзийклмнопрстуфхцчшщыэюя"

# OCR confusion lookups (ordered longest-first when scanned).
_OCR_LATIN = {"rn": "m", "cl": "d", "m": "rn", "o": "0", "l": "1", "i": "1", "b": "6",
              "s": "5", "g": "9", "q": "9", "z": "2"}
_OCR_CYR = {"о": "0", "з": "3", "б": "6"}

# Phonetic confusion lookups (Latin).
_PHONETIC = {"ph": "f", "ck": "k", "kh": "h", "sh": "s", "ee": "i", "oo": "u",
             "y": "i", "z": "s", "x": "ks"}

# Diacritic loss (AZ Latin special letter -> ASCII).
_DIACRITIC = {"ə": "e", "ğ": "g", "ç": "c", "ş": "s", "ö": "o", "ü": "u", "ı": "i",
              "x": "kh", "q": "g"}

# AZ-QWERTY keyboard adjacency (base Latin keys).
_KEYBOARD = {
    "q": "wa", "w": "qes", "e": "wrd", "r": "etf", "t": "ryg", "y": "tuh", "u": "yij",
    "i": "uok", "o": "ipl", "p": "ol", "a": "qsz", "s": "awdx", "d": "serfc",
    "f": "drtgv", "g": "ftyhb", "h": "gyujn", "j": "huikm", "k": "jiol", "l": "kop",
    "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb", "b": "vghn", "n": "bhjm",
    "m": "njk",
}


def _alphabet(script: str) -> str:
    if script == CYRL:
        return _CYR_ALPHABET
    if script == LATN_AZ:
        return _LATIN_ALPHABET + _AZ_EXTRA
    return _LATIN_ALPHABET


def _char_edit(token: str, rng: np.random.Generator, alphabet: str) -> tuple[str, bool]:
    ops = ["insert", "substitute", "transpose", "delete"]
    op = str(rng.choice(ops))
    if len(token) < 2 and op != "insert":
        op = "insert"
    pos = int(rng.integers(0, len(token) + (1 if op == "insert" else 0)))
    if op == "insert":
        ch = alphabet[int(rng.integers(0, len(alphabet)))]
        return token[:pos] + ch + token[pos:], True
    if op == "delete":
        return token[:pos] + token[pos + 1:], True
    if op == "substitute":
        ch = alphabet[int(rng.integers(0, len(alphabet)))]
        return token[:pos] + ch + token[pos + 1:], True
    # transpose adjacent
    j = min(pos, len(token) - 2)
    return token[:j] + token[j + 1] + token[j] + token[j + 2:], True


def _apply_lookup(token: str, rng: np.random.Generator,
                  table: dict[str, str]) -> tuple[str, bool]:
    """Replace one occurrence of a table key (longest-first) at a random eligible site."""
    low = token.lower()
    sites: list[tuple[int, str, str]] = []
    for key in sorted(table, key=len, reverse=True):
        start = 0
        while (idx := low.find(key, start)) != -1:
            sites.append((idx, key, table[key]))
            start = idx + 1
    if not sites:
        return token, False
    idx, key, rep = sites[int(rng.integers(0, len(sites)))]
    return token[:idx] + rep + token[idx + len(key):], True


def _keyboard(token: str, rng: np.random.Generator) -> tuple[str, bool]:
    positions = [i for i, c in enumerate(token) if c.lower() in _KEYBOARD]
    if not positions:
        return token, False
    i = positions[int(rng.integers(0, len(positions)))]
    neighbors = _KEYBOARD[token[i].lower()]
    rep = neighbors[int(rng.integers(0, len(neighbors)))]
    if token[i].isupper():
        rep = rep.upper()
    return token[:i] + rep + token[i + 1:], True


def _diacritic_loss(token: str, _rng: np.random.Generator) -> tuple[str, bool]:
    if not any(c.lower() in _DIACRITIC for c in token):
        return token, False
    out = []
    for c in token:
        rep = _DIACRITIC.get(c.lower())
        if rep is None:
            out.append(c)
        else:
            out.append(rep[0].upper() + rep[1:] if c.isupper() else rep)
    return "".join(out), True


def _abbreviation(token: str, _rng: np.random.Generator) -> tuple[str, bool]:
    if len(token) < 2:
        return token, False
    return token[0] + ".", True


def _corrupt_token(token: str, script: str, rng: np.random.Generator,
                   rates: dict[str, float]) -> tuple[str, str]:
    applicable = ["char_edit", "ocr", "abbreviation"]
    if script in (LATN_AZ, LATN_TRANSLIT):
        applicable += ["phonetic", "keyboard"]
    if script == LATN_AZ:
        applicable.append("diacritic_loss")

    weights = np.array([max(0.0, float(rates.get(t, 0.0))) for t in applicable])
    if weights.sum() <= 0:
        weights = np.ones(len(applicable))
    chosen = str(rng.choice(applicable, p=weights / weights.sum()))

    alphabet = _alphabet(script)
    ocr_table = _OCR_CYR if script == CYRL else _OCR_LATIN
    dispatch = {
        "char_edit": lambda t, r: _char_edit(t, r, alphabet),
        "ocr": lambda t, r: _apply_lookup(t, r, ocr_table),
        "phonetic": lambda t, r: _apply_lookup(t, r, _PHONETIC),
        "keyboard": _keyboard,
        "diacritic_loss": _diacritic_loss,
        "abbreviation": _abbreviation,
    }
    new, applied = dispatch[chosen](token, rng)
    if not applied:  # fall back so an intended corruption is realized + labelled honestly
        new, _ = _char_edit(token, rng, alphabet)
        chosen = "char_edit"
    return new, chosen


def corrupt(text: str, script: str, rng: np.random.Generator, cfg: dict[str, Any],
            *, droppable_indices: list[int] | None = None) -> tuple[str, list[str]]:
    """Return a corrupted copy of ``text`` and the sorted list of corruption types applied.

    ``droppable_indices`` names token positions eligible for ``patronymic_drop`` (the caller
    knows which tokens are the patronymic). An empty result list means no corruption fired.
    """
    tokens = text.split()
    if not tokens:
        return text, []
    types: set[str] = set()

    p_tok = float(get(cfg, "noise.p_corrupt_token", 0.35))
    rates = dict(get(cfg, "noise.rates", {}))
    for i, tok in enumerate(tokens):
        if rng.random() < p_tok:
            tokens[i], applied_type = _corrupt_token(tok, script, rng, rates)
            types.add(applied_type)

    rl = dict(get(cfg, "noise.record_level", {}))

    # patronymic drop (before reorder so indices stay valid)
    if droppable_indices and rng.random() < float(rl.get("p_patronymic_drop", 0.0)):
        drop = set(droppable_indices)
        tokens = [t for j, t in enumerate(tokens) if j not in drop]
        types.add("patronymic_drop")

    # token reorder (swap two positions)
    if len(tokens) >= 2 and rng.random() < float(rl.get("p_token_reorder", 0.0)):
        a, b = (int(x) for x in rng.choice(len(tokens), size=2, replace=False))
        tokens[a], tokens[b] = tokens[b], tokens[a]
        types.add("token_reorder")

    result = " ".join(tokens)

    # case change
    if rng.random() < float(rl.get("p_case_change", 0.0)):
        result = result.upper() if rng.random() < 0.5 else result.lower()
        types.add("case")

    # whitespace / punctuation noise
    if rng.random() < float(rl.get("p_punct_ws", 0.0)):
        result = _punct_ws(result, rng)
        types.add("whitespace_punct")

    return result, sorted(types)


def _punct_ws(text: str, rng: np.random.Generator) -> str:
    choice = int(rng.integers(0, 3))
    if choice == 0:
        return text.replace(" ", "  ", 1)  # double space
    if choice == 1:
        return text + "."  # trailing dot
    return text.replace(" ", "-", 1)  # hyphenate a separator
