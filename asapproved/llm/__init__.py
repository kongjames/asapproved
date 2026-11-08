"""One provider interface for every model call in this repository.

The assurance checks never need a model. The research agent (v0.2) does, and it talks to
exactly one interface: :class:`asapproved.llm.base.Provider`. Tests use
:class:`asapproved.llm.fake.FakeProvider`; CI never calls a live model.
"""

from asapproved.llm.base import Completion, Message, Provider, ProviderError
from asapproved.llm.fake import FakeProvider

__all__ = ["Completion", "FakeProvider", "Message", "Provider", "ProviderError"]
