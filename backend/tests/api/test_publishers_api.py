"""
API тесты для PublisherViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestPublisherAPI:
    """Тесты API издательств"""
    
    def test_list_publishers(self, authenticated_client, publisher):
        """Получение списка издательств"""
        response = authenticated_client.get('/api/publishers/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_retrieve_publisher(self, authenticated_client, publisher):
        """Получение издательства"""
        response = authenticated_client.get(f'/api/publishers/{publisher.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == publisher.name
    
    def test_search_publishers(self, authenticated_client, publisher):
        """Поиск издательств"""
        response = authenticated_client.get('/api/publishers/?search=Тестовое')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_filter_publishers_by_city(self, authenticated_client, publisher):
        """Фильтрация издательств по городу"""
        response = authenticated_client.get('/api/publishers/?city=Москва')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_publisher(self, authenticated_client):
        """Создание издательства"""
        data = {
            'name': 'Новое издательство',
            'city': 'СПб',
            'website': 'https://new.ru',
            'description': 'Описание'
        }
        response = authenticated_client.post('/api/publishers/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Новое издательство'
    
    def test_update_publisher(self, authenticated_client, publisher):
        """Обновление издательства"""
        data = {'city': 'Санкт-Петербург'}
        response = authenticated_client.patch(f'/api/publishers/{publisher.id}/', data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_publisher_books(self, authenticated_client, publisher, book):
        """Получение книг издательства"""
        response = authenticated_client.get(f'/api/publishers/{publisher.id}/books/')
        assert response.status_code == status.HTTP_200_OK

