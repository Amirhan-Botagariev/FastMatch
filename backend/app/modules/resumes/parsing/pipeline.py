from __future__ import annotations

from typing import List, Optional, Any, Dict

from app.modules.resumes.domain import ParsedResumeData, Section
from app.modules.file_extractors import FileTextExtractorFactory
from app.modules.resumes.parsing.llm_resume_parser import LLMResumeParser


class ResumeParsingPipeline:
    def __init__(
        self,
        extractor_factory: Optional[FileTextExtractorFactory] = None,
        llm_parser: LLMResumeParser | None = None,
    ) -> None:
        """
        extractor_factory:
            отвечает только за превращение (bytes -> raw_text, lines)
        llm_parser:
            доменный парсер резюме через LLM. Обязательная зависимость.
        """
        self._extractor_factory = extractor_factory or FileTextExtractorFactory()
        if llm_parser is None:
            raise ValueError("llm_parser must be provided to ResumeParsingPipeline")
        self._llm_parser = llm_parser

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str],
    ) -> ParsedResumeData:
        # 1. Достаём сырой текст из файла
        extract_result = self._extract_text(file_bytes, filename, content_type)
        raw_text = extract_result.raw_text

        # 2. Отправляем в LLM-парсер
        llm_data: Dict[str, Any] = self._llm_parser.parse(raw_text)

        if not isinstance(llm_data, dict):
            raise ValueError("LLM returned non-dict response for resume parsing")

        # 3. Собираем секции
        sections: List[Section] = []
        sections_data = llm_data.get("sections") or []

        if isinstance(sections_data, list):
            for idx, item in enumerate(sections_data):
                if not isinstance(item, dict):
                    continue

                sections.append(
                    Section(
                        title=item.get("title"),
                        content=item.get("content"),
                        raw_content=item.get("raw_content"),
                        order=idx,
                    )
                )

        # 4. Формируем ParsedResumeData
        return ParsedResumeData(
            raw_text=raw_text,
            sections=sections,
            meta={"llm_raw": llm_data},
        )

    def _extract_text(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str],
    ):
        extractor = self._extractor_factory.get_extractor(
            filename=filename,
            content_type=content_type,
        )
        return extractor.extract(file_bytes)