# Error-by-root-cause

False-negative counts per category, per matcher (at each matcher's best-F1 threshold).

| matcher | script_divergence (FN) | phonetic_orthographic (FN) | lexical (FN) | hard_negative_collision (FN) | homoglyph (FN) | other (FN) | FP(hard) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid_blend | 101 | 0 | 3 | 0 | 0 | 0 | 452 |
| hybrid_cascade | 92 | 0 | 0 | 0 | 0 | 0 | 452 |
| lexical | 26 | 0 | 0 | 0 | 0 | 0 | 452 |
| lexical_jaro_winkler | 14 | 0 | 2 | 0 | 0 | 0 | 452 |
| phonetic | 113 | 0 | 20 | 0 | 0 | 0 | 370 |
| phonetic_vanilla | 0 | 0 | 0 | 0 | 0 | 0 | 452 |
| regression_v1 | 86 | 1 | 38 | 0 | 0 | 0 | 34 |
| semantic | 5 | 0 | 0 | 0 | 0 | 0 | 452 |
