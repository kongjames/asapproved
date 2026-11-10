# Post-check corpus results — `check-brief`

Run 2026-11-10 · pharma-agents 0.1.2 · 10 claims per kind · seed = 3 · records from `examples/pharma_brief/records` (25 distinct ids cited)

| Kind | Expected | Supported | Unsupported | Warned | Description |
|---|---|---:|---:|---:|---|
| `correct` | supported | 10 | 0 | 0 | number matches the value at its path in the cited record |
| `correct_numeric_string` | supported | 10 | 0 | 0 | value at the path is a numeric string (label version); coerced and compared |
| `undeclared_figure` | supported | 10 | 0 | 10 | a second figure in the text has no numbers entry (warning, not failure) |
| `wrong_number` | unsupported | 0 | 10 | 0 | declared value differs from the value at the path |
| `ghost_record` | unsupported | 0 | 10 | 0 | record_ids cites an id that is not in the store |
| `number_in_ghost_record` | unsupported | 0 | 10 | 0 | a number cites a record that is not in the store |
| `wrong_path` | unsupported | 0 | 10 | 0 | the path does not exist in the record |
| `non_numeric_path` | unsupported | 0 | 10 | 0 | the path exists but holds text |
| `no_citation` | unsupported | 0 | 10 | 10 | the claim cites no record at all |
| `right_number_wrong_record` | supported (by design: the check cannot see this) | 10 | 0 | 0 | text is about study A; the number is real but taken from study B and cited to B |
| `wrong_reading` | supported (by design: the check cannot see this) | 10 | 0 | 0 | the number is real and traced, but the text says it means something it does not |
| `text_contradicts_declared` | supported (by design: the check cannot see this) | 10 | 0 | 10 | the text states a different figure than the declared number (warning only) |

**Catch rate** on faults the check is built to catch: 60/60

**False alarms** on correct claims: 0/30

**Blind spots** passed as supported, by design: 30/30 (`text_contradicts_declared` warned on 10/10)

No unexpected verdicts.

The three blind-spot kinds are the limit of a deterministic trace: it proves a number was found where the claim says it was, not that the claim reads it correctly or cites the record it is about. `text_contradicts_declared` is surfaced as a warning (an undeclared figure in the text), never as a failure. A reviewer, or a labelled model judgement (planned C3), is needed for these.
