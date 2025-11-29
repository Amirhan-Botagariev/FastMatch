from __future__ import annotations

from typing import Any, Dict

from app.core.logging import app_logger
from app.features.resumes.models import ParsedResumeData
from app.integrations.llm.client import LLMClient
from app.features.resumes.parsing.utils import (
    build_resume_parsing_prompt,
    map_llm_response_to_parsed_data,
)


class ParsingService:
    """
    Сервис для парсинга резюме через LLM.
    
    Отвечает за:
      - Формирование промпта для LLM
      - Вызов LLM
      - Преобразование ответа LLM в доменные модели
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def parse(self, raw_text: str) -> ParsedResumeData:
        """
        Парсит текст резюме через LLM и возвращает структурированные данные.
        """
        try:
            app_logger.debug("Starting resume parsing, text_length=%d", len(raw_text))
            
            # Формируем промпт
            prompt = build_resume_parsing_prompt(raw_text)
            
            # Вызываем LLM
            llm_response: Dict[str, Any] = self._llm_client.generate_json(prompt)
            
            app_logger.debug(
                "LLM response received: sections_count=%d",
                len(llm_response.get("sections", [])),
            )
            
            # Преобразуем ответ в доменные модели
            parsed_data = map_llm_response_to_parsed_data(llm_response, raw_text)
            
            app_logger.info(
                "Resume parsed successfully: sections_count=%d",
                len(parsed_data.sections),
            )
            
            return parsed_data
        except Exception as exc:
            app_logger.exception(
                exc,
                "Failed to parse resume text",
                text_length=len(raw_text),
            )
            raise

