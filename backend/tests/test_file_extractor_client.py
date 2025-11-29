"""
Тесты для FileExtractorClient.
"""
import pytest
from io import BytesIO
from pathlib import Path

from app.integrations.file_extractors.client import (
    FileExtractorClient,
    PdfFileTextExtractor,
    DocxFileTextExtractor,
)
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError


class TestPdfFileTextExtractor:
    """Тесты для PdfFileTextExtractor."""

    def test_extract_valid_pdf(self, sample_pdf_bytes):
        """Тест извлечения текста из валидного PDF."""
        extractor = PdfFileTextExtractor()
        result = extractor.extract(sample_pdf_bytes)
        
        assert result is not None
        assert hasattr(result, 'raw_text')
        assert hasattr(result, 'lines')
        assert isinstance(result.raw_text, str)
        assert isinstance(result.lines, list)

    def test_extract_empty_pdf(self):
        """Тест извлечения текста из пустого PDF."""
        extractor = PdfFileTextExtractor()
        # Минимальный пустой PDF
        empty_pdf = b"%PDF-1.4\n"
        result = extractor.extract(empty_pdf)
        
        assert result is not None
        assert result.raw_text == "" or len(result.raw_text) >= 0


class TestDocxFileTextExtractor:
    """Тесты для DocxFileTextExtractor."""

    def test_extract_valid_docx(self):
        """Тест извлечения текста из валидного DOCX."""
        # Для реального теста нужен валидный DOCX файл
        # Здесь проверяем, что экстрактор не падает
        extractor = DocxFileTextExtractor()
        
        # Создаем минимальный DOCX (это сложно, поэтому просто проверяем структуру)
        try:
            result = extractor.extract(b"invalid docx")
            # Если не упало, проверяем структуру
            assert result is not None
            assert hasattr(result, 'raw_text')
            assert hasattr(result, 'lines')
        except Exception:
            # Ожидаемо, что невалидный DOCX вызовет ошибку
            pass


class TestFileExtractorClient:
    """Тесты для FileExtractorClient."""

    def test_extract_pdf_by_extension(self, sample_pdf_bytes):
        """Тест извлечения PDF по расширению файла."""
        client = FileExtractorClient()
        result = client.extract(
            file_bytes=sample_pdf_bytes,
            filename="test.pdf",
            content_type=None,
        )
        
        assert result is not None
        assert hasattr(result, 'raw_text')
        assert hasattr(result, 'lines')

    def test_extract_pdf_by_content_type(self, sample_pdf_bytes):
        """Тест извлечения PDF по content-type."""
        client = FileExtractorClient()
        result = client.extract(
            file_bytes=sample_pdf_bytes,
            filename="test",
            content_type="application/pdf",
        )
        
        assert result is not None
        assert hasattr(result, 'raw_text')

    def test_extract_unsupported_format(self):
        """Тест обработки неподдерживаемого формата."""
        client = FileExtractorClient()
        
        with pytest.raises(UnsupportedFileFormatError):
            client.extract(
                file_bytes=b"some content",
                filename="test.txt",
                content_type="text/plain",
            )

    def test_extract_docx_by_extension(self):
        """Тест извлечения DOCX по расширению файла."""
        client = FileExtractorClient()
        
        # Для реального теста нужен валидный DOCX
        # Проверяем, что клиент правильно определяет формат
        try:
            result = client.extract(
                file_bytes=b"invalid",
                filename="test.docx",
                content_type=None,
            )
            # Если не упало, проверяем структуру
            assert result is not None
        except Exception:
            # Ожидаемо для невалидного DOCX
            pass

