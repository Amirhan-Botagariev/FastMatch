from __future__ import annotations

from typing import List, Optional, Dict

from fastapi import UploadFile, HTTPException, status

from app.core.logger import app_logger
from app.modules.resumes.domain import BaseResume, ParsedResumeData
from app.modules.resumes.storage import FileStorage
from app.modules.resumes.parsing.pipeline import ResumeParsingPipeline
from app.modules.file_extractors import UnsupportedFileFormatError  # <-- новый импорт


class ResumeService:
    """
    Сервис для работы с базовым резюме.

    Инкапсулирует:
      - сохранение файла (FileStorage)
      - парсинг через ResumeParsingPipeline
      - создание доменной сущности BaseResume

    Пока мы не подключили БД, резюме хранятся в памяти (_in_memory_store),
    чтобы можно было быстро писать и гонять юнит-тесты.
    """

    def __init__(
        self,
        file_storage: FileStorage,
        parsing_pipeline: ResumeParsingPipeline,
    ) -> None:
        self._file_storage = file_storage
        self._parsing_pipeline = parsing_pipeline

        # Временное хранилище резюме в памяти (до появления БД)
        self._in_memory_store: Dict[str, BaseResume] = {}

    async def create_base_resume_from_upload(
        self,
        file: UploadFile,
        user_id: Optional[str] = None,  # user_id пока не используем, но оставляем для будущего
    ) -> tuple[BaseResume, List[str]]:
        """
        Основной сценарий:

        1. Принять файл от пользователя.
        2. Сохранить его во внешнее хранилище (пока на диск).
        3. Попробовать распарсить через ResumeParsingPipeline.
        4. Создать доменную сущность BaseResume.
        5. Положить её во временное in-memory хранилище.
        6. Вернуть резюме и список warnings.

        Поведение по ТЗ:

          - Неподдерживаемый формат (например, .txt) → HTTP 400.
          - Ошибка парсинга → parsed_data = None + warning в ответе.
        """
        warnings: List[str] = []

        app_logger.info("Uploading resume file: %s (%s)", file.filename, file.content_type)

        # Читаем содержимое файла
        file_bytes = await file.read()

        # 1. Сохраняем файл в хранилище (даже если парсинг упадёт — файл у нас останется)
        saved_path = await self._file_storage.save(file_bytes, file.filename)
        app_logger.debug("Resume file saved at: %s", saved_path)

        # 2. Пытаемся распарсить через пайплайн
        parsed_data: Optional[ParsedResumeData] = None
        try:
            parsed_data = self._parsing_pipeline.parse(
                file_bytes=file_bytes,
                filename=file.filename,
                content_type=file.content_type,
            )
            app_logger.info(
                "Resume parsed successfully: filename=%s, sections_count=%s",
                file.filename,
                len(parsed_data.sections) if parsed_data and parsed_data.sections else 0,
            )
        except UnsupportedFileFormatError as exc:
            # Неподдерживаемый формат — это явная ошибка клиента → 400
            app_logger.warning(
                "Unsupported resume file format: filename=%s, content_type=%s",
                file.filename,
                file.content_type,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            # Любая иная ошибка парсинга:
            # по ТЗ — не падаем, а возвращаем parsed_data=None + warning
            app_logger.exception(
                exc,
                "Failed to parse resume file",
                filename=file.filename,
            )
            warnings.append("Failed to parse resume. Parsed data is not available.")
            parsed_data = None

        # 3. Создаём доменную сущность через фабричный метод
        resume = BaseResume.create(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            file_path=saved_path,
            parsed_data=parsed_data,
        )

        # 4. Временно кладём резюме в память (позже тут будет репозиторий/БД)
        self._in_memory_store[str(resume.id)] = resume
        return resume, warnings

    # На будущее — методы для получения резюме из хранилища (in-memory пока):

    def get_resume(self, resume_id: str) -> Optional[BaseResume]:
        return self._in_memory_store.get(resume_id)

    def list_resumes(self) -> List[BaseResume]:
        return list(self._in_memory_store.values())