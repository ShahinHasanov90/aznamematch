"""Command-line interface: ``aznamematch generate | block | bench | report``."""

from __future__ import annotations

import typer

app = typer.Typer(
    add_completion=False,
    help="AzNameMatch — synthetic cross-script name-matching benchmark.",
    no_args_is_help=True,
)


@app.command()
def generate(
    config: str = typer.Option(
        "configs/generation.yaml", "--config", "-c", help="Path to generation config YAML."
    ),
) -> None:
    """Generate the synthetic dataset (canonical -> translit -> noise -> homoglyph -> pairs).

    Implemented in Phase 4; wired here as the pipeline lands.
    """
    from aznamematch.generate.pipeline import run_generation

    run_generation(config)


def _deferred(name: str, phase: str) -> None:
    typer.secho(
        f"`{name}` is part of {phase} and is not built in this milestone "
        f"(generation only). See docs/DESIGN.md for the roadmap.",
        fg=typer.colors.YELLOW,
    )
    raise typer.Exit(code=2)


@app.command()
def block(
    config: str = typer.Option("configs/generation.yaml", "--config", "-c"),
    cap: int = typer.Option(6, "--cap", help="Max surfaces per identity (bounds all-pairs)."),
) -> None:
    """Run the blockers over generated surfaces and print RR / PQ / PC."""
    import pandas as pd

    from aznamematch.blocking.blockers import compare_blockers, records_from_surface_rows
    from aznamematch.config import REPO_ROOT, get, load_config

    cfg = load_config(config)
    surf_path = (REPO_ROOT / get(cfg, "output.full_dir", "data/full") / "surfaces.parquet")
    if not surf_path.exists():
        typer.secho(f"No surfaces at {surf_path}. Run `aznamematch generate` first.",
                    fg=typer.colors.RED)
        raise typer.Exit(code=2)

    rows = pd.read_parquet(surf_path).to_dict("records")
    records = records_from_surface_rows(rows, per_identity_cap=cap)
    typer.echo(f"Blocking over {len(records)} records (cap {cap}/identity):")
    typer.echo(f"  {'blocker':14} {'RR':>7} {'PC':>7} {'PQ':>7}  {'cands':>9}")
    for name, m in compare_blockers(records).items():
        typer.echo(f"  {name:14} {m.reduction_ratio:7.4f} {m.pair_completeness:7.4f} "
                   f"{m.pair_quality:7.4f}  {m.n_candidates:9d}")


@app.command()
def bench(
    config: str = typer.Option("configs/benchmark.yaml", "--config", "-c"),
) -> None:
    """Run all matchers over the labeled pairs and write results/ (accuracy + perf views)."""
    from aznamematch.config import REPO_ROOT, get, load_config
    from aznamematch.eval.report import write_results
    from aznamematch.eval.runner import run_benchmark

    typer.echo("Running benchmark (numbers come from this run; none are hardcoded)...")
    results = run_benchmark(config)
    out_dir = REPO_ROOT / get(load_config(config), "paths.results", "results")
    write_results(results, out_dir)
    typer.secho(f"Wrote results to {out_dir}", fg=typer.colors.GREEN)
    report(config)


@app.command()
def report(
    config: str = typer.Option("configs/benchmark.yaml", "--config", "-c"),
) -> None:
    """Print the results SUMMARY (run `bench` first to (re)generate it)."""
    from aznamematch.config import REPO_ROOT, get, load_config

    summary = REPO_ROOT / get(load_config(config), "paths.results", "results") / "SUMMARY.md"
    if not summary.exists():
        typer.secho(f"No summary at {summary}. Run `aznamematch bench` first.",
                    fg=typer.colors.RED)
        raise typer.Exit(code=2)
    typer.echo(summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
