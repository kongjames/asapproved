"""Command line: ``check-table``, ``recompute``, ``research`` and ``check-brief``."""

from __future__ import annotations

from pathlib import Path

import typer

from pharma_agents import __version__

app = typer.Typer(no_args_is_help=True, add_completion=False,
                  help="Check that an automated analysis still does what it was shown to do when it was approved.")


@app.command()
def version() -> None:
    typer.echo(f"pharma-agents {__version__}")


@app.command("recompute")
def recompute_cmd(
    recipe: Path = typer.Argument(..., help="recipe.yaml"),
    out: Path = typer.Option(Path("table.csv"), "--out", "-o", help="where to write the long-format table"),
) -> None:
    """Derive a table from a recipe and its dataset (use this to create an approved baseline)."""
    from pharma_agents.assurance.recompute import recompute
    from pharma_agents.data.cdisc_pilot import load_csv
    from pharma_agents.schema.artifact import Recipe

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
    from pharma_agents.assurance.agent import run_check_table
    from pharma_agents.assurance.render import to_markdown

    report = run_check_table(recipe, approved, candidate, reviewer=reviewer, notes=notes, run_date=date)
    out.write_text(to_markdown(report))
    if json_out:
        json_out.write_text(report.model_dump_json(indent=2))
    for c in report.checks:
        typer.echo(f"{'PASS' if c.passed else 'FAIL'}  {c.name}: {c.matches} match, {c.mismatches} mismatch, "
                   f"{c.missing} missing, {c.unexpected} unexpected")
    typer.echo(f"{report.verdict}  report written to {out}")
    raise typer.Exit(code=0 if report.verdict == "PASS" else 1)


@app.command("research")
def research_cmd(
    question: str = typer.Argument(..., help="the question to answer from public sources"),
    out: Path = typer.Option(Path("runs"), "--out", "-o", help="folder; the run is written to <out>/<run-id>/"),
    provider: str = typer.Option("anthropic", "--provider", help="anthropic | fake"),
    model: str | None = typer.Option(None, "--model", help="model id for the anthropic provider"),
    effort: str | None = typer.Option(None, "--effort", help="low | medium | high | xhigh | max"),
    script: Path | None = typer.Option(None, "--script", help="JSON list of scripted responses (fake provider)"),
    run_id: str | None = typer.Option(None, "--run-id", help="override the run id, for reproducible folders"),
) -> None:
    """Plan, fetch public records, draft a brief, then post-check it. Exit 1 if any claim is unsupported."""
    import json

    from pharma_agents.research.agent import ResearchAgent

    if provider == "fake":
        from pharma_agents.llm.fake import FakeProvider

        responses = json.loads(script.read_text()) if script else []
        prov = FakeProvider(responses)
    elif provider == "anthropic":
        from pharma_agents.llm.anthropic import DEFAULT_MODEL, AnthropicProvider

        prov = AnthropicProvider(model or DEFAULT_MODEL, effort=effort)
    else:
        raise typer.BadParameter("provider must be anthropic or fake")
    _brief, check, run_dir = ResearchAgent(prov, out, run_id=run_id).run(question)
    typer.echo(f"{check.verdict}  {check.supported}/{check.claims_total} claims supported, "
               f"{check.numbers_traced}/{check.numbers_total} numbers traced; written to {run_dir}")
    raise typer.Exit(code=0 if check.verdict == "PASS" else 1)


@app.command("check-brief")
def check_brief_cmd(
    brief: Path = typer.Argument(..., help="brief.json"),
    records: Path | None = typer.Option(None, "--records", help="records folder (default: <brief dir>/records)"),
    reviewer: str | None = typer.Option(None, "--reviewer"),
    notes: str | None = typer.Option(None, "--notes"),
    out: Path = typer.Option(Path("brief_report.md"), "--out", "-o"),
    json_out: Path | None = typer.Option(None, "--json"),
    date: str | None = typer.Option(None, "--date", help="override check date (YYYY-MM-DD), for reproducible reports"),
) -> None:
    """Re-run the deterministic checks on a brief against its stored records. No model, no network."""
    import datetime as dt

    from pharma_agents.research.postcheck import check_brief
    from pharma_agents.research.render import brief_to_markdown
    from pharma_agents.schema.brief import EvidenceBrief
    from pharma_agents.sources.base import RecordStore

    store = RecordStore(records or brief.parent / "records")
    b = EvidenceBrief.model_validate_json(brief.read_text(encoding="utf-8"))
    checked, check = check_brief(b, store.index())
    out.write_text(brief_to_markdown(checked, check, store.index(), reviewer=reviewer, notes=notes,
                                     run_date=date or dt.date.today().isoformat()), encoding="utf-8")
    if json_out:
        json_out.write_text(check.model_dump_json(indent=2))
    for c in checked.claims:
        typer.echo(f"{'OK  ' if c.status == 'supported' else 'FAIL'} {c.id}: {'; '.join(c.reasons) or 'supported'}")
    typer.echo(f"{check.verdict}  report written to {out}")
    raise typer.Exit(code=0 if check.verdict == "PASS" else 1)


if __name__ == "__main__":  # pragma: no cover
    app()
