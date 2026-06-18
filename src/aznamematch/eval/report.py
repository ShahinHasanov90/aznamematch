"""Write the benchmark results to ``results/``: JSON, markdown tables, and plots.

Two views (nomenklatura ``name_bench`` style): an ACCURACY view (F1/P/R/AUCs/sensitivity/
fairness gap/robustness + per-script + per-root-cause + cost ranking) and a PERF view
(μs mean/p50/p95 + slowest). Every value is passed through from a real run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import precision_recall_curve  # noqa: E402


def _f(x: Any, nd: int = 4) -> str:
    try:
        return "nan" if x != x else f"{float(x):.{nd}f}"  # x!=x detects NaN
    except (TypeError, ValueError):
        return str(x)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return f"{line}\n{sep}\n{body}\n"


def write_results(results: dict[str, Any], out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    score_cache = results.pop("score_cache", {})

    _write_json(results, out)
    _write_accuracy(results, out)
    _write_perf(results, out)
    _write_breakdown(results, out)
    _write_cost(results, out)
    _write_robustness_fairness(results, out)
    _write_homoglyph(results, out)
    _plot_pr_curves(score_cache, out)
    _plot_rootcause(results, out)
    _plot_per_script(results, out)
    _write_summary(results, out)


def _write_json(results: dict, out: Path) -> None:
    (out / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True),
                                      encoding="utf-8")


def _write_accuracy(results: dict, out: Path) -> None:
    headers = ["matcher", "F1", "P", "R", "best-F1", "thr", "PR-AUC", "ROC-AUC",
               "thr-sens", "fairness-gap", "x-std-robust"]
    rows = []
    for name, a in sorted(results["accuracy"].items()):
        rob = results["robustness"].get(name, {}).get("cross_standard", {}).get("robustness")
        gap = results["fairness"].get(name, {}).get("max_f1_gap")
        rows.append([name, _f(a["best_f1"]), _f(a["best_f1_precision"]),
                     _f(a["best_f1_recall"]), _f(a["best_f1"]), _f(a["best_f1_threshold"], 2),
                     _f(a["pr_auc"]), _f(a["roc_auc"]), _f(a["threshold_sensitivity"]),
                     _f(gap), _f(rob)])
    (out / "accuracy.md").write_text(
        "# Accuracy view\n\nBest-F1 operating point per matcher (computed from the run).\n\n"
        + _table(headers, rows), encoding="utf-8")


def _write_perf(results: dict, out: Path) -> None:
    headers = ["matcher", "mean μs", "p50 μs", "p95 μs", "max μs"]
    rows = [[name, _f(p["mean_us"], 1), _f(p["p50_us"], 1), _f(p["p95_us"], 1),
             _f(p["max_us"], 1)] for name, p in sorted(results["perf"].items())]
    (out / "perf.md").write_text("# Performance view\n\nPer-pair latency (sampled).\n\n"
                                 + _table(headers, rows), encoding="utf-8")


def _write_breakdown(results: dict, out: Path) -> None:
    parts = ["# Error-by-root-cause\n\nFalse-negative counts per category, per matcher "
             "(at each matcher's best-F1 threshold).\n"]
    cats = ["script_divergence", "phonetic_orthographic", "lexical",
            "hard_negative_collision", "homoglyph", "other"]
    headers = ["matcher", *[c + " (FN)" for c in cats], "FP(hard)"]
    rows = []
    for name, b in sorted(results["breakdown"].items()):
        bc = b["by_category"]
        fn_cells = [str(bc[c]["fn"]) for c in cats]
        rows.append([name, *fn_cells, str(bc["hard_negative_collision"]["fp"])])
    parts.append(_table(headers, rows))
    (out / "breakdown.md").write_text("\n".join(parts), encoding="utf-8")


def _write_cost(results: dict, out: Path) -> None:
    parts = ["# Expected-cost ranking (parametric)\n\n`ECT = P(FP)·c_FP + P(FN)·c_FN`. "
             "Cost ratios are inputs; no absolute monetary costs are claimed.\n"]
    for ratio, rows in results["cost"].items():
        parts.append(f"\n## {ratio}\n")
        parts.append(_table(["rank", "matcher", "ECT", "thr"],
                            [[str(r["rank"]), r["matcher"], _f(r["ect"]),
                              _f(r["threshold"], 2)] for r in rows]))
    (out / "cost.md").write_text("\n".join(parts), encoding="utf-8")


def _write_robustness_fairness(results: dict, out: Path) -> None:
    parts = ["# Robustness & fairness\n\n## Cross-standard robustness (Unknown-Standard)\n",
             "F1 retained when tuned on named standards and evaluated on ad-hoc "
             "(1.0 = no loss).\n"]
    rrows = []
    for name, r in sorted(results["robustness"].items()):
        cs = r["cross_standard"]
        rrows.append([name, _f(cs.get("f1_named")), _f(cs.get("f1_adhoc")),
                      _f(cs.get("robustness"))])
    parts.append(_table(["matcher", "F1 (named)", "F1 (ad-hoc)", "robustness"], rrows))

    parts.append("\n## Fairness — F1 by name-origin group\n")
    groups = ["russified", "national_zade", "national_soy", "national_li", "organization"]
    frows = []
    for name, fr in sorted(results["fairness"].items()):
        bg = fr["by_group"]
        cells = [_f(bg[g]["f1"]) if g in bg else "-" for g in groups]
        frows.append([name, *cells, _f(fr["max_f1_gap"])])
    parts.append(_table(["matcher", *groups, "max gap"], frows))
    (out / "robustness_fairness.md").write_text("\n".join(parts), encoding="utf-8")


def _write_homoglyph(results: dict, out: Path) -> None:
    if not results.get("homoglyph"):
        return
    headers = ["matcher", "homoglyph recall", "n", "thr"]
    rows = [[name, _f(h["recall"]), str(h["n"]), _f(h["threshold"], 2)]
            for name, h in sorted(results["homoglyph"].items())]
    (out / "homoglyph.md").write_text(
        "# Adversarial homoglyph slice (capability check)\n\nRecall on Latin-vs-Cyrillic-"
        "confusable positives at the FIXED operating threshold (0.5). Low recall = the matcher "
        "does not fold confusables (a near-binary capability check, not graded difficulty).\n\n"
        + _table(headers, rows), encoding="utf-8")


def _plot_pr_curves(score_cache: dict, out: Path) -> None:
    if not score_cache:
        return
    plt.figure(figsize=(7, 5))
    for name, (labels, scores) in sorted(score_cache.items()):
        if len(np.unique(labels)) < 2:
            continue
        prec, rec, _ = precision_recall_curve(labels, scores)
        plt.plot(rec, prec, label=name, linewidth=1.3)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall curves")
    plt.legend(fontsize=7, loc="lower left")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out / "pr_curves.png", dpi=120)
    plt.close()


def _plot_rootcause(results: dict, out: Path) -> None:
    cats = ["script_divergence", "phonetic_orthographic", "lexical",
            "hard_negative_collision", "homoglyph"]
    names = sorted(results["breakdown"])
    if not names:
        return
    data = np.array([[results["breakdown"][n]["by_category"][c]["fn"] for c in cats]
                     for n in names], dtype=float)
    x = np.arange(len(cats))
    w = 0.8 / max(1, len(names))
    plt.figure(figsize=(9, 5))
    for i, n in enumerate(names):
        plt.bar(x + i * w, data[i], width=w, label=n)
    plt.xticks(x + 0.4, cats, rotation=20, ha="right", fontsize=8)
    plt.ylabel("False negatives")
    plt.title("Errors by root cause (FN)")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(out / "error_by_rootcause.png", dpi=120)
    plt.close()


def _plot_per_script(results: dict, out: Path) -> None:
    cells = ["AZ-RU", "AZ-EN", "RU-EN", "same"]
    names = sorted(results["accuracy"])
    rows = [[results["accuracy"][n].get("by_script", {}).get(c, {}).get("f1", np.nan)
             for c in cells] for n in names]
    data = np.array(rows, dtype=float)
    if data.size == 0:
        return
    x = np.arange(len(cells))
    w = 0.8 / max(1, len(names))
    plt.figure(figsize=(9, 5))
    for i, n in enumerate(names):
        plt.bar(x + i * w, np.nan_to_num(data[i]), width=w, label=n)
    plt.xticks(x + 0.4, cells)
    plt.ylabel("F1 (best threshold)")
    plt.title("F1 by script-pair cell")
    plt.legend(fontsize=7)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(out / "per_script_f1.png", dpi=120)
    plt.close()


def _write_summary(results: dict, out: Path) -> None:
    cfg = results["config"]
    lines = [
        "# AzNameMatch — reference results",
        "",
        f"Test pairs: {cfg['test_n']} | RegressionV1 train pairs: {cfg['train_n']} | "
        f"seed: {cfg['seed']} | semantic: {cfg['with_semantic']}",
        "",
        "All numbers are produced by `aznamematch bench`; none are hardcoded. See the per-"
        "view files: [accuracy](accuracy.md), [perf](perf.md), [breakdown](breakdown.md), "
        "[cost](cost.md), [robustness & fairness](robustness_fairness.md), "
        "[homoglyph](homoglyph.md). Plots: `pr_curves.png`, `error_by_rootcause.png`, "
        "`per_script_f1.png`.",
        "",
        "## Accuracy (best-F1 per matcher)",
        "",
    ]
    headers = ["matcher", "F1", "P", "R", "PR-AUC", "ROC-AUC"]
    rows = [[n, _f(a["best_f1"]), _f(a["best_f1_precision"]), _f(a["best_f1_recall"]),
             _f(a["pr_auc"]), _f(a["roc_auc"])] for n, a in sorted(results["accuracy"].items())]
    lines.append(_table(headers, rows))
    (out / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
