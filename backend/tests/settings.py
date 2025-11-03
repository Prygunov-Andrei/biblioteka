"""
Тестовые настройки Django для pytest
"""
from config.settings import *
import tempfile

# Переопределяем БД для тестов (SQLite in-memory быстрее для тестов)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Отключаем миграции в тестах (используем только create_table)
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Медиа файлы во временной папке
MEDIA_ROOT = tempfile.mkdtemp()

# Отключаем кэширование в тестах
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Ускоряем пароли в тестах
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Отключаем логирование в тестах (опционально)
# LOGGING = {}

# CORS настройки для тестов
CORS_ALLOW_ALL_ORIGINS = True

# Отключаем проверку безопасности для тестов
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery (если используется) - отключаем в тестах
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

