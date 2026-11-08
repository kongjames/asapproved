"""Independent re-computation of a table from its recipe and dataset.

This is the step a second programmer performs in clinical statistical programming:
derive the same table again, from the source data, without looking at the first result.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from asapproved.schema.artifact import TABLE_COLUMNS, Recipe, RowSpec

MISSING_LABEL = "Missing"


def _stat(series: pd.Series, name: str) -> float:
    s = pd.to_numeric(series, errors="coerce")
    valid = s.dropna()
    if name == "n":
        return float(valid.shape[0])
    if name == "nmiss":
        return float(s.shape[0] - valid.shape[0])
    if valid.empty:
        return float("nan")
    if name == "mean":
        return float(valid.mean())
    if name == "sd":
        return float(valid.std(ddof=1)) if valid.shape[0] > 1 else float("nan")
    if name == "median":
        return float(valid.median())
    if name == "min":
        return float(valid.min())
    if name == "max":
        return float(valid.max())
    if name == "q1":
        return float(valid.quantile(0.25))
    if name == "q3":
        return float(valid.quantile(0.75))
    raise ValueError(f"unknown statistic {name!r}")


@dataclass
class Trace:
    """What was done, in enough detail for a reviewer's guide."""

    dataset_path: str
    rows_total: int
    rows_in_population: int
    population_filter: str | None
    group_by: str
    groups: list[str]
    derivations: list[dict] = field(default_factory=list)


def _groups(df: pd.DataFrame, recipe: Recipe) -> list[tuple[str, pd.DataFrame]]:
    col = recipe.group_by
    if col not in df.columns:
        raise KeyError(f"group_by column {col!r} not in dataset")
    out = [(str(k), g) for k, g in df.groupby(col, dropna=False, sort=True)]
    if recipe.include_total:
        out.append((recipe.total_label, df))
    return out


def _continuous_rows(spec: RowSpec, groups: list[tuple[str, pd.DataFrame]]) -> list[dict]:
    rows = []
    for gname, g in groups:
        for stat in spec.stats:
            rows.append({
                "variable": spec.variable, "category": "", "statistic": stat,
                "group": gname, "value": _stat(g[spec.variable], stat),
            })
    return rows


def _categorical_rows(spec: RowSpec, groups: list[tuple[str, pd.DataFrame]]) -> list[dict]:
    # Category order: fixed if given, else observed values sorted; "Missing" last if present.
    if spec.categories:
        cats = list(spec.categories)
    else:
        observed = set()
        for _, g in groups:
            observed.update(str(v) for v in g[spec.variable].dropna().unique())
        cats = sorted(observed)
    any_missing = any(g[spec.variable].isna().any() for _, g in groups)
    if any_missing and MISSING_LABEL not in cats:
        cats.append(MISSING_LABEL)
    rows = []
    for gname, g in groups:
        denom = g.shape[0]
        col = g[spec.variable]
        for cat in cats:
            count = int(col.isna().sum()) if cat == MISSING_LABEL else int((col.astype("string") == cat).sum())
            pct = 100.0 * count / denom if denom else float("nan")
            rows.append({"variable": spec.variable, "category": cat, "statistic": "n", "group": gname, "value": float(count)})
            rows.append({"variable": spec.variable, "category": cat, "statistic": "pct", "group": gname, "value": pct})
    return rows


def recompute(recipe: Recipe, df: pd.DataFrame, dataset_path: str = "") -> tuple[pd.DataFrame, Trace]:
    """Return the table (long format) and a trace of how it was derived."""
    rows_total = int(df.shape[0])
    pop = df.query(recipe.population.filter) if recipe.population.filter else df
    groups = _groups(pop, recipe)
    trace = Trace(
        dataset_path=dataset_path, rows_total=rows_total, rows_in_population=int(pop.shape[0]),
        population_filter=recipe.population.filter, group_by=recipe.group_by,
        groups=[g for g, _ in groups],
    )
    records: list[dict] = []
    for spec in recipe.rows:
        if spec.variable not in pop.columns:
            raise KeyError(f"variable {spec.variable!r} not in dataset")
        if spec.type == "continuous":
            records.extend(_continuous_rows(spec, groups))
            derivation = f"{', '.join(spec.stats)} of {spec.variable} (non-missing values; sd uses n-1)"
        else:
            records.extend(_categorical_rows(spec, groups))
            derivation = f"count and percent of {spec.variable} per category; percent denominator = subjects in the column"
        trace.derivations.append({
            "variable": spec.variable, "label": spec.label or spec.variable, "type": spec.type,
            "derivation": derivation,
            "population": recipe.population.filter or "all rows", "columns": recipe.group_by,
        })
    table = pd.DataFrame.from_records(records, columns=TABLE_COLUMNS)
    table["value"] = table["value"].astype(float).round(recipe.decimals)
    table["value"] = table["value"].replace({np.nan: None})
    return table, trace
