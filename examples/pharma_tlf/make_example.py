"""Build the example's approved and candidate tables, and the expected (golden) report.

The approved table is the independent re-computation itself, standing in for an output a
first programmer produced and that was reviewed and approved. The candidate stands in for
a re-implementation (for example, a migration from SAS to R, or AI-generated code) and
carries two deliberate defects so the report has something to show:

  1. Mean AGE in the "Xanomeline High Dose" column is shifted by +0.7 years.
  2. The SEX = F percentage for "Placebo" is missing.

Run from the repository root:  python examples/pharma_tlf/make_example.py
"""

from __future__ import annotations

from pathlib import Path

from pharma_agents.assurance.agent import run_check_table
from pharma_agents.assurance.recompute import recompute
from pharma_agents.assurance.render import to_markdown
from pharma_agents.data.cdisc_pilot import load_csv
from pharma_agents.schema.artifact import Recipe

HERE = Path(__file__).parent
FIXED_DATE = "2026-11-07"


def main() -> None:
    recipe = Recipe.load(HERE / "recipe.yaml")
    table, _ = recompute(recipe, load_csv(recipe.dataset_path), str(recipe.dataset_path))
    approved = HERE / "approved_sas_table.csv"
    table.to_csv(approved, index=False)

    cand = table.copy()
    m = (cand.variable == "AGE") & (cand.statistic == "mean") & (cand.group == "Xanomeline High Dose")
    assert m.sum() == 1
    cand.loc[m, "value"] = round(float(cand.loc[m, "value"].iloc[0]) + 0.7, recipe.decimals)
    drop = (cand.variable == "SEX") & (cand.category == "F") & (cand.statistic == "pct") & (cand.group == "Placebo")
    assert drop.sum() == 1
    cand = cand[~drop]
    candidate = HERE / "candidate_r_table.csv"
    cand.to_csv(candidate, index=False)

    report = run_check_table(HERE / "recipe.yaml", approved, candidate,
                             reviewer="Example Reviewer, Statistical Programmer (personal capacity)",
                             run_date=FIXED_DATE)
    (HERE / "expected_report.md").write_text(to_markdown(report))
    print(f"approved: {len(table)} cells; candidate: {len(cand)} cells; verdict {report.verdict}")


if __name__ == "__main__":
    main()
