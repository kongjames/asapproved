"""The research agent: plan → fetch → draft → post-check. About a hundred lines, no framework.

The model sees the question when planning, and only the stored records when drafting. It never
sees a URL it did not fetch through an adapter, and the post-check is deterministic, so a brief
that passes is one whose every number was found in a stored record.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from asapproved import __version__
from asapproved.llm.base import Provider
from asapproved.research import prompts
from asapproved.research.postcheck import check_brief
from asapproved.research.render import brief_to_markdown
from asapproved.schema.brief import (
    BriefCheck,
    Claim,
    EvidenceBrief,
    NumberRef,
    RunMeta,
    SearchQuery,
)
from asapproved.sources.base import RecordStore, SourceRecord
from asapproved.sources.clinicaltrials import ClinicalTrialsAdapter
from asapproved.sources.openfda import OpenFDAAdapter

_PLAN_PARAM_KEYS = ("condition", "intervention", "status", "generic_name", "limit")
_LIMITS = {"clinicaltrials.search": 10, "openfda.labels": 2, "openfda.event_counts": 10}


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _prompt_hash() -> str:
    blob = json.dumps([prompts.PLAN_SYSTEM, prompts.PLAN_SCHEMA, prompts.DRAFT_SYSTEM, prompts.DRAFT_SCHEMA], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def records_for_model(records: list[SourceRecord]) -> str:
    """What the drafting call sees: record_id, source and payload. Nothing else."""
    return json.dumps(
        [{"record_id": r.record_id, "source": r.source, "payload": r.payload} for r in records],
        ensure_ascii=False, indent=1,
    )


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        out_dir: str | Path,
        *,
        clinicaltrials: ClinicalTrialsAdapter | None = None,
        openfda: OpenFDAAdapter | None = None,
        run_id: str | None = None,
    ):
        self.provider = provider
        self.out_dir = Path(out_dir)
        self.ct = clinicaltrials or ClinicalTrialsAdapter()
        self.fda = openfda or OpenFDAAdapter()
        self.run_id = run_id or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
        self.usage: dict[str, int] = {}

    # -- steps -----------------------------------------------------------------------------
    def plan(self, question: str) -> list[SearchQuery]:
        c = self.provider.complete([{"role": "user", "content": f"Question: {question}"}],
                                   system=prompts.PLAN_SYSTEM, json_schema=prompts.PLAN_SCHEMA)
        self._add_usage(c.usage)
        out: list[SearchQuery] = []
        for q in (c.parsed or {}).get("queries", []):
            src = q.get("source")
            if src not in prompts.ALLOWED_SOURCES:
                continue
            params = {k: q[k] for k in _PLAN_PARAM_KEYS if q.get(k) is not None}
            params["limit"] = min(int(params.get("limit") or _LIMITS[src]), _LIMITS[src])
            out.append(SearchQuery(source=src, params=params))
        return out

    def fetch(self, queries: list[SearchQuery]) -> list[SourceRecord]:
        recs: list[SourceRecord] = []
        for q in queries:
            p = q.params
            if q.source == "clinicaltrials.search":
                recs += self.ct.search(condition=p.get("condition"), intervention=p.get("intervention"),
                                       status=p.get("status"), limit=p["limit"])
            elif q.source == "openfda.labels" and p.get("generic_name"):
                recs += self.fda.labels(p["generic_name"], limit=p["limit"])
            elif q.source == "openfda.event_counts" and p.get("generic_name"):
                recs.append(self.fda.event_counts(p["generic_name"], limit=p["limit"]))
        # de-duplicate by key, keep first
        seen: dict[str, SourceRecord] = {}
        for r in recs:
            seen.setdefault(r.key, r)
        return list(seen.values())

    def draft(self, question: str, records: list[SourceRecord]) -> EvidenceBrief:
        user = f"Question: {question}\n\nRecords (JSON):\n{records_for_model(records)}"
        c = self.provider.complete([{"role": "user", "content": user}],
                                   system=prompts.DRAFT_SYSTEM, json_schema=prompts.DRAFT_SCHEMA)
        self._add_usage(c.usage)
        data: dict[str, Any] = c.parsed or {"summary": "", "claims": []}
        claims = [
            Claim(id=cl["id"], text=cl["text"], record_ids=cl.get("record_ids", []),
                  numbers=[NumberRef(**n) for n in cl.get("numbers", [])])
            for cl in data.get("claims", [])
        ]
        return EvidenceBrief(question=question, summary=data.get("summary", ""), claims=claims)

    # -- the run ---------------------------------------------------------------------------
    def run(self, question: str) -> tuple[EvidenceBrief, BriefCheck, Path]:
        run_dir = self.out_dir / self.run_id
        store = RecordStore(run_dir / "records")
        queries = self.plan(question)
        records = self.fetch(queries)
        store.save_all(records)
        brief = self.draft(question, records)
        brief.run_meta = RunMeta(
            run_id=self.run_id, created_at=_now(), tool_version=__version__,
            provider=self.provider.name, model_id=getattr(self.provider, "model_id", "?"),
            usage=dict(self.usage), queries=queries, record_count=len(records), prompt_sha256=_prompt_hash(),
        )
        checked, check = check_brief(brief, store.index())
        (run_dir / "brief.json").write_text(checked.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "check.json").write_text(check.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "brief.md").write_text(brief_to_markdown(checked, check, store.index()), encoding="utf-8")
        return checked, check, run_dir

    def _add_usage(self, usage: dict[str, int]) -> None:
        for k, v in usage.items():
            self.usage[k] = self.usage.get(k, 0) + v
