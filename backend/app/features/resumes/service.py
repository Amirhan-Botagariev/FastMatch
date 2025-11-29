from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import app_logger
from app.features.resumes.models import BaseResume, ParsedResumeData
from app.features.resumes.ingestion.service import IngestionService
from app.features.resumes.parsing.service import ParsingService
from app.features.resumes.parsing.utils import (
    build_resume_customization_prompt,
    build_cover_letter_prompt,
)
from app.features.resumes.persistence.repository import ResumeRepository
from app.features.resumes.persistence.models import ResumeModel, ResumeVersionModel
from app.integrations.file_extractors.exceptions import UnsupportedFileFormatError
from app.integrations.llm.client import LLMClient


class ResumeService:
    """
    Оркестратор сценариев работы с резюме.

    Инкапсулирует:
      - прием файла (IngestionService)
      - парсинг через ParsingService
      - создание доменной сущности BaseResume
      - работу с БД через ResumeRepository
    """

    def __init__(
        self,
        ingestion_service: IngestionService,
        parsing_service: ParsingService,
        db_session: Optional[AsyncSession] = None,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self._ingestion_service = ingestion_service
        self._parsing_service = parsing_service
        self._db_session = db_session
        self._llm_client = llm_client

    async def create_base_resume_from_upload(
        self,
        file: UploadFile,
        user_id: Optional[str] = None,
    ) -> tuple[BaseResume, List[str]]:
        """
        Основной сценарий:

        1. Принять файл от пользователя.
        2. Сохранить его во внешнее хранилище (пока на диск).
        3. Извлечь текст из файла.
        4. Попробовать распарсить через ParsingService.
        5. Создать доменную сущность BaseResume.
        6. Вернуть резюме и список warnings.

        Поведение по ТЗ:

          - Неподдерживаемый формат (например, .txt) → HTTP 400.
          - Ошибка парсинга → parsed_data = None + warning в ответе.
        """
        warnings: List[str] = []

        app_logger.info("Uploading resume file: %s (%s)", file.filename, file.content_type)

        # Читаем содержимое файла
        file_bytes = await file.read()

        # 1. Сохраняем файл в хранилище
        try:
            saved_path = await self._ingestion_service.save_file(file_bytes, file.filename or "unknown")
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to save resume file",
                filename=file.filename,
                file_size=len(file_bytes),
            )
            raise

        # 2. Извлекаем текст из файла
        try:
            raw_text = self._ingestion_service.extract_text(
                file_bytes=file_bytes,
                filename=file.filename or "unknown",
                content_type=file.content_type,
            )
        except UnsupportedFileFormatError as exc:
            # Неподдерживаемый формат — это явная ошибка клиента → 400
            app_logger.warning(
                "Unsupported file format rejected: filename=%s, content_type=%s",
                file.filename,
                file.content_type,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        # 3. Пытаемся распарсить через сервис парсинга
        parsed_data: Optional[ParsedResumeData] = None
        try:
            parsed_data = self._parsing_service.parse(raw_text)
            app_logger.info(
                "Resume parsed successfully: filename=%s, sections_count=%s",
                file.filename,
                len(parsed_data.sections) if parsed_data and parsed_data.sections else 0,
            )
        except Exception as exc:
            # Любая ошибка парсинга:
            # по ТЗ — не падаем, а возвращаем parsed_data=None + warning
            app_logger.exception(
                exc,
                "Failed to parse resume file",
                filename=file.filename,
            )
            warnings.append("Failed to parse resume. Parsed data is not available.")
            parsed_data = None

        # 4. Создаём доменную сущность через фабричный метод
        resume = BaseResume.create(
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_path=saved_path,
            parsed_data=parsed_data,
        )

        return resume, warnings

    async def list_resumes(
        self,
        user_id: Optional[UUID] = None,
    ) -> List[ResumeModel]:
        """
        Получает список резюме пользователя.

        Args:
            user_id: ID пользователя. Если None, возвращает все резюме.

        Returns:
            Список ORM-моделей резюме.
        """
        if self._db_session is None:
            app_logger.warning(
                "Database session not provided to ResumeService. "
                "Cannot retrieve resumes from database."
            )
            return []

        try:
            repository = ResumeRepository(self._db_session)
            resumes = await repository.list_by_user_id(user_id)
            app_logger.info(
                "Retrieved %d resumes for user_id=%s",
                len(resumes),
                user_id,
            )
            return resumes
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to list resumes",
                user_id=str(user_id) if user_id else None,
            )
            raise

    async def get_resume_by_id(
        self,
        resume_id: UUID,
    ) -> ResumeModel:
        """
        Получает резюме по ID с загруженными секциями.

        Args:
            resume_id: ID резюме

        Returns:
            ORM-модель резюме с секциями

        Raises:
            HTTPException: Если резюме не найдено
        """
        if self._db_session is None:
            app_logger.warning(
                "Database session not provided to ResumeService. "
                "Cannot retrieve resume from database."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available",
            )

        try:
            repository = ResumeRepository(self._db_session)
            resume = await repository.get_by_id(resume_id, load_sections=True)
            
            if resume is None:
                app_logger.warning("Resume not found: id=%s", resume_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume with id {resume_id} not found",
                )
            
            app_logger.info(
                "Resume retrieved successfully: id=%s, sections_count=%d",
                resume_id,
                len(resume.sections) if resume.sections else 0,
            )
            return resume
        except HTTPException:
            # Перебрасываем HTTP исключения как есть
            raise
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to get resume by id",
                resume_id=str(resume_id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during resume retrieval",
            ) from exc

    async def create_custom_version(
        self,
        resume_id: UUID,
        job_description: str,
    ) -> ResumeVersionModel:
        """
        Создает кастомную версию резюме под описание вакансии через LLM.

        Args:
            resume_id: ID исходного резюме
            job_description: Описание вакансии

        Returns:
            Созданная модель версии с секциями

        Raises:
            HTTPException: Если резюме не найдено или произошла ошибка
        """
        if self._db_session is None:
            app_logger.warning(
                "Database session not provided to ResumeService. "
                "Cannot create resume version."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available",
            )

        if self._llm_client is None:
            app_logger.warning(
                "LLM client not provided to ResumeService. "
                "Cannot create resume version."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM client not available",
            )

        try:
            # Получаем исходное резюме с секциями
            repository = ResumeRepository(self._db_session)
            resume = await repository.get_by_id(resume_id, load_sections=True)
            
            if resume is None:
                app_logger.warning("Resume not found for version creation: id=%s", resume_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume with id {resume_id} not found",
                )

            if not resume.sections:
                app_logger.warning(
                    "Resume has no sections for version creation: id=%s",
                    resume_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resume has no sections to customize",
                )

            # Преобразуем секции в словари для промпта
            resume_sections = []
            for section in resume.sections:
                resume_sections.append({
                    "title": section.title,
                    "content": section.content,
                    "raw_content": section.raw_content,
                })

            # Формируем промпт для кастомизации
            prompt = build_resume_customization_prompt(resume_sections, job_description)
            
            # Вызываем LLM для кастомизации
            app_logger.info(
                "Creating custom resume version: resume_id=%s, job_description_length=%d",
                resume_id,
                len(job_description),
            )
            
            llm_response = self._llm_client.generate_json(prompt)
            
            if not isinstance(llm_response, dict) or "sections" not in llm_response:
                app_logger.error(
                    "Invalid LLM response for resume customization: %s",
                    llm_response,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from LLM for resume customization",
                )

            custom_sections = llm_response.get("sections", [])
            if not isinstance(custom_sections, list):
                custom_sections = []

            # Генерируем cover letter
            cover_letter: Optional[str] = None
            try:
                cover_letter_prompt = build_cover_letter_prompt(resume_sections, job_description)
                cover_letter_response = self._llm_client.generate_json(cover_letter_prompt)
                
                if isinstance(cover_letter_response, dict) and "cover_letter" in cover_letter_response:
                    cover_letter = cover_letter_response.get("cover_letter")
                    app_logger.info("Cover letter generated successfully for resume_id=%s", resume_id)
                else:
                    app_logger.warning(
                        "Invalid LLM response for cover letter generation: %s",
                        cover_letter_response,
                    )
            except Exception as exc:
                app_logger.exception(
                    exc,
                    "Failed to generate cover letter, continuing without it",
                    resume_id=str(resume_id),
                )
                # Продолжаем без cover letter, это не критично

            # Создаем версию в БД
            version = await repository.create_version(
                resume_id=resume_id,
                job_description=job_description,
                custom_sections=custom_sections,
                cover_letter=cover_letter,
            )

            app_logger.info(
                "Custom resume version created successfully: version_id=%s, resume_id=%s, sections_count=%d",
                version.id,
                resume_id,
                len(custom_sections),
            )

            return version
        except HTTPException:
            raise
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to create custom resume version",
                resume_id=str(resume_id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during resume version creation",
            ) from exc

    async def get_version_by_id(
        self,
        version_id: UUID,
    ) -> ResumeVersionModel:
        """
        Получает версию резюме по ID с загруженными секциями.

        Args:
            version_id: ID версии

        Returns:
            ORM-модель версии с секциями

        Raises:
            HTTPException: Если версия не найдена
        """
        if self._db_session is None:
            app_logger.warning(
                "Database session not provided to ResumeService. "
                "Cannot retrieve resume version from database."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available",
            )

        try:
            repository = ResumeRepository(self._db_session)
            version = await repository.get_version_by_id(version_id, load_sections=True)
            
            if version is None:
                app_logger.warning("Resume version not found: id=%s", version_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume version with id {version_id} not found",
                )
            
            app_logger.info(
                "Resume version retrieved successfully: id=%s, sections_count=%d",
                version_id,
                len(version.sections) if version.sections else 0,
            )
            return version
        except HTTPException:
            raise
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to get resume version by id",
                version_id=str(version_id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during resume version retrieval",
            ) from exc

