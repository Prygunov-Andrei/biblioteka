# 📁 Структура проекта

## Обзор

```
biblioteka/
├── backend/                  # Backend (Django)
│   ├── books/               # Основное приложение
│   │   ├── models.py       # Модели данных
│   │   ├── views/          # API Views (модули)
│   │   ├── serializers.py  # Сериализаторы
│   │   ├── permissions.py  # Кастомные permissions
│   │   ├── constants.py    # Константы проекта
│   │   ├── exceptions.py   # Кастомные исключения
│   │   ├── services/       # Бизнес-логика (сервисы)
│   │   ├── management/     # Management команды
│   │   ├── utils.py        # Утилиты (фильтрация, парсинг)
│   │   ├── pagination.py   # Кастомная пагинация
│   │   └── data/           # Данные (JSON, фикстуры)
│   ├── config/             # Конфигурация проекта
│   │   ├── settings.py     # Настройки Django
│   │   └── urls.py         # URL маршруты
│   ├── tests/              # Тесты
│   └── manage.py           # Django CLI
│
├── frontend/                 # Frontend (React)
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы
│   │   ├── services/       # API сервисы
│   │   └── utils/          # Утилиты
│   └── public/             # Статические файлы
│
├── docs/                    # Документация
│   ├── api/                # API документация
│   ├── testing/            # Документация по тестам
│   ├── reference/          # Справочная информация
│   ├── getting-started/    # Руководства
│   └── deployment/         # Развертывание
│
├── test_data_factory/       # Фабрика тестовых данных
│   ├── factory.py          # Основная фабрика
│   ├── generators/         # Генераторы данных
│   └── data/               # JSON данные
│
├── media/                   # Медиа файлы
│   └── books/              # Файлы книг
│
└── README.md               # Главный README
```

## Backend структура

### books/ (Основное приложение)

```
books/
├── models.py               # Все модели данных
├── serializers.py          # Все сериализаторы
├── permissions.py          # Кастомные permissions
├── constants.py            # Константы (лимиты и т.д.)
├── exceptions.py           # Кастомные исключения
├── admin.py               # Django Admin (опционально)
│
├── views/                  # API Views (модульная структура)
│   ├── __init__.py        # Экспорт всех ViewSets
│   ├── categories.py      # CategoryViewSet
│   ├── authors.py         # AuthorViewSet
│   ├── publishers.py      # PublisherViewSet
│   ├── books.py           # BookViewSet (основной)
│   ├── book_images.py     # BookImageViewSet
│   ├── book_electronic.py # BookElectronicViewSet
│   ├── book_pages.py      # BookPageViewSet
│   ├── users.py           # UserProfileViewSet
│   ├── libraries.py       # LibraryViewSet
│   ├── hashtags.py        # HashtagViewSet
│   └── reviews.py         # BookReviewViewSet
│
├── services/              # Бизнес-логика (сервисный слой)
│   ├── document_processor.py  # Обработка документов
│   ├── hashtag_service.py    # Работа с хэштегами
│   ├── transfer_service.py   # Передача книг
│   └── book_service.py       # Сложная логика книг
│
├── management/            # Management команды
│   └── commands/
│       ├── sync_categories.py         # Синхронизация категорий из канонического JSON
│       ├── delete_all_books.py        # Удаление всех книг
│       └── generate_test_books.py     # Генерация тестовых книг
│
├── data/                  # Данные
│   └── categories_canonical.json  # Канонический JSON с категориями
│
└── migrations/            # Миграции БД
```

### config/ (Конфигурация)

```
config/
├── settings.py           # Настройки Django
└── urls.py              # URL маршруты
```

### tests/ (Тесты)

```
tests/
├── unit/                 # Unit тесты
│   ├── models/
│   ├── serializers/
│   ├── services/
│   └── management/
├── api/                  # API тесты
├── integration/          # Интеграционные тесты
├── fixtures/             # Тестовые данные
├── conftest.py           # Фикстуры pytest
└── settings.py           # Тестовые настройки
```

## Модели данных

### Основные модели
- `Category` — категории книг
- `Author` — авторы
- `Publisher` — издательства
- `Book` — книги
- `BookAuthor` — связь книг и авторов
- `BookImage` — изображения книг
- `BookElectronic` — электронные версии
- `BookPage` — страницы для обработки

## API Endpoints

Все API endpoints находятся в модулях `books/views/`:
- `CategoryViewSet` (categories.py)
- `AuthorViewSet` (authors.py)
- `PublisherViewSet` (publishers.py)
- `BookViewSet` (books.py)
- `BookImageViewSet` (book_images.py)
- `BookElectronicViewSet` (book_electronic.py)
- `BookPageViewSet` (book_pages.py)
- `UserProfileViewSet` (users.py)
- `LibraryViewSet` (libraries.py)
- `HashtagViewSet` (hashtags.py)
- `BookReviewViewSet` (reviews.py)

URL маршруты регистрируются в `config/urls.py`.

## Сервисный слой

Бизнес-логика вынесена в отдельные сервисы:

- `HashtagService` — работа с хэштегами (нормализация, создание, добавление к книгам)
- `TransferService` — передача книг между библиотеками и пользователями
- `BookService` — создание книг со связями (авторы, хэштеги)
- `document_processor` — обработка страниц документов с коррекцией перспективы

## Константы и исключения

- `constants.py` — централизованные константы (лимиты хэштегов, авторов, изображений)
- `exceptions.py` — кастомные исключения (`HashtagLimitExceeded`, `TransferError`, и т.д.)

## Frontend структура

### frontend/ (React приложение)

```
frontend/
├── src/
│   ├── components/        # React компоненты
│   │   ├── Header.js      # Шапка сайта (цитата, меню пользователя, выбор библиотек)
│   │   ├── Sidebar.js     # Боковая панель (категории с счетчиками, хэштеги)
│   │   ├── BookCard.js    # Карточка книги
│   │   ├── BookGrid.js    # Сетка карточек
│   │   ├── Filters.js     # Фильтры книг
│   │   ├── LibrarySelector.js # Выбор библиотек (dropdown с чекбоксами)
│   │   └── PrivateRoute.js # Защищенный маршрут
│   ├── pages/            # Страницы
│   │   ├── LoginPage.js   # Страница авторизации
│   │   ├── MainPage.js    # Главная страница (список книг с фильтрами)
│   │   └── UserPage.js    # Страница пользователя (профиль, управление библиотеками)
│   ├── services/          # API сервисы
│   │   └── api.js        # Axios клиент и API методы
│   └── utils/            # Утилиты
│       └── auth.js       # Утилиты для работы с токенами
├── public/                # Статические файлы
└── package.json          # Зависимости npm
```

### Основные компоненты

- **Header** — шапка сайта с цитатой (ссылка на главную), меню пользователя и выбором библиотек
- **Sidebar** — боковая панель с иерархией категорий и динамическими хэштегами
- **LibrarySelector** — компонент выбора библиотек (отображается в шапке)
- **MainPage** — главная страница с фильтрацией книг по категориям, хэштегам и библиотекам
- **UserPage** — страница пользователя для управления профилем и библиотеками

### Особенности

- Динамические счетчики книг в категориях с учетом выбранных библиотек
- Визуализация хэштегов с переменным размером шрифта (8px-20px) в зависимости от частоты
- Сохранение выбранных библиотек в localStorage
- Фильтрация: если не выбрана ни одна библиотека — книги не отображаются

---

**Последнее обновление:** 2025-01-27 (добавлен BookDetailModal, система обложек, отображение страниц и электронных версий книг)

