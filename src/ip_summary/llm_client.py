from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from .config import LLMSettings


class LLMClient:
    """
    Thin wrapper around the DeepSeek ChatCompletion API.
    """

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.model,
            messages=messages,
            temperature=self._resolve_temperature(temperature),
            top_p=self.settings.top_p,
            max_tokens=max_output_tokens or self.settings.max_output_tokens,
            timeout=self.settings.request_timeout,
        )
        return response.choices[0].message.content or ""

    def _resolve_temperature(self, temperature: Optional[float]) -> float:
        if temperature is None:
            return self.settings.temperature
        return temperature
