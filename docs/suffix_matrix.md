# Post-Soviet suffix transition matrix

Source: `src/aznamematch/generate/suffix_matrix.py`. Config: `suffix_matrix.*` in
`configs/generation.yaml`.

## What it models

A single Azerbaijani family-name **root** has been rendered differently across political
eras and registration practices. AzNameMatch generates several such renderings for the same
canonical identity, so that a matcher is tested on same-entity pairs whose surface forms
diverge by *morphology*, not just by transliteration or typo.

| Style | Suffix | Example (root `Əli`) | Era / register |
|-------|--------|----------------------|----------------|
| `russified` | `-ov / -ova`, or `-yev / -yeva` after a vowel | `Əliyev` / `Əliyeva` | Soviet / Russified administrative form (→ Cyrillic `Алиев` in transliteration) |
| `zade` | `-zadə` | `Əlizadə` | Contemporary national |
| `soy` | `-soy` | `Əlisoy` | Contemporary national |
| `li` | `-lı / -li / -lu / -lü` (vowel harmony) | `Əlili` | Contemporary national |

Patronymics transition too: the AZ form `Vaqif oğlu` (son) / `Vaqif qızı` (daughter)
vs the Russified `Vaqifoviç` / `Vaqifovna` (→ Cyrillic `Вагифович` / `Вагифовна`).

### Vowel harmony for `-li`

The national `-li` suffix harmonizes with the last vowel of the root:

| Last vowel | Class | Suffix | Example |
|------------|-------|--------|---------|
| `a`, `ı` | back unrounded | `-lı` | `Murad → Muradlı` |
| `o`, `u` | back rounded | `-lu` | `Davud → Davudlu` |
| `e`, `ə`, `i` | front unrounded | `-li` | `Vəli → Vəlili` |
| `ö`, `ü` | front rounded | `-lü` | `Mövsüm → Mövsümlü` |

## How variants are produced

Each canonical identity picks one **canonical style** (russified dominant; see weights in
`choose_canonical_style`). The suffix matrix then *may* add same-entity alternates,
controlled by config probabilities:

- `p_national_alt` → a different national style, tagged `suffix_transform = national`.
- `p_russified` (only if the canonical style is not already russified) → the `-ov/-yev`
  form, tagged `suffix_transform = assimilation`.

These alternates feed Phase 4 positive pairs.

## ⚠️ Modeling assumption (read this)

Treating `Əlizadə` and `Əliyev` (same root `Əli`) as the **same entity** is a deliberate
modeling choice that reflects how one family's surname has been written across eras. **It is
not a universal truth** that every such pair denotes the same person — two unrelated people
named `Əlizadə` and `Əliyev` certainly exist.

The benchmark therefore measures matching performance *under this stated assumption*. Results
should be read as "how well does a matcher recover entities given that surname morphology can
shift this way," not as ground truth about real-world identity. This caveat is repeated in
the README's Limitations section.
