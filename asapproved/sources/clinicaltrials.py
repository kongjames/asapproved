"""ClinicalTrials.gov API v2 (https://clinicaltrials.gov/data-api/api). Public domain US government data.

Only the fields named in ``FIELDS`` are requested and stored. The record id is the NCT number;
the URL is the study's public page.
"""

from __future__ import annotations

import datetime as dt
import urllib.parse
from collections.abc import Callable
from typing import Any

from asapproved.sources.base import SourceRecord
from asapproved.sources.http import fetch_json

BASE = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = [
    "NCTId", "BriefTitle", "OverallStatus", "Phase", "EnrollmentInfo", "StartDate", "CompletionDate",
    "LeadSponsorName", "Condition", "InterventionName",
]


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def build_url(condition: str | None, intervention: str | None, status: str | None, limit: int) -> str:
    q: dict[str, str] = {"pageSize": str(limit), "fields": ",".join(FIELDS), "format": "json"}
    if condition:
        q["query.cond"] = condition
    if intervention:
        q["query.intr"] = intervention
    if status:
        q["filter.overallStatus"] = status
    return f"{BASE}?{urllib.parse.urlencode(q, quote_via=urllib.parse.quote)}"


def study_to_record(study: dict[str, Any], retrieved_at: str) -> SourceRecord:
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    enrol = design.get("enrollmentInfo", {})
    nct = ident.get("nctId", "")
    payload = {
        "nct_id": nct,
        "brief_title": ident.get("briefTitle"),
        "overall_status": status.get("overallStatus"),
        "phases": design.get("phases", []),
        "enrollment_count": enrol.get("count"),
        "enrollment_type": enrol.get("type"),
        "start_date": status.get("startDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),
        "lead_sponsor": p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
        "conditions": p.get("conditionsModule", {}).get("conditions", []),
        "interventions": [i.get("name") for i in p.get("armsInterventionsModule", {}).get("interventions", [])],
    }
    return SourceRecord.build("clinicaltrials.gov", nct, f"https://clinicaltrials.gov/study/{nct}", retrieved_at, payload)


class ClinicalTrialsAdapter:
    name = "clinicaltrials.gov"

    def __init__(self, fetch: Callable[[str], dict[str, Any]] = fetch_json):
        self._fetch = fetch

    def search(
        self,
        condition: str | None = None,
        intervention: str | None = None,
        status: str | None = None,
        limit: int = 5,
    ) -> list[SourceRecord]:
        if not (condition or intervention):
            raise ValueError("give a condition or an intervention")
        data = self._fetch(build_url(condition, intervention, status, limit))
        ts = _now()
        return [study_to_record(s, ts) for s in data.get("studies", [])]
