from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Depends

from app.modules.resumes.schemas import ResumeOut, SectionSchema
from app.modules.resumes.storage import DiskFileStorage
from app.modules.resumes.service import ResumeService
from app.modules.resumes.parsing.pipeline import ResumeParsingPipeline
from app.modules.resumes.parsing.llm_resume_parser import LLMResumeParser
from app.modules.file_extractors import FileTextExtractorFactory
from app.integrations.llm.factory import create_llm_client  # фабрика LLM-клиента (Gemini/OpenAI и т.д.)

router = APIRouter()


def get_resume_service() -> ResumeService:
    """
    Простейшая "инъекция зависимостей":
      - DiskFileStorage для сохранения файлов на диск
      - LLM-клиент (через фабрику)
      - LLMResumeParser для работы с LLM
      - ResumeParsingPipeline для парсинга резюме в секции

    Позже это можно заменить на полноценный DI-контейнер.
    """
    storage = DiskFileStorage(base_dir="storage/resumes")

    llm_client = create_llm_client()  # выбирает провайдера по конфигу (gemini/openai/...)
    llm_parser = LLMResumeParser(llm_client)
    extractor_factory = FileTextExtractorFactory()
    pipeline = ResumeParsingPipeline(
        extractor_factory=extractor_factory,
        llm_parser=llm_parser,
    )

    return ResumeService(file_storage=storage, parsing_pipeline=pipeline)


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
      3. Парсим через ResumeParsingPipeline (LLM → секции).
      4. Создаём базовое резюме.
      5. Возвращаем метаданные + список секций.

    Ошибки:
      - 400 — если формат файла не поддерживается.
      - 201 с warnings — если файл загрузился, но распарсить не вышло.
    """
    resume, warnings = await resume_service.create_base_resume_from_upload(
        file=file,
        user_id=None,  # auth пока не реализован
    )

    # Преобразуем доменные Section → SectionSchema для ответа API
    sections: list[SectionSchema] = []
    if resume.parsed_data is not None and resume.parsed_data.sections:
        sections = [
            SectionSchema.model_validate(section)
            for section in resume.parsed_data.sections
        ]

    return ResumeOut(
        id=resume.id,
        filename=resume.filename,
        content_type=resume.content_type,
        sections=sections,
        warnings=warnings,
        created_at=resume.created_at,
    )