"""The table artifact: a recipe that says how a table is derived from a dataset.

A recipe is the analysis specification in machine-readable form. Given the same
dataset, anyone can re-compute the table from it. That is what makes an
independent check possible.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

Stat = Literal["n", "nmiss", "mean", "sd", "median", "min", "max", "q1", "q3"]

# Column order of every table this package reads or writes ("long" format).
TABLE_KEY = ["variable", "category", "statistic", "group"]
TABLE_COLUMNS = TABLE_KEY + ["value"]


class Population(BaseModel):
    """Which rows of the dataset the table describes."""

    filter: str | None = None  # a pandas ``DataFrame.query`` expression
    description: str | None = None


class RowSpec(BaseModel):
    """One block of rows in the table: a variable and how it is summarised."""

    variable: str
    label: str | None = None
    type: Literal["continuous", "categorical"]
    stats: list[Stat] = Field(default_factory=lambda: ["n", "mean", "sd", "median", "min", "max"])
    categories: list[str] | None = None  # fixed display order; None = observed, sorted


class Tolerances(BaseModel):
    """How close two numbers must be to count as the same."""

    numeric_abs: float = 0.0
    numeric_rel: float = 0.0
    pct_abs: float | None = None  # if None, ``numeric_abs`` applies to percentages too


class Recipe(BaseModel):
    name: str
    title: str | None = None
    dataset: str  # path, relative to the recipe file
    population: Population = Field(default_factory=Population)
    group_by: str
    include_total: bool = True
    total_label: str = "Total"
    rows: list[RowSpec]
    tolerances: Tolerances = Field(default_factory=Tolerances)
    decimals: int = 4
    recipe_path: Path | None = Field(default=None, exclude=True)

    @classmethod
    def load(cls, path: str | Path) -> Recipe:
        path = Path(path)
        with path.open() as fh:
            raw = yaml.safe_load(fh)
        recipe = cls.model_validate(raw)
        recipe.recipe_path = path.resolve()
        return recipe

    @property
    def dataset_path(self) -> Path:
        base = self.recipe_path.parent if self.recipe_path else Path.cwd()
        return (base / self.dataset).resolve()
