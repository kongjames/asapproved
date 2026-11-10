# Method — what each check computes

This page describes, in the order the reports print them, what `pharmaagents` computes and what a
result means. Everything here is deterministic: given the same files, the same checks produce the
same report. The regulatory documents these checks resemble are listed in
[REGULATORY_CONTEXT.md](REGULATORY_CONTEXT.md); what the checks do not show is in
[LIMITS.md](LIMITS.md). This page does not repeat either.

## Part A — tables (`check-table`, `recompute`)

### A1. Inputs

| Input | What it is | Where it is recorded in the report |
|---|---|---|
| **Recipe** (`recipe.yaml`) | The analysis specification in machine-readable form: dataset path, population filter, grouping column, the variables to summarise and how, tolerances, decimals | Title, "Inputs", "Trace" |
| **Dataset** (CSV) | The analysis dataset the recipe names, one row per subject | Path, SHA-256, row count before and after the population filter |
| **Approved table** (CSV, long format) | The output that was reviewed and approved | Path and SHA-256 |
| **Candidate table** (CSV, long format, optional) | The new output: migrated code, AI-generated code, a refreshed run | Path and SHA-256 |

Tables are **long**: one row per cell, columns `variable, category, statistic, group, value`. The
first four columns are the cell's key and must be unique within a table; a duplicate key stops the
run with an error rather than silently picking one row. Key values are compared as trimmed strings.

### A2. Independent re-computation

The tool derives the table again from the dataset and the recipe, without reading either table
first. This is the step a second programmer performs in clinical statistical programming.

1. **Population.** Rows are filtered with the recipe's `population.filter`, a pandas `query`
   expression (for example `SAFFL == 'Y'`). No filter means all rows.
2. **Columns.** Rows are grouped by `group_by`, groups sorted by value. If `include_total` is true,
   a column named `total_label` holds every row in the population.
3. **Continuous variables** (`type: continuous`): for each column and each statistic in `stats`,
   over non-missing values after numeric coercion. `n` counts non-missing values; `nmiss` counts
   missing; `sd` uses the n−1 denominator and is empty when n ≤ 1; `q1`/`q3` are pandas quantiles
   (linear interpolation).
4. **Categorical variables** (`type: categorical`): for each column and each category, `n` (count)
   and `pct` (100 × count ÷ subjects in the column). Category order is `categories` if given,
   otherwise observed values sorted. A `Missing` category is appended when any value is missing.
5. **Rounding.** Every value is rounded to `decimals` places. Rounding happens once, here, so the
   approved and candidate tables are expected to be rounded the same way.

The trace table in the report states, per variable, the derivation sentence, the population
filter and the grouping column that step produced.

### A3. Cell comparison

Two tables are compared cell by cell, keyed on `(variable, category, statistic, group)`. Every cell
of either table appears exactly once in the result with one of four statuses:

| Status | Meaning |
|---|---|
| `match` | Both tables have the cell and the values agree within tolerance |
| `mismatch` | Both have the cell; the values disagree |
| `missing` | The reference has the cell; the compared table does not |
| `unexpected` | The compared table has a cell the reference does not |

**Tolerance.** Two numeric values agree when `|other − reference| ≤ abs_tol`, or, if
`numeric_rel` is set and the reference is not zero, when `|other − reference| / |reference| ≤
numeric_rel`. `abs_tol` is `tolerances.pct_abs` for the `pct` statistic when it is set, otherwise
`tolerances.numeric_abs`. Defaults are zero, so with no tolerances declared only exact agreement
matches. Two non-numeric values agree when their trimmed strings are equal. A numeric value against
a non-numeric or empty one is a mismatch. The report prints `delta = other − reference` for
numeric pairs.

### A4. The three checks

| Check | Reference | Compared | Question it answers |
|---|---|---|---|
| 1 | re-computed | approved | Does the approved output reproduce from the stated source and recipe? |
| 2 | approved | candidate | Does the new output agree with what was approved? |
| 3 | re-computed | candidate | Does the new output reproduce from source? |

Checks 2 and 3 run only when a candidate is given. A check **passes** when it has zero
mismatches, zero missing and zero unexpected cells. The report's **verdict is PASS only when every
check passes**; the CLI exits `1` otherwise. A failing Check 1 means the approved table itself does
not reproduce; that is reported, not excused, because the candidate is then being compared to a
baseline that does not follow from its own recipe.

### A5. The report

Sections in order: verdict line (tool version, run date) · Summary table (one row per check, with
cell counts) · Inputs (paths relative to the recipe folder, SHA-256 prefixes, row counts, columns)
· one section per check listing every non-matching cell (at most 200 rows per check, then a count
of the rest) · Trace · Limits · Reviewer block (name and role, capacity line, notes, signature and
date). Paths are shown relative to the recipe's folder so the same run produces the same report on
any machine.

## Part B — evidence briefs (`research`, `check-brief`)

### B1. How a brief is produced (`research`)

1. **Plan.** The model receives the question and returns a list of queries, each naming one of the
   allowed source calls (`clinicaltrials.search`, `openfda.labels`, `openfda.event_counts`) with
   its parameters. Queries to any other source are dropped; result limits are capped per source
   (10, 2, 10).
2. **Fetch.** The adapters run the queries and store each result as a `SourceRecord` with its
   source, record id, URL, retrieval time, a SHA-256 of the canonical JSON payload, and the payload
   itself. Records are de-duplicated by `source:record_id`. What each adapter keeps is listed in
   [DATA_SOURCES.md](DATA_SOURCES.md).
3. **Draft.** The model receives **only** the stored records (id, source, payload) and must return
   a summary and claims. Each claim carries the record ids it rests on and a list of numbers, each
   with a value, unit, record id and the dotted path to that value inside the record. The question
   is not shown again at this step.
4. **Check.** The post-check below runs on the draft and the stored records. The run folder holds
   the records, `brief.json`, `check.json` and `brief.md`.

The run block in the report records the tool version, provider, model id, token usage, the queries
that were run, the record count and a SHA-256 over the prompts and schemas, so a later difference
can be attributed to the sources, the model or the prompt.

### B2. The post-check (`check-brief`)

No model and no network are involved. For every claim:

| Check | Rule | Failure reason printed |
|---|---|---|
| **C1 citation trace** | The claim cites at least one record id, and every cited id is in the run's record store | `no source record cited`; `cited record not in store: <id>` |
| **C2 number trace** | For every declared number, the record exists, the dotted path resolves inside its payload, the value there is numeric (after removing thousands separators) and equals the declared value within tolerance | `number V cites a record not in store`; `number V: no value at <id>.<path>`; `… is not numeric`; `number V ≠ W at <id>.<path>` |

A claim is **supported** when it has no failure reason, otherwise **unsupported**. The brief's
verdict is PASS only when no claim is unsupported; the CLI exits `1` otherwise.

**Path syntax.** `a.b[0].c` means key `a`, then key `b`, then list index 0, then key `c`. A path
that does not exist is a failure, not a skip.

**Tolerance.** `|declared − found| ≤ max(abs_tol, rel_tol × |found|)` with defaults
`rel_tol = 1e-6`, `abs_tol = 1e-9`: in practice, exact agreement.

**Warnings.** A standalone figure in the claim text (not part of an identifier such as `NCT02401880`,
a date or a version string) that matches no declared number is reported as a warning. The claim can
still pass. The summary is prose; the report counts the digits in it but checks nothing there.

The check table in the report gives: claims, supported, unsupported, numbers declared, numbers
traced, record ids cited, record ids unresolved, undeclared figures. The Sources section lists every
cited record with source, URL, retrieval time and SHA-256 prefix, or marks it **not in store**.

## What "deterministic" means here

The checks in A3, A4 and B2 are pure functions of their input files. The re-computation in A2 depends
on pandas semantics (numeric coercion, quantile interpolation, group sort order), which are stated
above and pinned by the golden tests. The planning and drafting steps in B1 call a language model
and are not deterministic; that is why the loop stores records and the check reads only those.
