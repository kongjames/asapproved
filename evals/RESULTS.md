# Fault-injection results — `check-table`

Run 2026-11-10 · pharma-agents 0.1.2 · n = 1000 · seed = 7 · example `examples/pharma_tlf` (80 cells, tolerance 0.005)

| Mutation | Must | Runs | Wrong verdicts | Rate |
|---|---|---:|---:|---:|
| `identity` — no change | PASS | 100 | 0 | 0.0% |
| `reorder_rows` — rows shuffled; keys and values unchanged | PASS | 100 | 0 | 0.0% |
| `value_within_tol` — one value moved by less than the recipe tolerance | PASS | 100 | 0 | 0.0% |
| `key_whitespace` — trailing space added to one key field (keys are trimmed on read) | PASS | 100 | 0 | 0.0% |
| `value_beyond_tol` — one value moved by more than the recipe tolerance | FAIL | 100 | 0 | 0.0% |
| `swap_values` — two cells with different values exchanged | FAIL | 100 | 0 | 0.0% |
| `drop_cell` — one cell removed | FAIL | 100 | 0 | 0.0% |
| `add_cell` — one cell added under a category that does not exist | FAIL | 100 | 0 | 0.0% |
| `rename_group` — one column label changed on every cell that carries it | FAIL | 100 | 0 | 0.0% |
| `blank_value` — one value blanked | FAIL | 100 | 0 | 0.0% |

**Detection rate** (mutations that must fail and did): 600/600 = 100.00%

**False-alarm rate** (benign mutations that failed): 0/400 = 0.00%

No wrong verdicts.

Each run writes the mutated candidate to CSV and runs the full `check-table` path, so the CSV round trip is included. `value_within_tol` moves a value by at most 80% of the tolerance; `value_beyond_tol` by at least twice it. `key_whitespace` passes by design: keys are trimmed when a table is read.
