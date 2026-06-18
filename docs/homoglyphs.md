# Adversarial homoglyphs (Unicode TR39 confusables)

Source: `src/aznamematch/generate/homoglyph.py`. Config: `homoglyph.*` in
`configs/generation.yaml`. Output: `data/adversarial/homoglyph_v1/` (frozen, versioned).

## Threat model

A *deliberate* sanctions-evasion / IDN-homograph technique: replace Latin letters in a name
with visually-identical Cyrillic code points. The rendered glyphs look the same to a human,
but the byte sequence differs, so naive string matching treats the names as unrelated.

This is **kept separate** from the core cross-script positives. The core set models
*incidental* divergence (a name genuinely written in two scripts/standards); homoglyphs model
*intentional* obfuscation. Mixing them would distort the cross-script findings, so homoglyph
pairs live in their own versioned directory.

## Confusable table (Latin → Cyrillic)

Grounded in the Unicode TR39 confusables data. Each pair is shape-identical, code-point
distinct.

| Latin | Cyrillic | Latin | Cyrillic | Latin | Cyrillic |
|-------|----------|-------|----------|-------|----------|
| A U+0041 | А U+0410 | H U+0048 | Н U+041D | P U+0050 | Р U+0420 |
| B U+0042 | В U+0412 | I U+0049 | І U+0406 | S U+0053 | Ѕ U+0405 |
| C U+0043 | С U+0421 | J U+004A | Ј U+0408 | T U+0054 | Т U+0422 |
| E U+0045 | Е U+0415 | K U+004B | К U+041A | X U+0058 | Х U+0425 |
| O U+004F | О U+041E | M U+004D | М U+041C | Y U+0059 | У U+0423 |

Lowercase analogues: `a e o c p x y i j s k m` → `а е о с р х у і ј ѕ к м`, plus `h → һ`
(U+04BB). Full mapping in `HOMOGLYPHS`.

## Why `unidecode` is NOT the fix — TR39 skeleton is

A subtle, important point (and an honest finding the benchmark should surface):

`unidecode` transliterates Cyrillic by **sound / romanization convention**, not by **shape**.
So an attacked `Наѕаnоv` (Cyrillic `Н`, `ѕ`, `а`, `о`) becomes `Nadzanov` under `unidecode`
(`Н→N`, `ѕ→dz`, `х→kh`, `С→S`) — which does **not** recover the original `Hasanov`.

The correct repair is the **TR39 confusable skeleton**: map each confusable back to the
Latin letter it *looks like*. `confusable_fold()` implements this, and the property
`confusable_fold(attacked) == confusable_fold(clean)` holds (tested), while
`unidecode(attacked) != clean` for shape-vs-sound mismatches like `С/Н/Х/Р/ѕ`.

## Interpretation

Because the only thing standing between "0% match" and "full match" on this slice is whether
a matcher applies TR39 confusable folding, this slice behaves as a near-binary **capability
check** ("does the matcher normalize confusables?"), not a graded difficulty axis. Report it
as such; do not average it into the incidental cross-script difficulty.
