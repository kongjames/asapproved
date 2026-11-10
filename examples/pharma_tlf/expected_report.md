# Validation report — Table 14.1.1 — Demographics, safety population (CDISC pilot ADSL)

**Verdict: FAIL** · pharma-agents 0.1.2 · run date 2026-11-07

## Summary

| Check | Reference | Compared | Cells | Match | Mismatch | Missing | Unexpected | Result |
|---|---|---|---:|---:|---:|---:|---:|---|
| Check 1 — approved output vs independent re-computation | re-computed | approved | 80 | 80 | 0 | 0 | 0 | PASS |
| Check 2 — candidate output vs approved output | approved | candidate | 80 | 78 | 1 | 1 | 0 | FAIL |
| Check 3 — candidate output vs independent re-computation | re-computed | candidate | 80 | 78 | 1 | 1 | 0 | FAIL |

## Inputs

- Dataset: `data/adsl.csv` (sha256 `4dc82ac20cd79b42…`), 306 rows; population filter `SAFFL == 'Y'` → 254 rows
- Columns: `TRT01A` → Placebo, Xanomeline High Dose, Xanomeline Low Dose, Total
- Approved table: `approved_sas_table.csv (sha256 cb1e6ff6012c3cfb…)`
- Candidate table: `candidate_r_table.csv (sha256 844a87b898d09e8a…)`

## Check 1 — approved output vs independent re-computation

All cells agree within tolerance.

## Check 2 — candidate output vs approved output

2 cell(s) do not agree:

| Variable | Category | Statistic | Column | Reference | Compared | Delta | Status |
|---|---|---|---|---:|---:|---:|---|
| AGE |  | mean | Xanomeline High Dose | 73.78 | 74.48 | 0.7 | mismatch |
| SEX | F | pct | Placebo | 61.63 |  |  | missing |

## Check 3 — candidate output vs independent re-computation

2 cell(s) do not agree:

| Variable | Category | Statistic | Column | Reference | Compared | Delta | Status |
|---|---|---|---|---:|---:|---:|---|
| AGE |  | mean | Xanomeline High Dose | 73.78 | 74.48 | 0.7 | mismatch |
| SEX | F | pct | Placebo | 61.63 |  |  | missing |

## Trace (how each row block was derived)

| Variable | Type | Derivation | Population | Columns |
|---|---|---|---|---|
| Age (years) (`AGE`) | continuous | n, mean, sd, median, min, max of AGE (non-missing values; sd uses n-1) | `SAFFL == 'Y'` | `TRT01A` |
| Sex (`SEX`) | categorical | count and percent of SEX per category; percent denominator = subjects in the column | `SAFFL == 'Y'` | `TRT01A` |
| Race (`RACE`) | categorical | count and percent of RACE per category; percent denominator = subjects in the column | `SAFFL == 'Y'` | `TRT01A` |
| Age group (`AGEGR1`) | categorical | count and percent of AGEGR1 per category; percent denominator = subjects in the column | `SAFFL == 'Y'` | `TRT01A` |

## Limits

This report shows whether the tables agree with each other and with an independent re-computation from the stated dataset and recipe. It does not show that the recipe is the right analysis, that the dataset is correct, or that any system is validated for regulated use. See docs/LIMITS.md and docs/REGULATORY_CONTEXT.md.

## Reviewer

- Name and role: Example Reviewer, Statistical Programmer (personal capacity)
- Capacity: personal; public data only; no patient or employer data
- Notes: 
- Signature: _______________________________  Date: ____________
