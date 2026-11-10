"""Build the example: records from the test fixtures, and a hand-written brief with two deliberate faults.

The brief is NOT model output. It is written by hand to show what the post-check catches:
claim c3 states an enrollment of 90 where the record says 89; claim c4 cites a record that was
never fetched. Claim c1 also shows a warning: "phase 1" is a figure in the text with no declared number. Run from the repository root: ``python examples/pharma_brief/make_example.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from pharmaagents import __version__
from pharmaagents.research.postcheck import check_brief
from pharmaagents.research.render import brief_to_markdown
from pharmaagents.schema.brief import Claim, EvidenceBrief, NumberRef, RunMeta, SearchQuery
from pharmaagents.sources.base import RecordStore
from pharmaagents.sources.clinicaltrials import ClinicalTrialsAdapter
from pharmaagents.sources.openfda import OpenFDAAdapter

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
HERE = Path(__file__).resolve().parent
RETRIEVED = "2026-11-07T22:00:00+00:00"

QUESTION = "What do public records say about metformin hydrochloride in type 2 diabetes: completed trials, the label's boxed warning, and the most reported adverse events?"


def _fx(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def main() -> None:
    ct = ClinicalTrialsAdapter(fetch=lambda u: _fx("ctgov_studies.json"))
    fda = OpenFDAAdapter(fetch=lambda u: _fx("openfda_label.json"))
    fda_ev = OpenFDAAdapter(fetch=lambda u: _fx("openfda_event_counts.json"))
    recs = ct.search(condition="type 2 diabetes", intervention="metformin", status="COMPLETED", limit=3)
    recs += fda.labels("metformin hydrochloride", limit=1)
    recs.append(fda_ev.event_counts("metformin hydrochloride", limit=5))
    for r in recs:  # fixed timestamp so the example is identical on every machine
        r.retrieved_at = RETRIEVED
    store = RecordStore(HERE / "records")
    for p in store.folder.glob("*.json"):
        p.unlink()
    store.save_all(recs)

    label_id = next(r.record_id for r in recs if r.source == "openfda.label")
    counts_id = next(r.record_id for r in recs if r.source == "openfda.event")
    brief = EvidenceBrief(
        question=QUESTION,
        summary=("Three completed trials of metformin in the stated condition were retrieved, one current "
                 "label for a sitagliptin and metformin combination product, and the most frequently reported "
                 "reaction terms from spontaneous reports. The label carries a boxed warning for lactic acidosis."),
        claims=[
            Claim(id="c1", text="NCT00899470, a phase 1 bioequivalence study of saxagliptin and metformin formulations, enrolled 24 participants.",
                  record_ids=["NCT00899470"],
                  numbers=[NumberRef(value=24, unit="participants", record_id="NCT00899470", path="enrollment_count")]),
            Claim(id="c2", text="The retrieved label (version 6, effective 2026-08-12) has a boxed warning for lactic acidosis.",
                  record_ids=[label_id],
                  numbers=[NumberRef(value=6, unit=None, record_id=label_id, path="version")]),
            Claim(id="c3", text="NCT02401880 enrolled 90 participants.",
                  record_ids=["NCT02401880"],
                  numbers=[NumberRef(value=90, unit="participants", record_id="NCT02401880", path="enrollment_count")]),
            Claim(id="c4", text="A separate registry entry reports a phase 3 outcome study with 4,000 participants.",
                  record_ids=["NCT99999999"],
                  numbers=[NumberRef(value=4000, unit="participants", record_id="NCT99999999", path="enrollment_count")]),
            Claim(id="c5", text="In spontaneous reports, the most reported reaction term is diarrhoea with 6342 reports; these are report counts, not rates.",
                  record_ids=[counts_id],
                  numbers=[NumberRef(value=6342, unit="reports", record_id=counts_id, path="terms[0].count")]),
        ],
        run_meta=RunMeta(
            run_id="example", created_at=RETRIEVED, tool_version=__version__,
            provider="hand-written (not model output)", model_id="n/a",
            queries=[SearchQuery(source="clinicaltrials.search", params={"condition": "type 2 diabetes", "intervention": "metformin", "status": "COMPLETED", "limit": 3}),
                     SearchQuery(source="openfda.labels", params={"generic_name": "metformin hydrochloride", "limit": 1}),
                     SearchQuery(source="openfda.event_counts", params={"generic_name": "metformin hydrochloride", "limit": 5})],
            record_count=len(recs),
        ),
    )
    (HERE / "brief.json").write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    checked, check = check_brief(brief, store.index())
    (HERE / "expected_report.md").write_text(
        brief_to_markdown(checked, check, store.index(), reviewer="Example Reviewer (personal capacity)", run_date="2026-11-07"),
        encoding="utf-8")
    print(f"{check.verdict}: {check.supported}/{check.claims_total} supported, {check.numbers_traced}/{check.numbers_total} numbers traced")


if __name__ == "__main__":
    main()
