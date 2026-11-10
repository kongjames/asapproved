"""A scripted provider for tests and offline demos. Returns canned responses in order."""

from __future__ import annotations

import json
from typing import Any

from pharmaagents.llm.base import Completion, Message, ProviderError


class FakeProvider:
    name = "fake"

    def __init__(self, responses: list[str | dict[str, Any]] | None = None, model_id: str = "fake-1"):
        self._responses = list(responses or [])
        self.model_id = model_id
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 16000,
    ) -> Completion:
        self.calls.append({"messages": messages, "system": system, "json_schema": json_schema, "max_tokens": max_tokens})
        if not self._responses:
            raise ProviderError("FakeProvider has no scripted response left")
        nxt = self._responses.pop(0)
        if isinstance(nxt, dict):
            text, parsed = json.dumps(nxt, sort_keys=True), nxt
        else:
            text = nxt
            parsed = None
            if json_schema is not None:
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ProviderError(f"scripted response is not JSON: {exc}") from exc
        return Completion(text=text, model_id=self.model_id, parsed=parsed,
                          usage={"input_tokens": 0, "output_tokens": 0}, stop_reason="end_turn")
