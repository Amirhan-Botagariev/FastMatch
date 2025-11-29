from __future__ import annotations

import textwrap
from typing import Any, Dict, List

from app.core.logging import app_logger
from app.features.resumes.models import ParsedResumeData, Section


def build_resume_parsing_prompt(text: str) -> str:
    """
    Строит промпт для LLM для парсинга резюме.

    - Резюме может быть на любом языке (русский, английский, смешанный).
    - Наша задача — только структурировать его на секции, НЕ переводя текст.
    - Выходной формат: JSON с полем "sections", без доменных типов вроде "experience".
    """
    prompt = f"""
    You are a resume parsing engine.

    The input is a resume in arbitrary format. It may be written in English, Russian,
    or any other language (or even a mix of languages).

    Your task:
    - Read the resume text.
    - Split it into logical sections in the order they appear.
    - For each section, detect:
        - "title": the section heading as it appears in the resume (if there is no clear heading, use null),
        - "content": a cleaned, normalized version of the section text (you may merge lines / bullet points),
        - "raw_content": the raw text of this section as it appears in the resume (use the same language, do not translate).

    IMPORTANT LANGUAGE RULES:
    - Do NOT translate or rewrite the text into another language.
    - Keep the language of each section exactly as in the original resume.
    - If the resume is in Russian, return Russian text.
    - If the resume is in English, return English text.
    - If the resume is mixed, keep each part in its original language.

    Output MUST be valid JSON, UTF-8, with double quotes, without comments or explanations.
    The top-level JSON object MUST have the following structure:

    Schema:
    {{
      "sections": [
        {{
          "title": "string or null",
          "content": "string or null",
          "raw_content": "string or null"
        }}
      ]
    }}

    Additional rules:
    - Preserve the original order of sections from top to bottom.
    - Do not invent fake sections; only create sections that are supported by the text.
    - If you are unsure about a section boundary, choose the simplest reasonable split.
    - If some field is unknown, set it to null.

    Resume text (may contain Russian, English or any other language):

    \"\"\"{text}\"\"\"
    """
    return textwrap.dedent(prompt).strip()


def map_llm_response_to_parsed_data(
    llm_response: Dict[str, Any],
    raw_text: str,
) -> ParsedResumeData:
    """
    Преобразует сырой ответ LLM в доменную модель ParsedResumeData.
    """
    try:
        if not isinstance(llm_response, dict):
            raise ValueError("LLM returned non-dict response for resume parsing")

        sections: List[Section] = []
        sections_data = llm_response.get("sections") or []

        if isinstance(sections_data, list):
            for idx, item in enumerate(sections_data):
                if not isinstance(item, dict):
                    app_logger.warning(
                        "Skipping invalid section item at index %d: expected dict, got %s",
                        idx,
                        type(item).__name__,
                    )
                    continue

                sections.append(
                    Section(
                        title=item.get("title"),
                        content=item.get("content"),
                        raw_content=item.get("raw_content"),
                        order=idx,
                    )
                )
        else:
            app_logger.warning(
                "LLM response 'sections' is not a list: got %s",
                type(sections_data).__name__,
            )

        return ParsedResumeData(
            raw_text=raw_text,
            sections=sections,
            meta={"llm_raw": llm_response},
        )
    except Exception as exc:
        app_logger.exception(
            exc,
            "Failed to map LLM response to parsed data",
            llm_response_type=type(llm_response).__name__,
        )
        raise


def build_resume_customization_prompt(
    resume_sections: List[Dict[str, Any]],
    job_description: str,
) -> str:
    """
    Строит промпт для LLM для кастомизации резюме под описание вакансии.

    Args:
        resume_sections: Список секций исходного резюме
        job_description: Описание вакансии

    Returns:
        Промпт для LLM
    """
    # Формируем текст резюме из секций
    resume_text_parts = []
    for section in resume_sections:
        title = section.get("title", "")
        content = section.get("content") or section.get("raw_content", "")
        if title:
            resume_text_parts.append(f"{title}\n{content}")
        else:
            resume_text_parts.append(content)
    
    resume_text = "\n\n".join(resume_text_parts)

    prompt = f"""
    You are a resume customization assistant. Your task is to adapt a resume to match a specific job description.

    ORIGINAL RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Your task:
    - Analyze the job description and identify key requirements, skills, and qualifications.
    - Review the original resume sections.
    - Create a customized version of the resume that highlights relevant experience, skills, and achievements that match the job description.
    - Keep the same structure and section titles as the original resume when possible.
    - Emphasize and rephrase content to better align with the job requirements.
    - Do NOT add false information or make up experiences that don't exist in the original resume.
    - Keep the language of the resume (if it's in Russian, keep it in Russian; if English, keep English).

    Output MUST be valid JSON, UTF-8, with double quotes, without comments or explanations.
    The top-level JSON object MUST have the following structure:

    Schema:
    {{
      "sections": [
        {{
          "title": "string or null",
          "content": "string or null",
          "raw_content": "string or null"
        }}
      ]
    }}

    Return ONLY the JSON object, nothing else.
    """
    
    return textwrap.dedent(prompt).strip()

