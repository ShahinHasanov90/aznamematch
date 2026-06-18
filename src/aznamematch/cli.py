"""Command-line interface: ``aznamematch generate | block | bench | report``.

Only ``generate`` is implemented in this milestone (Phases 0-4). ``block``, ``bench`` and
``report`` are documented stubs for the deferred phases and exit with a clear message
rather than pretending to run.
"""

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
def block() -> None:
    """Candidate blocking with RR / PQ / PC metrics (Phase 5 — deferred)."""
    _deferred("block", "Phase 5 (blocking)")


@app.command()
def bench() -> None:
    """Run matchers over the labeled pairs (Phase 6 — deferred)."""
    _deferred("bench", "Phase 6 (matchers)")


@app.command()
def report() -> None:
    """Emit accuracy + performance views into results/ (Phase 7 — deferred)."""
    _deferred("report", "Phase 7 (evaluation)")


if __name__ == "__main__":
    app()
