"""SourceRecord: the unit of evidence. RecordStore: where a run keeps them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def canonical_sha256(payload: Any) -> str:
    """sha256 of the payload serialised canonically (sorted keys, no whitespace, UTF-8)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class SourceRecord(BaseModel):
    source: str  # adapter name, e.g. "clinicaltrials.gov"
    record_id: str  # stable id within the source, e.g. "NCT02401880"
    url: str  # where a human can see the same thing
    retrieved_at: str  # ISO-8601 UTC
    sha256: str  # canonical_sha256(payload)
    payload: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def build(cls, source: str, record_id: str, url: str, retrieved_at: str, payload: dict[str, Any]) -> SourceRecord:
        return cls(source=source, record_id=record_id, url=url, retrieved_at=retrieved_at,
                   sha256=canonical_sha256(payload), payload=payload)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.record_id}"


class RecordStore:
    """One JSON file per record under ``folder``; lookup by ``record_id`` or ``source:record_id``."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def _path(self, rec: SourceRecord) -> Path:
        safe = rec.key.replace("/", "_").replace(":", "__")
        return self.folder / f"{safe}.json"

    def save(self, rec: SourceRecord) -> Path:
        p = self._path(rec)
        p.write_text(rec.model_dump_json(indent=1), encoding="utf-8")
        return p

    def save_all(self, recs: list[SourceRecord]) -> list[Path]:
        return [self.save(r) for r in recs]

    def load_all(self) -> list[SourceRecord]:
        return [SourceRecord.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(self.folder.glob("*.json"))]

    def index(self) -> dict[str, SourceRecord]:
        out: dict[str, SourceRecord] = {}
        for r in self.load_all():
            out[r.key] = r
            out.setdefault(r.record_id, r)
        return out
