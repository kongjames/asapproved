# Limits

pharmaagents answers one narrow question: **does this output still agree with what was approved, and
does it reproduce from the stated source and recipe?** It does not answer:

- whether the recipe is the right analysis (that is the statistical analysis plan's job);
- whether the dataset is correct, complete or current;
- whether any system is "validated" for regulated use. Validation is something a regulated
  organisation does for its own intended use under its own procedures; a tool cannot confer it.

v0.1 checks tables. Comparisons are cell by cell within the tolerances the recipe declares; a table
that matches within tolerance can still be wrong if the recipe is wrong. The planned drift check (v0.2)
will use an informal reference interval built from re-runs, which detects change, not correctness.

## Evidence briefs (`research`, `check-brief`)

- The post-check proves that each cited record is in the run's store and that each declared number
  is at the stated path in that record. It does not prove the records are complete, current or
  correct, or that the claim is the right reading of them.
- Only declared numbers are checked. A figure in claim text without a `numbers` entry is reported
  as a warning. The summary is prose and is not checked at all; the renderer notes when it contains
  digits.
- The research step depends on a language model for planning and drafting. The post-check is
  deterministic, so a brief that passes is one whose figures were found in stored records; it is
  not a statement about the model.
- FAERS counts are spontaneous reports with no denominator. They are not incidence rates and are
  never presented as such.
- Stored records are what the adapter kept (see `docs/DATA_SOURCES.md`), not full source documents.
