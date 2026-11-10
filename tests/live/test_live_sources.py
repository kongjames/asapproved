"""Live smoke tests. Skipped unless PHARMAAGENTS_LIVE=1; never run in CI."""

import os

import pytest

from pharmaagents.sources import ClinicalTrialsAdapter, OpenFDAAdapter

pytestmark = pytest.mark.skipif(os.environ.get("PHARMAAGENTS_LIVE") != "1", reason="set PHARMAAGENTS_LIVE=1 to hit the network")


@pytest.mark.live
def test_clinicaltrials_live():
    recs = ClinicalTrialsAdapter().search(condition="type 2 diabetes", status="COMPLETED", limit=2)
    assert len(recs) == 2 and all(r.record_id.startswith("NCT") for r in recs)


@pytest.mark.live
def test_openfda_live():
    fda = OpenFDAAdapter()
    assert fda.labels("metformin hydrochloride")[0].payload["sections"]
    assert fda.event_counts("metformin hydrochloride", limit=3).payload["terms"]
