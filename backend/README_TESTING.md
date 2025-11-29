# 🧪 Тестирование приложения

## Быстрый старт

Проект использует **Poetry** для управления зависимостями.

### 1. Установка зависимостей

```bash
cd backend
poetry install
```

Это установит все зависимости, включая dev-зависимости (pytest, pytest-asyncio и т.д.).

### 2. Запуск всех тестов

```bash
poetry run pytest tests/ -v
```

Или используйте удобный скрипт:

```bash
./scripts/test.sh
```

## 📋 Основные команды

### Все тесты

```bash
poetry run pytest tests/ -v
```

### Конкретный файл

```bash
poetry run pytest tests/test_ingestion_service.py -v
```

### Конкретный тест

```bash
poetry run pytest tests/test_ingestion_service.py::TestIngestionService::test_save_file_success -v
```

### С подробным выводом

```bash
poetry run pytest tests/ -v -s
```

### Только упавшие тесты

```bash
poetry run pytest tests/ --lf -v
```

## 📊 Покрытие кода

### Установка pytest-cov

```bash
poetry add --group dev pytest-cov
```

### Запуск с покрытием

```bash
poetry run pytest tests/ --cov=app --cov-report=html --cov-report=term
```

Или через скрипт:

```bash
./scripts/test.sh --coverage
```

Отчет будет сохранен в `htmlcov/index.html`. Откройте его в браузере:

```bash
open htmlcov/index.html  # macOS
```

## 🔧 Использование Poetry shell

Если вы часто запускаете тесты, удобнее активировать виртуальное окружение:

```bash
poetry shell
pytest tests/ -v
```

После этого можно запускать `pytest` напрямую без `poetry run`.

## 📁 Структура тестов

```
tests/
├── conftest.py                    # Общие фикстуры
├── test_file_extractor_client.py # Тесты извлечения текста
├── test_llm_client.py            # Тесты LLM клиентов
├── test_ingestion_service.py     # Тесты приема файлов
├── test_parsing_service.py       # Тесты парсинга
└── test_resume_service.py        # Тесты основного сервиса
```

## 🐛 Отладка тестов

### Запуск с отладчиком

```bash
poetry run pytest tests/ -v -s --pdb
```

### Вывод print-ов

```bash
poetry run pytest tests/ -v -s
```

### Остановка на первой ошибке

```bash
poetry run pytest tests/ -v -x
```

## ✅ Проверка перед коммитом

Рекомендуется запускать тесты перед каждым коммитом:

```bash
poetry run pytest tests/ -v
```

Или добавить в git hooks (`.git/hooks/pre-commit`):

```bash
#!/bin/bash
cd backend && poetry run pytest tests/ -v
```

