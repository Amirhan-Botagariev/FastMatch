import json
from typing import Any, Dict

from google import genai

from app.core.config import settings
from app.integrations.llm.base import LLMClient

from app.core.debugger import debug


class GeminiClient(LLMClient):
    def __init__(self, model: str | None = None) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = model or settings.GEMINI_MODEL  # например "gemini-2.5-flash"

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        raw = resp.text

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            # здесь можно залогировать сырое тело, кинуть своё доменное исключение и т.п.
            raise ValueError(f"Gemini returned invalid JSON: {raw!r}") from e