from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from io import BytesIO

from PyPDF2 import PdfReader
import docx

from app.integrations.file_extractors.models import FileExtractResult
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError


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


class PdfFileTextExtractor(FileTextExtractor):
    """
    Экстрактор текста из PDF с помощью PyPDF2.

    Ограничения:
      - PyPDF2 не всегда идеально достаёт текст (особенно из сложных PDF),
        но для MVP обычно достаточно.
      - При необходимости можно заменить реализацию на pdfplumber/PyMuPDF,
        не меняя интерфейс FileTextExtractor.
    """

    def extract(self, file_bytes: bytes) -> FileExtractResult:
        reader = PdfReader(BytesIO(file_bytes))
        texts = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)

        full_text = "\n".join(texts)

        # Разбиваем по строкам и слегка чистим пробелы
        lines = [line.strip() for line in full_text.splitlines()]

        return FileExtractResult(raw_text=full_text, lines=lines)


class DocxFileTextExtractor(FileTextExtractor):
    """
    Экстрактор текста из DOCX (Word) с помощью python-docx.
    """

    def extract(self, file_bytes: bytes) -> FileExtractResult:
        document = docx.Document(BytesIO(file_bytes))

        paragraphs = [p.text.strip() for p in document.paragraphs]

        # Убираем полностью пустые абзацы — они редко несут полезную инфу
        cleaned_paragraphs = [p for p in paragraphs if p]

        full_text = "\n".join(cleaned_paragraphs)

        return FileExtractResult(raw_text=full_text, lines=cleaned_paragraphs)


class FileExtractorClient:
    """
    Клиент для извлечения текста из файлов.
    
    Использование:
        client = FileExtractorClient()
        result = await client.extract(file_bytes, filename, content_type)
    """

    PDF_CONTENT_TYPES = {"application/pdf"}
    DOCX_CONTENT_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self) -> None:
        self._pdf_extractor = PdfFileTextExtractor()
        self._docx_extractor = DocxFileTextExtractor()

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str],
    ) -> FileExtractResult:
        """
        Извлекает текст из файла, выбирая подходящий экстрактор.
        
        Raises:
            UnsupportedFileFormatError: если формат файла не поддерживается
        """
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            return self._pdf_extractor.extract(file_bytes)
        if extension == ".docx":
            return self._docx_extractor.extract(file_bytes)

        if content_type in self.PDF_CONTENT_TYPES:
            return self._pdf_extractor.extract(file_bytes)
        if content_type in self.DOCX_CONTENT_TYPES:
            return self._docx_extractor.extract(file_bytes)

        raise UnsupportedFileFormatError(
            f"Unsupported file format: extension={extension!r}, "
            f"content_type={content_type!r}"
        )

