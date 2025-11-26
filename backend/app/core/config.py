from __future__ import annotations

import os
from typing import Literal
from dotenv import load_dotenv


load_dotenv()

class Settings:
    """
    Глобальные настройки приложения.
    Читаются из переменных окружения (или значений по умолчанию).
    """

    def __init__(self) -> None:
        # Общие настройки
        self.DEBUG: bool = self._bool(os.getenv("DEBUG", "false"))

        # Хранилище резюме
        self.RESUME_STORAGE_DIR: str = os.getenv(
            "RESUME_STORAGE_DIR",
            "storage/resumes"
        )

        raw = os.getenv("LLM_PROVIDER", "gemini").lower()
        allowed: tuple[Literal["gemini", "openai"], ...] = (
            "gemini", "openai",
        )
        if raw not in allowed:
            raise ValueError(f"Invalid LLM_PROVIDER '{raw}', expected one of {allowed}")

        self.LLM_PROVIDER: Literal["gemini", "openai"] = raw

        # Ключи API
        self.GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL: str | None = os.getenv("GEMINI_MODEL")

        self.OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

        # Таймауты LLM
        self.LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

    @staticmethod
    def _bool(value: str) -> bool:
        return value.lower() in {"1", "true", "yes", "on"}


settings = Settings()