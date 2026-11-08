"""Command line: ``asapproved check-table`` and ``asapproved recompute``."""

from __future__ import annotations

from pathlib import Path

import typer

from asapproved import __version__

app = typer.Typer(no_args_is_help=True, add_completion=False,
                  help="Check that an automated analysis still does what it was shown to do when it was approved.")


@app.command()
def version() -> None:
    typer.echo(f"asapproved {__version__}")


@app.command("recompute")
def recompute_cmd(
    recipe: Path = typer.Argument(..., help="recipe.yaml"),
    out: Path = typer.Option(Path("table.csv"), "--out", "-o", help="where to write the long-format table"),
) -> None:
    """Derive a table from a recipe and its dataset (use this to create an approved baseline)."""
    from asapproved.assurance.recompute import recompute
    from asapproved.data.cdisc_pilot import load_csv
    from asapproved.schema.artifact import Recipe

    r = Recipe.load(recipe)
    table, trace = recompute(r, load_csv(r.dataset_path), str(r.dataset_path))
    table.to_csv(out, index=False)
    typer.echo(f"wrote {out}: {len(table)} cells, {trace.rows_in_population}/{trace.rows_total} rows in population")


@app.command("check-table")
def check_table(
    recipe: Path = typer.Argument(..., help="recipe.yaml"),
    approved: Path = typer.Option(..., "--approved", help="approved baseline table (long CSV)"),
    candidate: Path | None = typer.Option(None, "--candidate", help="new output to check (long CSV)"),
    reviewer: str | None = typer.Option(None, "--reviewer", help='e.g. "Jane Doe, Statistical Programmer (personal capacity)"'),
    notes: str | None = typer.Option(None, "--notes"),
    out: Path = typer.Option(Path("report.md"), "--out", "-o"),
    json_out: Path | None = typer.Option(None, "--json"),
    date: str | None = typer.Option(None, "--date", help="override run date (YYYY-MM-DD), for reproducible reports"),
) -> None:
    """Re-compute the table from source and compare approved and candidate outputs cell by cell."""
    from asapproved.assurance.agent import run_check_table
    from asapproved.assurance.render import to_markdown

    report = run_check_table(recipe, approved, candidate, reviewer=reviewer, notes=notes, run_date=date)
    out.write_text(to_markdown(report))
    if json_out:
        json_out.write_text(report.model_dump_json(indent=2))
    for c in report.checks:
        typer.echo(f"{'PASS' if c.passed else 'FAIL'}  {c.name}: {c.matches} match, {c.mismatches} mismatch, "
                   f"{c.missing} missing, {c.unexpected} unexpected")
    typer.echo(f"{report.verdict}  report written to {out}")
    raise typer.Exit(code=0 if report.verdict == "PASS" else 1)


if __name__ == "__main__":  # pragma: no cover
    app()
