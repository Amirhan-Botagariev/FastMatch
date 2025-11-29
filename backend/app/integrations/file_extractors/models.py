from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class FileExtractResult:
    """
    Результат низкоуровневого извлечения текста из файла.

    raw_text:
        Слитый текст всего файла одной строкой (с переводами строк внутри).
    lines:
        Уже разбитый на строки текст, пригодный для дальнейшего парсинга.
    """
    raw_text: str
    lines: List[str]

