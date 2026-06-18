# AzNameMatch — reference results

Test pairs: 1592 | RegressionV1 train pairs: 1046 | seed: 20260618 | semantic: True

All numbers are produced by `aznamematch bench`; none are hardcoded. See the per-view files: [accuracy](accuracy.md), [perf](perf.md), [breakdown](breakdown.md), [cost](cost.md), [robustness & fairness](robustness_fairness.md), [homoglyph](homoglyph.md). Plots: `pr_curves.png`, `error_by_rootcause.png`, `per_script_f1.png`.

## Accuracy (best-F1 per matcher)

| matcher | F1 | P | R | PR-AUC | ROC-AUC |
| --- | --- | --- | --- | --- | --- |
| hybrid_blend | 0.7266 | 0.5728 | 0.9932 | 0.4941 | 0.4634 |
| hybrid_cascade | 0.7266 | 0.5728 | 0.9932 | 0.4879 | 0.4362 |
| lexical | 0.7190 | 0.5690 | 0.9763 | 0.4370 | 0.3225 |
| lexical_jaro_winkler | 0.7160 | 0.5620 | 0.9865 | 0.5584 | 0.4064 |
| phonetic | 0.7537 | 0.6672 | 0.8658 | 0.6069 | 0.6122 |
| phonetic_vanilla | 0.7156 | 0.5572 | 1.0000 | 0.4920 | 0.3619 |
| regression_v1 | 0.8600 | 0.8835 | 0.8377 | 0.9511 | 0.9276 |
| semantic | 0.7197 | 0.5654 | 0.9899 | 0.4805 | 0.4215 |
