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

### Engineered cross-script distribution (NOT a natural frequency)

The script-pair cell sizes (AZ-RU / AZ-EN / RU-EN / same) are **deliberately engineered**, by
design, so that each cell — the AZ↔RU cell in particular — is large enough to compute stable
per-cell metrics and to be compared against the others. Two mechanisms:

- **Cyrillic-surface emphasis** (`noise.cyrillic_extra_corrupted`): extra corrupted twins are
  generated for each clean Cyrillic surface. Cyrillic forms are otherwise outnumbered ~4:1 by
  Latin romanizations (one AZ-Cyrillic + one Russian-Cyrillic surface per rendering vs ~9 Latin
  ones), which would starve the AZ-RU cell. The emphasis raises the Cyrillic pool so AZ-RU
  pairs can be drawn with *diversity* rather than reusing one Cyrillic form.
- **Stratified sampling** (`pairs.script_pair_targets`): both positives and easy negatives are
  allocated across cells to configured target proportions (default AZ-RU 0.30 / RU-EN 0.30 /
  AZ-EN 0.22 / same 0.18), and the cells are kept label-balanced so each is individually
  evaluable.

**This means the cell proportions in this dataset do NOT estimate how often each script pair
co-occurs in real compliance data.** They are a controlled experimental design. Any per-cell
result must be read as "performance *on this engineered cell*", and absolute cell sizes carry
no real-world prevalence information. (Hard negatives are synthesized in AZ-Latin and so fall
in the `same` script cell; they are sliced by `hard_negative_type`, a separate axis.)

## Related work to be replicated / compared (deferred phases)

- **Production baseline** — OpenSanctions nomenklatura **RegressionV1**, an 18-feature
  logistic regression over name/date/identifier/demographic similarity (≈91% F1 on
  OpenSanctions Pairs *per their report*; off-the-shelf LLMs ≈99% *per their report* — these
  are cited external numbers, not ours). We will replicate a name-centric RegressionV1.
- **Harness alignment** — nomenklatura's `name_bench` reports an accuracy mode (confusion +
  calibration) and a perf mode (μs mean/p50/p95 + slowest cases); we will emit both.
- **Neural EM reference** — Ditto (Li et al., 2020); not trained here. Sentence-embedding +
  optional LLM matchers are the modern comparison points.
### Evaluation split (entity-disjoint)

The benchmark uses an **entity-disjoint** train/test split (`eval/runner.py`): canonical
entities — not pair rows — are partitioned, so no test entity's surfaces are ever seen while
training RegressionV1. Positives (whose two members share one `canonical_id`) stay whole;
easy negatives whose two entities land on opposite sides are dropped; synthetic hard negatives
(unique ids per pair) are coin-assigned. Exact-duplicate surface pairs are removed at
generation time so an identical labeled pair cannot straddle the split. This is the
textbook-correct ER protocol and prevents entity memorization from inflating results.

- **Evaluation rigor** — EM = blocking → matching; we will report blocking (RR/PQ/PC) and
  matching (P/R/F1, PR-AUC, ROC-AUC) plus threshold sensitivity, an error-by-root-cause
  taxonomy, a cross-standard (Unknown-Standard) robustness score, fairness gaps across
  `name_origin_group`, calibration (only for probabilistic matchers), and a parametric
  expected-cost ranking (no absolute monetary costs).

## Honesty commitments

Zero fabricated numbers (`docs/rules/zero-fabricated-numbers.md`); standards cited not
invented; the suffix-transition positives are a stated modeling assumption; the homoglyph
slice is a capability check, not graded difficulty.
