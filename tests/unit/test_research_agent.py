import json
from pathlib import Path

from pharmaagents.llm.fake import FakeProvider
from pharmaagents.research.agent import ResearchAgent, records_for_model
from pharmaagents.sources.clinicaltrials import ClinicalTrialsAdapter
from pharmaagents.sources.openfda import OpenFDAAdapter

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _fx(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _fda_fetch(url):
    return _fx("openfda_event_counts.json") if "/event.json" in url else _fx("openfda_label.json")


PLAN = {"queries": [
    {"source": "clinicaltrials.search", "condition": "type 2 diabetes", "intervention": "metformin", "status": "COMPLETED", "generic_name": None, "limit": 50},
    {"source": "openfda.event_counts", "condition": None, "intervention": None, "status": None, "generic_name": "metformin hydrochloride", "limit": 5},
    {"source": "pubmed.search", "condition": None, "intervention": None, "status": None, "generic_name": None, "limit": 1},
]}
DRAFT = {"summary": "Trials and reports were found.", "claims": [
    {"id": "c1", "text": "NCT00899470 enrolled 24.", "record_ids": ["NCT00899470"],
     "numbers": [{"value": 24, "unit": None, "record_id": "NCT00899470", "path": "enrollment_count"}]},
    {"id": "c2", "text": "Top term diarrhoea, 6342 reports.", "record_ids": ["faers-count:metformin-hydrochloride:patient.reaction.reactionmeddrapt.exact"],
     "numbers": [{"value": 6342, "unit": "reports", "record_id": "faers-count:metformin-hydrochloride:patient.reaction.reactionmeddrapt.exact", "path": "terms[0].count"}]},
    {"id": "c3", "text": "NCT02401880 enrolled 90.", "record_ids": ["NCT02401880"],
     "numbers": [{"value": 90, "unit": None, "record_id": "NCT02401880", "path": "enrollment_count"}]},
]}


def test_end_to_end_with_fake_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("PHARMAAGENTS_OFFLINE", "1")  # adapters below use fixture fetchers, so nothing hits the network
    prov = FakeProvider([PLAN, DRAFT])
    agent = ResearchAgent(prov, tmp_path, run_id="t1",
                          clinicaltrials=ClinicalTrialsAdapter(fetch=lambda u: _fx("ctgov_studies.json")),
                          openfda=OpenFDAAdapter(fetch=_fda_fetch))
    brief, check, run_dir = agent.run("metformin in type 2 diabetes?")

    assert run_dir == tmp_path / "t1" and (run_dir / "brief.json").exists() and (run_dir / "brief.md").exists()
    assert len(list((run_dir / "records").glob("*.json"))) == 4  # 3 trials + 1 counts record
    assert [q.source for q in brief.run_meta.queries] == ["clinicaltrials.search", "openfda.event_counts"]  # pubmed dropped
    assert brief.run_meta.queries[0].params["limit"] == 10  # capped
    assert brief.run_meta.provider == "fake" and brief.run_meta.record_count == 4 and brief.run_meta.prompt_sha256

    by = {c.id: c for c in brief.claims}
    assert by["c1"].status == "supported" and by["c2"].status == "supported"
    assert by["c3"].status == "unsupported" and "90 ≠ 89" in by["c3"].reasons[0]
    assert check.verdict == "FAIL" and check.numbers_traced == 2

    # the drafting call saw only stored records, as JSON, after the question
    draft_call = prov.calls[1]
    assert "Records (JSON):" in draft_call["messages"][0]["content"]
    assert json.loads(draft_call["messages"][0]["content"].split("Records (JSON):\n", 1)[1])[0]["record_id"].startswith("NCT")
    assert draft_call["json_schema"]["required"] == ["summary", "claims"]


def test_records_for_model_only_exposes_three_fields():
    recs = ClinicalTrialsAdapter(fetch=lambda u: _fx("ctgov_studies.json")).search(condition="x")
    rows = json.loads(records_for_model(recs))
    assert set(rows[0]) == {"record_id", "source", "payload"}
