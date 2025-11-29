# Features (Бизнес-логика)

Модули, реализующие бизнес-логику приложения.

## Стандартная структура feature-модуля

Каждый feature-модуль должен иметь следующую структуру:

```
feature_name/
├── __init__.py
├── router.py          # API эндпоинты (FastAPI routes)
├── service.py         # Основной сервис (оркестратор бизнес-логики)
├── schemas.py         # Pydantic схемы для API (DTO)
├── models.py          # Доменные модели (dataclasses)
├── repository.py      # Репозиторий для работы с БД (если нужен)
├── models.py          # ORM модели (если нужны, обычно в подмодуле)
└── submodule/         # Подмодули (опционально)
    ├── service.py      # Специфичный сервис
    ├── utils.py        # Вспомогательные функции
    └── ...
```

## Текущие модули

### resumes
Модуль для работы с резюме.

**Основные файлы:**
- `router.py` - API эндпоинты `/api/v1/resumes`
- `service.py` - ResumeService (оркестратор)
- `schemas.py` - ResumeOut, SectionSchema (Pydantic схемы)
- `models.py` - BaseResume, ParsedResumeData, Section (доменные модели)

**Подмодули:**
- `ingestion/` - прием и первичная обработка файлов
  - `service.py` - IngestionService
- `parsing/` - парсинг резюме через LLM
  - `service.py` - ParsingService
  - `utils.py` - build_resume_parsing_prompt, map_llm_response_to_parsed_data
- `persistence/` - работа с БД
  - `repository.py` - ResumeRepository
  - `models.py` - ResumeModel, ResumeSectionModel (ORM)

## Правила создания нового feature-модуля

1. Создайте папку с именем модуля в `app/features/`
2. Создайте основные файлы:
   - `router.py` - API роуты
   - `service.py` - основной сервис
   - `schemas.py` - Pydantic схемы
   - `models.py` - доменные модели
3. При необходимости создайте подмодули:
   - `submodule/service.py` - специфичные сервисы
   - `submodule/utils.py` - утилиты
   - `submodule/repository.py` - репозитории
   - `submodule/models.py` - ORM модели
4. Следуйте единообразной структуре для всех модулей

