# Example: an evidence brief with two deliberate faults

## What this shows
`pharmaagents check-brief` on a brief whose every claim cites stored public records. Two claims are
wrong on purpose: **c3** states an enrollment of 90 where the stored ClinicalTrials.gov record says
89, and **c4** cites a registry entry that was never fetched. Both are flagged, the brief fails,
and the report shows exactly why. Claim **c1** also carries a warning: "phase 1" is a figure in
the text with no declared number.

The brief is **hand-written**, not model output, so the faults are known. The records are real
API responses captured on 2026-11-07 (see `tests/fixtures/`), stored by the adapters with only
the declared fields.

## How to run
```bash
pharmaagents check-brief examples/pharma_brief/brief.json --reviewer "Your Name, Role (personal capacity)"
```
Exit code 1 and `brief_report.md` next to you. No API key, no network.

To produce a brief of your own from live public records (needs `pip install 'pharmaagents[llm]'` and an
Anthropic credential in the environment):
```bash
pharmaagents research "What do public records say about metformin hydrochloride in type 2 diabetes?" --out runs
pharmaagents check-brief runs/<run-id>/brief.json
```

## How it works
1. `records/` holds one JSON per `SourceRecord`: source, record id, URL, retrieval time, sha256 of
   the stored payload, payload.
2. `brief.json` lists claims; each names its record ids and each number's record id and dotted
   path (`enrollment_count`, `terms[0].count`).
3. `check-brief` resolves every citation and every number against the store, marks each claim
   supported or unsupported, and renders `expected_report.md` with footnoted sources, a run block
   and a signature block.

`make_example.py` rebuilds the records and the brief from the fixtures.
