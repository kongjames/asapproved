"""EvidenceBrief: what the research agent produces, and what the assurance agent checks.

A brief is a list of claims. Every claim names the source records it rests on; every number in
a claim names the record and the path inside that record's payload where the number sits. The
post-check (``research.postcheck``) resolves each of those and marks the claim supported or not.
Only declared numbers are checked. A figure that appears in claim text without a matching
``numbers`` entry is reported as a warning, not a failure; the summary is prose and is not checked.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class NumberRef(BaseModel):
    value: float
    unit: str | None = None
    record_id: str
    path: str = Field(description='dotted path into the record payload, e.g. "enrollment_count" or "terms[0].count"')


class Claim(BaseModel):
    id: str
    text: str
    record_ids: list[str] = Field(default_factory=list)
    numbers: list[NumberRef] = Field(default_factory=list)
    status: Literal["supported", "unsupported", "unchecked"] = "unchecked"
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    source: str
    params: dict[str, Any] = Field(default_factory=dict)


class RunMeta(BaseModel):
    run_id: str
    created_at: str
    tool_version: str
    provider: str
    model_id: str
    usage: dict[str, int] = Field(default_factory=dict)
    queries: list[SearchQuery] = Field(default_factory=list)
    record_count: int = 0
    prompt_sha256: str | None = None


class EvidenceBrief(BaseModel):
    question: str
    summary: str
    claims: list[Claim]
    run_meta: RunMeta | None = None


class BriefCheck(BaseModel):
    claims_total: int
    supported: int
    unsupported: int
    numbers_total: int
    numbers_traced: int
    record_ids_cited: int
    record_ids_unresolved: list[str] = Field(default_factory=list)
    summary_numbers_unchecked: int = 0
    undeclared_numbers: int = 0  # digits in claim text with no matching entry in numbers

    @property
    def verdict(self) -> str:
        return "PASS" if self.unsupported == 0 else "FAIL"
