# AzNameMatch

A reproducible, open-source benchmark for **cross-script personal- and organization-name
matching** across **Azerbaijani (Latin) ↔ Russian (Cyrillic) ↔ English/Latin
transliteration**, for the fraud / AML / sanctions-screening domain.

> **The gap.** Synthetic entity-resolution generators (FEBRL → GeCo → pseudopeople) corrupt
> names *within one script*. They do not model cross-script transliteration variance — the
> dominant divergence for post-Soviet names (`Əliyev` / `Алиев` / `Aliyev` / `Aliev`).
> AzNameMatch extends that corruption paradigm with a standard-grounded **cross-script**
> dimension plus an **adversarial homoglyph** layer.

## Status

🚧 **Under construction.** Milestone 1 builds the synthetic data pipeline through a frozen
v1.0 labeled-pair dataset (Phases 0–4). Matchers and the evaluation harness (Phases 5–8)
are not built yet, so **this repo contains no measured results.** Every metric in this
benchmark is produced by running the harness; none are hardcoded.

## Quickstart (generation)

```bash
uv sync                      # create the env (Python 3.11+) and install deps
uv run aznamematch generate --config configs/generation.yaml
uv run pytest                # run the test suite
```

## Principles

- 100% synthetic, fully seeded, reproducible — same seed → identical dataset; no real
  persons, no PII.
- Realistic > clean — standard-grounded cross-script variation + intra-script corruption +
  adversarial obfuscation.
- Zero fabricated numbers — all metrics come from a run.
- Standards-grounded — BGN/PCGN, ALA-LC, ISO 9, ICAO 9303, GOST 7.79, Unicode TR39 (cited
  in `docs/`).

> **⚠️ The cross-script cell distribution is engineered, not natural.** Positive and negative
> pairs are *deliberately* stratified across script-pair cells (AZ-RU / AZ-EN / RU-EN / same)
> and the Cyrillic surface pool is enlarged so the AZ↔RU cell is large, diverse, and
> label-balanced enough for stable per-cell metrics. These proportions are a controlled
> experimental design — they do **not** estimate how often each script pair occurs in real
> compliance data. Tune them in `configs/generation.yaml` (`pairs.script_pair_targets`,
> `noise.cyrillic_extra_corrupted`). See `docs/methodology.md` → "Engineered cross-script
> distribution".

See `docs/DESIGN.md` and `docs/` for design detail. License: MIT (`LICENSE`).
