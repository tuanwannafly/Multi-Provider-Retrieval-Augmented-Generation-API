"""Gemini provider (gemini-1.5-flash). The google-generativeai SDK is synchronous,
so calls are offloaded to a thread via asyncio.to_thread."""
from __future__ import annotations

import asyncio
import time

from .base import LLMProvider, LLMResponse, ProviderUnavailableError, estimate_cost


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model = genai.GenerativeModel(self.model_id)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_id(self) -> str:
        return "gemini-1.5-flash"

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        start = time.monotonic()
        try:
            response = await asyncio.to_thread(self._model.generate_content, full_prompt)
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
