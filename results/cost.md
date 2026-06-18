# Expected-cost ranking (parametric)

`ECT = P(FP)·c_FP + P(FN)·c_FN`. Cost ratios are inputs; no absolute monetary costs are claimed.


## c_fn:c_fp=1:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.1383 | 0.49 |
| 2 | phonetic | 0.2900 | 0.01 |
| 3 | hybrid_blend | 0.3889 | 0.12 |
| 4 | hybrid_cascade | 0.4117 | 0.14 |
| 5 | lexical_jaro_winkler | 0.4594 | 0.92 |
| 6 | lexical | 0.4706 | 0.06 |
| 7 | semantic | 0.4767 | 0.60 |
| 8 | phonetic_vanilla | 0.5094 | 0.00 |


## c_fn:c_fp=10:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.4439 | 0.03 |
| 2 | semantic | 0.5050 | 0.21 |
| 3 | lexical | 0.5094 | 0.00 |
| 4 | lexical_jaro_winkler | 0.5094 | 0.00 |
| 5 | phonetic | 0.5094 | 0.00 |
| 6 | phonetic_vanilla | 0.5094 | 0.00 |
| 7 | hybrid_blend | 0.5094 | 0.00 |
| 8 | hybrid_cascade | 0.5094 | 0.00 |


## c_fn:c_fp=100:1

| rank | matcher | ECT | thr |
| --- | --- | --- | --- |
| 1 | regression_v1 | 0.4439 | 0.03 |
| 2 | semantic | 0.5050 | 0.21 |
| 3 | lexical | 0.5094 | 0.00 |
| 4 | lexical_jaro_winkler | 0.5094 | 0.00 |
| 5 | phonetic | 0.5094 | 0.00 |
| 6 | phonetic_vanilla | 0.5094 | 0.00 |
| 7 | hybrid_blend | 0.5094 | 0.00 |
| 8 | hybrid_cascade | 0.5094 | 0.00 |
