# 🧪 Система тестирования проекта Biblioteka

## 📋 Обзор

Проект использует **pytest** с плагинами для Django REST Framework для комплексного тестирования всех компонентов системы.

## 📁 Структура тестов

```
tests/
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
├── fixtures/                # Тестовые данные
│   ├── factories.py        # Factory Boy фабрики
│   ├── sample_books.json   # Примеры книг
│   └── sample_images/      # Тестовые изображения
│
├── conftest.py             # Общие фикстуры pytest
├── settings.py             # Тестовые настройки Django
└── TESTING.md              # Этот файл
```

## 🎯 Принципы тестирования

### 1. Разделение по уровням

- **Unit тесты** — тестируют изолированные компоненты (модели, сериализаторы, функции)
- **API тесты** — тестируют HTTP endpoints через DRF test client
- **Интеграционные тесты** — тестируют полные сценарии взаимодействия компонентов

### 2. Принцип AAA (Arrange-Act-Assert)

Каждый тест должен следовать структуре:
1. **Arrange** — подготовка данных
2. **Act** — выполнение действия
3. **Assert** — проверка результата

### 3. Изоляция тестов

- Каждый тест должен быть независимым
- Использовать фикстуры для подготовки данных
- Очистка БД между тестами (автоматически через `pytest-django`)

## 🔧 Настройка и запуск

### Установка зависимостей

```bash
pip install pytest pytest-django pytest-cov factory-boy
```

### Конфигурация

- **pytest.ini** — настройки pytest (маркеры, пути, плагины)
- **.coveragerc** — настройки покрытия кода
- **tests/conftest.py** — общие фикстуры
- **tests/settings.py** — тестовая конфигурация Django

### Команды запуска

```bash
# Все тесты
pytest

# Только unit тесты
pytest -m unit

# Только API тесты
pytest -m api

# Только интеграционные тесты
pytest -m integration

# С покрытием кода
pytest --cov=books --cov-report=html

# Конкретный файл
pytest tests/unit/models/test_book.py

# По паттерну
pytest -k "book"

# Подробный вывод
pytest -v

# Остановка на первой ошибке
pytest -x
```

## 📝 Маркеры pytest

Маркеры используются для группировки и фильтрации тестов:

- `@pytest.mark.unit` — unit тесты
- `@pytest.mark.api` — API тесты
- `@pytest.mark.integration` — интеграционные тесты
- `@pytest.mark.slow` — долгие тесты (например, обработка изображений)

**Использование:**
```python
@pytest.mark.unit
def test_create_book(db):
    ...
```

## 🧩 Фикстуры

### Общие фикстуры (conftest.py)

- `db` — доступ к тестовой БД (pytest-django)
- `api_client` — DRF API client для HTTP запросов
- `admin_client` — API client с правами администратора
- `category_factory` — Factory Boy для категорий
- `author_factory` — Factory Boy для авторов
- `publisher_factory` — Factory Boy для издательств
- `book_factory` — Factory Boy для книг
- `tmp_media_root` — временная папка для медиа файлов

### Пример использования

```python
def test_create_book(api_client, category_factory, author_factory):
    category = category_factory()
    author = author_factory()
    
    data = {
        'title': 'Test Book',
        'category': category.id,
        'author_ids': [author.id]
    }
    
    response = api_client.post('/api/books/', data)
    assert response.status_code == 201
```

## 📊 Что тестируется

### Модели (tests/unit/models/)

**Category:**
- ✅ Создание категории
- ✅ Уникальность кода
- ✅ Порядок сортировки
- ✅ Подсчет книг в категории

**Author:**
- ✅ Создание автора
- ✅ Валидация годов (birth_year < death_year)
- ✅ Связи с книгами

**Publisher:**
- ✅ Создание издательства
- ✅ URL валидация

**Book:**
- ✅ Создание книги
- ✅ Связь с категорией
- ✅ Связь с авторами (до 3-х через BookAuthor)
- ✅ Валидация полей
- ✅ Property `images_count`

**BookAuthor:**
- ✅ Ограничение до 3-х авторов
- ✅ Уникальность (book, order)
- ✅ Валидация MaxValueValidator(3)

**BookImage:**
- ✅ Загрузка изображения
- ✅ Порядок (1-20)
- ✅ Уникальность (book, order)

**BookElectronic:**
- ✅ Создание электронной версии
- ✅ Выбор формата

### Сериализаторы (tests/unit/serializers/)

- ✅ Сериализация всех моделей
- ✅ Валидация входных данных
- ✅ Вложенные объекты (авторы, категория, издательство)
- ✅ Создание/обновление с author_ids
- ✅ Ограничение до 3-х авторов

### Сервисы (tests/unit/services/)

**document_processor:**
- ✅ `order_points()` — упорядочивание точек
- ✅ `four_point_transform()` — преобразование перспективы
- ✅ `process_document()` — полная обработка
- ✅ Обработка ошибок
- ✅ Валидация входных данных

### API (tests/api/)

**Categories API:**
- ✅ GET /api/categories/ — список
- ✅ GET /api/categories/{slug}/ — детали
- ✅ POST /api/categories/ — создание
- ✅ PUT /api/categories/{slug}/ — обновление
- ✅ DELETE /api/categories/{slug}/ — удаление
- ✅ Фильтрация, сортировка

**Authors API:**
- ✅ CRUD операции
- ✅ Валидация данных

**Publishers API:**
- ✅ CRUD операции
- ✅ Валидация URL

**Books API:**
- ✅ GET /api/books/ — список с фильтрами
- ✅ GET /api/books/{id}/ — детали
- ✅ POST /api/books/ — создание с авторами
- ✅ PUT /api/books/{id}/ — обновление
- ✅ DELETE /api/books/{id}/ — удаление
- ✅ Фильтрация по категории
- ✅ Поиск по названию/автору
- ✅ Поиск по диапазону дат (year)
- ✅ Сортировка

**Books Images API:**
- ✅ POST /api/books/{id}/images/ — загрузка
- ✅ GET /api/books/{id}/images/ — список
- ✅ DELETE /api/images/{id}/ — удаление
- ✅ Порядок изображений

**Books Electronic API:**
- ✅ POST /api/books/{id}/electronic/ — добавление
- ✅ GET /api/books/{id}/electronic/ — список
- ✅ DELETE /api/electronic/{id}/ — удаление

**Books Pages API:**
- ✅ POST /api/books/{id}/pages/ — загрузка страницы
- ✅ GET /api/books/{id}/pages/ — список
- ✅ POST /api/pages/{id}/process/ — обработка страницы

### Интеграционные тесты (tests/integration/)

**test_book_lifecycle.py:**
- ✅ Полный цикл: автор → издательство → книга
- ✅ Добавление изображений
- ✅ Добавление электронных версий
- ✅ Каскадное удаление

**test_category_sync.py:**
- ✅ Синхронизация категорий из JSON
- ✅ Обновление существующих
- ✅ Обработка дубликатов

**test_search_filtering.py:**
- ✅ Поиск по диапазону дат (year_min, year_max)
- ✅ Фильтрация по категории
- ✅ Поиск по автору
- ✅ Комплексные фильтры

## 🏭 Factory Boy

Используется для создания тестовых данных:

```python
# factories.py
import factory
from books.models import Author, Publisher, Book

class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author
    
    full_name = factory.Faker('name', locale='ru_RU')
    birth_year = factory.Faker('year', minimum=1800, maximum=2000)

class PublisherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Publisher
    
    name = factory.Faker('company', locale='ru_RU')
    city = factory.Faker('city', locale='ru_RU')

class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book
    
    title = factory.Faker('sentence', nb_words=4, locale='ru_RU')
    year = factory.Faker('year', minimum=1900, maximum=2024)
    category = factory.SubFactory(CategoryFactory)
    publisher = factory.SubFactory(PublisherFactory)
```

## 📈 Покрытие кода

Цель: **минимум 80% покрытия**

Проверка покрытия:
```bash
pytest --cov=books --cov-report=term-missing
pytest --cov=books --cov-report=html  # HTML отчет в htmlcov/
```

Исключения в `.coveragerc`:
- Миграции
- Админка (если не тестируется)
- Служебные файлы

## 🚫 Что НЕ тестируется

- Миграции Django (тестируются через применение)
- Админка Django (опционально)
- Внешние API (мокируются)

## 🔄 CI/CD интеграция

Тесты должны запускаться автоматически при:
- Push в основную ветку
- Pull Request
- Ночных сборках

Пример GitHub Actions:
```yaml
- name: Run tests
  run: |
    pytest --cov=books --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 📚 Полезные ресурсы

- [pytest документация](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)

## 🎓 Примеры тестов

### Пример 1: Unit тест модели

```python
# tests/unit/models/test_book.py
import pytest
from books.models import Book, Author, Category

@pytest.mark.unit
@pytest.mark.django_db
def test_create_book(category_factory, author_factory):
    category = category_factory()
    author = author_factory()
    book = Book.objects.create(
        title='Test Book',
        category=category,
        year=2023
    )
    book.authors.add(author)
    
    assert book.title == 'Test Book'
    assert book.category == category
    assert book.authors.count() == 1
```

### Пример 2: API тест

```python
# tests/api/test_books_api.py
import pytest
from rest_framework import status

@pytest.mark.api
@pytest.mark.django_db
def test_create_book(api_client, category_factory, author_factory):
    category = category_factory()
    author = author_factory()
    
    data = {
        'title': 'Test Book',
        'category': category.id,
        'author_ids': [author.id],
        'year': 2023
    }
    
    response = api_client.post('/api/books/', data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'Test Book'
```

### Пример 3: Интеграционный тест

```python
# tests/integration/test_book_lifecycle.py
@pytest.mark.integration
@pytest.mark.django_db
def test_book_lifecycle(api_client):
    # Создание автора
    author_data = {'full_name': 'Иван Иванов'}
    author_response = api_client.post('/api/authors/', author_data)
    author_id = author_response.data['id']
    
    # Создание книги
    book_data = {
        'title': 'Test Book',
        'author_ids': [author_id]
    }
    book_response = api_client.post('/api/books/', book_data)
    book_id = book_response.data['id']
    
    # Проверка связи
    book_detail = api_client.get(f'/api/books/{book_id}/')
    assert len(book_detail.data['authors']) == 1
```

## ✅ Чеклист для нового теста

- [ ] Тест находится в правильной директории (unit/api/integration)
- [ ] Используются соответствующие маркеры
- [ ] Используются фикстуры для данных
- [ ] Тест независим от других тестов
- [ ] Тест следует принципу AAA
- [ ] Проверяются граничные случаи
- [ ] Проверяются ошибки и валидация
- [ ] Тест имеет понятное название

## 🔍 Отладка тестов

```bash
# Запуск с выводом print()
pytest -s

# Запуск с pdb (debugger)
pytest --pdb

# Остановка на первой ошибке
pytest -x

# Подробный вывод
pytest -vv

# Запуск последнего упавшего теста
pytest --lf
```

---

**Последнее обновление:** 2025-11-03  
**Версия:** 1.0

