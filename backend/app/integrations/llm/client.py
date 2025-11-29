from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import re

from google import genai

from app.core.config import settings
from app.core.debugger import debug
from app.core.logging import app_logger


class LLMClient(ABC):
    """
    Базовый интерфейс для LLM-клиентов.
    """
    
    @abstractmethod
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Сгенерировать JSON на основе промпта.
        """
        raise NotImplementedError


class GeminiClient(LLMClient):
    """
    Клиент для работы с Google Gemini API.
    """
    
    def __init__(self, model: str | None = None) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = model or settings.GEMINI_MODEL  # например "gemini-2.5-flash"

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """
        Очищает ответ LLM от markdown разметки и лишних символов.
        
        Удаляет:
        - Markdown код-блоки (```json ... ```)
        - Лишние пробелы и переносы строк в начале/конце
        - Обратные кавычки и одинарные кавычки вокруг JSON
        - Лишние кавычки в начале и конце строки
        """
        if not text:
            return text
        
        # Удаляем markdown код-блоки (может быть в начале или в конце)
        text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
        
        # Удаляем обратные кавычки в начале и конце
        text = text.strip().strip('`')
        
        # Удаляем одинарные или двойные кавычки, если они оборачивают весь JSON
        # (но только если это действительно обертка, а не часть JSON)
        text = text.strip()
        if text.startswith("'") and text.endswith("'"):
            # Проверяем, что это не часть JSON (например, строка внутри JSON)
            # Если после первой кавычки идет { или [, то это обертка
            if len(text) > 2 and text[1] in ['{', '[']:
                text = text[1:-1]
        elif text.startswith('"') and text.endswith('"'):
            if len(text) > 2 and text[1] in ['{', '[']:
                text = text[1:-1]
        
        # Удаляем лишние пробелы и переносы строк
        text = text.strip()
        
        return text

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        raw = resp.text

        # Очищаем ответ от markdown разметки
        cleaned = self._clean_json_response(raw)
        
        app_logger.debug("Gemini raw response: %s", raw[:200] if len(raw) > 200 else raw)
        app_logger.debug("Gemini cleaned response: %s", cleaned[:200] if len(cleaned) > 200 else cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Логируем ошибку с полным контекстом
            app_logger.error(
                "Failed to parse Gemini JSON response. Raw: %s, Cleaned: %s, Error: %s",
                raw[:500] if len(raw) > 500 else raw,
                cleaned[:500] if len(cleaned) > 500 else cleaned,
                str(e),
            )
            raise ValueError(f"Gemini returned invalid JSON. Error: {e}. Cleaned response: {cleaned[:200]}") from e


class OpenAIClient(LLMClient):
    """
    Клиент для работы с OpenAI API.
    
    Пока — заглушка, позже можно реализовать через официальное OpenAI API.
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


def create_llm_client() -> LLMClient:
    """
    Фабрика для создания LLM-клиента на основе настроек.
    """
    provider = settings.LLM_PROVIDER

    if provider == "gemini":
        return GeminiClient()

    if provider == "openai":
        return OpenAIClient()

    raise ValueError(f"Unsupported LLM provider: {provider}")

