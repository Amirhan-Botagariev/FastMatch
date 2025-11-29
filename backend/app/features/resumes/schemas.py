from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ========= Схема секции =========

class SectionSchema(BaseModel):
    """
    Одна секция резюме в том виде, как мы её видим после парсинга.
    Без догадок про её тип.
    """
    title: Optional[str] = Field(
        None,
        description="Заголовок секции как в резюме ('Experience', 'Skills', 'Проекты', ...)",
    )
    content: Optional[str] = Field(
        None,
        description="Нормализованный текст секции (например, объединённый в один блок).",
    )
    raw_content: Optional[str] = Field(
        None,
        description="Сырой текст секции целиком, как мы вытащили его из файла.",
    )


# ========= Схема набора секций (всего резюме) =========

class ResumeSectionsSchema(BaseModel):
    """
    Резюме как набор секций в прямом порядке.
    Никакой заранее определённой структуры — только то, что реально есть.
    """
    sections: List[SectionSchema] = Field(default_factory=list)


# ========= Схема ответа API =========

class ResumeOut(BaseModel):
    """
    Ответ API на загрузку/получение резюме.
    """
    id: UUID
    filename: str
    content_type: str

    sections: List[SectionSchema] = Field(
        default_factory=list,
        description="Секции резюме в том виде, как мы их распознали логикой парсинга.",
    )

    warnings: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeListItem(BaseModel):
    """
    Упрощенная схема резюме для списка (без секций).
    """
    id: UUID
    filename: str
    content_type: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========= Схемы для версий резюме =========

class VersionCreate(BaseModel):
    """
    Схема для создания кастомной версии резюме.
    """
    job_description: str = Field(
        ...,
        description="Описание вакансии, под которую создается кастомная версия резюме",
    )


class VersionOut(BaseModel):
    """
    Схема ответа API для версии резюме.
    """
    id: UUID
    resume_id: UUID
    job_description: str
    cover_letter: Optional[str] = Field(
        None,
        description="Сопроводительное письмо, сгенерированное для этой версии резюме",
    )
    sections: List[SectionSchema] = Field(
        default_factory=list,
        description="Кастомизированные секции резюме под описание вакансии",
    )
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

