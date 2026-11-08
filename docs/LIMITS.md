# Limits

asapproved answers one narrow question: **does this output still agree with what was approved, and
does it reproduce from the stated source and recipe?** It does not answer:

- whether the recipe is the right analysis (that is the statistical analysis plan's job);
- whether the dataset is correct, complete or current;
- whether any system is "validated" for regulated use. Validation is something a regulated
  organisation does for its own intended use under its own procedures; a tool cannot confer it.

v0.1 checks tables. Comparisons are cell by cell within the tolerances the recipe declares; a table
that matches within tolerance can still be wrong if the recipe is wrong. The planned drift check (v0.2)
will use an informal reference interval built from re-runs, which detects change, not correctness.
