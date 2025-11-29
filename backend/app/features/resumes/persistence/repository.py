from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import app_logger
from app.features.resumes.persistence.models import (
    ResumeModel,
    ResumeSectionModel,
    ResumeVersionModel,
    ResumeVersionSectionModel,
)
from app.features.resumes.models import BaseResume, ParsedResumeData


class ResumeRepository:
    """
    Репозиторий для работы с резюме в БД.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, resume: BaseResume) -> ResumeModel:
        """
        Создает новое резюме в БД.
        """
        try:
            model = ResumeModel(
                id=resume.id,
                filename=resume.filename,
                content_type=resume.content_type,
                file_path=resume.file_path,
                raw_text=resume.parsed_data.raw_text if resume.parsed_data else None,
                created_at=resume.created_at,
            )
            self._session.add(model)
            await self._session.flush()
            app_logger.debug("Resume created in DB: id=%s, filename=%s", resume.id, resume.filename)
            return model
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to create resume in DB",
                resume_id=str(resume.id),
                filename=resume.filename,
            )
            raise

    async def get_by_id(self, resume_id: UUID, load_sections: bool = True) -> Optional[ResumeModel]:
        """
        Получает резюме по ID.

        Args:
            resume_id: ID резюме
            load_sections: Если True, загружает связанные секции (по умолчанию True)

        Returns:
            ResumeModel с загруженными секциями или None, если не найдено
        """
        try:
            query = select(ResumeModel).where(ResumeModel.id == resume_id)
            
            # Загружаем секции, если нужно
            if load_sections:
                query = query.options(selectinload(ResumeModel.sections))
            
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            
            if model:
                app_logger.debug(
                    "Resume retrieved from DB: id=%s, sections_count=%d",
                    resume_id,
                    len(model.sections) if model.sections else 0,
                )
            else:
                app_logger.debug("Resume not found in DB: id=%s", resume_id)
            return model
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to get resume from DB",
                resume_id=str(resume_id),
            )
            raise

    async def list_all(self) -> list[ResumeModel]:
        """
        Получает все резюме.
        """
        try:
            result = await self._session.execute(select(ResumeModel))
            models = list(result.scalars().all())
            app_logger.debug("Retrieved %d resumes from DB", len(models))
            return models
        except Exception as exc:
            app_logger.exception(exc, "Failed to list resumes from DB")
            raise

    async def list_by_user_id(self, user_id: Optional[UUID] = None) -> list[ResumeModel]:
        """
        Получает резюме по user_id.
        Если user_id=None, возвращает все резюме (для совместимости).
        """
        try:
            if user_id is None:
                # Если user_id не указан, возвращаем все резюме
                result = await self._session.execute(
                    select(ResumeModel).order_by(ResumeModel.created_at.desc())
                )
            else:
                # Фильтруем по user_id
                result = await self._session.execute(
                    select(ResumeModel)
                    .where(ResumeModel.user_id == user_id)
                    .order_by(ResumeModel.created_at.desc())
                )
            models = list(result.scalars().all())
            app_logger.debug(
                "Retrieved %d resumes from DB for user_id=%s",
                len(models),
                user_id,
            )
            return models
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to list resumes from DB",
                user_id=str(user_id) if user_id else None,
            )
            raise

    async def create_version(
        self,
        resume_id: UUID,
        job_description: str,
        custom_sections: list[dict],
        cover_letter: Optional[str] = None,
    ) -> ResumeVersionModel:
        """
        Создает кастомную версию резюме под описание вакансии.

        Args:
            resume_id: ID исходного резюме
            job_description: Описание вакансии
            custom_sections: Список кастомизированных секций (словари с title, content, raw_content, order)

        Returns:
            Созданная модель версии с секциями
        """
        try:
            import uuid
            version_id = uuid.uuid4()
            
            # Создаем версию
            version = ResumeVersionModel(
                id=version_id,
                resume_id=resume_id,
                job_description=job_description,
                cover_letter=cover_letter,
            )
            self._session.add(version)
            await self._session.flush()

            # Создаем секции версии
            for idx, section_data in enumerate(custom_sections):
                section = ResumeVersionSectionModel(
                    id=uuid.uuid4(),
                    version_id=version_id,
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    raw_content=section_data.get("raw_content"),
                    order=section_data.get("order", idx),
                )
                self._session.add(section)

            await self._session.flush()
            
            # Загружаем секции для возврата
            await self._session.refresh(version, ["sections"])
            
            app_logger.debug(
                "Resume version created: version_id=%s, resume_id=%s, sections_count=%d",
                version_id,
                resume_id,
                len(custom_sections),
            )
            return version
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to create resume version in DB",
                resume_id=str(resume_id),
            )
            raise

