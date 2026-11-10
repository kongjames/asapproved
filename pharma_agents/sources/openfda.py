"""openFDA (https://open.fda.gov). Drug labels (SPL) and FAERS adverse-event counts.

Terms: https://open.fda.gov/terms/ and licence https://open.fda.gov/license/. openFDA's own
disclaimer applies to every record and is stored with it: results are unvalidated and are not
to be relied on for decisions about medical care. FAERS counts are spontaneous reports; they are
not incidence rates and carry no denominator.

Only the label sections named in ``LABEL_SECTIONS`` are stored.
"""

from __future__ import annotations

import datetime as dt
import urllib.parse
from collections.abc import Callable
from typing import Any

from pharma_agents.sources.base import SourceRecord
from pharma_agents.sources.http import fetch_json

LABEL_URL = "https://api.fda.gov/drug/label.json"
EVENT_URL = "https://api.fda.gov/drug/event.json"
LABEL_SECTIONS = [
    "boxed_warning", "indications_and_usage", "dosage_and_administration", "contraindications",
    "warnings_and_cautions", "adverse_reactions",
]
OPENFDA_KEYS = ["application_number", "brand_name", "generic_name", "manufacturer_name", "route", "product_type", "substance_name"]
DEFAULT_COUNT_FIELD = "patient.reaction.reactionmeddrapt.exact"


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def build_label_url(generic_name: str, limit: int) -> str:
    search = f'openfda.generic_name:"{generic_name}"'
    return f"{LABEL_URL}?{urllib.parse.urlencode({'search': search, 'limit': str(limit)}, quote_via=urllib.parse.quote)}"


def build_event_count_url(generic_name: str, count_field: str, limit: int) -> str:
    search = f'patient.drug.openfda.generic_name:"{generic_name}"'
    q = {"search": search, "count": count_field, "limit": str(limit)}
    return f"{EVENT_URL}?{urllib.parse.urlencode(q, quote_via=urllib.parse.quote)}"


def label_to_record(result: dict[str, Any], meta: dict[str, Any], retrieved_at: str) -> SourceRecord:
    set_id = result.get("set_id", "")
    payload = {
        "set_id": set_id,
        "spl_id": result.get("id"),
        "version": result.get("version"),
        "effective_time": result.get("effective_time"),
        "openfda": {k: result.get("openfda", {}).get(k) for k in OPENFDA_KEYS if k in result.get("openfda", {})},
        "sections": {k: result[k] for k in LABEL_SECTIONS if k in result},
        "openfda_last_updated": meta.get("last_updated"),
        "openfda_disclaimer": meta.get("disclaimer"),
    }
    url = f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}"
    return SourceRecord.build("openfda.label", set_id, url, retrieved_at, payload)


def counts_to_record(data: dict[str, Any], generic_name: str, count_field: str, url: str, retrieved_at: str) -> SourceRecord:
    meta = data.get("meta", {})
    payload = {
        "generic_name": generic_name,
        "count_field": count_field,
        "terms": [{"term": r.get("term"), "count": r.get("count")} for r in data.get("results", [])],
        "openfda_last_updated": meta.get("last_updated"),
        "openfda_disclaimer": meta.get("disclaimer"),
    }
    rid = f"faers-count:{generic_name.lower().replace(' ', '-')}:{count_field}"
    return SourceRecord.build("openfda.event", rid, url, retrieved_at, payload)


class OpenFDAAdapter:
    name = "openfda"

    def __init__(self, fetch: Callable[[str], dict[str, Any]] = fetch_json):
        self._fetch = fetch

    def labels(self, generic_name: str, limit: int = 1) -> list[SourceRecord]:
        data = self._fetch(build_label_url(generic_name, limit))
        ts = _now()
        return [label_to_record(r, data.get("meta", {}), ts) for r in data.get("results", [])]

    def event_counts(self, generic_name: str, count_field: str = DEFAULT_COUNT_FIELD, limit: int = 10) -> SourceRecord:
        url = build_event_count_url(generic_name, count_field, limit)
        return counts_to_record(self._fetch(url), generic_name, count_field, url, _now())
