# AzNameMatch — Design & Conventions

A reproducible, open-source benchmark for **cross-script personal/organization name
matching** across Azerbaijani (Latin) ↔ Russian (Cyrillic) ↔ English/Latin
transliteration, for the fraud / AML / sanctions-screening domain.

**The gap:** synthetic entity-resolution generators (FEBRL → GeCo → pseudopeople) corrupt
names *within one script*. They do not model cross-script transliteration variance — the
dominant divergence for post-Soviet names (`Əliyev` / `Алиев` / `Aliyev` / `Aliev`).
AzNameMatch extends that corruption paradigm with a standard-grounded **cross-script**
dimension plus an **adversarial homoglyph** layer, for the AZ↔RU↔EN triple.

This repo is a **research artifact** (dataset + matchers + eval harness + report), not a
paper.

## Principles (non-negotiable — see `docs/rules/`)

- **100% synthetic, fully seeded, reproducible.** No real persons, no PII. Same seed →
  identical dataset. Ground-truth `canonical_id` on every record.
- **Realistic > clean.** Inject standard-grounded cross-script variation + intra-script
  corruption + adversarial obfuscation so results mean something.
- **ZERO fabricated numbers.** Every metric is produced by running the harness. Never
  hardcode/guess/illustrate F1/precision/etc. — not in README, docstrings, or comments.
  Hypotheses are stated in words, with no numbers, to be confirmed by a run.
- **Standards-grounded.** Transliteration & homoglyph mappings come from real, cited
  standards (BGN/PCGN, ALA-LC, ISO 9, ICAO 9303, GOST 7.79, Unicode TR39) — never invented.
- **Honest reporting.** Numbers as they fall, including against our own phonetic layer.

## Current status

**Complete (Phases 0–8).** Frozen v1.0 dataset + blocking + matchers + evaluation harness +
committed reference `results/`. All numbers in `results/` come from `aznamematch bench`; the
LLM tier is built but gated off (kept out of the deterministic reference run).

## Repo map

```
src/aznamematch/
  components/      # invented, AZ-realistic name banks (*.txt)
  generate/        # canonical.py, suffix_matrix.py, noise.py, homoglyph.py, surface.py, pairs.py, pipeline.py
    translit/      # az_cyrl.py, ru_latn.py, adhoc.py
  matchers/        # base, normalize (AZ-RU layer), lexical, phonetic, semantic, regression_v1, hybrid, llm
  blocking/        # blockers.py (exact-token, q-gram, phonetic-key, naive-script; RR/PQ/PC)
  eval/            # metrics, breakdown, robustness, fairness, calibration, cost, report, runner
  cli.py           # generate | block | bench | report  (all implemented)
configs/           # generation.yaml, benchmark.yaml
docs/              # transliteration, homoglyphs, suffix_matrix, dataset_schema, methodology
data/sample/       # tiny committed CSV sample
data/adversarial/  # frozen, versioned homoglyph set
results/           # committed reference run (accuracy + perf views, plots) — written by bench
tests/             # one module per source module
```

## Dev workflow

- Env: **uv** with Python 3.11+ (`uv sync`, `uv run ...`). System python is 3.9 — always
  go through uv.
- Test: `uv run pytest`. Lint: `uv run ruff check` (must be clean before each commit).
- Generate: `uv run aznamematch generate --config configs/generation.yaml`.
- **Commit after each phase**, clear messages. Tests live alongside each module.

## Conventions

- **Seeding:** one master `seed` in `configs/generation.yaml`. Derive per-stage child seeds
  with `numpy.random.SeedSequence(seed).spawn(...)` so each stage is independently
  reproducible. Never call unseeded RNGs. See `docs/rules/seeding.md`.
- **Provenance:** every surface form and every pair carries the full metadata schema
  (`docs/dataset_schema.md`). This powers later error-decomposition, fairness, calibration,
  and the Unknown-Standard protocol — get it right at generation time.
- **Mappings cite a standard.** Each transliteration/homoglyph mapping references a named
  standard in `docs/` (`transliteration.md`, `homoglyphs.md`). See
  `docs/rules/transliteration-fidelity.md`.
- **No real persons.** Generate plausible-but-fictional combinations; a denylist guards
  against accidentally emitting a well-known real full name.
  See `docs/rules/no-real-persons.md`.

Detail lives in `docs/rules/` and `docs/` to keep this file short.
