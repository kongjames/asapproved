"""Render an EvidenceBrief and its check as Markdown with footnoted sources and a signature block."""

from __future__ import annotations

from pharmaagents.schema.brief import BriefCheck, EvidenceBrief
from pharmaagents.sources.base import SourceRecord

LIMITS = (
    "This check shows that every cited record exists in the run's store and that every number in a "
    "claim was found, unchanged, at the stated place in a stored record. It does not show that the "
    "records are complete, current or correct, that the claims are the right reading of them, or "
    "that the summary is accurate. FAERS counts are spontaneous reports, not rates. See docs/LIMITS.md."
)


def brief_to_markdown(
    brief: EvidenceBrief,
    check: BriefCheck,
    records: dict[str, SourceRecord],
    *,
    reviewer: str | None = None,
    notes: str | None = None,
    run_date: str | None = None,
) -> str:
    L: list[str] = []
    meta = brief.run_meta
    L.append(f"# Evidence brief — {brief.question}")
    L.append("")
    head = f"**Verdict: {check.verdict}**"
    if meta:
        head += f" · pharmaagents {meta.tool_version} · run {meta.run_id} · provider {meta.provider} ({meta.model_id})"
    if run_date:
        head += f" · checked {run_date}"
    L.append(head)
    L.append("")
    L.append("## Check")
    L.append("")
    L.append("| Claims | Supported | Unsupported | Numbers | Traced | Records cited | Unresolved | Undeclared figures |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    L.append(f"| {check.claims_total} | {check.supported} | {check.unsupported} | {check.numbers_total} | "
             f"{check.numbers_traced} | {check.record_ids_cited} | {len(check.record_ids_unresolved)} | "
             f"{check.undeclared_numbers} |")
    if check.summary_numbers_unchecked:
        L.append("")
        L.append(f"Note: the summary contains {check.summary_numbers_unchecked} digit(s); summary text is not checked.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(brief.summary or "_(empty)_")
    L.append("")
    L.append("## Claims")
    L.append("")
    for c in brief.claims:
        mark = "✅" if c.status == "supported" else "❌"
        cites = " ".join(f"[^{r}]" for r in c.record_ids)
        L.append(f"- {mark} **{c.id}** — {c.text} {cites}".rstrip())
        for n in c.numbers:
            unit = f" {n.unit}" if n.unit else ""
            L.append(f"  - {n.value:g}{unit} ← `{n.record_id}` · `{n.path}`")
        for r in c.reasons:
            L.append(f"  - ⚠ {r}")
        for w in c.warnings:
            L.append(f"  - ⓘ {w}")
    L.append("")
    L.append("## Sources")
    L.append("")
    cited = sorted({rid for c in brief.claims for rid in c.record_ids} | {n.record_id for c in brief.claims for n in c.numbers})
    for rid in cited:
        rec = records.get(rid)
        if rec:
            L.append(f"[^{rid}]: {rec.source} · {rec.url} · retrieved {rec.retrieved_at} · sha256 `{rec.sha256[:16]}…`")
        else:
            L.append(f"[^{rid}]: **not in store**")
    if meta:
        L.append("")
        L.append("## Run")
        L.append("")
        L.append(f"- Created {meta.created_at}; {meta.record_count} records stored; prompt sha256 `{meta.prompt_sha256[:16] + '…' if meta.prompt_sha256 else 'n/a'}`")
        for q in meta.queries:
            L.append(f"- Query `{q.source}` {q.params}")
        if meta.usage:
            L.append(f"- Usage {meta.usage}")
    L.append("")
    L.append("## Limits")
    L.append("")
    L.append(LIMITS)
    L.append("")
    L.append("## Reviewer")
    L.append("")
    L.append(f"- Name and role: {reviewer or '____________________'}")
    L.append(f"- Notes: {notes or ''}")
    L.append("- Data: public sources only, run in a personal capacity.")
    L.append("- Signature and date: ____________________")
    L.append("")
    return "\n".join(L)
