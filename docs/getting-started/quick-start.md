# 🚀 Быстрый старт

## Аутентификация

Для работы с API требуется JWT токен (кроме чтения публичных данных).

### Получение токена

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Использование токена

Добавьте заголовок в запросы:
```bash
curl -X GET http://localhost:8000/api/books/ \
  -H "Authorization: Bearer {access_token}"
```

### Создание пользователя

Создайте суперпользователя для доступа к админке:
```bash
python manage.py createsuperuser
```

---

## Запуск за 5 минут

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройка БД

Убедитесь, что PostgreSQL запущен и создайте БД:

```bash
psql -U postgres -c "CREATE DATABASE biblioteka;"
```

### 3. Миграции

```bash
python manage.py migrate
python manage.py sync_categories
```

### 4. Запуск

```bash
python manage.py runserver
```

Готово! API доступен на http://localhost:8000/api/

## Первые шаги

### Создание категории

```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "test",
    "name": "Тестовая категория",
    "slug": "test-category"
  }'
```

### Создание автора

```bash
curl -X POST http://localhost:8000/api/authors/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иванов И.И.",
    "birth_year": 1950
  }'
```

### Создание книги

**Требует:** JWT токен (см. раздел "Аутентификация")

```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "title": "Тестовая книга",
    "author_ids": [1],
    "category": 1,
    "year": 2023,
    "status": "want_to_read",
    "hashtag_names": ["#фантастика"]
  }'
```

**Примечание:** `owner` устанавливается автоматически (текущий пользователь)

### Создание библиотеки

```bash
curl -X POST http://localhost:8000/api/libraries/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "name": "Моя библиотека",
    "address": "ул. Ленина, д. 1",
    "city": "Москва",
    "country": "Россия"
  }'
```

### Свой профиль

```bash
# Получить профиль
curl -X GET http://localhost:8000/api/user-profiles/me/ \
  -H "Authorization: Bearer {access_token}"

# Обновить профиль
curl -X PATCH http://localhost:8000/api/user-profiles/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "full_name": "Иван Иванов",
    "description": "Мое описание"
  }'
```

## Полная документация

- [Установка](installation.md)
- [API Endpoints](../api/endpoints.md)
- [Тестирование](../testing/testing-guide.md)

---

**Последнее обновление:** 2025-11-03

