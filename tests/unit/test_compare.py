import pandas as pd
import pytest

from asapproved.assurance.compare import compare_tables
from asapproved.schema.artifact import TABLE_COLUMNS, Tolerances


def _t(rows):
    return pd.DataFrame(rows, columns=TABLE_COLUMNS)


REF = _t([("AGE", "", "mean", "A", 61.0), ("AGE", "", "n", "A", 2), ("SEX", "F", "pct", "A", 66.667)])


def test_identical_tables_match():
    d = compare_tables(REF, REF.copy())
    assert [x.status for x in d] == ["match"] * 3


def test_mismatch_missing_unexpected():
    oth = _t([("AGE", "", "mean", "A", 61.5), ("AGE", "", "n", "A", 2), ("RACE", "WHITE", "n", "A", 1)])
    d = {(x.variable, x.category, x.statistic): x for x in compare_tables(REF, oth)}
    assert d[("AGE", "", "mean")].status == "mismatch" and d[("AGE", "", "mean")].delta == pytest.approx(0.5)
    assert d[("AGE", "", "n")].status == "match"
    assert d[("SEX", "F", "pct")].status == "missing"
    assert d[("RACE", "WHITE", "n")].status == "unexpected"


def test_tolerance_absolute_and_pct():
    oth = _t([("AGE", "", "mean", "A", 61.004), ("AGE", "", "n", "A", 2), ("SEX", "F", "pct", "A", 66.7)])
    d = {x.statistic: x.status for x in compare_tables(REF, oth, Tolerances(numeric_abs=0.005, pct_abs=0.05))}
    assert d == {"mean": "match", "n": "match", "pct": "match"}
    d2 = {x.statistic: x.status for x in compare_tables(REF, oth, Tolerances(numeric_abs=0.005))}
    assert d2["pct"] == "mismatch"


def test_duplicate_cells_rejected():
    dup = pd.concat([REF, REF.iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate"):
        compare_tables(dup, REF)
