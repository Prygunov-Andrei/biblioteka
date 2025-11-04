"""
Общие фикстуры pytest для проекта Biblioteka
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from PIL import Image
import io


# Временная папка для медиа файлов в тестах
@pytest.fixture(scope='session')
def tmp_media_root():
    """Создает временную папку для MEDIA_ROOT в тестах"""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker, tmp_media_root):
    """Настраивает тестовую БД с переопределением MEDIA_ROOT"""
    with django_db_blocker.unblock():
        with override_settings(MEDIA_ROOT=tmp_media_root):
            yield


# API клиенты
@pytest.fixture
def api_client():
    """DRF API клиент для тестов"""
    return APIClient()


@pytest.fixture
def admin_client(api_client):
    """API клиент с правами администратора"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=admin_user)
    return api_client


# Тестовые изображения
@pytest.fixture
def sample_image():
    """Создает простое тестовое изображение в памяти"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile(
        'test_image.jpg',
        img_io.read(),
        content_type='image/jpeg'
    )


@pytest.fixture
def sample_image_file(tmp_path):
    """Создает тестовое изображение в файловой системе"""
    img_path = tmp_path / 'test_image.jpg'
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(img_path)
    return img_path


# Простые helper-функции для создания тестовых объектов
@pytest.fixture
def user(db):
    """Создает тестового пользователя"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2(db):
    """Создает второго тестового пользователя"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )


@pytest.fixture
def category(db):
    """Создает тестовую категорию"""
    from books.models import Category
    return Category.objects.create(
        code='test_cat',
        name='Тестовая категория',
        slug='test-category',
        icon='📚',
        order=1
    )


@pytest.fixture
def author(db):
    """Создает тестового автора"""
    from books.models import Author
    return Author.objects.create(
        full_name='Тестов Автор Иванович',
        birth_year=1950,
        death_year=2000,
        biography='Тестовая биография'
    )


@pytest.fixture
def publisher(db):
    """Создает тестовое издательство"""
    from books.models import Publisher
    return Publisher.objects.create(
        name='Тестовое издательство',
        city='Москва',
        website='https://test.ru',
        description='Тестовое описание'
    )


@pytest.fixture
def language(db):
    """Создает тестовый язык"""
    from books.models import Language
    return Language.objects.create(
        name='Русский',
        code='ru'
    )


@pytest.fixture
def library(db, user):
    """Создает тестовую библиотеку"""
    from books.models import Library
    return Library.objects.create(
        owner=user,
        name='Тестовая библиотека',
        address='Тестовый адрес',
        city='Москва',
        country='Россия',
        description='Тестовое описание'
    )


@pytest.fixture
def book(db, user, category, author, publisher, library, language):
    """Создает тестовую книгу"""
    from books.models import Book, BookAuthor
    book = Book.objects.create(
        owner=user,
        library=library,
        category=category,
        publisher=publisher,
        language=language,
        title='Тестовая книга',
        subtitle='Подзаголовок',
        description='Описание книги',
        status='none',
        year=2020,
        pages_info='300 стр.',
        circulation=5000,
        binding_type='hard',
        format='regular',
        condition='good',
        price_rub=1000.00
    )
    BookAuthor.objects.create(book=book, author=author, order=1)
    return book


@pytest.fixture
def authenticated_client(api_client, user):
    """API клиент с аутентифицированным пользователем"""
    api_client.force_authenticate(user=user)
    return api_client

