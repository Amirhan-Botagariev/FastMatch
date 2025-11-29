from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import UUID

import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import app_logger
from app.features.resumes.schemas import (
    ResumeOut,
    SectionSchema,
    ResumeListItem,
    VersionCreate,
    VersionOut,
)
from app.features.resumes.service import ResumeService
from app.features.resumes.ingestion.service import IngestionService
from app.features.resumes.parsing.service import ParsingService
from app.integrations.llm.client import create_llm_client

router = APIRouter()


def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    """
    Простейшая "инъекция зависимостей":
      - IngestionService для приема и сохранения файлов
      - ParsingService для парсинга через LLM
      - ResumeService как оркестратор
      - AsyncSession для работы с БД
      - LLMClient для кастомизации резюме

    Позже это можно заменить на полноценный DI-контейнер.
    """
    ingestion_service = IngestionService()
    llm_client = create_llm_client()
    parsing_service = ParsingService(llm_client)
    
    return ResumeService(
        ingestion_service=ingestion_service,
        parsing_service=parsing_service,
        db_session=db,
        llm_client=llm_client,
    )


@router.post("/", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Загрузка файла резюме (PDF или DOCX).

    Сценарий:
      1. Принимаем файл.
      2. Сохраняем его (пока на диск).
      3. Парсим через ParsingService (LLM → секции).
      4. Создаём базовое резюме.
      5. Возвращаем метаданные + список секций.

    Ошибки:
      - 400 — если формат файла не поддерживается.
      - 201 с warnings — если файл загрузился, но распарсить не вышло.
    """
    try:
        app_logger.info(
            "Resume upload request received: filename=%s, content_type=%s",
            file.filename,
            file.content_type,
        )
        
        resume, warnings = await resume_service.create_base_resume_from_upload(
            file=file,
            user_id=None,  # auth пока не реализован
        )

        # Преобразуем доменные Section → SectionSchema для ответа API
        sections: list[SectionSchema] = []
        if resume.parsed_data is not None and resume.parsed_data.sections:
            for section in resume.parsed_data.sections:
                try:
                    # Преобразуем dataclass в словарь, исключая поле 'order' (его нет в схеме)
                    section_dict = {
                        "title": section.title,
                        "content": section.content,
                        "raw_content": section.raw_content,
                    }
                    sections.append(SectionSchema.model_validate(section_dict))
                except Exception as exc:
                    app_logger.warning(
                        "Failed to validate section schema: %s, error: %s",
                        section,
                        str(exc),
                    )
                    # Пропускаем проблемную секцию, но продолжаем обработку
                    continue

        app_logger.info(
            "Resume uploaded successfully: id=%s, filename=%s, sections_count=%d, warnings_count=%d",
            resume.id,
            resume.filename,
            len(sections),
            len(warnings),
        )

        return ResumeOut(
            id=resume.id,
            filename=resume.filename,
            content_type=resume.content_type,
            sections=sections,
            warnings=warnings,
            created_at=resume.created_at,
        )
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume upload",
            filename=file.filename,
            content_type=file.content_type,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume upload",
        ) from exc


@router.get("/", response_model=list[ResumeListItem])
async def list_resumes(
    user_id: Optional[UUID] = Query(None, description="ID пользователя (пока не используется)"),
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Получить список резюме пользователя.

    Возвращает упрощенный список резюме (без секций) для отображения в списке.
    Резюме отсортированы по дате создания (новые первыми).

    Args:
        user_id: ID пользователя. Если не указан, возвращает все резюме.

    Returns:
        Список резюме с базовой информацией (id, filename, content_type, created_at).
    """
    try:
        app_logger.info(
            "Resume list request received: user_id=%s",
            user_id,
        )

        resume_models = await resume_service.list_resumes(user_id=user_id)

        # Преобразуем ORM-модели в Pydantic схемы
        resume_list = [
            ResumeListItem(
                id=model.id,
                filename=model.filename,
                content_type=model.content_type,
                created_at=model.created_at,
            )
            for model in resume_models
        ]

        app_logger.info(
            "Resume list retrieved successfully: count=%d, user_id=%s",
            len(resume_list),
            user_id,
        )

        return resume_list
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume list retrieval",
            user_id=str(user_id) if user_id else None,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume list retrieval",
        ) from exc


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: UUID,
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Получить детальную информацию о резюме по ID.

    Возвращает полную информацию о резюме, включая:
    - Базовую информацию (id, filename, content_type, created_at)
    - Секции резюме (parsed_data)
    - Warnings (если были при загрузке/парсинге)

    Args:
        resume_id: UUID резюме

    Returns:
        Полная информация о резюме в формате ResumeOut

    Raises:
        404: Если резюме не найдено
        500: При внутренней ошибке сервера
    """
    try:
        app_logger.info(
            "Resume detail request received: resume_id=%s",
            resume_id,
        )

        resume_model = await resume_service.get_resume_by_id(resume_id)

        # Преобразуем ORM-модели секций в SectionSchema
        sections: list[SectionSchema] = []
        if resume_model.sections:
            for section_model in resume_model.sections:
                try:
                    section_data = {
                        "title": section_model.title,
                        "content": section_model.content,
                        "raw_content": section_model.raw_content,
                    }
                    sections.append(SectionSchema.model_validate(section_data))
                except Exception as exc:
                    app_logger.warning(
                        "Failed to validate section schema: section_id=%s, error=%s",
                        section_model.id,
                        str(exc),
                    )
                    # Пропускаем проблемную секцию, но продолжаем обработку
                    continue

        # Секции уже отсортированы по order в модели (order_by="ResumeSectionModel.order")

        app_logger.info(
            "Resume detail retrieved successfully: id=%s, sections_count=%d",
            resume_id,
            len(sections),
        )

        return ResumeOut(
            id=resume_model.id,
            filename=resume_model.filename,
            content_type=resume_model.content_type,
            sections=sections,
            warnings=[],  # Warnings не хранятся в БД, оставляем пустым
            created_at=resume_model.created_at,
        )
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume detail retrieval",
            resume_id=str(resume_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume detail retrieval",
        ) from exc


@router.get("/{resume_id}/file")
async def download_resume_file(
    resume_id: UUID,
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Скачать исходный файл резюме.

    Возвращает оригинальный файл резюме (PDF или DOCX), который был загружен.

    Args:
        resume_id: UUID резюме

    Returns:
        Файл с правильными заголовками Content-Type и Content-Disposition

    Raises:
        404: Если резюме не найдено или файл не существует
        500: При внутренней ошибке сервера
    """
    try:
        app_logger.info(
            "Resume file download request received: resume_id=%s",
            resume_id,
        )

        # Получаем резюме из БД
        resume_model = await resume_service.get_resume_by_id(resume_id)

        # Проверяем, что файл существует
        file_path = Path(resume_model.file_path)
        if not file_path.exists():
            app_logger.warning(
                "Resume file not found on disk: resume_id=%s, file_path=%s",
                resume_id,
                resume_model.file_path,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume file not found for resume {resume_id}",
            )

        # Читаем файл асинхронно
        try:
            async with aiofiles.open(file_path, "rb") as f:
                file_content = await f.read()
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to read resume file from disk",
                resume_id=str(resume_id),
                file_path=str(file_path),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read resume file",
            ) from exc

        app_logger.info(
            "Resume file downloaded successfully: resume_id=%s, filename=%s, size=%d bytes",
            resume_id,
            resume_model.filename,
            len(file_content),
        )

        # Возвращаем файл с правильными заголовками
        return Response(
            content=file_content,
            media_type=resume_model.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{resume_model.filename}"',
            },
        )
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume file download",
            resume_id=str(resume_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume file download",
        ) from exc


@router.post("/{resume_id}/versions", response_model=VersionOut, status_code=201)
async def create_resume_version(
    resume_id: UUID,
    version_data: VersionCreate,
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Создать кастомную версию резюме под описание вакансии.

    Использует LLM для адаптации резюме под требования вакансии:
    - Анализирует описание вакансии
    - Адаптирует секции резюме под требования
    - Подчеркивает релевантный опыт и навыки
    - Сохраняет структуру и язык исходного резюме

    Args:
        resume_id: UUID исходного резюме
        version_data: Данные для создания версии (job_description)

    Returns:
        Созданная версия резюме с кастомизированными секциями

    Raises:
        404: Если резюме не найдено
        400: Если у резюме нет секций для кастомизации
        500: При внутренней ошибке сервера
    """
    try:
        app_logger.info(
            "Resume version creation request received: resume_id=%s, job_description_length=%d",
            resume_id,
            len(version_data.job_description),
        )

        version = await resume_service.create_custom_version(
            resume_id=resume_id,
            job_description=version_data.job_description,
        )

        # Преобразуем ORM-модели секций в SectionSchema
        sections: list[SectionSchema] = []
        if version.sections:
            for section_model in version.sections:
                try:
                    section_data = {
                        "title": section_model.title,
                        "content": section_model.content,
                        "raw_content": section_model.raw_content,
                    }
                    sections.append(SectionSchema.model_validate(section_data))
                except Exception as exc:
                    app_logger.warning(
                        "Failed to validate section schema: section_id=%s, error=%s",
                        section_model.id,
                        str(exc),
                    )
                    continue

        app_logger.info(
            "Resume version created successfully: version_id=%s, resume_id=%s, sections_count=%d",
            version.id,
            resume_id,
            len(sections),
        )

        return VersionOut(
            id=version.id,
            resume_id=version.resume_id,
            job_description=version.job_description,
            sections=sections,
            created_at=version.created_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume version creation",
            resume_id=str(resume_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume version creation",
        ) from exc


@router.get("/versions/{version_id}", response_model=VersionOut)
async def get_resume_version(
    version_id: UUID,
    resume_service: ResumeService = Depends(get_resume_service),
):
    """
    Получить детальную информацию о версии резюме по ID.

    Возвращает полную информацию о версии резюме, включая:
    - Базовую информацию (id, resume_id, job_description, created_at)
    - Сопроводительное письмо (cover_letter)
    - Кастомизированные секции резюме (sections)

    Args:
        version_id: UUID версии резюме

    Returns:
        Полная информация о версии резюме в формате VersionOut

    Raises:
        404: Если версия не найдена
        500: При внутренней ошибке сервера
    """
    try:
        app_logger.info(
            "Resume version detail request received: version_id=%s",
            version_id,
        )

        version = await resume_service.get_version_by_id(version_id)

        # Преобразуем ORM-модели секций в SectionSchema
        sections: list[SectionSchema] = []
        if version.sections:
            for section_model in version.sections:
                try:
                    section_data = {
                        "title": section_model.title,
                        "content": section_model.content,
                        "raw_content": section_model.raw_content,
                    }
                    sections.append(SectionSchema.model_validate(section_data))
                except Exception as exc:
                    app_logger.warning(
                        "Failed to validate section schema: section_id=%s, error=%s",
                        section_model.id,
                        str(exc),
                    )
                    continue

        app_logger.info(
            "Resume version detail retrieved successfully: version_id=%s, sections_count=%d, has_cover_letter=%s",
            version_id,
            len(sections),
            version.cover_letter is not None,
        )

        return VersionOut(
            id=version.id,
            resume_id=version.resume_id,
            job_description=version.job_description,
            cover_letter=version.cover_letter,
            sections=sections,
            created_at=version.created_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        app_logger.exception(
            exc,
            "Unexpected error during resume version detail retrieval",
            version_id=str(version_id),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during resume version detail retrieval",
        ) from exc

