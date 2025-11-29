"""
Тесты для LLM клиентов.
"""
import pytest
import json
from unittest.mock import Mock, patch

from app.integrations.llm.client import GeminiClient


class TestGeminiClient:
    """Тесты для GeminiClient."""

    @patch('app.integrations.llm.client.genai')
    def test_generate_json_success(self, mock_genai, sample_llm_response):
        """Тест успешной генерации JSON."""
        # Настраиваем мок
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(sample_llm_response)
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        result = client.generate_json("test prompt")
        
        assert result == sample_llm_response
        mock_client.models.generate_content.assert_called_once()

    @patch('app.integrations.llm.client.genai')
    def test_generate_json_with_markdown(self, mock_genai, sample_llm_response):
        """Тест генерации JSON с markdown разметкой."""
        # Настраиваем мок с markdown оберткой
        mock_client = Mock()
        mock_response = Mock()
        json_text = json.dumps(sample_llm_response)
        mock_response.text = f"```json\n{json_text}\n```"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        result = client.generate_json("test prompt")
        
        assert result == sample_llm_response

    @patch('app.integrations.llm.client.genai')
    def test_generate_json_invalid_json(self, mock_genai):
        """Тест обработки невалидного JSON."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "not a valid json"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        
        with pytest.raises(ValueError, match="invalid JSON"):
            client.generate_json("test prompt")


class TestCleanJsonResponse:
    """Тесты для функции очистки JSON ответа через GeminiClient."""

    @patch('app.integrations.llm.client.genai')
    def test_clean_markdown_code_block(self, mock_genai, sample_llm_response):
        """Тест очистки markdown код-блока."""
        json_text = json.dumps(sample_llm_response)
        wrapped = f"```json\n{json_text}\n```"
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = wrapped
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        result = client.generate_json("test")
        
        assert result == sample_llm_response

    @patch('app.integrations.llm.client.genai')
    def test_clean_with_backticks(self, mock_genai, sample_llm_response):
        """Тест очистки обратных кавычек."""
        json_text = json.dumps(sample_llm_response)
        wrapped = f"`{json_text}`"
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = wrapped
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        result = client.generate_json("test")
        
        assert result == sample_llm_response

    @patch('app.integrations.llm.client.genai')
    def test_clean_with_quotes(self, mock_genai, sample_llm_response):
        """Тест очистки кавычек."""
        json_text = json.dumps(sample_llm_response)
        wrapped = f'"{json_text}"'
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = wrapped
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        client = GeminiClient()
        result = client.generate_json("test")
        
        assert result == sample_llm_response

