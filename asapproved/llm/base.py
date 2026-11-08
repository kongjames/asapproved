"""The provider protocol: ``complete(messages) -> Completion``. Nothing else leaks out.

Design notes
------------
* No sampling parameters. ``temperature`` / ``top_p`` / ``top_k`` are not part of the protocol,
  so a run cannot be made "more deterministic" by a flag nobody can audit. Determinism in this
  repository comes from the post-checks (every number must trace to a stored record), not from
  the model.
* ``json_schema`` asks the provider for schema-constrained JSON. The provider parses it into
  ``Completion.parsed``; callers validate it again with their own pydantic model.
* ``Completion.model_id`` and ``usage`` are recorded in every run's metadata so a brief can be
  re-run later and the difference attributed to the model, the sources, or the prompt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypedDict, runtime_checkable


class Message(TypedDict):
    role: str  # "user" | "assistant"
    content: str


@dataclass(frozen=True)
class Completion:
    text: str
    model_id: str
    parsed: dict[str, Any] | None = None
    usage: dict[str, int] = field(default_factory=dict)
    stop_reason: str | None = None
    request_id: str | None = None


class ProviderError(RuntimeError):
    """Raised when a provider cannot return a usable completion (refusal, truncation, transport)."""


@runtime_checkable
class Provider(Protocol):
    name: str

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 16000,
    ) -> Completion: ...
