import json

import pytest

from pharma_agents.llm import FakeProvider, Provider, ProviderError
from pharma_agents.llm.anthropic import FALLBACK_BETA, AnthropicProvider, build_request

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"], "additionalProperties": False}


def test_fake_provider_scripted_json_and_text():
    p = FakeProvider([{"a": 1}, "plain text"])
    assert isinstance(p, Provider)
    c1 = p.complete([{"role": "user", "content": "hi"}], json_schema=SCHEMA)
    assert c1.parsed == {"a": 1} and json.loads(c1.text) == {"a": 1}
    c2 = p.complete([{"role": "user", "content": "hi"}])
    assert c2.text == "plain text" and c2.parsed is None
    assert len(p.calls) == 2 and p.calls[0]["json_schema"] == SCHEMA


def test_fake_provider_exhausted_and_bad_json():
    with pytest.raises(ProviderError):
        FakeProvider([]).complete([{"role": "user", "content": "x"}])
    with pytest.raises(ProviderError):
        FakeProvider(["not json"]).complete([{"role": "user", "content": "x"}], json_schema=SCHEMA)


def test_build_request_shape():
    req = build_request([{"role": "user", "content": "q"}], model="claude-opus-5-5", system="sys",
                        json_schema=SCHEMA, max_tokens=4000, effort="high")
    assert req["model"] == "claude-opus-5-5" and req["system"] == "sys" and req["max_tokens"] == 4000
    assert req["output_config"] == {"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}}
    for forbidden in ("temperature", "top_p", "top_k", "output_format", "thinking"):
        assert forbidden not in req
    bare = build_request([{"role": "user", "content": "q"}], model="m", system=None, json_schema=None,
                         max_tokens=16000, effort=None)
    assert "output_config" not in bare and "system" not in bare


class _Block:
    def __init__(self, text):
        self.type, self.text = "text", text


class _Usage:
    def model_dump(self):
        return {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 0, "speed": "standard"}


class _Resp:
    def __init__(self, text, stop_reason="end_turn", category=None):
        self.content = [_Block(text)]
        self.stop_reason = stop_reason
        self.stop_details = type("SD", (), {"category": category})() if stop_reason == "refusal" else None
        self.usage = _Usage()
        self.model = "claude-opus-5-5"
        self._request_id = "req_test"


class _FakeClient:
    """Stands in for anthropic.Anthropic(); records the request it was given."""

    def __init__(self, resp):
        self.resp, self.last = resp, None
        outer = self

        class _Msgs:
            def create(self, **kw):
                outer.last = kw
                return outer.resp

        class _Beta:
            messages = _Msgs()

        self.messages, self.beta = _Msgs(), _Beta()


def test_anthropic_provider_parses_json_and_uses_fallbacks(monkeypatch):
    monkeypatch.delenv("PHARMA_AGENTS_OFFLINE", raising=False)
    client = _FakeClient(_Resp('{"a": 2}'))
    p = AnthropicProvider(client=client, effort="low")
    c = p.complete([{"role": "user", "content": "q"}], json_schema=SCHEMA)
    assert c.parsed == {"a": 2} and c.usage == {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 0}
    assert c.request_id == "req_test"
    assert client.last["betas"] == [FALLBACK_BETA] and client.last["fallbacks"] == "default"
    assert client.last["output_config"]["format"]["type"] == "json_schema"


def test_anthropic_provider_without_fallbacks_uses_plain_messages(monkeypatch):
    monkeypatch.delenv("PHARMA_AGENTS_OFFLINE", raising=False)
    client = _FakeClient(_Resp("ok"))
    AnthropicProvider(client=client, fallbacks=False).complete([{"role": "user", "content": "q"}])
    assert "betas" not in client.last and "fallbacks" not in client.last


@pytest.mark.parametrize("stop,category", [("refusal", "cyber"), ("max_tokens", None)])
def test_anthropic_provider_refusal_and_truncation_raise(monkeypatch, stop, category):
    monkeypatch.delenv("PHARMA_AGENTS_OFFLINE", raising=False)
    p = AnthropicProvider(client=_FakeClient(_Resp("partial", stop_reason=stop, category=category)))
    with pytest.raises(ProviderError):
        p.complete([{"role": "user", "content": "q"}])


def test_anthropic_provider_respects_offline(monkeypatch):
    monkeypatch.setenv("PHARMA_AGENTS_OFFLINE", "1")
    with pytest.raises(ProviderError):
        AnthropicProvider(client=object())
