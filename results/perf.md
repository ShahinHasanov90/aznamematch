# Performance view

Per-pair latency (sampled).

| matcher | mean μs | p50 μs | p95 μs | max μs |
| --- | --- | --- | --- | --- |
| hybrid_blend | 24.6 | 24.7 | 34.2 | 59.2 |
| hybrid_cascade | 14.5 | 16.0 | 32.9 | 122.2 |
| lexical | 1.3 | 1.3 | 1.7 | 6.8 |
| lexical_jaro_winkler | 0.3 | 0.3 | 0.5 | 4.4 |
| phonetic | 22.7 | 22.4 | 32.2 | 90.1 |
| phonetic_vanilla | 2.7 | 2.7 | 3.5 | 11.9 |
| regression_v1 | 184.7 | 174.4 | 233.9 | 1214.5 |
| semantic | 16318.1 | 13757.8 | 35804.7 | 140854.7 |
