# Robustness & fairness

## Cross-standard robustness (Unknown-Standard)

F1 retained when tuned on named standards and evaluated on ad-hoc (1.0 = no loss).

| matcher | F1 (named) | F1 (ad-hoc) | robustness |
| --- | --- | --- | --- |
| hybrid_blend | 0.9079 | 0.8791 | 0.9682 |
| hybrid_cascade | 0.8966 | 0.8800 | 0.9815 |
| lexical | 0.8876 | 0.8623 | 0.9715 |
| lexical_jaro_winkler | 0.8845 | 0.8520 | 0.9634 |
| phonetic | 0.9257 | 0.9177 | 0.9914 |
| phonetic_vanilla | 0.8811 | 0.8463 | 0.9605 |
| regression_v1 | 0.9106 | 0.8411 | 0.9236 |
| semantic | 0.8937 | 0.8564 | 0.9583 |


## Fairness — F1 by name-origin group

| matcher | russified | national_zade | national_soy | national_li | organization | max gap |
| --- | --- | --- | --- | --- | --- | --- |
| hybrid_blend | 0.8333 | 0.8156 | 0.8675 | 0.8148 | 0.7889 | 0.0786 |
| hybrid_cascade | 0.8333 | 0.8156 | 0.8675 | 0.8148 | 0.7889 | 0.0786 |
| lexical | 0.8281 | 0.7968 | 0.8675 | 0.8148 | 0.7740 | 0.0935 |
| lexical_jaro_winkler | 0.8144 | 0.8031 | 0.8405 | 0.7920 | 0.7645 | 0.0759 |
| phonetic | 0.9155 | 0.9010 | 0.8788 | 0.9247 | 0.9753 | 0.0965 |
| phonetic_vanilla | 0.8129 | 0.7833 | 0.8244 | 0.7765 | 0.7709 | 0.0535 |
| regression_v1 | 0.8594 | 0.8333 | 0.9167 | 0.8750 | 0.8134 | 0.1032 |
| semantic | 0.8269 | 0.7841 | 0.8372 | 0.7984 | 0.8094 | 0.0531 |
