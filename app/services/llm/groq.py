"""Groq provider (llama-3.3-70b-versatile)."""
from __future__ import annotations

import time

from .base import LLMProvider, LLMResponse, ProviderUnavailableError, estimate_cost


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str):
        from groq import AsyncGroq

        self.client = AsyncGroq(api_key=api_key)

    @property
    def name(self) -> str:
        return "groq"

    @property
    def model_id(self) -> str:
        return "llama-3.3-70b-versatile"

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        start = time.monotonic()
        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Groq request failed: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        usage = response.usage
        tokens = usage.total_tokens if usage else 0
        in_tokens = getattr(usage, "prompt_tokens", 0) or 0
        out_tokens = getattr(usage, "completion_tokens", 0) or 0

        return LLMResponse(
            answer=response.choices[0].message.content or "",
            model=self.model_id,
            latency_ms=latency_ms,
            tokens=tokens,
            estimated_cost_usd=estimate_cost(self.name, in_tokens, out_tokens),
        )
