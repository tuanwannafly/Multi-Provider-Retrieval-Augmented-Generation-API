"""Provider factory: builds and caches provider singletons by name."""
from __future__ import annotations

from app.config import settings
from app.errors import RAGAPIException

from .anthropic import AnthropicProvider
from .base import LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider

AVAILABLE_PROVIDERS = ["groq", "gemini", "anthropic"]

_registry: dict[str, LLMProvider] = {}


def _build_provider(name: str) -> LLMProvider:
    if name == "groq":
        return GroqProvider(settings.groq_api_key)
    if name == "gemini":
        return GeminiProvider(settings.gemini_api_key)
    if name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key)
    raise ValueError(f"Unknown provider: {name}. Allowed: {AVAILABLE_PROVIDERS}")


def get_provider(name: str) -> LLMProvider:
    if name not in AVAILABLE_PROVIDERS:
        raise RAGAPIException(
            code="INVALID_PROVIDER",
            message=f"Provider '{name}' is not valid. Allowed: {AVAILABLE_PROVIDERS}",
            status_code=400,
        )
    if name not in _registry:
        _registry[name] = _build_provider(name)
    return _registry[name]


def set_provider(name: str, provider: LLMProvider) -> None:
    """Inject a provider instance (used by tests)."""
    _registry[name] = provider


def reset_registry() -> None:
    _registry.clear()
