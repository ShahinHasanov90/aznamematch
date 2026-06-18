# Transliteration standards & mappings

Source: `src/aznamematch/generate/translit/`. Config: `transliteration.*` in
`configs/generation.yaml`. Every generated variant is tagged with the standard that produced
it (`translit_standard`) — the **divergence between competing standards** is the phenomenon
the benchmark measures.

> **Fidelity note.** These are *divergence profiles grounded in* the cited standards,
> implemented at the granularity that matters for personal-name matching (the letters where
> standards visibly disagree). They are not byte-perfect, edition-complete implementations of
> each full standard — real-world ad-hoc transliteration is itself inconsistent, which is the
> point. Reversibility is implemented (and tested) only where a standard guarantees it.

## 1. Azerbaijani Latin ⇄ Cyrillic — `az_cyrl.py`

### 1a. Soviet Azerbaijani Cyrillic alphabet (bijective, reversible)

The 1958–1991 Azerbaijani Cyrillic alphabet. This is a 1:1 script mapping, so
`to_latin(to_cyrillic(x)) == x` (tested) — it carries the **ISO 9 reversibility property**
that distinguishes reversible standards from lossy ones. Produces the national `cyrl`
surface. Schwa: Latin `Ə` ⇄ Cyrillic `Ә` (U+04D8).

| Latin | ə | x | q | g | ğ | c | ç | ş | ö | ü | ı | y | j | h |
|-------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cyr   | ә | х | г | ҝ | ғ | ҹ | ч | ш | ө | ү | ы | ј | ж | һ |

(Plain letters a б в … map as in Russian Cyrillic; full table in code.)

### 1b. Russified Russian-Cyrillic rendering (lossy, many-to-one)

How an Azerbaijani name was written in Soviet/Russian-language documents:
`Əliyev → Алиев`, `Hüseyn → Гусейн`, `Cəfər → Джафар`. Salient choices: `ə→а`, `h→г`,
`c→дж`, `x→х`, `q→г`, the `-iyev → -иев` collapse. Tagged `cyrl` / `standard=none`.

### 1c. AZ Latin → ASCII Latin romanization profiles

Competing plain-Latin renderings. The headline divergences:

| AZ letter | BGN/PCGN (1993) | ALA-LC | (ad-hoc options) |
|-----------|-----------------|--------|------------------|
| ə | **e** | **a** | e, a |
| ğ | **gh** | **g** | gh, (drop) |
| x | kh | kh | kh, h |
| q | g | g | g, q |
| c | j | j | j, dj |
| ç / ş | ch / sh | ch / sh | ch / sh |
| ö / ü / ı | o / u / i | o / u / i | o·oe / u·ue / i |

So `Əli → Eli` (BGN/PCGN) vs `Ali` (ALA-LC). Standards: BGN/PCGN 1993 romanization of
Azerbaijani; ALA-LC Azerbaijani romanization table.

## 2. Russian Cyrillic → Latin — `ru_latn.py`

| Cyr | ICAO 9303 | GOST 7.79 (System B) | BGN/PCGN 1947 | ALA-LC 1997 |
|-----|-----------|----------------------|---------------|-------------|
| х | kh | **x** | kh | kh |
| ц | ts | cz | ts | ts |
| ч | ch | ch | ch | ch |
| ш | sh | sh | sh | sh |
| щ | shch | shh | shch | shch |
| й | i | j | y | ĭ |
| е | e | e | **ye** (initial / after vowel) | e |
| ё | e | yo | yo | ë |
| ъ | **ie** | `` (marker) | (drop) | ʺ |
| ы | y | y\` | y | y |
| ю | iu | yu | yu | iu |
| я | ia | ya | ya | ia |
| э | e | e\` | e | ė |

Worked example — `Юрий`: `Iurii` (ICAO) / `Yurij` (GOST) / `Yuriy` (BGN/PCGN) / `Iuriĭ`
(ALA-LC). And `Алиев`: `Aliev` (ICAO/ALA) vs `Aliyev` (BGN/PCGN, via `е→ye` after the vowel
`и`).

- **ICAO Doc 9303** — machine-readable travel documents (passports).
- **GOST 7.79-2000 System B / ISO 9** — univocal & **reversible**:
  `gost_decode(gost_encode(x)) == x` (tested), incl. `щ→shh`, `ъ→``, `ы→y``.
- **BGN/PCGN 1947** — also used on Russian driving licences; context rule `е→ye`.
- **ALA-LC 1997** — library/scholarly romanization.

## 3. Ad-hoc standardless transliteration — `adhoc.py`

The common real case: no consistent standard. Per AZ special letter / `-iy-` cluster, a
spelling is sampled from attested competing options, yielding
`Əliyev → Aliyev | Aliev | Alyev | Alijev | Eliyev | …`. Tagged `ad_hoc`. Seeded, so the set
of variants for a name is reproducible.

## Reversibility summary

| Mapping | Reversible? | Tested |
|---------|-------------|--------|
| AZ Latin ⇄ Soviet AZ Cyrillic | yes (bijective alphabet) | `test_az_latin_cyrillic_roundtrip` |
| GOST 7.79 System B (RU) | yes (univocal) | `test_gost_roundtrip` |
| Russified RU-Cyrillic, ICAO, BGN/PCGN, ALA-LC, ad-hoc | no (many-to-one by design) | — |
