# Error-by-root-cause

False-negative counts per category, per matcher (at each matcher's best-F1 threshold).

| matcher | script_divergence (FN) | phonetic_orthographic (FN) | lexical (FN) | hard_negative_collision (FN) | homoglyph (FN) | other (FN) | FP(hard) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hybrid_blend | 6 | 0 | 0 | 0 | 0 | 0 | 445 |
| hybrid_cascade | 6 | 0 | 0 | 0 | 0 | 0 | 445 |
| lexical | 21 | 0 | 0 | 0 | 0 | 0 | 445 |
| lexical_jaro_winkler | 11 | 0 | 1 | 0 | 0 | 0 | 445 |
| phonetic | 103 | 0 | 16 | 0 | 0 | 0 | 373 |
| phonetic_vanilla | 0 | 0 | 0 | 0 | 0 | 0 | 445 |
| regression_v1 | 92 | 3 | 49 | 0 | 0 | 0 | 34 |
| semantic | 7 | 0 | 2 | 0 | 0 | 0 | 445 |
