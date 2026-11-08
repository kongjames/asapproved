# Example — validating a demographics table (CDISC pilot ADSL)

## What This Shows
A first programmer produced and got approval for a demographics table (`approved_sas_table.csv`). A
second implementation — a migration to R, or code an AI assistant wrote — produced
`candidate_r_table.csv`. `asapproved check-table` re-computes the table independently from the public
dataset and the recipe, then compares all three cell by cell and writes a report a reviewer can sign.

## Features
- Re-computation from source (`recipe.yaml` + `data/adsl.csv`), so the check does not trust either table.
- Three comparisons: approved vs re-computed, candidate vs approved, candidate vs re-computed.
- Tolerances declared in the recipe, not hidden in code.
- A trace appendix in reviewer's-guide style and a signature block.

## How To Run
```bash
pip install asapproved
asapproved check-table examples/pharma_tlf/recipe.yaml \
  --approved examples/pharma_tlf/approved_sas_table.csv \
  --candidate examples/pharma_tlf/candidate_r_table.csv \
  --reviewer "Your Name, Your Role (personal capacity)" \
  --out report.md
```
Exit code 0 means every check passed; 1 means at least one cell disagreed. The candidate here is
built with two deliberate defects (see `make_example.py`), so expect `FAIL` with 2 flagged cells.

## How It Works
`data/adsl.csv` is a column subset of ADSL from the pharmaverse `pharmaverseadam` package
(Apache-2.0; see `NOTICE`). The recipe says: safety population (`SAFFL == 'Y'`), columns by `TRT01A`
plus Total, continuous summary of AGE, counts and percents for SEX, RACE and AGEGR1. Tables are in
long format with columns `variable, category, statistic, group, value`, one row per cell.
