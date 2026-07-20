import json
from typing import Any

import httpx

from core.config import settings

try:
    from openai import OpenAI
except ModuleNotFoundError:  # Allows local demo without installing OpenAI globally.
    OpenAI = None


class LLMService:
    def __init__(self) -> None:
        self.client = (
            OpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx.Client(trust_env=False))
            if OpenAI is not None and settings.OPENAI_API_KEY
            else None
        )
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    @property
    def available(self) -> bool:
        return bool(self.client and settings.LLM_ENABLED)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self.available:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            return {**fallback, "llm_error": str(exc)}

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.available or not texts:
            return []

        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]


llm_service = LLMService()
