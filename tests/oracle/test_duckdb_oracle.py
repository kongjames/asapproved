"""E1 — independent oracle. The example's demographics table derived a second way, in SQL by DuckDB,
with no pandas arithmetic and no pharma_agents code in the derivation. Every cell must agree with
``recompute`` to 1e-6 before rounding."""

from pathlib import Path

import duckdb

from pharma_agents.assurance.compare import compare_tables
from pharma_agents.assurance.recompute import recompute
from pharma_agents.data.cdisc_pilot import load_csv
from pharma_agents.schema.artifact import Recipe, Tolerances

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parents[1] / "examples" / "pharma_tlf"


def oracle_table():
    sql = (HERE / "demographics_oracle.sql").read_text().replace("{adsl}", str(EXAMPLE / "data" / "adsl.csv"))
    return duckdb.sql(sql).df()


def test_recompute_agrees_with_duckdb_oracle_before_rounding():
    recipe = Recipe.load(EXAMPLE / "recipe.yaml")
    recipe.decimals = 10  # compare the derivation, not the rounding
    ours, trace = recompute(recipe, load_csv(recipe.dataset_path))
    theirs = oracle_table()
    assert len(theirs) == len(ours) == 80
    diffs = compare_tables(theirs, ours, Tolerances(numeric_abs=1e-6))
    bad = [d for d in diffs if d.status != "match"]
    assert not bad, [d.as_dict() for d in bad[:10]]
    assert trace.rows_in_population == 254


def test_oracle_has_every_group_and_category():
    t = oracle_table()
    assert set(t["group"]) == {"Placebo", "Xanomeline High Dose", "Xanomeline Low Dose", "Total"}
    assert set(t[t.variable == "SEX"].category) == {"F", "M"}
    assert set(t[t.variable == "AGEGR1"].category) == {"18-64", ">64"}
