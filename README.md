# pharma-agents

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24102334.svg)](https://doi.org/10.5281/zenodo.24102334)
[![CI](https://github.com/kongjames/pharma-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/kongjames/pharma-agents/actions/workflows/ci.yml)

**Check that an automated analysis still does what it was shown to do when it was approved.**

In clinical statistical programming an output is validated once: a second programmer derives the
ADaM dataset or the table, listing or figure independently, the two results are compared, and the
approved version goes into the submission. Then the legacy SAS program is migrated to R, an AI
assistant rewrites a derivation, or the analysis dataset refreshes, and the output keeps looking
confident. `pharma-agents` applies the validation discipline the field already has to those new
outputs: it re-computes the table from the analysis dataset and a machine-readable recipe, compares
the approved output and the new output cell by cell within declared tolerances, and writes a
validation report, with a reviewer's-guide-style trace of every derivation, that a reviewer can
read, sign and date. The first worked example is a demographics table (the Table 14.1.1 pattern)
built on public CDISC pilot ADSL data.

> **Scope and disclaimer.** `pharma-agents` is a research and education tool. It is not a validated
> system under 21 CFR Part 11 or GAMP 5, it is not endorsed by the FDA or any regulator, and it is not
> medical advice. It uses public data only; never give it patient or employer data. Validation of a
> system for regulated use is something your organisation does under its own procedures; this tool
> can support that work but cannot perform it. See [docs/REGULATORY_CONTEXT.md](docs/REGULATORY_CONTEXT.md)
> and [docs/LIMITS.md](docs/LIMITS.md).

## Who this is for

Statistical programmers, biostatisticians and the people who review their work, in these situations:

| You have | `pharma-agents` gives you |
|---|---|
| An approved SAS table and the same table from the migrated R program | A cell-by-cell comparison of the two, plus an independent re-computation of both from the ADaM dataset, so a difference is attributed to the migration and not to the approved output |
| A derivation an AI coding assistant generated or rewrote | Proof that its output agrees with the approved output and reproduces from source, or the exact cells where it does not |
| A refreshed analysis dataset and a re-run TLF | The same three checks, with the dataset's hash and row counts on the report |
| A QC step that needs a record | A Markdown validation report with a summary table, every disagreeing cell, a trace of each derivation (variable, derivation, population, columns) and a signature block |
| A drug-information question answered from public records | A brief in which every number points at a stored ClinicalTrials.gov or openFDA record, checked by the same deterministic trace |

The vocabulary is the field's. A **recipe** is the analysis specification for one output: population
flag, treatment variable, which variables are summarised and how, tolerances. The **dataset** is an
ADaM dataset such as ADSL. The **approved** table is the output that passed QC. The **candidate** is
the new output. The **trace** is what a reviewer's guide asks for: how each row block was derived.
Tables travel as CSV in long format, so SAS and R users export and never touch Python.

It does not replace an organisation's validation procedures and it does not make anything
"validated". It gives the person running those procedures a deterministic, repeatable check and a
record of it.

## How it works

![Schema: the assurance agent re-computes and compares tables; the research agent produces briefs that the same deterministic checks verify](assets/schema.svg)

Two agents, one job. What each check computes, step by step, is in [docs/METHOD.md](docs/METHOD.md).

<table><tr>
<td><img src="assets/assurance-agent.svg" alt="Assurance agent role card" width="470"></td>
<td><img src="assets/research-agent.svg" alt="Research agent role card" width="470"></td>
</tr></table>

### Assurance agent (v0.1 — shipped, no API key needed)
Given a **recipe** (how a table is derived) and a **dataset**, it:
1. re-computes the table from source, the way a second programmer would;
2. compares the **approved** output against that re-computation;
3. compares a **candidate** output (migrated code, AI-generated code, a refreshed run) against both;
4. writes a Markdown report: summary, every disagreeing cell, a trace of each derivation, limits,
   and a signature block.

### Research agent (loop shipped; re-run baseline and drift flag in v0.2)
Answers a question from public sources only (ClinicalTrials.gov, openFDA, PubMed) and produces a
brief in which every number and claim points at a stored source record. The assurance agent then
checks that brief the same way it checks a table, and a baseline of re-runs lets it flag change
beyond normal day-to-day variation.

Shipped so far: the loop itself (`pharma-agents research`: plan → fetch → draft → post-check, about a
hundred lines in `pharma_agents/research/agent.py`), the provider interface (`pharma_agents/llm/`, one
`complete()` call; Anthropic and a scripted fake), the source adapters with stored, hashed records
(`pharma_agents/sources/`: ClinicalTrials.gov API v2, openFDA labels and FAERS counts), and the
deterministic post-check (`pharma-agents check-brief`). The model sees only the records the adapters
stored; the check then resolves every citation and every number back to a stored record. What each
adapter stores and under which terms: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md). A worked
example with two deliberate faults: [examples/pharma_brief](examples/pharma_brief/README.md).
Still to come: the re-run baseline and drift flag.

![Terminal output of pharma-agents check-brief on the shipped example: c3 fails on a wrong enrollment figure, c4 on a record not in the store](assets/cli-check-brief.svg)

## Start using

| You want to | Run |
|---|---|
| See it work on the shipped example | `pharma-agents check-table examples/pharma_tlf/recipe.yaml --approved examples/pharma_tlf/approved_sas_table.csv --candidate examples/pharma_tlf/candidate_r_table.csv` |
| Create an approved baseline from a recipe | `pharma-agents recompute my_recipe.yaml --out approved.csv` |
| Check a new output against it | `pharma-agents check-table my_recipe.yaml --approved approved.csv --candidate new.csv --reviewer "Name, Role (personal capacity)"` |
| Check the shipped example brief (no key, no network) | `pharma-agents check-brief examples/pharma_brief/brief.json` |
| Answer a question from public records and check the brief | `pharma-agents research "What do public records say about X?" --out runs` (needs `pharma-agents[llm]` and an Anthropic credential) |
| Leave a public record of your run | [docs/ADOPTER_WORKFLOW.md](docs/ADOPTER_WORKFLOW.md) |

Exit code `0` = all checks pass; `1` = at least one cell disagrees or one claim is unsupported.

## Worked example: Table 14.1.1 demographics, approved output vs a re-implementation

`examples/pharma_tlf/` holds a recipe (safety population `SAFFL = Y`, by actual treatment `TRT01A`,
AGE summary statistics and SEX/RACE/AGEGR1 counts and percentages), a column subset of the public
CDISC pilot **ADSL** dataset (via [pharmaverseadam](https://github.com/pharmaverse/pharmaverseadam),
Apache-2.0), an approved table standing in for the QC'd SAS output, and a candidate table standing in
for a migrated or AI-generated re-implementation, with two deliberate defects: one changed mean and
one dropped cell. Both tables were produced for the example; neither came from SAS or R. The expected report is checked in:
[examples/pharma_tlf/expected_report.md](examples/pharma_tlf/expected_report.md).

![Terminal output of pharma-agents check-table on the shipped example: Check 1 passes, Checks 2 and 3 fail with one mismatch and one missing cell](assets/cli-check-table.svg)

![Excerpt of the validation report: summary table, inputs with dataset hash and row counts, and the two disagreeing cells](assets/report-check-table.svg)

The images are SVG generated from the real CLI output and report by `assets/make_assets.py`; a
test keeps them in step with the code.

## Install

```bash
pip install pharma-agents            # library + CLI
pip install 'pharma-agents[data]'    # + pyreadr, to re-export the pilot data from upstream
pip install 'pharma-agents[llm]'     # + the Anthropic SDK, for the research agent (the checks never need it)
```
Python 3.11 or later. Development: `uv sync --extra dev && uv run pytest`.

## Table format

Tables are **long**: one row per cell, columns `variable, category, statistic, group, value`. Export
from SAS (`PROC EXPORT` of a stacked dataset) or R (`write.csv` of a pivoted data frame) in that shape
and the comparison works regardless of the language that produced it. XPT is not read directly yet;
convert to CSV first.

## Who uses it

See [ADOPTERS.md](ADOPTERS.md). Add a row by pull request after filing a
[validation report](.github/ISSUE_TEMPLATE/validation-report.yml).

## Tests

`uv run pytest`: unit tests for re-computation, comparison, the provider interface, the source
adapters (on captured fixtures), the research loop (with the scripted provider) and the post-check;
golden tests that both shipped examples reproduce their expected reports byte for byte. CI sets
`PHARMA_AGENTS_OFFLINE=1` and never calls a network or a language model; live smoke tests run only
with `PHARMA_AGENTS_LIVE=1`.

## AI disclosure, citation, licence

Built with AI assistance and reviewed line by line: [AI_DISCLOSURE.md](AI_DISCLOSURE.md).
Cite with [CITATION.cff](CITATION.cff); the archive of every release is at
[doi:10.5281/zenodo.24102334](https://doi.org/10.5281/zenodo.24102334) (this version: 10.5281/zenodo.24102578). Apache-2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE).
