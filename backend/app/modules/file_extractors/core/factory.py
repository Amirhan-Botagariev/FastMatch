from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.modules.file_extractors.core.base import FileTextExtractor
from app.modules.file_extractors.core.pdf_extractor import PdfFileTextExtractor
from app.modules.file_extractors.core.docx_extractor import DocxFileTextExtractor
from app.modules.file_extractors import UnsupportedFileFormatError


class FileTextExtractorFactory:
    """
    Фабрика для выбора нужного экстрактора по расширению/контент-тайпу.

    Использование:
        factory = FileTextExtractorFactory()
        extractor = factory.get_extractor(filename, content_type)
        result = extractor.extract(file_bytes)
    """

    PDF_CONTENT_TYPES = {"application/pdf"}
    DOCX_CONTENT_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def get_extractor(
        self,
        filename: str,
        content_type: Optional[str],
    ) -> FileTextExtractor:
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            return PdfFileTextExtractor()
        if extension == ".docx":
            return DocxFileTextExtractor()

        if content_type in self.PDF_CONTENT_TYPES:
            return PdfFileTextExtractor()
        if content_type in self.DOCX_CONTENT_TYPES:
            return DocxFileTextExtractor()

        raise UnsupportedFileFormatError(
            f"Unsupported file format: extension={extension!r}, "
            f"content_type={content_type!r}"
        )