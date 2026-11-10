"""Cell-by-cell comparison of two tables in long format."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import pandas as pd

from pharmaagents.schema.artifact import TABLE_COLUMNS, TABLE_KEY, Tolerances


@dataclass
class CellDiff:
    variable: str
    category: str
    statistic: str
    group: str
    reference: float | str | None
    other: float | str | None
    status: str  # match | mismatch | missing | unexpected
    delta: float | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _as_float(v):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _same(ref, oth, statistic: str, tol: Tolerances) -> tuple[bool, float | None]:
    rf, of = _as_float(ref), _as_float(oth)
    if rf is None and of is None:
        return (str(ref or "").strip() == str(oth or "").strip()), None
    if rf is None or of is None:
        return False, None
    delta = of - rf
    abs_tol = tol.pct_abs if (statistic == "pct" and tol.pct_abs is not None) else tol.numeric_abs
    if abs(delta) <= abs_tol:
        return True, delta
    if tol.numeric_rel and rf != 0 and abs(delta) / abs(rf) <= tol.numeric_rel:
        return True, delta
    return False, delta


def normalise(table: pd.DataFrame) -> pd.DataFrame:
    """Coerce a table read from CSV into the canonical long format."""
    missing = [c for c in TABLE_COLUMNS if c not in table.columns]
    if missing:
        raise ValueError(f"table is missing columns {missing}; expected {TABLE_COLUMNS}")
    t = table[TABLE_COLUMNS].copy()
    for c in TABLE_KEY:
        t[c] = t[c].fillna("").astype(str).str.strip()
    return t


def compare_tables(reference: pd.DataFrame, other: pd.DataFrame, tol: Tolerances | None = None) -> list[CellDiff]:
    """Compare ``other`` against ``reference``. Every cell of either table appears once in the result."""
    tol = tol or Tolerances()
    ref = normalise(reference).set_index(TABLE_KEY)
    oth = normalise(other).set_index(TABLE_KEY)
    if ref.index.duplicated().any() or oth.index.duplicated().any():
        raise ValueError("duplicate cells: each (variable, category, statistic, group) must appear once")
    diffs: list[CellDiff] = []
    for key in ref.index:
        rv = ref.at[key, "value"]
        if key in oth.index:
            ov = oth.at[key, "value"]
            ok, delta = _same(rv, ov, key[2], tol)
            diffs.append(CellDiff(*key, rv, ov, "match" if ok else "mismatch", delta))
        else:
            diffs.append(CellDiff(*key, rv, None, "missing"))
    for key in oth.index.difference(ref.index):
        diffs.append(CellDiff(*key, None, oth.at[key, "value"], "unexpected"))
    return diffs
