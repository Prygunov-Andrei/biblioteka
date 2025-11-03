"""
API тесты для CategoryViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestCategoryAPI:
    """Тесты API категорий"""
    
    def test_list_categories(self, authenticated_client, category):
        """Получение списка категорий"""
        response = authenticated_client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_retrieve_category_by_slug(self, authenticated_client, category):
        """Получение категории по slug"""
        response = authenticated_client.get(f'/api/categories/{category.slug}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['slug'] == category.slug
    
    def test_search_categories_by_name(self, authenticated_client, category):
        """Поиск категорий по названию"""
        response = authenticated_client.get('/api/categories/?search=Тестовая')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_search_categories_by_code(self, authenticated_client, category):
        """Поиск категорий по коду"""
        response = authenticated_client.get('/api/categories/?search=test_cat')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_create_category(self, authenticated_client):
        """Создание категории"""
        data = {
            'code': 'new_cat',
            'name': 'Новая категория',
            'slug': 'new-category',
            'icon': '📚',
            'order': 1
        }
        response = authenticated_client.post('/api/categories/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'new_cat'
    
    def test_update_category(self, authenticated_client, category):
        """Обновление категории"""
        data = {'name': 'Обновленное название'}
        response = authenticated_client.patch(
            f'/api/categories/{category.slug}/',
            data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Обновленное название'
    
    def test_delete_category(self, authenticated_client, category):
        """Удаление категории"""
        response = authenticated_client.delete(f'/api/categories/{category.slug}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

