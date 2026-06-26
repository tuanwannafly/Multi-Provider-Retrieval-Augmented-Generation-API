"""Anthropic provider (claude-3-5-haiku-latest)."""
from __future__ import annotations

import time
from typing import AsyncIterator

from .base import LLMProvider, LLMResponse, ProviderUnavailableError, estimate_cost


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model_id(self) -> str:
        return "claude-3-5-haiku-latest"

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        start = time.monotonic()
        try:
            response = await self.client.messages.create(
                model=self.model_id,
                max_tokens=self.max_tokens,
                system=system or None,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Anthropic request failed: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        answer = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        in_tokens = getattr(response.usage, "input_tokens", 0) or 0
        out_tokens = getattr(response.usage, "output_tokens", 0) or 0

        return LLMResponse(
            answer=answer,
            model=self.model_id,
            latency_ms=latency_ms,
            tokens=in_tokens + out_tokens,
            estimated_cost_usd=estimate_cost(self.name, in_tokens, out_tokens),
        )

    async def complete_stream(
        self, prompt: str, system: str = ""
    ) -> AsyncIterator[str]:
        try:
            async with self.client.messages.stream(
                model=self.model_id,
                max_tokens=self.max_tokens,
                system=system or None,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as exc:
            raise ProviderUnavailableError(f"Anthropic stream failed: {exc}") from exc
