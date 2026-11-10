"""Anthropic provider. Optional: ``pip install 'pharma-agents[llm]'``.

What this does and does not do
------------------------------
* Uses the official SDK, ``client.messages.create`` (or the beta surface when server-side
  refusal fallbacks are on, the default), with adaptive thinking left at the model's default.
* Schema-constrained JSON goes through ``output_config.format`` (structured outputs). The text
  block is parsed and returned as ``Completion.parsed``.
* A ``refusal`` or ``max_tokens`` stop is an error, never silently returned as content.
* Honors ``PHARMA_AGENTS_OFFLINE=1``: constructing the provider raises, so CI cannot reach a model.
* Credentials come from the environment (``ANTHROPIC_API_KEY``, ``ANTHROPIC_AUTH_TOKEN`` or an
  ``ant auth login`` profile). Nothing is read from this repository.
"""

from __future__ import annotations

import json
import os
from typing import Any

from pharma_agents.llm.base import Completion, Message, ProviderError

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def build_request(
    messages: list[Message],
    *,
    model: str,
    system: str | None,
    json_schema: dict[str, Any] | None,
    max_tokens: int,
    effort: str | None,
) -> dict[str, Any]:
    """The request body, as a plain dict, so tests can assert on it without a client."""
    req: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": list(messages)}
    if system:
        req["system"] = system
    output_config: dict[str, Any] = {}
    if effort:
        output_config["effort"] = effort
    if json_schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": json_schema}
    if output_config:
        req["output_config"] = output_config
    return req


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        effort: str | None = None,
        fallbacks: bool = True,
        client: Any | None = None,
    ):
        if os.environ.get("PHARMA_AGENTS_OFFLINE") == "1":
            raise ProviderError("PHARMA_AGENTS_OFFLINE=1: live model calls are disabled")
        if client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - exercised only without the extra
                raise ProviderError("anthropic SDK not installed: pip install 'pharma-agents[llm]'") from exc
            client = anthropic.Anthropic()
        self._client = client
        self.model_id = model
        self.effort = effort
        self.fallbacks = fallbacks

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 16000,
    ) -> Completion:
        req = build_request(messages, model=self.model_id, system=system, json_schema=json_schema,
                            max_tokens=max_tokens, effort=self.effort)
        try:
            if self.fallbacks:
                resp = self._client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **req)
            else:
                resp = self._client.messages.create(**req)
        except Exception as exc:  # SDK error classes are caught by type below when available
            raise _wrap(exc) from exc

        if resp.stop_reason == "refusal":
            details = getattr(resp, "stop_details", None)
            cat = getattr(details, "category", None) if details else None
            raise ProviderError(f"model declined the request (category={cat})")
        if resp.stop_reason == "max_tokens":
            raise ProviderError(f"response truncated at max_tokens={max_tokens}; raise the limit")

        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        parsed = None
        if json_schema is not None:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ProviderError(f"model returned non-JSON despite json_schema: {exc}") from exc
        usage = getattr(resp, "usage", None)
        usage_d = {k: int(v) for k, v in (usage.model_dump() if usage else {}).items() if isinstance(v, int)}
        return Completion(text=text, model_id=getattr(resp, "model", self.model_id), parsed=parsed, usage=usage_d,
                          stop_reason=resp.stop_reason, request_id=getattr(resp, "_request_id", None))


def _wrap(exc: Exception) -> ProviderError:
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        return ProviderError(str(exc))
    if isinstance(exc, anthropic.RateLimitError):
        return ProviderError(f"rate limited: {exc}")
    if isinstance(exc, anthropic.APIStatusError):
        return ProviderError(f"API error {exc.status_code}: {exc.message}")
    if isinstance(exc, anthropic.APIConnectionError):
        return ProviderError(f"connection error: {exc}")
    if isinstance(exc, ProviderError):
        return exc
    return ProviderError(str(exc))
