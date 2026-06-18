# Rule: Provenance & metadata

Every generated surface form and every labeled pair carries structured metadata. This is
what makes later error-decomposition, fairness, calibration, and the Unknown-Standard
protocol possible — so it must be correct at generation time, not bolted on later.

## Per surface form
- `canonical_id` — ground-truth identity ID.
- `script` — `latn-az` | `cyrl` | `latn-translit`.
- `translit_standard` — `ICAO` | `GOST` | `ISO9` | `BGN_PCGN` | `ALA_LC` | `ad_hoc` |
  `none` (may be multiple).
- `corruption_types` — list of applied intra-script corruptions (may be empty).
- `suffix_transform` — `none` | `national` | `patronymic` | `assimilation`.
- `is_homoglyph` (bool) + `homoglyph_codepoints` (which swaps were applied).
- `name_origin_group` — for fairness slicing.
- Structured components kept separate: `given`, `patronymic`, `family`, `org_tokens`.

## Per labeled pair
- `script_pair` — `AZ-RU` | `AZ-EN` | `RU-EN` | `same`.
- `hardness` — `easy` | `hard`.
- `hard_negative_type` — `none` | `token_swap` | `generation_collision` |
  `surname_collision` | `one_edit`.
- The union of both members' provenance.
- `label` — 1 (same entity) / 0 (different), and the ground-truth ids of both members.

The canonical schema lives in `docs/dataset_schema.md`. Keep code and doc in sync.
