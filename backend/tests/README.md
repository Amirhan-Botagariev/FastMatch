# Тесты

## Установка зависимостей

Проект использует Poetry для управления зависимостями. Установите все зависимости (включая dev-зависимости):

```bash
cd backend
poetry install
```

Или только dev-зависимости:

```bash
poetry install --with dev
```

## Запуск тестов

### Все тесты

Запустить все тесты через Poetry:

```bash
cd backend
poetry run pytest tests/ -v
```

Или активируйте виртуальное окружение Poetry и запускайте напрямую:

```bash
cd backend
poetry shell
pytest tests/ -v
```

### Конкретный файл тестов

```bash
poetry run pytest tests/test_ingestion_service.py -v
```

### Конкретный тест

```bash
poetry run pytest tests/test_ingestion_service.py::TestIngestionService::test_save_file_success -v
```

### С выводом подробной информации

```bash
poetry run pytest tests/ -v -s
```

### Только быстрые тесты (без async)

```bash
poetry run pytest tests/ -v -k "not async"
```

## Покрытие кода

Для проверки покрытия кода тестами сначала установите pytest-cov:

```bash
poetry add --group dev pytest-cov
```

Затем запустите тесты с покрытием:

```bash
poetry run pytest tests/ --cov=app --cov-report=html --cov-report=term
```

Отчет в HTML будет в `htmlcov/index.html`:

```bash
open htmlcov/index.html  # macOS
# или
xdg-open htmlcov/index.html  # Linux
```

## Структура тестов

- `conftest.py` - общие фикстуры для всех тестов
- `test_file_extractor_client.py` - тесты для извлечения текста из файлов
- `test_llm_client.py` - тесты для LLM клиентов
- `test_ingestion_service.py` - тесты для сервиса приема файлов
- `test_parsing_service.py` - тесты для сервиса парсинга
- `test_resume_service.py` - тесты для основного сервиса резюме

