import json
from pathlib import Path

import pytest

from pharmaagents.sources import (
    ClinicalTrialsAdapter,
    OfflineError,
    OpenFDAAdapter,
    RecordStore,
    SourceRecord,
    canonical_sha256,
    fetch_json,
)
from pharmaagents.sources.clinicaltrials import build_url

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_canonical_sha256_is_order_independent():
    assert canonical_sha256({"b": 1, "a": [1, 2]}) == canonical_sha256({"a": [1, 2], "b": 1})
    assert canonical_sha256({"a": 1}) != canonical_sha256({"a": 2})


def test_clinicaltrials_maps_fixture_to_records():
    seen = []

    def fetch(url):
        seen.append(url)
        return _fixture("ctgov_studies.json")

    recs = ClinicalTrialsAdapter(fetch=fetch).search(condition="type 2 diabetes", intervention="metformin",
                                                     status="COMPLETED", limit=3)
    assert "query.cond=type%202%20diabetes" in seen[0] and "filter.overallStatus=COMPLETED" in seen[0]
    assert [r.record_id for r in recs] == ["NCT02401880", "NCT00899470", "NCT00375388"]
    r = recs[0]
    assert r.source == "clinicaltrials.gov" and r.url.endswith("/study/NCT02401880")
    assert r.payload["enrollment_count"] == 89 and r.payload["phases"] == ["PHASE4"]
    assert r.payload["lead_sponsor"].startswith("Profil Institut")
    assert r.sha256 == canonical_sha256(r.payload)


def test_clinicaltrials_requires_a_query():
    with pytest.raises(ValueError):
        ClinicalTrialsAdapter(fetch=lambda u: {}).search()
    assert "pageSize=2" in build_url(None, "x", None, 2)


def test_openfda_label_keeps_only_declared_sections():
    recs = OpenFDAAdapter(fetch=lambda u: _fixture("openfda_label.json")).labels("metformin hydrochloride")
    assert len(recs) == 1
    r = recs[0]
    assert r.source == "openfda.label" and r.record_id == "0098dec4-f0e5-45d5-8aa4-5d0faf9ab142"
    assert "setid=0098dec4" in r.url
    assert set(r.payload["sections"]) <= {"boxed_warning", "indications_and_usage", "dosage_and_administration",
                                          "contraindications", "warnings_and_cautions", "adverse_reactions"}
    assert r.payload["openfda"]["generic_name"] == ["SITAGLIPTIN AND METFORMIN HYDROCHLORIDE"]
    assert r.payload["openfda_disclaimer"].startswith("Do not rely on openFDA")
    assert "clinical_pharmacology" not in r.payload and "clinical_pharmacology" not in r.payload["sections"]


def test_openfda_event_counts_record():
    r = OpenFDAAdapter(fetch=lambda u: _fixture("openfda_event_counts.json")).event_counts("metformin hydrochloride", limit=5)
    assert r.source == "openfda.event" and r.record_id.startswith("faers-count:metformin-hydrochloride:")
    assert r.payload["terms"][0] == {"term": "DIARRHOEA", "count": 6342} and len(r.payload["terms"]) == 5
    assert "count=patient.reaction.reactionmeddrapt.exact" in r.url


def test_record_store_round_trip(tmp_path):
    recs = ClinicalTrialsAdapter(fetch=lambda u: _fixture("ctgov_studies.json")).search(condition="x")
    store = RecordStore(tmp_path / "records")
    paths = store.save_all(recs)
    assert len(paths) == 3 and all(p.exists() for p in paths)
    back = store.load_all()
    assert [r.model_dump() for r in back] == [r.model_dump() for r in sorted(recs, key=lambda r: r.key)]
    idx = store.index()
    assert idx["NCT00899470"].payload["enrollment_count"] == 24
    assert idx["clinicaltrials.gov:NCT00899470"] is idx["NCT00899470"]


def test_fetch_json_respects_offline(monkeypatch):
    monkeypatch.setenv("PHARMAAGENTS_OFFLINE", "1")
    with pytest.raises(OfflineError):
        fetch_json("https://example.invalid/x.json")


def test_source_record_build_sets_hash():
    r = SourceRecord.build("s", "id1", "https://x", "2026-01-01T00:00:00+00:00", {"k": "v"})
    assert r.key == "s:id1" and r.sha256 == canonical_sha256({"k": "v"})
