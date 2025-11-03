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


# Заглушки для будущих Factory Boy фабрик
# TODO: Реализовать после установки factory-boy
# @pytest.fixture
# def category_factory():
#     from tests.fixtures.factories import CategoryFactory
#     return CategoryFactory
#
# @pytest.fixture
# def author_factory():
#     from tests.fixtures.factories import AuthorFactory
#     return AuthorFactory
#
# @pytest.fixture
# def publisher_factory():
#     from tests.fixtures.factories import PublisherFactory
#     return PublisherFactory
#
# @pytest.fixture
# def book_factory():
#     from tests.fixtures.factories import BookFactory
#     return BookFactory

