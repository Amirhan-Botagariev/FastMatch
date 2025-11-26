from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


# ========= Секция резюме =========


@dataclass
class Section:
    """
    Одна секция резюме (доменная модель).
    """
    title: Optional[str] = None        # Заголовок секции, если есть
    content: Optional[str] = None      # Нормализованный текст секции
    raw_content: Optional[str] = None  # Сырой текст секции (как вытащили из файла)

    # опционально можно добавить order, если хочешь явно хранить позицию
    order: Optional[int] = None        # Порядковый номер секции в резюме


# ========= Распарсенное резюме =========


@dataclass
class ParsedResumeData:
    """
    Результат парсинга резюме.
    """
    raw_text: str                                # Полный текст резюме
    sections: List[Section] = field(default_factory=list)
    meta: dict = field(default_factory=dict)     # Для любых дополнительных данных, если захотим


# ========= Базовое резюме (загруженный файл) =========


@dataclass
class BaseResume:
    """
    Базовое (оригинальное) резюме, загруженное пользователем.

    Здесь:
      - метаданные файла
      - путь к файлу
      - результат парсинга (ParsedResumeData) — уже в виде секций.
    """
    id: uuid.UUID
    filename: str
    content_type: str
    file_path: str                            # путь до сохранённого файла (на диске/S3 и т.д.)
    parsed_data: Optional[ParsedResumeData] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        filename: str,
        content_type: str,
        file_path: str,
        parsed_data: Optional[ParsedResumeData] = None,
    ) -> "BaseResume":
        """
        Фабричный метод — единая точка создания базового резюме.
        """
        return cls(
            id=uuid.uuid4(),
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            parsed_data=parsed_data,
        )