"""Phase 4 (part 3): end-to-end generation pipeline + dataset writers.

``run_generation`` is the single entry point behind ``aznamematch generate``. It runs
canonical -> surfaces -> pairs, builds the frozen adversarial homoglyph set, and writes:

- ``data/full/`` — full pairs + surfaces parquet (regenerable from the seed; git-ignored).
- ``data/sample/`` — tiny committed CSV samples (identities, surfaces, pairs).
- ``data/adversarial/homoglyph_v1/`` — the frozen, versioned homoglyph attack set (committed).

All printed numbers describe the dataset (counts, label balance) — never a measured metric.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from aznamematch.config import REPO_ROOT, get, load_config
from aznamematch.generate import pairs as pairs_mod
from aznamematch.generate.canonical import generate_identities
from aznamematch.generate.homoglyph import attack
from aznamematch.generate.surface import SurfaceForm, build_surfaces
from aznamematch.generate.translit import az_cyrl
from aznamematch.generate.translit.base import BGN_PCGN
from aznamematch.seeds import record_rng, stage_seeds


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def _build_homoglyphs(identities, cfg: dict[str, Any], seeds) -> pd.DataFrame:
    """Frozen adversarial homoglyph set: (clean, attacked) twins for a subset of identities."""
    from aznamematch.generate.homoglyph import confusable_fold

    n = int(get(cfg, "homoglyph.n_identities", 150))
    p_swap = float(get(cfg, "homoglyph.p_char_swap", 0.6))
    p_strip = float(get(cfg, "homoglyph.p_diacritic_strip", 0.5))
    seq = seeds.seq("homoglyph")

    rows: list[dict[str, Any]] = []
    for i, ident in enumerate(identities[:n]):
        # Attack an ASCII-Latin transliteration (where Cyrillic confusables apply).
        base = az_cyrl.romanize(ident.canonical, BGN_PCGN) if ident.entity_type == "person" \
            else ident.canonical
        atk = attack(base, record_rng(seq, i), p_char_swap=p_swap, p_diacritic_strip=p_strip)
        if not atk.is_attack:
            continue
        rows.append({
            "canonical_id": ident.canonical_id,
            "clean": atk.clean,
            "attacked": atk.attacked,
            "label": 1,  # same entity (adversarial positive)
            "is_homoglyph": True,
            "swapped_codepoints": ";".join(atk.swapped_codepoints),
            "diacritics_stripped": atk.diacritics_stripped,
            # Demonstrates the capability check: shape-fold matches, raw strings do not.
            "fold_clean": confusable_fold(atk.clean),
            "fold_attacked": confusable_fold(atk.attacked),
        })
    return pd.DataFrame(rows)


def run_generation(config_path: str | None = None) -> dict[str, Any]:
    """Generate the full dataset and write all artifacts. Returns a summary dict."""
    cfg = load_config(config_path)
    seeds = stage_seeds(int(cfg["seed"]))

    identities = generate_identities(cfg, seeds)

    surfaces: list[SurfaceForm] = []
    by_id: dict[str, list[SurfaceForm]] = {}
    surf_seq = seeds.seq("surface")
    for i, ident in enumerate(identities):
        sfs = build_surfaces(ident, cfg, record_rng(surf_seq, i))
        by_id[ident.canonical_id] = sfs
        surfaces.extend(sfs)

    pairs = pairs_mod.build_pairs(identities, by_id, cfg, seeds)
    homoglyphs = _build_homoglyphs(identities, cfg, seeds)

    # --- frames ---
    ident_df = pd.DataFrame([i.to_row() for i in identities])
    surf_df = pd.DataFrame([s.to_row() for s in surfaces])
    pair_df = pd.DataFrame([p.to_row() for p in pairs])

    # --- write ---
    full_dir = _resolve(get(cfg, "output.full_dir", "data/full"))
    sample_dir = _resolve(get(cfg, "output.sample_dir", "data/sample"))
    adv_dir = _resolve(get(cfg, "output.adversarial_dir", "data/adversarial")) / "homoglyph_v1"
    for d in (full_dir, sample_dir, adv_dir):
        d.mkdir(parents=True, exist_ok=True)

    sample_rows = int(get(cfg, "output.sample_rows", 50))
    surf_df.to_parquet(full_dir / "surfaces.parquet", index=False)
    pair_df.to_parquet(full_dir / "pairs.parquet", index=False)

    ident_df.head(sample_rows).to_csv(sample_dir / "identities_sample.csv", index=False)
    surf_df.head(sample_rows).to_csv(sample_dir / "surfaces_sample.csv", index=False)
    pair_df.head(sample_rows).to_csv(sample_dir / "pairs_sample.csv", index=False)

    homoglyphs.to_parquet(adv_dir / "homoglyphs.parquet", index=False)
    homoglyphs.head(sample_rows).to_csv(adv_dir / "homoglyphs_sample.csv", index=False)

    summary = {
        "identities": len(identities),
        "surfaces": len(surfaces),
        "pairs": len(pairs),
        "positives": int((pair_df["label"] == 1).sum()),
        "negatives": int((pair_df["label"] == 0).sum()),
        "hard_negatives": int((pair_df["hardness"] == "hard").sum()),
        "homoglyph_attacks": len(homoglyphs),
        "script_pair_counts": pair_df["script_pair"].value_counts().to_dict(),
        "hard_type_counts": pair_df[pair_df["hardness"] == "hard"]
        ["hard_negative_type"].value_counts().to_dict(),
    }
    _print_summary(summary, full_dir, sample_dir, adv_dir)
    return summary


def _print_summary(s: dict[str, Any], full_dir: Path, sample_dir: Path, adv_dir: Path) -> None:
    print("AzNameMatch — generation complete (dataset counts only; no metrics).")
    print(f"  identities       : {s['identities']}")
    print(f"  surface forms    : {s['surfaces']}")
    print(f"  labeled pairs    : {s['pairs']}  "
          f"(+{s['positives']} / -{s['negatives']}, {s['hard_negatives']} hard)")
    print(f"  homoglyph attacks: {s['homoglyph_attacks']}  (frozen, separate)")
    print(f"  script pairs     : {s['script_pair_counts']}")
    print(f"  hard-neg types   : {s['hard_type_counts']}")
    print(f"  full parquet     : {full_dir}")
    print(f"  committed sample : {sample_dir}")
    print(f"  adversarial set  : {adv_dir}")
