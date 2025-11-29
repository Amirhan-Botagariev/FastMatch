from __future__ import annotations

import os
from typing import Literal
from urllib.parse import quote_plus
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

        # Настройки PostgreSQL
        # Поддерживаем как DB_*, так и POSTGRES_* для обратной совместимости
        # Приоритет: DB_HOST > POSTGRES_HOST > localhost (для локального запуска)
        # Для локального запуска миграций используем localhost (порт проброшен из Docker)
        # Для запуска внутри Docker используем postgres (имя сервиса)
        # Если явно указан DB_HOST, используем его (имеет приоритет)
        # Иначе используем POSTGRES_HOST, если указан
        # Иначе используем localhost (для локального подключения к Docker контейнеру)
        self.DB_HOST: str = (
            os.getenv("DB_HOST") 
            or os.getenv("POSTGRES_HOST") 
            or "localhost"
        )
        self.DB_PORT: int = int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432"))
        self.DB_USER: str = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.DB_NAME: str = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "fastmatch")
        self.DB_ECHO: bool = self._bool(os.getenv("DB_ECHO", "false"))

    @property
    def DATABASE_URL(self) -> str:
        """
        Формирует URL для подключения к PostgreSQL.
        
        Использует URL-кодирование для учетных данных, чтобы корректно обрабатывать
        специальные символы в паролях и именах пользователей.
        """
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+asyncpg://{encoded_user}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @staticmethod
    def _bool(value: str) -> bool:
        return value.lower() in {"1", "true", "yes", "on"}


settings = Settings()