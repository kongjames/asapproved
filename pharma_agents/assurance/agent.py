"""The assurance agent's first job: check a table against its approved baseline and a candidate.

Three comparisons, all deterministic:
  1. Approved vs independent re-computation — does the approved output reproduce from source?
  2. Candidate vs approved — does the new (AI-generated, migrated) output agree with what was approved?
  3. Candidate vs independent re-computation — does the new output reproduce from source?
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from pharma_agents import __version__
from pharma_agents.assurance.compare import CellDiff, compare_tables
from pharma_agents.assurance.recompute import recompute
from pharma_agents.data.cdisc_pilot import load_csv, sha256_of
from pharma_agents.schema.artifact import Recipe
from pharma_agents.schema.report import CheckSummary, ValidationReport


def _display(path: str | Path, base: Path) -> str:
    """Show paths relative to the recipe's folder so reports are the same on every machine."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(base))
    except ValueError:
        return path.name


def _summarise(name: str, ref_label: str, oth_label: str, diffs: list[CellDiff]) -> tuple[CheckSummary, list[dict]]:
    counts = {"match": 0, "mismatch": 0, "missing": 0, "unexpected": 0}
    for d in diffs:
        counts[d.status] += 1
    summary = CheckSummary(
        name=name, reference_label=ref_label, other_label=oth_label,
        cells_compared=len(diffs), matches=counts["match"], mismatches=counts["mismatch"],
        missing=counts["missing"], unexpected=counts["unexpected"],
    )
    return summary, [d.as_dict() for d in diffs if d.status != "match"]


def run_check_table(
    recipe_path: str | Path,
    approved_path: str | Path,
    candidate_path: str | Path | None = None,
    reviewer: str | None = None,
    notes: str | None = None,
    run_date: str | None = None,
) -> ValidationReport:
    recipe = Recipe.load(recipe_path)
    ds_path = recipe.dataset_path
    df = load_csv(ds_path)
    recomputed, trace = recompute(recipe, df, dataset_path=str(ds_path))
    approved = pd.read_csv(approved_path)
    tol = recipe.tolerances

    base = recipe.recipe_path.parent if recipe.recipe_path else Path.cwd()
    checks, diffs = [], {}
    inputs = {"Approved table": f"{_display(approved_path, base)} (sha256 {sha256_of(approved_path)[:16]}…)"}
    s, d = _summarise("Check 1 — approved output vs independent re-computation", "re-computed", "approved",
                      compare_tables(recomputed, approved, tol))
    checks.append(s); diffs[s.name] = d

    if candidate_path is not None:
        candidate = pd.read_csv(candidate_path)
        inputs["Candidate table"] = f"{_display(candidate_path, base)} (sha256 {sha256_of(candidate_path)[:16]}…)"
        s, d = _summarise("Check 2 — candidate output vs approved output", "approved", "candidate",
                          compare_tables(approved, candidate, tol))
        checks.append(s); diffs[s.name] = d
        s, d = _summarise("Check 3 — candidate output vs independent re-computation", "re-computed", "candidate",
                          compare_tables(recomputed, candidate, tol))
        checks.append(s); diffs[s.name] = d

    return ValidationReport(
        tool_version=__version__,
        run_date=run_date or dt.date.today().isoformat(),
        recipe_name=recipe.name, recipe_title=recipe.title,
        dataset_path=_display(ds_path, base), dataset_sha256=sha256_of(ds_path),
        rows_total=trace.rows_total, rows_in_population=trace.rows_in_population,
        population_filter=trace.population_filter, group_by=trace.group_by, groups=trace.groups,
        inputs=inputs, checks=checks, diffs=diffs, trace=trace.derivations,
        reviewer=reviewer, notes=notes,
    )
