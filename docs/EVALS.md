# Evidence that the checks work

Unit and golden tests show the code does what it was written to do. These two evaluations ask a
different question: does it do the right thing on the real example, and does it catch what it must?
Both run offline, with no key, in CI.

## E1 — independent oracle (`tests/oracle/`)

The example's demographics table is derived a second time in SQL, run by DuckDB, with no pandas
arithmetic and no `pharma_agents` code in the derivation (`demographics_oracle.sql`). The test
compares every cell with `recompute` **before rounding**, to 1e-6. 80 of 80 cells agree.

Why this matters: the shipped example's approved table is the tool's own re-computation saved to
disk, so Check 1 passing on the example proves nothing by itself. The oracle is the independent
second programmer for the re-computation step.

Limits: one recipe, one dataset. A new statistic or a new recipe needs its own oracle rows.

## E2 — fault injection (`evals/fault_injection.py`, `evals/RESULTS.md`)

Start from a candidate identical to the approved table, apply one random mutation, run the full
`check-table` path including the CSV round trip, and record whether the verdict matched what the
mutation demands. Ten mutation kinds: four that must pass (identity, row order, a move smaller than
the tolerance, trailing whitespace in a key) and six that must fail (a move beyond tolerance, two
values swapped, a dropped cell, an added cell, a renamed column, a blanked value).

Last full run: 1,000 mutations, seed 7, **detection 600/600, false alarms 0/400**
([evals/RESULTS.md](../evals/RESULTS.md)). CI repeats a 120-mutation run on every push and fails on
any wrong verdict.

Limits: mutations are single and random; a wrong recipe, a wrong dataset, or a change the tolerance
was set to ignore are outside what this measures. `key_whitespace` passing is a documented
behaviour (keys are trimmed on read), not a finding.

## E3 — post-check fault corpus (`evals/postcheck_corpus.py`, `evals/RESULTS_POSTCHECK.md`)

Claims generated from the five captured records in `examples/pharma_brief/records`, twelve kinds,
ten claims each, every claim labelled with what the post-check should say about it. Six kinds are
faults the check is built to catch (wrong number, ghost record, number in a ghost record, wrong
path, non-numeric path, no citation); three are correct claims; three are **blind spots**, claims
that are wrong in a way a deterministic trace cannot see.

Last run (seed 3): **caught 60/60, false alarms 0/30, blind spots passed 30/30 by design**, and the
text-contradicts-declared kind warned on 10/10. CI repeats a five-per-kind run and fails if any
label stops holding, including the blind spots: if a change starts catching them it is a feature
that must be stated, and if a change stops warning it is a regression.

The blind spots, stated plainly:

| Kind | What is wrong | What the check sees |
|---|---|---|
| right number, wrong record | the text is about study A; the number is real but comes from, and is cited to, study B | number found at the cited path: supported |
| wrong reading | the number is real and traced, but the text says it means something it does not | supported |
| text contradicts declared | the text states one figure, `numbers` declares another that does trace | supported, with a warning about the undeclared figure |

These are why a brief's report has a reviewer block, and why a model-judged check (C3) is planned
and will be labelled as a model's opinion when it ships.

## Not yet measured

- Any run against a real language model (planned E4; costs money).
- A run by anyone other than the author (planned E5).

To reproduce: `uv sync --extra dev && PHARMA_AGENTS_OFFLINE=1 uv run pytest -q tests/oracle tests/evals`,
`uv run python evals/fault_injection.py --n 1000 --seed 7` and `uv run python evals/postcheck_corpus.py --per-type 10 --seed 3`.
