"""
Тесты для IngestionService.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.features.resumes.ingestion.service import IngestionService
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError
from app.integrations.file_extractors.models import FileExtractResult


class TestIngestionService:
    """Тесты для IngestionService."""

    @pytest.mark.asyncio
    async def test_save_file_success(self, temp_storage_dir, sample_pdf_bytes):
        """Тест успешного сохранения файла."""
        service = IngestionService(storage_base_dir=temp_storage_dir)
        
        result_path = await service.save_file(sample_pdf_bytes, "test.pdf")
        
        assert result_path is not None
        assert Path(result_path).exists()
        assert Path(result_path).is_file()
        
        # Проверяем, что файл содержит правильные данные
        with open(result_path, "rb") as f:
            saved_data = f.read()
        assert saved_data == sample_pdf_bytes

    @pytest.mark.asyncio
    async def test_save_file_generates_uuid(self, temp_storage_dir, sample_pdf_bytes):
        """Тест генерации UUID для имени файла."""
        service = IngestionService(storage_base_dir=temp_storage_dir)
        
        result_path = await service.save_file(sample_pdf_bytes, "test.pdf")
        filename = Path(result_path).name
        
        # Проверяем, что имя файла содержит UUID и расширение
        assert filename.endswith(".pdf")
        assert len(filename) > 4  # UUID + расширение

    @pytest.mark.asyncio
    async def test_save_file_sanitizes_filename(self, temp_storage_dir, sample_pdf_bytes):
        """Тест очистки имени файла от опасных символов."""
        service = IngestionService(storage_base_dir=temp_storage_dir)
        
        # Пытаемся сохранить файл с опасным именем
        dangerous_name = "../../../etc/passwd.pdf"
        result_path = await service.save_file(sample_pdf_bytes, dangerous_name)
        
        # Проверяем, что путь не содержит ../ и находится в temp_storage_dir
        assert str(result_path).startswith(str(temp_storage_dir))
        assert "../" not in result_path

    def test_extract_text_success(self, mock_file_extractor_client):
        """Тест успешного извлечения текста."""
        expected_text = "Sample resume text"
        mock_file_extractor_client.extract.return_value = FileExtractResult(
            raw_text=expected_text,
            lines=[expected_text]
        )
        
        service = IngestionService(extractor_client=mock_file_extractor_client)
        
        result = service.extract_text(
            file_bytes=b"test",
            filename="test.pdf",
            content_type="application/pdf",
        )
        
        assert result == expected_text
        mock_file_extractor_client.extract.assert_called_once()

    def test_extract_text_unsupported_format(self, mock_file_extractor_client):
        """Тест обработки неподдерживаемого формата."""
        mock_file_extractor_client.extract.side_effect = UnsupportedFileFormatError(
            "Unsupported format"
        )
        
        service = IngestionService(extractor_client=mock_file_extractor_client)
        
        with pytest.raises(UnsupportedFileFormatError):
            service.extract_text(
                file_bytes=b"test",
                filename="test.txt",
                content_type="text/plain",
            )

    def test_extract_text_extraction_error(self, mock_file_extractor_client):
        """Тест обработки ошибки извлечения текста."""
        mock_file_extractor_client.extract.side_effect = Exception("Extraction failed")
        
        service = IngestionService(extractor_client=mock_file_extractor_client)
        
        with pytest.raises(Exception, match="Extraction failed"):
            service.extract_text(
                file_bytes=b"test",
                filename="test.pdf",
                content_type="application/pdf",
            )

