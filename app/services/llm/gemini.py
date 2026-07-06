"""Gemini provider (gemini-2.0-flash). Uses the new google-genai SDK."""
from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

from google.generativeai.types import GenerationConfig # Added import
import google.generativeai as genai # Changed import

from .base import LLMProvider, LLMResponse, ProviderUnavailableError, estimate_cost


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = genai.GenerativeModel(self.model_id) # Changed from _genai
        genai.configure(api_key=api_key) # Moved configure here

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_id(self) -> str:
        return "gemini-2.0-flash" # Updated model ID

    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        messages = [
            {"role": "user", "parts": [prompt]}
        ]
        if system:
            messages.insert(0, {"role": "system", "parts": [system]}) # Added system role

        start = time.monotonic()
        try:
            response = await asyncio.to_thread(
                self.client.generate_content,
                messages, # Changed to messages
                generation_config=GenerationConfig(max_output_tokens=self.max_tokens) # Added max_output_tokens
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
        messages = [
            {"role": "user", "parts": [prompt]}
        ]
        if system:
            messages.insert(0, {"role": "system", "parts": [system]})

        try:
            stream_response = await asyncio.to_thread(
                self.client.generate_content,
                messages,
                generation_config=GenerationConfig(max_output_tokens=self.max_tokens),
                stream=True,
            )
            for chunk in stream_response:
                yield chunk.text
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini stream failed: {exc}") from exc
