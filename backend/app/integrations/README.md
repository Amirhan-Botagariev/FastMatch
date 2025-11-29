# Интеграции

Модули для работы с внешними сервисами и библиотеками.

## Стандартная структура модуля

Каждый модуль интеграции должен иметь следующую структуру:

```
module_name/
├── __init__.py      # Экспорты публичного API модуля
├── client.py        # Клиенты для работы с внешним сервисом
├── models.py        # Модели данных (dataclasses, Pydantic модели)
├── exceptions.py    # Исключения, специфичные для модуля
└── utils.py         # Вспомогательные функции и утилиты
```

## Текущие модули

### file_extractors
Извлечение текста из файлов (PDF, DOCX и т.д.)

- `client.py` - FileExtractorClient и реализации экстракторов
- `models.py` - FileExtractResult
- `exceptions.py` - UnsupportedFileFormatError
- `utils.py` - вспомогательные функции

### llm
Интеграция с LLM провайдерами (Gemini, OpenAI и т.д.)

- `client.py` - LLMClient и реализации (GeminiClient, OpenAIClient)
- `models.py` - модели данных для LLM (если нужны)
- `exceptions.py` - LLMError, LLMInvalidResponseError, LLMTimeoutError
- `utils.py` - вспомогательные функции

## Правила создания нового модуля

1. Создайте папку с именем модуля в `app/integrations/`
2. Создайте все стандартные файлы:
   - `__init__.py` - экспортируйте публичный API
   - `client.py` - клиенты
   - `models.py` - модели данных
   - `exceptions.py` - исключения
   - `utils.py` - утилиты
3. Следуйте единообразной структуре для всех модулей

