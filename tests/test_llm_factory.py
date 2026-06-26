import pytest

from app.services.llm import factory
from app.services.llm.base import LLMResponse, estimate_cost


def test_invalid_provider_raises():
    factory.reset_registry()
    with pytest.raises(Exception):
        factory.get_provider("openai")


def test_available_providers():
    assert factory.AVAILABLE_PROVIDERS == ["groq", "gemini", "anthropic"]


def test_set_and_get_provider(monkeypatch):
    factory.reset_registry()

    class FakeProvider:
        @property
        def name(self):
            return "groq"

        @property
        def model_id(self):
            return "fake-model"

        async def complete(self, prompt, system=""):
            return LLMResponse(answer="ok", model="fake-model", latency_ms=5, tokens=1)

    factory.set_provider("groq", FakeProvider())
    provider = factory.get_provider("groq")
    assert provider.name == "groq"
    assert provider.model_id == "fake-model"
    factory.reset_registry()


def test_estimate_cost():
    assert estimate_cost("groq", 1000, 500) == 0.0
    assert estimate_cost("gemini", 1000, 500) == 0.0
    cost = estimate_cost("anthropic", 1_000_000, 1_000_000)
    assert cost == round(0.25 + 1.25, 6)
