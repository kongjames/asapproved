# Evidence brief — What do public records say about metformin hydrochloride in type 2 diabetes: completed trials, the label's boxed warning, and the most reported adverse events?

**Verdict: FAIL** · asapproved 0.1.0.dev0 · run example · provider hand-written (not model output) (n/a) · checked 2026-11-07

## Check

| Claims | Supported | Unsupported | Numbers | Traced | Records cited | Unresolved | Undeclared figures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 3 | 2 | 5 | 3 | 5 | 1 | 2 |

## Summary

Three completed trials of metformin in the stated condition were retrieved, one current label for a sitagliptin and metformin combination product, and the most frequently reported reaction terms from spontaneous reports. The label carries a boxed warning for lactic acidosis.

## Claims

- ✅ **c1** — NCT00899470, a phase 1 bioequivalence study of saxagliptin and metformin formulations, enrolled 24 participants. [^NCT00899470]
  - 24 participants ← `NCT00899470` · `enrollment_count`
  - ⓘ figure 1 appears in the text but is not declared in numbers
- ✅ **c2** — The retrieved label (version 6, effective 2026-08-12) has a boxed warning for lactic acidosis. [^0098dec4-f0e5-45d5-8aa4-5d0faf9ab142]
  - 6 ← `0098dec4-f0e5-45d5-8aa4-5d0faf9ab142` · `version`
- ❌ **c3** — NCT02401880 enrolled 90 participants. [^NCT02401880]
  - 90 participants ← `NCT02401880` · `enrollment_count`
  - ⚠ number 90 ≠ 89 at NCT02401880.enrollment_count
- ❌ **c4** — A separate registry entry reports a phase 3 outcome study with 4,000 participants. [^NCT99999999]
  - 4000 participants ← `NCT99999999` · `enrollment_count`
  - ⚠ cited record not in store: NCT99999999
  - ⚠ number 4000 cites a record not in store: NCT99999999
  - ⓘ figure 3 appears in the text but is not declared in numbers
- ✅ **c5** — In spontaneous reports, the most reported reaction term is diarrhoea with 6342 reports; these are report counts, not rates. [^faers-count:metformin-hydrochloride:patient.reaction.reactionmeddrapt.exact]
  - 6342 reports ← `faers-count:metformin-hydrochloride:patient.reaction.reactionmeddrapt.exact` · `terms[0].count`

## Sources

[^0098dec4-f0e5-45d5-8aa4-5d0faf9ab142]: openfda.label · https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=0098dec4-f0e5-45d5-8aa4-5d0faf9ab142 · retrieved 2026-11-07T22:00:00+00:00 · sha256 `99567a6244277994…`
[^NCT00899470]: clinicaltrials.gov · https://clinicaltrials.gov/study/NCT00899470 · retrieved 2026-11-07T22:00:00+00:00 · sha256 `2952ba443f891ea1…`
[^NCT02401880]: clinicaltrials.gov · https://clinicaltrials.gov/study/NCT02401880 · retrieved 2026-11-07T22:00:00+00:00 · sha256 `a1ed86aefd0cd7cc…`
[^NCT99999999]: **not in store**
[^faers-count:metformin-hydrochloride:patient.reaction.reactionmeddrapt.exact]: openfda.event · https://api.fda.gov/drug/event.json?search=patient.drug.openfda.generic_name%3A%22metformin%20hydrochloride%22&count=patient.reaction.reactionmeddrapt.exact&limit=5 · retrieved 2026-11-07T22:00:00+00:00 · sha256 `08928c979dac952b…`

## Run

- Created 2026-11-07T22:00:00+00:00; 5 records stored; prompt sha256 `n/a`
- Query `clinicaltrials.search` {'condition': 'type 2 diabetes', 'intervention': 'metformin', 'status': 'COMPLETED', 'limit': 3}
- Query `openfda.labels` {'generic_name': 'metformin hydrochloride', 'limit': 1}
- Query `openfda.event_counts` {'generic_name': 'metformin hydrochloride', 'limit': 5}

## Limits

This check shows that every cited record exists in the run's store and that every number in a claim was found, unchanged, at the stated place in a stored record. It does not show that the records are complete, current or correct, that the claims are the right reading of them, or that the summary is accurate. FAERS counts are spontaneous reports, not rates. See docs/LIMITS.md.

## Reviewer

- Name and role: Example Reviewer (personal capacity)
- Notes: 
- Data: public sources only, run in a personal capacity.
- Signature and date: ____________________
