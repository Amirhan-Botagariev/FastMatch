#!/bin/bash
# Скрипт для запуска тестов через Poetry

set -e

cd "$(dirname "$0")/.."

echo "🧪 Запуск тестов..."

# Проверяем, что Poetry установлен
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry не установлен. Установите его: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Устанавливаем зависимости, если нужно
if [ "$1" != "--no-install" ]; then
    echo "📦 Установка зависимостей..."
    poetry install --with dev
fi

# Запускаем тесты
if [ "$1" == "--coverage" ] || [ "$2" == "--coverage" ]; then
    echo "📊 Запуск тестов с покрытием кода..."
    poetry run pytest tests/ --cov=app --cov-report=html --cov-report=term -v
    echo ""
    echo "✅ Отчет о покрытии сохранен в htmlcov/index.html"
elif [ "$1" == "--watch" ] || [ "$2" == "--watch" ]; then
    echo "👀 Запуск тестов в режиме watch..."
    poetry run pytest-watch tests/ -v
else
    poetry run pytest tests/ -v "$@"
fi

