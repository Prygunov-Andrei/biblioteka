# 🔧 Установка и настройка

## Требования

- Python 3.9+
- PostgreSQL 12+
- pip (менеджер пакетов Python)

## Установка зависимостей

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd biblioteka
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка Python зависимостей

```bash
cd backend
pip install -r requirements.txt
```

## Настройка базы данных

### 1. Установка PostgreSQL

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Создание базы данных

```bash
psql -U postgres
```

В консоли PostgreSQL:
```sql
CREATE DATABASE biblioteka;
CREATE USER biblioteka_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE biblioteka TO biblioteka_user;
\q
```

### 3. Настройка переменных окружения

Создайте файл `.env` в директории `backend/`:

```env
DB_NAME=biblioteka
DB_USER=biblioteka_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Применение миграций

```bash
cd backend
python manage.py migrate
```

### 5. Синхронизация категорий

```bash
python manage.py sync_categories
```

## Запуск сервера разработки

```bash
cd backend
python manage.py runserver
```

Сервер будет доступен по адресу: `http://localhost:8000`

## Проверка установки

Откройте в браузере:
- API Root: http://localhost:8000/api/
- Categories: http://localhost:8000/api/categories/
- Books: http://localhost:8000/api/books/

---

**Последнее обновление:** 2025-11-03

