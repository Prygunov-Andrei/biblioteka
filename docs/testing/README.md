# 🧪 Testing Documentation

## Обзор

Проект использует **pytest** с плагинами для Django REST Framework для комплексного тестирования всех компонентов системы.

## Структура тестов

```
backend/tests/
├── unit/                    # Unit тесты (изолированные компоненты)
│   ├── models/              # Тесты моделей Django
│   ├── serializers/          # Тесты сериализаторов DRF
│   ├── services/            # Тесты бизнес-логики
│   └── management/          # Тесты management команд
│
├── api/                     # API тесты (HTTP endpoints)
│   ├── test_categories_api.py
│   ├── test_authors_api.py
│   ├── test_publishers_api.py
│   ├── test_books_api.py
│   ├── test_books_images_api.py
│   ├── test_books_electronic_api.py
│   └── test_books_pages_api.py
│
├── integration/             # Интеграционные тесты
│   ├── test_book_lifecycle.py
│   ├── test_category_sync.py
│   └── test_search_filtering.py
│
└── fixtures/                # Тестовые данные
    ├── factories.py         # Factory Boy фабрики
    └── sample_images/       # Тестовые изображения
```

## Запуск тестов

```bash
# Все тесты
pytest

# Только unit тесты
pytest -m unit

# Только API тесты
pytest -m api

# С покрытием кода
pytest --cov=books --cov-report=html

# Конкретный файл
pytest tests/api/test_books_api.py

# По паттерну
pytest -k "book"
```

## Покрытие кода

Цель: **минимум 80% покрытия**

Проверка покрытия:
```bash
pytest --cov=books --cov-report=term-missing
pytest --cov=books --cov-report=html  # HTML отчет в htmlcov/
```

## Подробное руководство

Полное руководство по тестированию: [testing-guide.md](testing-guide.md)

---

**Последнее обновление:** 2025-11-03

