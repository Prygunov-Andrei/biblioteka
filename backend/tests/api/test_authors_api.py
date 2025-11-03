"""
API тесты для AuthorViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAuthorAPI:
    """Тесты API авторов"""
    
    def test_list_authors(self, authenticated_client, author):
        """Получение списка авторов"""
        response = authenticated_client.get('/api/authors/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_retrieve_author(self, authenticated_client, author):
        """Получение автора"""
        response = authenticated_client.get(f'/api/authors/{author.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == author.id
    
    def test_search_authors_by_name(self, authenticated_client, author):
        """Поиск авторов по имени"""
        response = authenticated_client.get('/api/authors/?search=Тестов')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_filter_authors_by_birth_year(self, authenticated_client, author):
        """Фильтрация авторов по году рождения"""
        response = authenticated_client.get('/api/authors/?birth_year_min=1950')
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_authors_by_birth_year_range(self, authenticated_client, author):
        """Фильтрация авторов по диапазону годов"""
        response = authenticated_client.get(
            '/api/authors/?birth_year_min=1940&birth_year_max=1960'
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_order_authors(self, authenticated_client):
        """Сортировка авторов"""
        response = authenticated_client.get('/api/authors/?ordering=-birth_year')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_author(self, authenticated_client):
        """Создание автора"""
        data = {
            'full_name': 'Новый Автор',
            'birth_year': 1960,
            'death_year': 2020,
            'biography': 'Биография'
        }
        response = authenticated_client.post('/api/authors/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['full_name'] == 'Новый Автор'
    
    def test_update_author(self, authenticated_client, author):
        """Обновление автора"""
        data = {'biography': 'Обновленная биография'}
        response = authenticated_client.patch(f'/api/authors/{author.id}/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['biography'] == 'Обновленная биография'
    
    def test_delete_author(self, authenticated_client, author):
        """Удаление автора"""
        response = authenticated_client.delete(f'/api/authors/{author.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_get_author_books(self, authenticated_client, author, book):
        """Получение книг автора"""
        response = authenticated_client.get(f'/api/authors/{author.id}/books/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

