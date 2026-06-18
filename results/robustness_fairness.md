# Robustness & fairness

## Cross-standard robustness (Unknown-Standard)

F1 retained when tuned on named standards and evaluated on ad-hoc (1.0 = no loss).

| matcher | F1 (named) | F1 (ad-hoc) | robustness |
| --- | --- | --- | --- |
| hybrid_blend | 0.8591 | 0.8458 | 0.9846 |
| hybrid_cascade | 0.8356 | 0.8509 | 1.0183 |
| lexical | 0.8135 | 0.8167 | 1.0039 |
| lexical_jaro_winkler | 0.8041 | 0.8089 | 1.0060 |
| phonetic | 0.9118 | 0.9186 | 1.0075 |
| phonetic_vanilla | 0.7946 | 0.7952 | 1.0008 |
| regression_v1 | 0.8857 | 0.8714 | 0.9839 |
| semantic | 0.8080 | 0.8124 | 1.0055 |


## Fairness — F1 by name-origin group

| matcher | russified | national_zade | national_soy | national_li | organization | max gap |
| --- | --- | --- | --- | --- | --- | --- |
| hybrid_blend | 0.8344 | 0.8010 | 0.7869 | 0.7488 | 0.8864 | 0.1376 |
| hybrid_cascade | 0.8068 | 0.7715 | 0.7615 | 0.7200 | 0.8299 | 0.1099 |
| lexical | 0.7487 | 0.6876 | 0.7672 | 0.6544 | 0.6959 | 0.1128 |
| lexical_jaro_winkler | 0.7310 | 0.6815 | 0.7476 | 0.6312 | 0.6875 | 0.1164 |
| phonetic | 0.8984 | 0.8882 | 0.8796 | 0.8929 | 0.9675 | 0.0879 |
| phonetic_vanilla | 0.7137 | 0.6729 | 0.7178 | 0.6138 | 0.6721 | 0.1040 |
| regression_v1 | 0.8478 | 0.8403 | 0.8843 | 0.7594 | 0.8458 | 0.1249 |
| semantic | 0.7262 | 0.6742 | 0.7200 | 0.6335 | 0.7143 | 0.0928 |
