import textwrap
from typing import Any, Dict

from app.integrations.llm.base import LLMClient


class LLMResumeParser:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def parse(self, raw_text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(raw_text)
        return self._llm.generate_json(prompt)

    @staticmethod
    def _build_prompt(text: str) -> str:
        """
        Строим промпт для LLM:

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