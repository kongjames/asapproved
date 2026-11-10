# Changelog

## 0.1.1 — 2026-11-10

- **Renamed** from `asapproved` to `pharmaagents`: package, CLI command, environment variables
  (`PHARMAAGENTS_OFFLINE`, `PHARMAAGENTS_LIVE`), citation metadata. No behaviour change. The 0.1.0
  tag and release keep the old name as history.
- Archived at Zenodo: concept DOI 10.5281/zenodo.24102334, this version 10.5281/zenodo.24102335.
- README rewritten for clinical statistical programmers: who it is for, the vocabulary map, and
  what the example tables are and are not.

## 0.1.0 — 2026-11-10

First release.

- **Assurance agent, tables.** `pharmaagents recompute` derives a table from a recipe and dataset;
  `pharmaagents check-table` compares the approved output and a candidate against that
  re-computation and against each other, cell by cell within declared tolerances, and writes a
  Markdown report with a trace appendix and a signature block. No API key, no network.
- **Research agent, briefs.** `pharmaagents research` plans queries against ClinicalTrials.gov
  (API v2) and openFDA (labels, FAERS counts), stores every record with a SHA-256, drafts claims
  from the stored records only, and post-checks them. `pharmaagents check-brief` re-runs the
  deterministic C1 citation trace and C2 number trace on any saved brief without a model or a
  network. Provider interface with an Anthropic implementation and a scripted fake for tests.
- **Worked examples.** `examples/pharma_tlf` (public CDISC pilot ADSL via pharmaverseadam, a
  candidate with two planted defects) and `examples/pharma_brief` (hand-written brief over
  captured records with two planted faults). Both expected reports are pinned by golden tests.
- **Docs.** Method, limits, regulatory context with the never-claim list, data sources, adopter
  workflow, AI disclosure, citation metadata.
- CI runs offline on Python 3.11–3.13 and never calls a network or a model.

Not in this release: the re-run baseline and drift flag, PubMed, a model-judged check.
