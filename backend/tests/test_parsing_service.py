"""
Тесты для ParsingService.
"""
import pytest
from unittest.mock import Mock

from app.features.resumes.parsing.service import ParsingService
from app.features.resumes.models import ParsedResumeData, Section


class TestParsingService:
    """Тесты для ParsingService."""

    def test_parse_success(self, mock_llm_client, sample_llm_response, sample_resume_text):
        """Тест успешного парсинга резюме."""
        mock_llm_client.generate_json.return_value = sample_llm_response
        
        service = ParsingService(mock_llm_client)
        result = service.parse(sample_resume_text)
        
        assert isinstance(result, ParsedResumeData)
        assert result.raw_text == sample_resume_text
        assert len(result.sections) == 3
        assert all(isinstance(s, Section) for s in result.sections)
        
        # Проверяем первую секцию
        first_section = result.sections[0]
        assert first_section.title == "Experience"
        assert first_section.order == 0
        
        mock_llm_client.generate_json.assert_called_once()

    def test_parse_empty_response(self, mock_llm_client, sample_resume_text):
        """Тест парсинга с пустым ответом от LLM."""
        mock_llm_client.generate_json.return_value = {"sections": []}
        
        service = ParsingService(mock_llm_client)
        result = service.parse(sample_resume_text)
        
        assert isinstance(result, ParsedResumeData)
        assert len(result.sections) == 0

    def test_parse_llm_error(self, mock_llm_client, sample_resume_text):
        """Тест обработки ошибки от LLM."""
        mock_llm_client.generate_json.side_effect = Exception("LLM error")
        
        service = ParsingService(mock_llm_client)
        
        with pytest.raises(Exception, match="LLM error"):
            service.parse(sample_resume_text)

    def test_parse_invalid_response_structure(self, mock_llm_client, sample_resume_text):
        """Тест обработки невалидной структуры ответа."""
        mock_llm_client.generate_json.return_value = {"invalid": "structure"}
        
        service = ParsingService(mock_llm_client)
        result = service.parse(sample_resume_text)
        
        # Должен вернуть ParsedResumeData с пустыми секциями
        assert isinstance(result, ParsedResumeData)
        assert len(result.sections) == 0

