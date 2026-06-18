"""Benchmark runner: load pairs -> split -> train -> score -> evaluate -> assemble results.

Produces a single results dict consumed by ``report.write_results``. Every number here is
computed from a real matcher run on the frozen dataset; nothing is hardcoded.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from aznamematch.config import REPO_ROOT, get, load_config
from aznamematch.eval import breakdown, calibration, cost, fairness, metrics, robustness
from aznamematch.matchers.hybrid import HybridMatcher
from aznamematch.matchers.lexical import LexicalMatcher
from aznamematch.matchers.phonetic import PhoneticMatcher
from aznamematch.matchers.regression_v1 import RegressionV1Matcher


def build_matchers(with_semantic: bool, with_llm: bool):
    matchers = [
        LexicalMatcher("token_set"),
        LexicalMatcher("jaro_winkler"),
        PhoneticMatcher("metaphone", normalize=True),
        PhoneticMatcher("metaphone", normalize=False),
        RegressionV1Matcher(),
        HybridMatcher(mode="blend"),
        HybridMatcher(mode="cascade"),
    ]
    if with_semantic:
        from aznamematch.matchers.semantic import SemanticMatcher
        matchers.append(SemanticMatcher())
    if with_llm:
        from aznamematch.matchers.llm import LLMMatcher
        if LLMMatcher.available():
            matchers.append(LLMMatcher())
        else:
            print("  [llm] skipped: LLM_API_KEY / llm SDK not available.")
    return matchers


def _perf(matcher, pairs: list[tuple[str, str]], sample: int) -> dict[str, float]:
    """Per-pair latency view (μs mean/p50/p95 + slowest) measured on a sample."""
    times_us: list[float] = []
    for a, b in pairs[:sample]:
        t0 = perf_counter()
        matcher.score(a, b)
        times_us.append((perf_counter() - t0) * 1e6)
    arr = np.array(times_us) if times_us else np.array([0.0])
    return {
        "mean_us": float(np.mean(arr)),
        "p50_us": float(np.percentile(arr, 50)),
        "p95_us": float(np.percentile(arr, 95)),
        "max_us": float(np.max(arr)),
    }


def run_benchmark(config_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path or str(REPO_ROOT / "configs" / "benchmark.yaml"))
    seed = int(get(cfg, "seed"))
    chosen = float(get(cfg, "chosen_threshold", 0.5))
    perf_sample = int(get(cfg, "perf_sample", 300))
    prob_names = set(get(cfg, "probabilistic", []))

    pairs_path = REPO_ROOT / get(cfg, "paths.pairs")
    df = pd.read_parquet(pairs_path).reset_index(drop=True)

    # Entity-disjoint, deterministic train/test split: partition canonical ENTITIES (not pair
    # rows) so no test entity's surfaces are ever seen during RegressionV1 training. Positives
    # have id1==id2 (one entity) so they stay whole; easy negatives whose two entities land on
    # opposite sides are dropped; synthetic hard negatives (unique ids per pair) get a coin.
    test_frac = float(get(cfg, "split.test_fraction", 0.6))
    ent_rng = np.random.default_rng(seed)
    canonical_entity_ids = sorted(
        {i for i in pd.concat([df["id1"], df["id2"]]) if str(i).startswith("E")})
    is_test_entity = {eid: bool(ent_rng.random() < test_frac) for eid in canonical_entity_ids}
    hn_rng = np.random.default_rng(seed + 1)

    split: list[str] = []
    for a, b in zip(df["id1"], df["id2"], strict=True):
        if str(a).startswith("E") and str(b).startswith("E"):
            ta, tb = is_test_entity[a], is_test_entity[b]
            split.append(("test" if ta else "train") if ta == tb else "drop")
        else:  # synthetic hard negative
            split.append("test" if hn_rng.random() < test_frac else "train")
    df = df.assign(_split=split)
    test_df = df[df["_split"] == "test"].drop(columns="_split").reset_index(drop=True)
    train_df = df[df["_split"] == "train"].drop(columns="_split").reset_index(drop=True)

    test_pairs = list(zip(test_df["surface1"], test_df["surface2"], strict=True))
    labels = test_df["label"].to_numpy()
    train_pairs = list(zip(train_df["surface1"], train_df["surface2"], strict=True))
    train_labels = list(train_df["label"])

    matchers = build_matchers(bool(get(cfg, "with_semantic", True)),
                              bool(get(cfg, "with_llm", False)))

    # Optional homoglyph adversarial set (all positives: clean vs attacked).
    hg_path = REPO_ROOT / get(cfg, "paths.homoglyphs")
    hg_df = pd.read_parquet(hg_path) if hg_path.exists() else None
    hg_pairs = (list(zip(hg_df["clean"], hg_df["attacked"], strict=True))
                if hg_df is not None else [])

    accuracy: dict[str, dict] = {}
    perf: dict[str, dict] = {}
    breakdowns: dict[str, dict] = {}
    fairness_res: dict[str, dict] = {}
    calibration_res: dict[str, dict] = {}
    robustness_res: dict[str, dict] = {}
    homoglyph_res: dict[str, dict] = {}
    score_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for m in matchers:
        name = m.name
        print(f"  matcher: {name}")
        if m.requires_training:
            m.fit(train_pairs, train_labels)
        scores = np.asarray(m.scores(test_pairs), dtype=float)
        score_cache[name] = (labels, scores)

        summary = metrics.summarize(labels, scores, chosen_threshold=chosen)
        thr = summary["best_f1_threshold"]
        by_script: dict[str, dict] = {}
        for cell in ("AZ-RU", "AZ-EN", "RU-EN", "same"):
            mask = (test_df["script_pair"] == cell).to_numpy()
            if mask.sum() == 0 or np.sum(labels[mask] == 1) < 20:
                continue
            by_script[cell] = metrics.prf1_at(labels[mask], scores[mask], thr)
        summary["by_script"] = by_script
        accuracy[name] = summary
        breakdowns[name] = breakdown.breakdown(test_df, scores, thr)
        fairness_res[name] = fairness.fairness(test_df, scores, thr)
        robustness_res[name] = {
            "cross_standard": robustness.cross_standard_score(test_df, scores),
            "per_standard_recall": robustness.per_standard_recall(test_df, scores, thr),
        }
        if name in prob_names:
            calibration_res[name] = calibration.calibration(test_df, scores)
        perf[name] = _perf(m, test_pairs, perf_sample)

        if hg_pairs:
            # Capability check at the FIXED operating threshold (not the degenerate best-F1
            # threshold, which is near-zero for weak matchers and would mask the failure).
            hg_scores = np.asarray(m.scores(hg_pairs), dtype=float)
            recall = float(np.mean(hg_scores >= chosen))
            homoglyph_res[name] = {"n": len(hg_pairs), "threshold": float(chosen),
                                   "recall": recall}

    cost_ranking = cost.rank_matchers(
        score_cache, [(float(a), float(b)) for a, b in get(cfg, "cost_ratios", [[1, 1]])])

    return {
        "config": {"seed": seed, "chosen_threshold": chosen,
                   "test_n": int(len(test_df)), "train_n": int(len(train_df)),
                   "with_semantic": bool(get(cfg, "with_semantic", True))},
        "accuracy": accuracy,
        "perf": perf,
        "breakdown": breakdowns,
        "fairness": fairness_res,
        "calibration": calibration_res,
        "robustness": robustness_res,
        "homoglyph": homoglyph_res,
        "cost": cost_ranking,
        "score_cache": score_cache,  # used for PR-curve plots; not serialized to JSON
    }
