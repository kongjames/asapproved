"""Render a ValidationReport as Markdown a reviewer can read, annotate, sign and date."""

from __future__ import annotations

from asapproved.schema.report import ValidationReport

LIMITS = (
    "This report shows whether the tables agree with each other and with an independent "
    "re-computation from the stated dataset and recipe. It does not show that the recipe is the "
    "right analysis, that the dataset is correct, or that any system is validated for regulated "
    "use. See docs/LIMITS.md and docs/REGULATORY_CONTEXT.md."
)


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def to_markdown(r: ValidationReport, max_rows: int = 200) -> str:
    L: list[str] = []
    L.append(f"# Validation report — {r.recipe_title or r.recipe_name}")
    L.append("")
    L.append(f"**Verdict: {r.verdict}** · {r.tool} {r.tool_version} · run date {r.run_date}")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append("| Check | Reference | Compared | Cells | Match | Mismatch | Missing | Unexpected | Result |")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---|")
    for c in r.checks:
        L.append(f"| {c.name} | {c.reference_label} | {c.other_label} | {c.cells_compared} | {c.matches} | "
                 f"{c.mismatches} | {c.missing} | {c.unexpected} | {'PASS' if c.passed else 'FAIL'} |")
    L.append("")
    L.append("## Inputs")
    L.append("")
    L.append(f"- Dataset: `{r.dataset_path}` (sha256 `{r.dataset_sha256[:16]}…`), {r.rows_total} rows; "
             f"population filter `{r.population_filter or 'none'}` → {r.rows_in_population} rows")
    L.append(f"- Columns: `{r.group_by}` → {', '.join(r.groups)}")
    for label, val in r.inputs.items():
        L.append(f"- {label}: `{val}`")
    L.append("")
    for c in r.checks:
        rows = r.diffs.get(c.name, [])
        L.append(f"## {c.name}")
        L.append("")
        if not rows:
            L.append("All cells agree within tolerance.")
        else:
            L.append(f"{len(rows)} cell(s) do not agree:")
            L.append("")
            L.append("| Variable | Category | Statistic | Column | Reference | Compared | Delta | Status |")
            L.append("|---|---|---|---|---:|---:|---:|---|")
            for d in rows[:max_rows]:
                L.append(f"| {d['variable']} | {d['category']} | {d['statistic']} | {d['group']} | "
                         f"{_fmt(d['reference'])} | {_fmt(d['other'])} | {_fmt(d['delta'])} | {d['status']} |")
            if len(rows) > max_rows:
                L.append(f"| … | | | | | | | {len(rows) - max_rows} more |")
        L.append("")
    L.append("## Trace (how each row block was derived)")
    L.append("")
    L.append("| Variable | Type | Derivation | Population | Columns |")
    L.append("|---|---|---|---|---|")
    for t in r.trace:
        L.append(f"| {t['label']} (`{t['variable']}`) | {t['type']} | {t['derivation']} | `{t['population']}` | `{t['columns']}` |")
    L.append("")
    L.append("## Limits")
    L.append("")
    L.append(LIMITS)
    L.append("")
    L.append("## Reviewer")
    L.append("")
    L.append(f"- Name and role: {r.reviewer or '_______________________________'}")
    L.append("- Capacity: personal; public data only; no patient or employer data")
    L.append(f"- Notes: {r.notes or ''}")
    L.append("- Signature: _______________________________  Date: ____________")
    L.append("")
    return "\n".join(L)
