"""Generate the README images as SVG. Standard library only; run from the repo root:

    python assets/make_assets.py

The terminal panels embed real CLI output captured from the shipped examples (paths shortened).
Re-run after changing the examples or the CLI text, and commit the result.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent
FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, Consolas, 'Liberation Mono', monospace"
INK = "#1f2328"
MUTED = "#57606a"
LINE = "#d0d7de"
PAPER = "#ffffff"
PANEL = "#f6f8fa"
GREEN = "#1a7f37"
RED = "#cf222e"
BLUE = "#0969da"
AMBER = "#9a6700"


def svg(width: int, height: int, body: list[str], title: str) -> str:
    head = [
        (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">'),
        f"<title id=\"t\">{escape(title)}</title>",
        f'<rect width="{width}" height="{height}" rx="10" fill="{PAPER}" stroke="{LINE}"/>',
    ]
    return "\n".join(head + body + ["</svg>", ""])


def text(x, y, s, *, size=14, fill=INK, weight="normal", family=FONT, anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')


def box(x, y, w, h, label, sub=None, *, fill=PANEL, stroke=LINE, mono=False) -> list[str]:
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
    cy = y + h / 2 + (0 if sub else 5)
    out.append(text(x + w / 2, cy - (8 if sub else 0), label, size=14, weight="600",
                    family=MONO if mono else FONT, anchor="middle"))
    if sub:
        out.append(text(x + w / 2, cy + 12, sub, size=12, fill=MUTED, anchor="middle"))
    return out


def arrow(x1, y1, x2, y2, label=None, *, color=MUTED) -> list[str]:
    out = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.6" marker-end="url(#ah)"/>']
    if label:
        out.append(text((x1 + x2) / 2, min(y1, y2) - 6, label, size=11, fill=MUTED, anchor="middle"))
    return out


MARKER = (f'<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
          f'<path d="M0,0 L8,4 L0,8 z" fill="{MUTED}"/></marker></defs>')


# ---------------------------------------------------------------- schema.svg
def schema() -> str:
    W, H = 960, 430
    b: list[str] = [MARKER]
    b.append(text(24, 34, "pharma-agents — two agents, one job", size=18, weight="700"))
    b.append(text(24, 56, "Does the output still agree with what was approved, and does it reproduce from its source?",
                  size=13, fill=MUTED))

    # Row 1: assurance agent (tables)
    y = 90
    b.append(text(24, y - 8, "Assurance agent · check-table (no API key)", size=13, weight="600", fill=BLUE))
    b += box(24, y, 150, 56, "recipe.yaml", "how the table is derived", mono=True)
    b += box(24, y + 72, 150, 56, "dataset.csv", "public ADSL subset", mono=True)
    b += box(230, y + 36, 170, 56, "re-compute", "independent derivation")
    b += box(460, y, 150, 56, "approved.csv", "reviewed once", mono=True)
    b += box(460, y + 72, 150, 56, "candidate.csv", "migrated / AI-generated", mono=True)
    b += box(670, y + 36, 130, 56, "compare", "cell by cell")
    b += box(840, y + 36, 100, 56, "report.md", "signable", mono=True)
    b += arrow(174, y + 28, 230, y + 58)
    b += arrow(174, y + 100, 230, y + 70)
    b += arrow(400, y + 64, 670, y + 64)
    b.append(text(410, y + 52, "Checks 1 & 3", size=11, fill=MUTED))
    b += arrow(610, y + 28, 670, y + 58)
    b += arrow(610, y + 100, 670, y + 70)
    b.append(text(612, y + 118, "Check 2", size=11, fill=MUTED))
    b += arrow(800, y + 64, 840, y + 64)

    # Row 2: research agent (briefs)
    y = 260
    b.append(text(24, y - 8, "Research agent · research → check-brief (the check never needs a key)",
                  size=13, weight="600", fill=BLUE))
    b += box(24, y, 90, 56, "question")
    b += box(142, y, 120, 56, "plan", "model picks queries")
    b += box(290, y, 170, 56, "fetch + store", "ClinicalTrials.gov, openFDA")
    b += box(488, y, 160, 56, "draft", "model sees records only")
    b += box(676, y, 150, 56, "post-check", "C1 citations · C2 numbers")
    b += box(854, y, 86, 56, "brief.md", mono=True)
    for x1, x2 in ((114, 142), (262, 290), (460, 488), (648, 676), (826, 854)):
        b += arrow(x1, y + 28, x2, y + 28)
    # records store
    b += box(270, y + 86, 210, 44, "records/", "hashed JSON, one per source record", mono=True)
    b += arrow(375, y + 56, 375, y + 86)
    b.append(f'<path d="M480,{y + 108} C 600,{y + 108} 700,{y + 100} 751,{y + 56}" '
             f'fill="none" stroke="{MUTED}" stroke-width="1.6" marker-end="url(#ah)"/>')
    b.append(text(500, y + 136, "the check reads only stored records", size=11, fill=MUTED))

    b.append(text(24, H - 22, "Deterministic parts: re-compute, compare, post-check. Model parts: plan, draft. Exit 1 on any disagreement.",
                  size=12, fill=MUTED))
    return svg(W, H, b, "pharma-agents schema: assurance agent checks tables; research agent produces briefs the same checks verify")


# ---------------------------------------------------------------- role cards
def role_card(title, subtitle, lines, verdict_line, filename_title) -> str:
    W, H = 470, 290
    b: list[str] = []
    b.append(f'<rect x="0" y="0" width="{W}" height="64" rx="10" fill="{PANEL}"/>')
    b.append(f'<rect x="0" y="40" width="{W}" height="24" fill="{PANEL}"/>')
    b.append(text(20, 30, title, size=18, weight="700"))
    b.append(text(20, 52, subtitle, size=12, fill=MUTED))
    y = 96
    for head, body in lines:
        b.append(text(20, y, head, size=13, weight="600", fill=BLUE))
        b.append(text(120, y, body, size=13))
        y += 30
    b.append(f'<line x1="20" y1="{H - 52}" x2="{W - 20}" y2="{H - 52}" stroke="{LINE}"/>')
    b.append(text(20, H - 28, verdict_line, size=12, fill=MUTED))
    return svg(W, H, b, filename_title)


def assurance_card() -> str:
    return role_card(
        "Assurance agent", "the endeavor · v0.1 shipped · deterministic · no API key",
        [("Input", "recipe + dataset + approved table (+ candidate)"),
         ("Does", "re-computes, then compares cell by cell"),
         ("Output", "Markdown report: diffs, trace, limits, signature"),
         ("Catches", "changed values, dropped cells, extra cells"),
         ("Cannot", "judge whether the recipe is the right analysis")],
        "pharma-agents check-table recipe.yaml --approved a.csv --candidate c.csv",
        "Assurance agent role card")


def research_card() -> str:
    return role_card(
        "Research agent", "what the assurance agent checks · v0.1 loop shipped · model-driven",
        [("Input", "a question, in plain words"),
         ("Does", "plans queries, fetches public records, drafts claims"),
         ("Sees", "only the records it stored, when drafting"),
         ("Output", "brief with every number pointed at a stored record"),
         ("Checked by", "C1 citation trace · C2 number trace (deterministic)")],
        "pharma-agents research \"…\" --out runs  ·  pharma-agents check-brief brief.json",
        "Research agent role card")


# ---------------------------------------------------------------- terminal panels
CHECK_TABLE_OUT = [
    ("$", "pharma-agents check-table examples/pharma_tlf/recipe.yaml \\"),
    ("", "    --approved examples/pharma_tlf/approved_sas_table.csv \\"),
    ("", "    --candidate examples/pharma_tlf/candidate_r_table.csv --out report.md"),
    ("PASS", "Check 1 — approved output vs independent re-computation: 80 match, 0 mismatch, 0 missing, 0 unexpected"),
    ("FAIL", "Check 2 — candidate output vs approved output: 78 match, 1 mismatch, 1 missing, 0 unexpected"),
    ("FAIL", "Check 3 — candidate output vs independent re-computation: 78 match, 1 mismatch, 1 missing, 0 unexpected"),
    ("FAIL", "report written to report.md"),
    ("$", "echo $?"),
    ("", "1"),
]

CHECK_BRIEF_OUT = [
    ("$", "pharma-agents check-brief examples/pharma_brief/brief.json --out brief_report.md"),
    ("OK", "c1: supported"),
    ("OK", "c2: supported"),
    ("FAIL", "c3: number 90 ≠ 89 at NCT02401880.enrollment_count"),
    ("FAIL", "c4: cited record not in store: NCT99999999; number 4000 cites a record not in store: NCT99999999"),
    ("OK", "c5: supported"),
    ("FAIL", "report written to brief_report.md"),
    ("$", "echo $?"),
    ("", "1"),
]


def terminal(lines, title) -> str:
    W = 960
    lh = 22
    H = 56 + lh * len(lines) + 16
    b: list[str] = []
    b.append(f'<rect x="1" y="1" width="{W - 2}" height="36" rx="10" fill="{PANEL}"/>')
    b.append(f'<rect x="1" y="20" width="{W - 2}" height="17" fill="{PANEL}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        b.append(f'<circle cx="{20 + i * 20}" cy="19" r="6" fill="{c}"/>')
    b.append(text(W / 2, 24, title, size=12, fill=MUTED, anchor="middle"))
    y = 62
    for tag, s in lines:
        x = 20
        if tag == "$":
            b.append(text(x, y, "$", size=13, fill=MUTED, family=MONO))
            x += 16
        elif tag in ("PASS", "OK"):
            b.append(text(x, y, tag, size=13, fill=GREEN, weight="700", family=MONO))
            x += 54
        elif tag == "FAIL":
            b.append(text(x, y, tag, size=13, fill=RED, weight="700", family=MONO))
            x += 54
        b.append(text(x, y, s, size=13, family=MONO))
        y += lh
    return svg(W, H, b, title)


# ---------------------------------------------------------------- report panel
def report_panel() -> str:
    W, H = 960, 470
    b: list[str] = []
    b.append(text(24, 36, "Validation report — Table 14.1.1 — Demographics, safety population (CDISC pilot ADSL)",
                  size=16, weight="700"))
    b.append(text(24, 60, "Verdict: ", size=13, fill=MUTED))
    b.append(text(82, 60, "FAIL", size=13, fill=RED, weight="700"))
    b.append(text(122, 60, "· pharma-agents 0.1.2 · run date 2026-11-07", size=13, fill=MUTED))

    # summary table
    y = 96
    b.append(text(24, y, "Summary", size=14, weight="600"))
    cols = [("Check", 24, 400), ("Cells", 430, 50), ("Match", 490, 50), ("Mismatch", 550, 70),
            ("Missing", 630, 60), ("Unexpected", 700, 80), ("Result", 800, 60)]
    y += 26
    b.append(f'<rect x="20" y="{y - 16}" width="{W - 40}" height="24" fill="{PANEL}"/>')
    for name, x, _w in cols:
        b.append(text(x, y, name, size=12, weight="600"))
    rows = [
        ("Check 1 — approved output vs independent re-computation", "80", "80", "0", "0", "0", "PASS"),
        ("Check 2 — candidate output vs approved output", "80", "78", "1", "1", "0", "FAIL"),
        ("Check 3 — candidate output vs independent re-computation", "80", "78", "1", "1", "0", "FAIL"),
    ]
    for r in rows:
        y += 26
        b.append(f'<line x1="20" y1="{y - 18}" x2="{W - 20}" y2="{y - 18}" stroke="{LINE}"/>')
        for (name, x, _w), v in zip(cols, r):
            color = GREEN if v == "PASS" else RED if v == "FAIL" else INK
            b.append(text(x, y, v, size=12, fill=color, weight="600" if v in ("PASS", "FAIL") else "normal"))

    # inputs
    y += 44
    b.append(text(24, y, "Inputs", size=14, weight="600"))
    y += 24
    b.append(text(24, y, "Dataset: data/adsl.csv (sha256 4dc82ac20cd79b42…), 306 rows; population filter SAFFL == 'Y' → 254 rows",
                  size=12, family=MONO))
    y += 20
    b.append(text(24, y, "Columns: TRT01A → Placebo, Xanomeline High Dose, Xanomeline Low Dose, Total", size=12, family=MONO))

    # diff table
    y += 40
    b.append(text(24, y, "Check 2 — candidate output vs approved output", size=14, weight="600"))
    y += 22
    b.append(text(24, y, "2 cell(s) do not agree:", size=12, fill=MUTED))
    dcols = [("Variable", 24), ("Category", 120), ("Statistic", 220), ("Column", 320), ("Reference", 520),
             ("Compared", 620), ("Delta", 720), ("Status", 800)]
    y += 26
    b.append(f'<rect x="20" y="{y - 16}" width="{W - 40}" height="24" fill="{PANEL}"/>')
    for name, x in dcols:
        b.append(text(x, y, name, size=12, weight="600"))
    drows = [("AGE", "", "mean", "Xanomeline High Dose", "73.78", "74.48", "0.7", "mismatch"),
             ("SEX", "F", "pct", "Placebo", "61.63", "", "", "missing")]
    for r in drows:
        y += 26
        b.append(f'<line x1="20" y1="{y - 18}" x2="{W - 20}" y2="{y - 18}" stroke="{LINE}"/>')
        for (name, x), v in zip(dcols, r):
            b.append(text(x, y, v, size=12, fill=RED if v in ("mismatch", "missing") else INK, family=MONO))

    b.append(text(24, H - 20, "Then: Check 3, Trace (how each row block was derived), Limits, Reviewer signature block.  Full file: examples/pharma_tlf/expected_report.md",
                  size=11, fill=MUTED))
    return svg(W, H, b, "Excerpt of the validation report for the shipped example")


OUTPUTS = {
    "schema.svg": schema,
    "assurance-agent.svg": assurance_card,
    "research-agent.svg": research_card,
    "cli-check-table.svg": lambda: terminal(CHECK_TABLE_OUT, "pharma-agents check-table — shipped example, two planted defects"),
    "cli-check-brief.svg": lambda: terminal(CHECK_BRIEF_OUT, "pharma-agents check-brief — shipped example, two planted faults"),
    "report-check-table.svg": report_panel,
}


def render_all() -> dict[str, str]:
    return {name: fn() for name, fn in OUTPUTS.items()}


if __name__ == "__main__":
    for name, content in render_all().items():
        (HERE / name).write_text(content, encoding="utf-8")
        print(f"wrote assets/{name} ({len(content)} bytes)")
