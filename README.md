# AzNameMatch

A reproducible, open-source benchmark for **cross-script personal- and organization-name
matching** across **Azerbaijani (Latin) ↔ Russian (Cyrillic) ↔ English/Latin
transliteration**, for the fraud / AML / sanctions-screening domain.

> **The gap.** Synthetic entity-resolution generators (FEBRL → GeCo → pseudopeople) corrupt
> names *within one script*. They do not model cross-script transliteration variance — the
> dominant divergence for post-Soviet names (`Əliyev` / `Алиев` / `Aliyev` / `Aliev`).
> AzNameMatch extends that corruption paradigm with a standard-grounded **cross-script**
> dimension plus an **adversarial homoglyph** layer, for the AZ↔RU↔EN triple.

This is a **research artifact** (dataset + matchers + eval harness + report), not a paper.
Every number below is produced by running the harness — none are hardcoded.

## Quickstart

```bash
uv sync --extra matchers --extra plots   # env (Python 3.11+) + deps; semantic tier on CPU
uv run aznamematch generate              # build the frozen v1.0 dataset (seeded)
uv run aznamematch block                 # blocking RR / PQ / PC over the surfaces
uv run aznamematch bench                 # run all matchers -> results/
uv run pytest                            # test suite
bash scripts/reproduce.sh                # all of the above, end to end
```

The first `bench` downloads the multilingual sentence-transformer weights (~CPU, no GPU).
For an offline run, set `with_semantic: false` in `configs/benchmark.yaml`.

## Reference results

From the committed run (`results/`): seed `20260618`, **1592 test pairs**, with an
**entity-disjoint** split (RegressionV1 trains on a 1046-pair split sharing no canonical
entity with the test set). Reproduce with `scripts/reproduce.sh`.

| matcher | F1 | P | R | PR-AUC | ROC-AUC |
|---------|----|----|----|--------|---------|
| **regression_v1** | **0.860** | 0.884 | 0.838 | **0.951** | **0.928** |
| phonetic (normalized) | 0.754 | 0.667 | 0.866 | 0.607 | 0.612 |
| hybrid_blend | 0.727 | 0.573 | 0.993 | 0.494 | 0.463 |
| hybrid_cascade | 0.727 | 0.573 | 0.993 | 0.488 | 0.436 |
| semantic (multilingual MiniLM cosine) | 0.720 | 0.565 | 0.990 | 0.481 | 0.422 |
| lexical (token-set) | 0.719 | 0.569 | 0.976 | 0.437 | 0.323 |
| lexical (Jaro-Winkler) | 0.716 | 0.562 | 0.987 | 0.558 | 0.406 |
| phonetic (vanilla) | 0.716 | 0.557 | 1.000 | 0.492 | 0.362 |

Full tables (threshold-sensitivity, fairness gap, cross-standard robustness, per-script-cell
F1, error-by-root-cause, expected-cost ranking, latency) and plots are in
[`results/`](results/SUMMARY.md).

**What the run shows** (the dataset is deliberately hard: 50% hard negatives, cross-script
positives):

- **RegressionV1** — the OpenSanctions-style production baseline — is strongest (ROC-AUC
  0.928), because it combines a cross-script phonetic signal with lexical features. The
  entity-disjoint split rules out memorization, so this reflects genuine generalization.
- The **AZ-RU phonetic normalization layer is the active ingredient**: normalized phonetic
  (ROC-AUC 0.612) far outperforms vanilla phonetic (ROC-AUC 0.362).
- **Lexical and vanilla-phonetic score below ROC-AUC 0.5** (0.32 / 0.36) — they rank the
  lexically-similar hard negatives (e.g. token swaps) *above* the cross-script positives they
  cannot read. This is exactly the failure mode the benchmark is built to expose.
- **Adversarial homoglyphs** (`results/homoglyph.md`) are a near-binary capability check: at
  the 0.5 operating point, normalized-phonetic / RegressionV1 recall the confusable twins
  (1.00) while vanilla phonetic collapses (0.13) — TR39 confusable folding is the deciding
  capability, and plain `unidecode` does not provide it.
- **Blocking** (`aznamematch block`): the phonetic-key blocker recovers the cross-script
  duplicates that naive raw-token / script-based blockers silently drop.

## Dataset

500 seeded synthetic identities → ~18k surface forms → **2993 labeled pairs** (1499/1494,
~50% hard negatives; exact duplicates removed) + a frozen adversarial homoglyph set. Schema
and provenance:
[`docs/dataset_schema.md`](docs/dataset_schema.md). Generation methodology and related-work
positioning: [`docs/methodology.md`](docs/methodology.md).

> ⚠️ **The cross-script cell distribution is engineered, not natural.** Pairs are stratified
> across script-pair cells (AZ-RU / AZ-EN / RU-EN / same) so each is large and label-balanced
> enough for stable per-cell metrics — these proportions are a controlled experimental design,
> **not** an estimate of real-world script-pair frequency. See `docs/methodology.md`.

## Related work / positioning

- **Corruption paradigm** — FEBRL (Christen 2008), GeCo/Gecko (Tran et al. 2013),
  pseudopeople (IHME 2024). We adopt their per-token corruption taxonomy and add the
  cross-script + adversarial dimensions.
- **Production baseline** — OpenSanctions nomenklatura **RegressionV1** (an 18-feature
  logistic regression; ≈91% F1 on OpenSanctions Pairs *per their report*, off-the-shelf LLMs
  ≈99% *per their report* — cited, not our measurements). We replicate its name-centric
  feature subset.
- **Harness alignment** — nomenklatura `name_bench` emits an accuracy view and a perf view;
  we emit both.
- **Neural EM reference** — Ditto (Li et al. 2020); not trained here. Sentence-embedding and
  optional LLM matchers are the modern comparison points.

## Standards (cited, never invented)

Transliteration: BGN/PCGN, ALA-LC, ISO 9, ICAO Doc 9303, GOST 7.79
([`docs/transliteration.md`](docs/transliteration.md)). Homoglyphs: Unicode TR39 confusables
([`docs/homoglyphs.md`](docs/homoglyphs.md)). Suffix transitions are a documented modeling
assumption ([`docs/suffix_matrix.md`](docs/suffix_matrix.md)).

## How to add a matcher

Subclass `Matcher`, implement `score(a, b) -> float` in `[0, 1]`, and register it:

```python
from aznamematch.matchers.base import Matcher, register

@register
class MyMatcher(Matcher):
    name = "my_matcher"
    def score(self, a: str, b: str) -> float:
        ...  # return a similarity in [0, 1]
```

Override `fit(pairs, labels)` if it needs training (set `requires_training = True`), or
`scores(pairs)` for an efficient batch path. Add it to `build_matchers` in
`src/aznamematch/eval/runner.py` to include it in the benchmark.

## Repo map

```
src/aznamematch/
  components/  generate/ (translit/)  matchers/  blocking/  eval/  cli.py
configs/  docs/  data/{sample,adversarial}  results/  tests/  scripts/reproduce.sh
```

See `docs/DESIGN.md` and `docs/rules/` for the project's non-negotiable principles.

## Limitations (honest)

- **Synthetic distribution ≠ real name frequency.** Components are invented; per-cell and
  script-pair proportions are engineered for evaluability, not prevalence.
- **Rule-based transliteration** is one of several valid renderings; our standard profiles
  capture the salient divergences, not every edition of every standard byte-for-byte.
- **Suffix-transition positives** (e.g. `Əliyev ↔ Əlizadə`) are a stated modeling assumption
  about geopolitical name variation, not a universal truth.
- **The homoglyph slice is a capability check**, not graded difficulty.
- **ECT cost ranking is parametric** — the cost ratio is an input; no absolute monetary costs
  are claimed.
- **The denylist guard is not exhaustive**; it reduces, not eliminates, accidental real-name
  collisions. The data is otherwise 100% synthetic with no PII.
- Results are an **upper-bound proxy** on this controlled distribution, not a production
  guarantee.

## Roadmap (v2 / v3 — not built)

**v2:** component saliency/explainability; full uncertainty quantification (Platt/isotonic
across all matchers); a frozen LLM-generated adversarial set; OpenSanctions/nomenklatura
integration as a regression plugin. **v3 (separate projects):** Turkic-family expansion
(Kazakh/Uzbek/…); a trained seq2seq transliteration model. Depth in AZ-RU-EN is the
differentiator, not breadth.

## License

MIT (code + data) — see [`LICENSE`](LICENSE). 100% synthetic; no real persons, no PII.
