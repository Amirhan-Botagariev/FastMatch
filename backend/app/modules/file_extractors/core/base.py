from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.file_extractors.models import FileExtractResult


class FileTextExtractor(ABC):
    """
    Базовый интерфейс для экстрактора текста из файла.
    Реализации зависят от формата (PDF, DOCX и т.п.).
    """

    @abstractmethod
    def extract(self, file_bytes: bytes) -> FileExtractResult:
        """
        Извлечь текст и строки из сырых байт файла.
        """
        raise NotImplementedError