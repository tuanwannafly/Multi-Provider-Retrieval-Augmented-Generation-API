"""Gemini provider (gemini-2.0-flash). Uses the new google-genai SDK."""
from __future__ import annotations

import time
from typing import AsyncIterator

from google import genai
from google.genai import types

from .base import LLMProvider, LLMResponse, ProviderUnavailableError, estimate_cost


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ProviderUnavailableError("Gemini API key is not configured")
        self._client = genai.Client(api_key=api_key)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_id(self) -> str:
        return "gemini-2.0-flash"

    def _build_contents(self, prompt: str, system: str) -> list[types.Content]:
        parts: list[types.Part] = [types.Part.from_text(text=prompt)]
        contents: list[types.Content] = [types.Content(role="user", parts=parts)]
        if system:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=system)],
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Understood.")],
                )
            )
        return contents

    def _config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            max_output_tokens=self.max_tokens,
        )

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        contents = self._build_contents(prompt, system)
        start = time.monotonic()
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=self._config(),
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini request failed: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        answer = getattr(response, "text", "") or ""
        usage = getattr(response, "usage_metadata", None)
        in_tokens = getattr(usage, "prompt_token_count", 0) or 0
        out_tokens = getattr(usage, "candidates_token_count", 0) or 0
        tokens = in_tokens + out_tokens

        return LLMResponse(
            answer=answer,
            model=self.model_id,
            latency_ms=latency_ms,
            tokens=tokens,
            estimated_cost_usd=estimate_cost(self.name, in_tokens, out_tokens),
        )

    async def complete_stream(
        self, prompt: str, system: str = ""
    ) -> AsyncIterator[str]:
        contents = self._build_contents(prompt, system)
        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=contents,
                config=self._config(),
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini stream failed: {exc}") from exc

        async for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text
