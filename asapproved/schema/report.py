"""What a validation run records. Rendered to Markdown by ``assurance.render``."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckSummary(BaseModel):
    name: str
    reference_label: str
    other_label: str
    cells_compared: int
    matches: int
    mismatches: int
    missing: int  # in reference, absent from other
    unexpected: int  # in other, absent from reference

    @property
    def passed(self) -> bool:
        return self.mismatches == 0 and self.missing == 0 and self.unexpected == 0


class ValidationReport(BaseModel):
    tool: str = "asapproved"
    tool_version: str
    run_date: str
    recipe_name: str
    recipe_title: str | None = None
    dataset_path: str
    dataset_sha256: str
    rows_total: int
    rows_in_population: int
    population_filter: str | None = None
    group_by: str
    groups: list[str]
    inputs: dict[str, str] = Field(default_factory=dict)  # label -> path or sha256
    checks: list[CheckSummary]
    diffs: dict[str, list[dict]] = Field(default_factory=dict)  # check name -> non-matching cells
    trace: list[dict] = Field(default_factory=list)
    reviewer: str | None = None
    notes: str | None = None

    @property
    def verdict(self) -> str:
        return "PASS" if all(c.passed for c in self.checks) else "FAIL"
