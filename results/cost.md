# Expected-cost ranking (parametric)

`ECT = P(FP)·c_FP + P(FN)·c_FN`. Cost ratios are inputs; no absolute monetary costs are claimed.


## c_fn:c_fp=1:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.1514 | 0.61 |
| 2 | phonetic | 0.3153 | 0.01 |
| 3 | hybrid_blend | 0.3832 | 0.11 |
| 4 | hybrid_cascade | 0.3926 | 0.14 |
| 5 | lexical | 0.4253 | 0.06 |
| 6 | semantic | 0.4296 | 0.34 |
| 7 | lexical_jaro_winkler | 0.4359 | 0.37 |
| 8 | phonetic_vanilla | 0.4428 | 0.00 |


## c_fn:c_fp=10:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.3555 | 0.13 |
| 2 | semantic | 0.4391 | 0.22 |
| 3 | lexical | 0.4428 | 0.00 |
| 4 | lexical_jaro_winkler | 0.4428 | 0.00 |
| 5 | phonetic | 0.4428 | 0.00 |
| 6 | phonetic_vanilla | 0.4428 | 0.00 |
| 7 | hybrid_blend | 0.4428 | 0.00 |
| 8 | hybrid_cascade | 0.4428 | 0.00 |


## c_fn:c_fp=100:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.3744 | 0.02 |
| 2 | semantic | 0.4391 | 0.22 |
| 3 | lexical | 0.4428 | 0.00 |
| 4 | lexical_jaro_winkler | 0.4428 | 0.00 |
| 5 | phonetic | 0.4428 | 0.00 |
| 6 | phonetic_vanilla | 0.4428 | 0.00 |
| 7 | hybrid_blend | 0.4428 | 0.00 |
| 8 | hybrid_cascade | 0.4428 | 0.00 |
