# Methodology

This document covers the **generation** methodology and the **related-work positioning**.
The evaluation methodology (matchers, metrics, robustness, fairness, calibration, cost) is
deferred to a later milestone and will be added here when the harness is built — until then,
this repo contains **no measured results**.

## The gap (why this benchmark exists)

Synthetic entity-resolution data generators are a mature lineage — **FEBRL** (Christen, KDD
2008) → **GeCo / Gecko** (Tran, Vatsalan & Christen, CIKM 2013) → **pseudopeople** (IHME,
2024). They share a corruption taxonomy (character edits, OCR/phonetic lookup substitutions,
keyboard-adjacency typos, applied per-token with configurable probabilities, ground-truth
ids on every record). **None model cross-script transliteration variance** — they corrupt
*within* one script.

Yet for post-Soviet names the dominant divergence is exactly cross-script: the same person as
`Əliyev` (AZ Latin) / `Алиев` (RU Cyrillic) / `Aliyev` / `Aliev` / `Alyev` (competing Latin
transliterations), plus deliberate homoglyph obfuscation. Large 2026 multilingual benchmarks
(OpenSanctions Pairs; Symphonym phonetic embeddings) include cross-script names but provide
no AZ-specific evaluation and no controlled cross-script / adversarial noise model.

**AzNameMatch** extends the GeCo/FEBRL/pseudopeople synthetic-corruption paradigm with a
*cross-script transliteration-variance dimension* grounded in real competing standards, plus
an *adversarial obfuscation layer*, for the AZ↔RU↔EN triple.

## Generation pipeline

Deterministic, seeded (`configs/generation.yaml`); same seed → byte-identical dataset.

1. **Canonical identities** (`generate/canonical.py`) — invented, AZ-realistic persons + orgs
   with structured components, optional DOB + synthetic id, and a fairness group. Denylist
   guard against real public figures. (`docs/suffix_matrix.md`)
2. **Suffix matrix** (`generate/suffix_matrix.py`) — same root rendered across eras
   (national `-zadə/-soy/-li`, Russified `-ov/-yev`, AZ vs Russified patronymics). An explicit
   **modeling assumption**, documented as such.
3. **Cross-script transliteration** (`generate/translit/`) — AZ Latin⇄Cyrillic, Russified
   Russian-Cyrillic, RU→Latin under ICAO / GOST / BGN-PCGN / ALA-LC, and ad-hoc standardless
   spellings. Every variant tagged with its standard. (`docs/transliteration.md`)
4. **Intra-script corruption** (`generate/noise.py`) — FEBRL/GeCo per-token noise with honest
   type labels.
5. **Adversarial homoglyphs** (`generate/homoglyph.py`) — TR39 Latin→Cyrillic confusables, a
   separate frozen threat model. (`docs/homoglyphs.md`)
6. **Labeled pairs** (`generate/pairs.py`) — positives, easy negatives, and four kinds of hard
   negatives, with full provenance. (`docs/dataset_schema.md`)

## Related work to be replicated / compared (deferred phases)

- **Production baseline** — OpenSanctions nomenklatura **RegressionV1**, an 18-feature
  logistic regression over name/date/identifier/demographic similarity (≈91% F1 on
  OpenSanctions Pairs *per their report*; off-the-shelf LLMs ≈99% *per their report* — these
  are cited external numbers, not ours). We will replicate a name-centric RegressionV1.
- **Harness alignment** — nomenklatura's `name_bench` reports an accuracy mode (confusion +
  calibration) and a perf mode (μs mean/p50/p95 + slowest cases); we will emit both.
- **Neural EM reference** — Ditto (Li et al., 2020); not trained here. Sentence-embedding +
  optional LLM matchers are the modern comparison points.
- **Evaluation rigor** — EM = blocking → matching; we will report blocking (RR/PQ/PC) and
  matching (P/R/F1, PR-AUC, ROC-AUC) plus threshold sensitivity, an error-by-root-cause
  taxonomy, a cross-standard (Unknown-Standard) robustness score, fairness gaps across
  `name_origin_group`, calibration (only for probabilistic matchers), and a parametric
  expected-cost ranking (no absolute monetary costs).

## Honesty commitments

Zero fabricated numbers (`docs/rules/zero-fabricated-numbers.md`); standards cited not
invented; the suffix-transition positives are a stated modeling assumption; the homoglyph
slice is a capability check, not graded difficulty.
