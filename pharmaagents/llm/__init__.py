"""One provider interface for every model call in this repository.

The assurance checks never need a model. The research agent (v0.2) does, and it talks to
exactly one interface: :class:`pharmaagents.llm.base.Provider`. Tests use
:class:`pharmaagents.llm.fake.FakeProvider`; CI never calls a live model.
"""

from pharmaagents.llm.base import Completion, Message, Provider, ProviderError
from pharmaagents.llm.fake import FakeProvider

__all__ = ["Completion", "FakeProvider", "Message", "Provider", "ProviderError"]
