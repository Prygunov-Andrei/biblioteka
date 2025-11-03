# Фикстуры для тестов

Эта директория содержит тестовые данные и фабрики для создания объектов.

## Структура

- `factories.py` — Factory Boy фабрики для создания тестовых объектов
- `categories.json` — примеры категорий для тестов
- `sample_books.json` — примеры книг для тестов
- `sample_images/` — тестовые изображения для тестов обработки документов

## Использование

### Factory Boy

```python
from tests.fixtures.factories import BookFactory, AuthorFactory

# Создание одного объекта
book = BookFactory()

# Создание с переопределением полей
book = BookFactory(title='Custom Title', year=2023)

# Создание нескольких объектов
books = BookFactory.create_batch(10)
```

### JSON фикстуры

```python
import json
from pathlib import Path

# Загрузка категорий
categories_path = Path(__file__).parent / 'categories.json'
with open(categories_path) as f:
    categories_data = json.load(f)
```

