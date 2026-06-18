"""AZ-RU cross-script phonetic normalization — the genuine technical contribution.

Competing transliterations of one name diverge on a small set of graphemes
(``ə`` -> e|a, ``x`` -> kh|h, ``q`` -> g, ``ç`` -> ch, ``ş`` -> sh, ``ğ`` -> gh|g,
``c`` -> j|dj, the ``-iy-`` cluster, Cyrillic ``я/ю`` -> ia/ya …). ``normalize_token``
collapses all of these to ONE abstract skeleton *before* phonetic coding, so
``Əliyev`` / ``Aliyev`` / ``Aliev`` / Cyrillic ``Алиев`` converge to the same key.

Two cross-script inputs are handled:
- **Genuine Cyrillic** (a token written entirely in Cyrillic) is romanized by *sound*
  (``unidecode``): ``Алиев`` -> ``aliev``.
- **Homoglyph attack** (a Latin token with sprinkled Cyrillic confusables, i.e. a token
  that mixes both scripts) is folded by *shape* (TR39): ``Наѕаnоv`` -> ``hasanov``.
  Mixing the two correctly is why a single ``unidecode`` pass is not enough.
"""

from __future__ import annotations

from unidecode import unidecode

from aznamematch.generate.homoglyph import confusable_fold

# Ordered digraph collapses (applied left-to-right on an ASCII-lower string).
_DIGRAPHS: list[tuple[str, str]] = [
    ("shch", "s"), ("kh", "h"), ("gh", "g"), ("ch", "j"), ("sh", "s"),
    ("zh", "j"), ("dj", "j"), ("ts", "s"), ("ya", "a"), ("yu", "o"),
    ("yo", "o"), ("ye", "a"), ("iy", "i"), ("ij", "i"),
]
# Single-char collapses (affricate/fricative + back-consonant equivalence classes).
_SINGLE: dict[str, str] = {"x": "h", "q": "g", "c": "j", "w": "v", "y": ""}
# Vowel classes: ə/e/a -> a ; o/u -> o ; ı/i -> i.
_VOWEL: dict[str, str] = {"a": "a", "e": "a", "o": "o", "u": "o", "i": "i"}


def _is_cyrillic(ch: str) -> bool:
    return 0x0400 <= ord(ch) <= 0x04FF


def _to_ascii(token: str) -> str:
    """Romanize a single token to ASCII lowercase, choosing shape- vs sound-fold."""
    t = token.replace("ə", "a").replace("Ə", "A")  # dodge unidecode's ə -> '@'
    has_cyr = any(_is_cyrillic(c) for c in t)
    has_lat = any("a" <= c.lower() <= "z" for c in t)
    if has_cyr and has_lat:           # mixed-script token == homoglyph attack -> shape fold
        t = confusable_fold(t)
    return unidecode(t).lower()


def _collapse(s: str) -> str:
    for src, dst in _DIGRAPHS:
        s = s.replace(src, dst)
    s = "".join(_SINGLE.get(c, c) for c in s)
    s = "".join(_VOWEL.get(c, c) for c in s)
    out: list[str] = []
    for c in s:
        if c.isalnum() and (not out or out[-1] != c):  # keep alnum, dedupe runs
            out.append(c)
    return "".join(out)


def normalize_token(token: str) -> str:
    """Collapse one token to its cross-script skeleton (e.g. ``Əliyev`` -> ``aliav``)."""
    return _collapse(_to_ascii(token))


def normalize_name(name: str) -> list[str]:
    """Per-token skeletons (empty tokens dropped)."""
    return [k for t in name.split() if (k := normalize_token(t))]
