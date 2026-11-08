"""Deterministic checks on an EvidenceBrief. No model involved.

C1 — citation trace: every cited record id resolves to a stored record.
C2 — number trace: every number resolves to a value at its path in its record, within tolerance.
A claim with no sources, an unresolved citation, or an untraceable number is ``unsupported``.
A figure in claim text that is not declared in ``numbers`` is a warning (the claim can still pass).
"""

from __future__ import annotations

import re
from typing import Any

from asapproved.schema.brief import BriefCheck, Claim, EvidenceBrief
from asapproved.sources.base import SourceRecord

_INDEX = re.compile(r"^([^\[\]]*)((?:\[\d+\])*)$")
# a standalone figure: not part of an identifier (NCT0123), a date (2026-08-12) or a version string
_FIGURE = re.compile(r"(?<![A-Za-z0-9.\-])\d[\d,]*(?:\.\d+)?(?![A-Za-z0-9.\-])")


def resolve_path(payload: Any, path: str) -> Any:
    """``"a.b[0].c"`` → payload["a"]["b"][0]["c"]. Raises KeyError / IndexError / TypeError when absent."""
    cur = payload
    for part in [p for p in path.split(".") if p]:
        m = _INDEX.match(part)
        if not m:
            raise KeyError(part)
        key, idx = m.group(1), m.group(2)
        if key:
            if not isinstance(cur, dict) or key not in cur:
                raise KeyError(key)
            cur = cur[key]
        for i in re.findall(r"\[(\d+)\]", idx):
            if not isinstance(cur, list):
                raise TypeError(f"{key or part} is not a list")
            cur = cur[int(i)]
    return cur


def _close(a: float, b: float, rel_tol: float, abs_tol: float) -> bool:
    return abs(a - b) <= max(abs_tol, rel_tol * abs(b))


def _check_claim(c: Claim, records: dict[str, SourceRecord], rel_tol: float, abs_tol: float) -> tuple[Claim, int]:
    reasons: list[str] = []
    traced = 0
    if not c.record_ids:
        reasons.append("no source record cited")
    for rid in c.record_ids:
        if rid not in records:
            reasons.append(f"cited record not in store: {rid}")
    for n in c.numbers:
        rec = records.get(n.record_id)
        if rec is None:
            reasons.append(f"number {n.value:g} cites a record not in store: {n.record_id}")
            continue
        try:
            found = resolve_path(rec.payload, n.path)
        except (KeyError, IndexError, TypeError):
            reasons.append(f"number {n.value:g}: no value at {n.record_id}.{n.path}")
            continue
        if isinstance(found, bool) or not isinstance(found, int | float):
            try:
                found = float(str(found).replace(",", ""))
            except ValueError:
                reasons.append(f"number {n.value:g}: value at {n.record_id}.{n.path} is not numeric ({found!r})")
                continue
        if not _close(n.value, float(found), rel_tol, abs_tol):
            reasons.append(f"number {n.value:g} ≠ {found:g} at {n.record_id}.{n.path}")
            continue
        traced += 1
    declared = {n.value for n in c.numbers}
    warnings = []
    for tok in _FIGURE.findall(c.text):
        try:
            v = float(tok.replace(",", ""))
        except ValueError:
            continue
        if not any(_close(v, d, rel_tol, abs_tol) for d in declared):
            warnings.append(f"figure {tok} appears in the text but is not declared in numbers")
    status = "unsupported" if reasons else "supported"
    return c.model_copy(update={"status": status, "reasons": reasons, "warnings": warnings}), traced


def check_brief(
    brief: EvidenceBrief,
    records: dict[str, SourceRecord],
    *,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-9,
) -> tuple[EvidenceBrief, BriefCheck]:
    """Return the brief with every claim's status set, and the counts."""
    checked: list[Claim] = []
    traced_total = 0
    for c in brief.claims:
        cc, traced = _check_claim(c, records, rel_tol, abs_tol)
        checked.append(cc)
        traced_total += traced
    cited = {rid for c in brief.claims for rid in c.record_ids} | {n.record_id for c in brief.claims for n in c.numbers}
    unresolved = sorted(r for r in cited if r not in records)
    summary_numbers = len(re.findall(r"\d", brief.summary))
    check = BriefCheck(
        claims_total=len(checked),
        supported=sum(c.status == "supported" for c in checked),
        unsupported=sum(c.status == "unsupported" for c in checked),
        numbers_total=sum(len(c.numbers) for c in checked),
        numbers_traced=traced_total,
        record_ids_cited=len(cited),
        record_ids_unresolved=unresolved,
        summary_numbers_unchecked=summary_numbers,
        undeclared_numbers=sum(len(c.warnings) for c in checked),
    )
    return brief.model_copy(update={"claims": checked}), check
