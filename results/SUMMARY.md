# AzNameMatch — reference results

Test pairs: 1800 | RegressionV1 train pairs: 1200 | seed: 20260618 | semantic: True

All numbers are produced by `aznamematch bench`; none are hardcoded. See the per-view files: [accuracy](accuracy.md), [perf](perf.md), [breakdown](breakdown.md), [cost](cost.md), [robustness & fairness](robustness_fairness.md), [homoglyph](homoglyph.md). Plots: `pr_curves.png`, `error_by_rootcause.png`, `per_script_f1.png`.

## Accuracy (best-F1 per matcher)

| matcher | F1 | P | R | PR-AUC | ROC-AUC |
| --- | --- | --- | --- | --- | --- |
| hybrid_blend | 0.6900 | 0.5665 | 0.8822 | 0.4734 | 0.5450 |
| hybrid_cascade | 0.6810 | 0.5493 | 0.8958 | 0.4687 | 0.5201 |
| lexical | 0.6693 | 0.5107 | 0.9706 | 0.3987 | 0.3765 |
| lexical_jaro_winkler | 0.6639 | 0.5014 | 0.9819 | 0.5101 | 0.4401 |
| phonetic | 0.7418 | 0.6585 | 0.8494 | 0.5834 | 0.6706 |
| phonetic_vanilla | 0.6582 | 0.4906 | 1.0000 | 0.4428 | 0.4175 |
| regression_v1 | 0.8570 | 0.8555 | 0.8584 | 0.9383 | 0.9231 |
| semantic | 0.6634 | 0.4977 | 0.9943 | 0.4411 | 0.4735 |
