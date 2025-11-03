# Frontend - Biblioteka

React приложение для управления библиотекой книг.

## Быстрый старт

1. Установить зависимости:
```bash
npm install
```

2. Запустить development server:
```bash
npm start
```

Приложение откроется на http://localhost:3000

## Структура проекта

```
src/
├── components/        # React компоненты
│   ├── Header.js      # Шапка сайта
│   ├── Sidebar.js     # Боковая панель
│   ├── BookCard.js    # Карточка книги
│   ├── BookGrid.js    # Сетка карточек
│   ├── Filters.js     # Фильтры книг
│   └── PrivateRoute.js # Защищенный маршрут
├── pages/            # Страницы
│   ├── LoginPage.js   # Страница авторизации
│   └── MainPage.js    # Главная страница
├── services/          # API сервисы
│   └── api.js        # Axios клиент и API методы
└── utils/            # Утилиты
    └── auth.js       # Утилиты для работы с токенами
```

## Учетные данные по умолчанию

- Логин: `admin`
- Пароль: `admin`

## Backend

Убедитесь, что backend запущен на http://localhost:8000
