# Data sources

Every source the research agent can cite is public, free, and fetched by an adapter in
`pharmaagents/sources/`. An adapter stores a `SourceRecord` per item: the source name, a stable
record id, the public URL, the UTC time of retrieval, a sha256 of the stored payload, and the
payload itself (only the fields listed below). Briefs may cite only record ids fetched during the
same run (closed world); `postcheck` fails any claim whose record id or number does not resolve.

| Source | Adapter | What is stored | Terms |
|---|---|---|---|
| ClinicalTrials.gov API v2 | `ClinicalTrialsAdapter.search(condition, intervention, status, limit)` | NCT id, brief title, overall status, phases, enrollment count and type, start and completion dates, lead sponsor, conditions, intervention names | US government work, public domain. API: https://clinicaltrials.gov/data-api/api |
| openFDA drug labels (SPL) | `OpenFDAAdapter.labels(generic_name, limit)` | set id, SPL id, version, effective time, openFDA brand/generic/manufacturer/route/application number, and six label sections: boxed warning, indications and usage, dosage and administration, contraindications, warnings and precautions, adverse reactions | https://open.fda.gov/terms/ and https://open.fda.gov/license/ |
| openFDA FAERS counts | `OpenFDAAdapter.event_counts(generic_name, count_field, limit)` | the count field, the top terms with counts, openFDA's last-updated date | same as above |
| CDISC pilot ADaM (pharmaverseadam) | `pharmaagents.data.cdisc_pilot` | ADSL columns used by the worked example | Apache-2.0, see `NOTICE` |

openFDA's disclaimer is stored inside every openFDA record and repeated here: do not rely on
openFDA to make decisions regarding medical care; results are unvalidated. FAERS counts are
spontaneous reports with no denominator and are not incidence rates.

## Offline rule

`PHARMAAGENTS_OFFLINE=1` makes every network call raise. CI sets it. Unit tests run on the fixtures
in `tests/fixtures/`, which are real API responses captured on 2026-11-07 and trimmed to the
stored fields. Live smoke tests run only with `PHARMAAGENTS_LIVE=1`.

## What is deliberately not stored

Full label documents, patient-level FAERS cases, and anything behind a login or a paid API.
PubMed abstracts (v0.2) will store PMIDs and short snippets only.
