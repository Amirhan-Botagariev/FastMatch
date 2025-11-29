from __future__ import annotations

from pathlib import Path
import uuid

import aiofiles

from app.core.logging import app_logger
from app.integrations.file_extractors.client import FileExtractorClient
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError


class IngestionService:
    """
    Сервис для приема и первичной обработки резюме.
    
    Отвечает за:
      - Сохранение файла на диск
      - Извлечение текста из файла через file_extractors
    """

    def __init__(
        self,
        storage_base_dir: str = "storage/resumes",
        extractor_client: FileExtractorClient | None = None,
    ) -> None:
        self.base_dir = Path(storage_base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._extractor_client = extractor_client or FileExtractorClient()

    async def save_file(self, data: bytes, filename: str) -> str:
        """
        Сохраняет файл на диск и возвращает путь к сохраненному файлу.
        """
        try:
            # Очищаем имя — убираем возможные '../' и т.п.
            safe_name = Path(filename).name

            # Достаём расширение (включая точку), например ".pdf" или ".docx"
            ext = Path(safe_name).suffix.lower()

            # Генерируем UUID и используем его как базовое имя файла
            file_id = uuid.uuid4()
            disk_name = f"{file_id}{ext}"

            target_path = self.base_dir / disk_name

            # Пишем данные асинхронно
            async with aiofiles.open(target_path, "wb") as f:
                await f.write(data)

            app_logger.debug("Resume file saved at: %s", target_path)
            return str(target_path)
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to save resume file",
                filename=filename,
                file_size=len(data),
            )
            raise

    def extract_text(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str | None,
    ) -> str:
        """
        Извлекает текст из файла через file_extractors.
        
        Raises:
            UnsupportedFileFormatError: если формат файла не поддерживается
        """
        try:
            result = self._extractor_client.extract(
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
            )
            app_logger.debug(
                "Text extracted successfully: filename=%s, text_length=%d",
                filename,
                len(result.raw_text),
            )
            return result.raw_text
        except UnsupportedFileFormatError:
            app_logger.warning(
                "Unsupported resume file format: filename=%s, content_type=%s",
                filename,
                content_type,
            )
            raise
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to extract text from file",
                filename=filename,
                content_type=content_type,
                file_size=len(file_bytes),
            )
            raise

