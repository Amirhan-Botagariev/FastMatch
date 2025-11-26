from __future__ import annotations

from io import BytesIO

from PyPDF2 import PdfReader

from app.modules.file_extractors.core.base import FileTextExtractor
from app.modules.file_extractors.models import FileExtractResult


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