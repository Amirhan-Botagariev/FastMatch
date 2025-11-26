from __future__ import annotations

from io import BytesIO

import docx  # python-docx

from app.modules.file_extractors.core.base import FileTextExtractor
from app.modules.file_extractors.models import FileExtractResult


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