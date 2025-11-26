from __future__ import annotations

from typing import Dict, Any
from app.integrations.llm.base import LLMClient


class OpenAIClient(LLMClient):
    """
    Заглушка клиента OpenAI.
    Позже можно реализовать через официальное OpenAI API (chat.completions).
    Сейчас — просто NotImplementedError, чтобы структура была полной.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

        if not api_key:
            raise ValueError("OpenAI API key is required for OpenAIClient")

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        В будущем будет вызывать OpenAI Chat Completions.
        Пока — заглушка.
        """
        raise NotImplementedError("OpenAIClient.generate_json() is not implemented yet.")