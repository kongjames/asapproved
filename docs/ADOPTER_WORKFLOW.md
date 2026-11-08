# Running asapproved and leaving a record (about 45 minutes, public data, personal capacity)

1. Install: `pip install asapproved` (or use the Dockerfile).
2. Run the shipped example, or point the recipe at your own public dataset and tables:
   ```bash
   asapproved check-table examples/pharma_tlf/recipe.yaml \
     --approved examples/pharma_tlf/approved_sas_table.csv \
     --candidate examples/pharma_tlf/candidate_r_table.csv \
     --reviewer "Your Name, Your Role (personal capacity)" --out report.md
   ```
3. Optional: write your own candidate table (for example, re-derive the table in R in a few minutes
   and export it in long format) and re-run.
4. Read `report.md`. Add notes on what the tool caught, missed or got wrong. Sign and date it.
5. Open a GitHub issue with the **Validation report** template and attach the report.
6. Add one row to `ADOPTERS.md` by pull request. Naming your organisation is optional.

No patient data, no employer data. The record you leave is yours, in your own words.
