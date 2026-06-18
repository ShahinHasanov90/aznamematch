# Adversarial homoglyph slice (capability check)

Recall on Latin-vs-Cyrillic-confusable positives at the FIXED operating threshold (0.5). Low recall = the matcher does not fold confusables (a near-binary capability check, not graded difficulty).

| matcher | homoglyph recall | n | thr |
| --- | --- | --- | --- |
| hybrid_blend | 0.9933 | 150 | 0.50 |
| hybrid_cascade | 0.8200 | 150 | 0.50 |
| lexical | 0.6933 | 150 | 0.50 |
| lexical_jaro_winkler | 1.0000 | 150 | 0.50 |
| phonetic | 1.0000 | 150 | 0.50 |
| phonetic_vanilla | 0.1267 | 150 | 0.50 |
| regression_v1 | 1.0000 | 150 | 0.50 |
| semantic | 0.9400 | 150 | 0.50 |
