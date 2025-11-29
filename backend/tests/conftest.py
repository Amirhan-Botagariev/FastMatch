"""
Конфигурация pytest для всех тестов.
"""
import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from app.integrations.file_extractors.client import FileExtractorClient
from app.integrations.llm.client import LLMClient


@pytest.fixture(autouse=True)
def disable_logging():
    """
    Автоматически отключает логирование во время тестов.
    Это предотвращает засорение app.log ошибками из тестов.
    """
    # Сохраняем текущий уровень логирования
    logger = logging.getLogger("FastMatch")
    original_level = logger.level
    
    # Отключаем все логи во время тестов
    logger.setLevel(logging.CRITICAL)
    
    # Также отключаем все обработчики
    original_handlers = logger.handlers[:]
    logger.handlers.clear()
    
    yield
    
    # Восстанавливаем после теста
    logger.setLevel(original_level)
    logger.handlers = original_handlers


@pytest.fixture
def enable_test_logging():
    """
    Фикстура для включения логирования в конкретном тесте, если нужно.
    Использование: def test_something(enable_test_logging):
    """
    logger = logging.getLogger("FastMatch")
    logger.setLevel(logging.DEBUG)
    yield
    logger.setLevel(logging.CRITICAL)


@pytest.fixture
def temp_storage_dir():
    """Создает временную директорию для хранения файлов."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_file_extractor_client():
    """Мок для FileExtractorClient."""
    client = Mock(spec=FileExtractorClient)
    return client


@pytest.fixture
def mock_llm_client():
    """Мок для LLMClient."""
    client = Mock(spec=LLMClient)
    return client


@pytest.fixture
def sample_pdf_bytes():
    """Пример байтов PDF файла (минимальный валидный PDF)."""
    # Минимальный валидный PDF
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"


@pytest.fixture
def sample_docx_bytes():
    """Пример байтов DOCX файла."""
    # Минимальный валидный DOCX (ZIP архив с определенной структурой)
    # Для тестов используем простой мок
    return b"PK\x03\x04" + b"\x00" * 100  # Минимальный ZIP заголовок


@pytest.fixture
def sample_resume_text():
    """Пример текста резюме для тестов."""
    return """
    John Doe
    Software Engineer
    
    Experience:
    - Senior Developer at Company X (2020-2024)
    - Junior Developer at Company Y (2018-2020)
    
    Education:
    - BS in Computer Science, University Z (2014-2018)
    
    Skills:
    - Python, JavaScript, SQL
    """


@pytest.fixture
def sample_llm_response():
    """Пример ответа от LLM для тестов."""
    return {
        "sections": [
            {
                "title": "Experience",
                "content": "Senior Developer at Company X (2020-2024), Junior Developer at Company Y (2018-2020)",
                "raw_content": "Experience:\n- Senior Developer at Company X (2020-2024)\n- Junior Developer at Company Y (2018-2020)"
            },
            {
                "title": "Education",
                "content": "BS in Computer Science, University Z (2014-2018)",
                "raw_content": "Education:\n- BS in Computer Science, University Z (2014-2018)"
            },
            {
                "title": "Skills",
                "content": "Python, JavaScript, SQL",
                "raw_content": "Skills:\n- Python, JavaScript, SQL"
            }
        ]
    }

