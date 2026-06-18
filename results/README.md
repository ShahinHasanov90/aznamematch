# results/

The committed reference run, written by `aznamematch bench` (Phase 7). Every number here is
produced by running the harness on the frozen v1.0 dataset — none are hardcoded (see the
project's zero-fabricated-numbers rule).

- [`SUMMARY.md`](SUMMARY.md) — top-level accuracy table + pointers.
- `accuracy.md` — best-F1 P/R/F1, PR-AUC, ROC-AUC, threshold-sensitivity, fairness gap,
  cross-standard robustness, per matcher.
- `perf.md` — per-pair latency (μs mean/p50/p95/max).
- `breakdown.md` — errors by root cause (FN per category, hard-negative FP).
- `cost.md` — parametric expected-cost ranking per cost ratio.
- `robustness_fairness.md` — Unknown-Standard robustness + per-group F1.
- `homoglyph.md` — adversarial confusable-folding capability check.
- `results.json` — the full machine-readable results.
- `pr_curves.png`, `error_by_rootcause.png`, `per_script_f1.png` — plots.

Regenerate with `bash scripts/reproduce.sh` (or `uv run aznamematch bench`). The LLM tier is
gated off in the reference run for determinism.
