"""Loaders for the invented, AZ-realistic component banks (``*.txt`` in this directory).

Banks use a simple line format: blank lines and ``# ...`` comments are ignored; a line of
the form ``[section]`` starts a named section (used for gender / token category). Items
before any section header go under the default ``""`` section.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from aznamematch.textnorm import fold_ascii

_DIR = Path(__file__).resolve().parent


def _read_sections(filename: str) -> dict[str, list[str]]:
    """Parse a bank into ``{section_name: [items...]}``.

    Items before any ``# section`` header go under the ``""`` (default) section.
    """
    sections: dict[str, list[str]] = {"": []}
    current = ""
    for raw in (_DIR / filename).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return sections


@cache
def given_names() -> dict[str, list[str]]:
    """Given names keyed by gender: ``{"m": [...], "f": [...]}``."""
    secs = _read_sections("az_given.txt")
    return {"m": secs.get("male", []), "f": secs.get("female", [])}


@cache
def family_roots() -> list[str]:
    """Family-name roots (a single default section)."""
    return _read_sections("az_family.txt")[""]


@cache
def patronymic_fathers() -> list[str]:
    """Male given-name roots used to build patronymics."""
    return _read_sections("patronymic.txt")[""]


@cache
def org_tokens() -> dict[str, list[str]]:
    """Org tokens keyed by category: ``{"brand": [...], "industry": [...], "legal": [...]}``."""
    secs = _read_sections("org_tokens.txt")
    return {k: secs.get(k, []) for k in ("brand", "industry", "legal")}


@cache
def denylist_folded() -> frozenset[str]:
    """Well-known real full names, ASCII-folded, for the no-real-persons guard."""
    secs = _read_sections("denylist.txt")
    names = [n for items in secs.values() for n in items]
    return frozenset(fold_ascii(n) for n in names)
