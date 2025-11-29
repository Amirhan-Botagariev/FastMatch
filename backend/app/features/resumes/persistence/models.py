from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResumeModel(Base):
    """
    ORM-модель для резюме.
    """
    __tablename__ = "resumes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)  # Пока пусто, для будущего
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Дополнительные метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связь с секциями
    sections: Mapped[list["ResumeSectionModel"]] = relationship(
        "ResumeSectionModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSectionModel.order",
    )

    # Связь с версиями
    versions: Mapped[list["ResumeVersionModel"]] = relationship(
        "ResumeVersionModel",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeVersionModel.created_at.desc()",
    )


class ResumeSectionModel(Base):
    """
    ORM-модель для секций резюме.
    """
    __tablename__ = "resume_sections"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    resume_id: Mapped[UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Связь с резюме
    resume: Mapped["ResumeModel"] = relationship("ResumeModel", back_populates="sections")


class ResumeVersionModel(Base):
    """
    ORM-модель для кастомных версий резюме под описание вакансии.
    """
    __tablename__ = "resume_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    resume_id: Mapped[UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    job_description: Mapped[str] = mapped_column(Text)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связь с резюме
    resume: Mapped["ResumeModel"] = relationship("ResumeModel", back_populates="versions")

    # Связь с секциями версии
    sections: Mapped[list["ResumeVersionSectionModel"]] = relationship(
        "ResumeVersionSectionModel",
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="ResumeVersionSectionModel.order",
    )


class ResumeVersionSectionModel(Base):
    """
    ORM-модель для секций кастомной версии резюме.
    """
    __tablename__ = "resume_version_sections"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    version_id: Mapped[UUID] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Связь с версией
    version: Mapped["ResumeVersionModel"] = relationship("ResumeVersionModel", back_populates="sections")

