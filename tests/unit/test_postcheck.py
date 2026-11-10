import pytest

from pharmaagents.research.postcheck import check_brief, resolve_path
from pharmaagents.schema.brief import Claim, EvidenceBrief, NumberRef
from pharmaagents.sources.base import SourceRecord

REC = SourceRecord.build("s", "R1", "https://x/R1", "2026-01-01T00:00:00+00:00",
                         {"n": 89, "terms": [{"term": "A", "count": 10}, {"term": "B", "count": 4}], "s": "12,345", "name": "x"})
RECS = {"R1": REC, "s:R1": REC}


def test_resolve_path():
    assert resolve_path(REC.payload, "n") == 89
    assert resolve_path(REC.payload, "terms[1].count") == 4
    assert resolve_path(REC.payload, "terms[0]") == {"term": "A", "count": 10}
    with pytest.raises(KeyError):
        resolve_path(REC.payload, "missing")
    with pytest.raises(IndexError):
        resolve_path(REC.payload, "terms[5].count")
    with pytest.raises(TypeError):
        resolve_path(REC.payload, "n[0]")


def _brief(*claims):
    return EvidenceBrief(question="q", summary="no digits here", claims=list(claims))


def test_supported_claim():
    b, chk = check_brief(_brief(Claim(id="c1", text="t", record_ids=["R1"],
                                      numbers=[NumberRef(value=89, record_id="R1", path="n"),
                                               NumberRef(value=12345, record_id="R1", path="s")])), RECS)
    assert b.claims[0].status == "supported" and chk.verdict == "PASS"
    assert chk.numbers_traced == 2 and chk.record_ids_cited == 1 and chk.summary_numbers_unchecked == 0


def test_wrong_number_missing_record_no_citation_non_numeric():
    b, chk = check_brief(_brief(
        Claim(id="wrong", text="t", record_ids=["R1"], numbers=[NumberRef(value=90, record_id="R1", path="n")]),
        Claim(id="ghost", text="t", record_ids=["R9"], numbers=[NumberRef(value=1, record_id="R9", path="n")]),
        Claim(id="none", text="t"),
        Claim(id="path", text="t", record_ids=["R1"], numbers=[NumberRef(value=1, record_id="R1", path="terms[0].nope")]),
        Claim(id="text", text="t", record_ids=["R1"], numbers=[NumberRef(value=1, record_id="R1", path="name")]),
        Claim(id="ok", text="t", record_ids=["R1"], numbers=[NumberRef(value=10, record_id="R1", path="terms[0].count")]),
    ), RECS)
    by = {c.id: c for c in b.claims}
    assert by["wrong"].status == "unsupported" and "90 ≠ 89" in by["wrong"].reasons[0]
    assert by["ghost"].status == "unsupported" and len(by["ghost"].reasons) == 2
    assert by["none"].reasons == ["no source record cited"]
    assert "no value at R1.terms[0].nope" in by["path"].reasons[0]
    assert "not numeric" in by["text"].reasons[0]
    assert by["ok"].status == "supported"
    assert chk.verdict == "FAIL" and chk.unsupported == 5 and chk.supported == 1
    assert chk.record_ids_unresolved == ["R9"] and chk.numbers_traced == 1 and chk.numbers_total == 5


def test_tolerance_and_summary_digits():
    b, chk = check_brief(EvidenceBrief(question="q", summary="There were 3 trials.", claims=[
        Claim(id="c", text="t", record_ids=["R1"], numbers=[NumberRef(value=89.0000001, record_id="R1", path="n")])]), RECS)
    assert b.claims[0].status == "supported" and chk.summary_numbers_unchecked == 1


def test_undeclared_figures_warn_but_do_not_fail():
    b, chk = check_brief(_brief(Claim(id="c", text="NCT00899470, a phase 1 study (version 2026-08-12), enrolled 24 of 4,000 screened.",
                                      record_ids=["R1"], numbers=[NumberRef(value=89, record_id="R1", path="n")])), RECS)
    c = b.claims[0]
    assert c.status == "supported" and chk.verdict == "PASS"
    assert c.warnings == ["figure 1 appears in the text but is not declared in numbers",
                          "figure 24 appears in the text but is not declared in numbers",
                          "figure 4,000 appears in the text but is not declared in numbers"]
    assert chk.undeclared_numbers == 3
