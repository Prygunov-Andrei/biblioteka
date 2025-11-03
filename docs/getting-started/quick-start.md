# 🚀 Быстрый старт

Минимальные шаги для запуска проекта с нуля.

## 1. Установка зависимостей

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## 2. Настройка базы данных

```bash
# Создать базу данных PostgreSQL
createdb biblioteka

# Применить миграции (все таблицы создадутся автоматически!)
cd backend
python manage.py migrate

# Загрузить категории
python manage.py sync_categories

# Создать суперпользователя
python manage.py createsuperuser
# username: admin
# password: admin
```

## 3. Запуск

```bash
# Из корня проекта
bash start_all.sh
```

Или вручную:

```bash
# Backend (в одном терминале)
cd backend
python manage.py runserver

# Frontend (в другом терминале)
cd frontend
npm start
```

## 4. Проверка

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/
- Войти: `admin` / `admin`

## Устранение проблем

### Ошибка "relation does not exist"

1. Проверьте состояние миграций:
```bash
python manage.py showmigrations
```

2. Если миграции не применены:
```bash
python manage.py migrate
```

3. Если миграции применены, но таблиц нет:
```bash
python manage.py check_db_schema
```

Подробнее: [Настройка базы данных](../../deployment/database-setup.md)

---

**Последнее обновление:** 2025-11-03
