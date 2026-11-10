"""Public data sources the research agent may cite. Each adapter returns :class:`SourceRecord`\\ s.

Closed world: a brief may only cite ``record_id``\\ s that an adapter fetched and stored during
that run. Every record carries the URL it came from, when it was retrieved and a sha256 of its
stored payload, so a later re-fetch can separate "the source changed" from "the model changed".
"""

from pharmaagents.sources.base import RecordStore, SourceRecord, canonical_sha256
from pharmaagents.sources.clinicaltrials import ClinicalTrialsAdapter
from pharmaagents.sources.http import OfflineError, fetch_json
from pharmaagents.sources.openfda import OpenFDAAdapter

__all__ = [
    "ClinicalTrialsAdapter", "OfflineError", "OpenFDAAdapter", "RecordStore", "SourceRecord",
    "canonical_sha256", "fetch_json",
]
