"""
Тесты для ResumeService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile
from io import BytesIO

from app.features.resumes.service import ResumeService
from app.features.resumes.models import BaseResume, ParsedResumeData, Section
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError


class TestResumeService:
    """Тесты для ResumeService."""

    @pytest.fixture
    def mock_ingestion_service(self):
        """Мок для IngestionService."""
        service = Mock()
        service.save_file = AsyncMock(return_value="/path/to/saved/file.pdf")
        service.extract_text = Mock(return_value="Sample resume text")
        return service

    @pytest.fixture
    def mock_parsing_service(self, sample_llm_response):
        """Мок для ParsingService."""
        service = Mock()
        parsed_data = ParsedResumeData(
            raw_text="Sample resume text",
            sections=[
                Section(
                    title="Experience",
                    content="Content",
                    raw_content="Raw content",
                    order=0,
                )
            ],
        )
        service.parse = Mock(return_value=parsed_data)
        return service

    @pytest.fixture
    def sample_upload_file(self, sample_pdf_bytes):
        """Создает мок UploadFile."""
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=sample_pdf_bytes)
        return file

    @pytest.mark.asyncio
    async def test_create_resume_success(
        self,
        mock_ingestion_service,
        mock_parsing_service,
        sample_upload_file,
    ):
        """Тест успешного создания резюме."""
        service = ResumeService(
            ingestion_service=mock_ingestion_service,
            parsing_service=mock_parsing_service,
        )
        
        resume, warnings = await service.create_base_resume_from_upload(
            file=sample_upload_file,
        )
        
        assert isinstance(resume, BaseResume)
        assert resume.filename == "test.pdf"
        assert resume.parsed_data is not None
        assert len(resume.parsed_data.sections) == 1
        assert len(warnings) == 0
        
        mock_ingestion_service.save_file.assert_called_once()
        mock_ingestion_service.extract_text.assert_called_once()
        mock_parsing_service.parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_resume_unsupported_format(
        self,
        mock_ingestion_service,
        mock_parsing_service,
        sample_upload_file,
    ):
        """Тест обработки неподдерживаемого формата."""
        mock_ingestion_service.extract_text.side_effect = UnsupportedFileFormatError(
            "Unsupported format"
        )
        
        service = ResumeService(
            ingestion_service=mock_ingestion_service,
            parsing_service=mock_parsing_service,
        )
        
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_base_resume_from_upload(file=sample_upload_file)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_resume_parsing_failure(
        self,
        mock_ingestion_service,
        mock_parsing_service,
        sample_upload_file,
    ):
        """Тест обработки ошибки парсинга."""
        mock_parsing_service.parse.side_effect = Exception("Parsing failed")
        
        service = ResumeService(
            ingestion_service=mock_ingestion_service,
            parsing_service=mock_parsing_service,
        )
        
        resume, warnings = await service.create_base_resume_from_upload(
            file=sample_upload_file,
        )
        
        # Резюме должно быть создано, но без parsed_data
        assert isinstance(resume, BaseResume)
        assert resume.parsed_data is None
        assert len(warnings) == 1
        assert "Failed to parse" in warnings[0]

    @pytest.mark.asyncio
    async def test_create_resume_save_file_failure(
        self,
        mock_ingestion_service,
        mock_parsing_service,
        sample_upload_file,
    ):
        """Тест обработки ошибки сохранения файла."""
        mock_ingestion_service.save_file.side_effect = Exception("Save failed")
        
        service = ResumeService(
            ingestion_service=mock_ingestion_service,
            parsing_service=mock_parsing_service,
        )
        
        with pytest.raises(Exception, match="Save failed"):
            await service.create_base_resume_from_upload(file=sample_upload_file)

