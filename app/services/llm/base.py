"""LLM provider abstraction: shared base, response model, pricing, errors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class ProviderUnavailableError(RuntimeError):
    """Raised when an LLM provider call fails (network, auth, rate limit, ...)."""


@dataclass
class LLMResponse:
    answer: str
    model: str
    latency_ms: int
    tokens: int
    estimated_cost_usd: float = 0.0


# Approximate USD per 1M tokens (input, output). Free tiers -> 0.0.
# (Used for the optional per-request cost estimate.)
PRICING_PER_1M: dict[str, dict[str, float]] = {
    "groq": {"input": 0.0, "output": 0.0},
    "gemini": {"input": 0.0, "output": 0.0},
    "anthropic": {"input": 0.25, "output": 1.25},
}


def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICING_PER_1M.get(provider, {"input": 0.0, "output": 0.0})
    return round(
        (input_tokens / 1_000_000) * price["input"]
        + (output_tokens / 1_000_000) * price["output"],
        6,
    )


class LLMProvider(ABC):
    max_tokens: int = 1024

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    async def complete(self, prompt: str, system: str = "") -> LLMResponse: ...

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{self.__class__.__name__} model={self.model_id}>"
