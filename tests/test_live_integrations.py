from types import SimpleNamespace

import litellm

from src.gateway.litellm_gateway import complete_with_fallback
from src.gateway.routing import RouteDecision


def _response(text: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def test_litellm_primary_completion_is_called(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        return _response("grounded primary response")

    monkeypatch.setattr(litellm, "completion", fake_completion)
    decision = RouteDecision("fast-faq", "openrouter/google/gemini-2.5-flash", "test")
    result = complete_with_fallback("question", decision, "draft")
    assert result.text == "grounded primary response"
    assert calls == [decision.model]
    assert result.fallback_used is False


def test_litellm_fallback_is_called_after_failure(monkeypatch):
    calls = []

    def fake_completion(**kwargs):
        calls.append(kwargs["model"])
        if len(calls) == 1:
            raise TimeoutError("primary timeout")
        return _response("grounded fallback response")

    monkeypatch.setattr(litellm, "completion", fake_completion)
    decision = RouteDecision("deep-support", "openai/gpt-4o", "test")
    result = complete_with_fallback("question", decision, "draft")
    assert result.text == "grounded fallback response"
    assert len(calls) == 2
    assert result.fallback_used is True
