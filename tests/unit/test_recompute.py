import pandas as pd

from pharma_agents.assurance.recompute import recompute
from pharma_agents.schema.artifact import Recipe


def _recipe(**over):
    base = {
        "name": "t", "dataset": "x.csv", "group_by": "ARM", "include_total": True, "decimals": 3,
        "rows": [{"variable": "AGE", "type": "continuous", "stats": ["n", "mean", "sd"]},
                 {"variable": "SEX", "type": "categorical", "categories": ["F", "M"]}],
    }
    base.update(over)
    return Recipe.model_validate(base)


def _df():
    return pd.DataFrame({
        "ARM": ["A", "A", "A", "B", "B"],
        "AGE": [60, 62, None, 70, 74],
        "SEX": ["F", "M", "F", "M", None],
        "FLAG": ["Y", "Y", "Y", "Y", "N"],
    })


def test_continuous_and_total():
    table, trace = recompute(_recipe(), _df())
    cell = lambda **k: table.loc[(table[list(k)] == pd.Series(k)).all(axis=1), "value"].iloc[0]
    assert cell(variable="AGE", statistic="n", group="A") == 2
    assert cell(variable="AGE", statistic="mean", group="A") == 61
    assert cell(variable="AGE", statistic="n", group="Total") == 4
    assert round(cell(variable="AGE", statistic="sd", group="B"), 3) == round(2.828, 3)
    assert trace.rows_total == 5 and trace.rows_in_population == 5
    assert trace.groups == ["A", "B", "Total"]


def test_categorical_counts_percent_and_missing():
    table, _ = recompute(_recipe(), _df())
    sexA = table[(table.variable == "SEX") & (table.group == "A")].set_index(["category", "statistic"])["value"]
    assert sexA[("F", "n")] == 2 and sexA[("M", "n")] == 1
    assert round(sexA[("F", "pct")], 3) == round(200 / 3, 3)
    sexB = table[(table.variable == "SEX") & (table.group == "B")].set_index(["category", "statistic"])["value"]
    assert sexB[("Missing", "n")] == 1 and sexB[("Missing", "pct")] == 50


def test_population_filter():
    table, trace = recompute(_recipe(population={"filter": "FLAG == 'Y'"}), _df())
    assert trace.rows_in_population == 4
    n_total = table[(table.variable == "AGE") & (table.statistic == "n") & (table.group == "Total")]["value"].iloc[0]
    assert n_total == 3
