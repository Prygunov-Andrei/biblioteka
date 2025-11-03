"""
API тесты для LibraryViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestLibraryAPI:
    """Тесты API библиотек"""
    
    def test_list_libraries(self, authenticated_client, library):
        """Получение списка библиотек"""
        response = authenticated_client.get('/api/libraries/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_create_library(self, authenticated_client, user):
        """Создание библиотеки"""
        data = {
            'name': 'Моя библиотека',
            'address': 'Москва, ул. Тестовая, 1',
            'city': 'Москва',
            'country': 'Россия',
            'description': 'Описание'
            # owner не передаем - он устанавливается через perform_create
        }
        response = authenticated_client.post('/api/libraries/', data)
        # perform_create автоматически устанавливает owner
        assert response.status_code == status.HTTP_201_CREATED, f"Expected 201, got {response.status_code}. Errors: {response.data if hasattr(response, 'data') else 'No data'}"
        assert response.data['name'] == 'Моя библиотека'
        # perform_create автоматически устанавливает owner, проверяем через owner_username
        assert response.data['owner_username'] == user.username
    
    def test_get_my_libraries(self, authenticated_client, user, library):
        """Получение своих библиотек"""
        response = authenticated_client.get('/api/libraries/my_libraries/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_update_library_owner(self, authenticated_client, library):
        """Обновление библиотеки владельцем"""
        data = {'name': 'Обновленное название'}
        response = authenticated_client.patch(f'/api/libraries/{library.id}/', data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_library_not_owner(self, library, user2):
        """Обновление библиотеки не владельцем"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=user2)
        
        data = {'name': 'Попытка изменить'}
        response = client.patch(f'/api/libraries/{library.id}/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_library_books(self, authenticated_client, library, book):
        """Получение книг библиотеки"""
        response = authenticated_client.get(f'/api/libraries/{library.id}/books/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_libraries_by_owner(self, authenticated_client, user, library):
        """Фильтрация библиотек по владельцу"""
        response = authenticated_client.get(f'/api/libraries/?owner={user.id}')
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_library(self, authenticated_client, library):
        """Удаление библиотеки"""
        library_id = library.id
        response = authenticated_client.delete(f'/api/libraries/{library_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

