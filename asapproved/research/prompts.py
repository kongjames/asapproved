"""Prompts and JSON schemas for the two model calls in a research run. Kept here so they can be read, diffed and hashed."""

from __future__ import annotations

ALLOWED_SOURCES = ("clinicaltrials.search", "openfda.labels", "openfda.event_counts")

PLAN_SYSTEM = """You plan which public records to fetch to answer a question about a drug, a condition or a trial.
You can only use these calls:
- clinicaltrials.search: params condition, intervention, status (e.g. COMPLETED, RECRUITING), limit (max 10)
- openfda.labels: params generic_name (the US generic name as it appears on the label), limit (max 2)
- openfda.event_counts: params generic_name, limit (max 10 terms)
Choose the smallest set of calls that could answer the question. Do not invent other sources.
Respond with JSON only."""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "enum": list(ALLOWED_SOURCES)},
                    "condition": {"type": ["string", "null"]},
                    "intervention": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"]},
                    "generic_name": {"type": ["string", "null"]},
                    "limit": {"type": ["integer", "null"]},
                },
                "required": ["source", "condition", "intervention", "status", "generic_name", "limit"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["queries"],
    "additionalProperties": False,
}

DRAFT_SYSTEM = """You write an evidence brief from the records given to you and nothing else.
Rules:
1. Every claim must cite at least one record_id from the records provided. Never cite anything else.
2. Every number in a claim must appear in "numbers" with the record_id and the exact dotted path to the value
   inside that record's payload (for example "enrollment_count", "terms[0].count", "version"). Copy values
   exactly; do not round, convert or compute. If a number is not in a record, do not state it.
3. The summary is prose and must contain no digits. Put every figure in a claim.
4. If the records do not answer the question, say so in the summary and make fewer claims.
5. FAERS counts are spontaneous reports, not rates. Say so if you cite them.
Respond with JSON only."""

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "record_ids": {"type": "array", "items": {"type": "string"}},
                    "numbers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "number"},
                                "unit": {"type": ["string", "null"]},
                                "record_id": {"type": "string"},
                                "path": {"type": "string"},
                            },
                            "required": ["value", "unit", "record_id", "path"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["id", "text", "record_ids", "numbers"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "claims"],
    "additionalProperties": False,
}
