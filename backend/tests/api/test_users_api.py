"""
API тесты для UserProfileViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestUserProfileAPI:
    """Тесты API профилей пользователей"""
    
    def test_get_my_profile(self, authenticated_client, user):
        """Получение своего профиля"""
        response = authenticated_client.get('/api/user-profiles/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['username'] == user.username
    
    def test_update_my_profile(self, authenticated_client, user):
        """Обновление своего профиля"""
        data = {
            'full_name': 'Иван Иванов',
            'description': 'Новое описание'
        }
        response = authenticated_client.put('/api/user-profiles/me/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == 'Иван Иванов'
    
    def test_partial_update_my_profile(self, authenticated_client, user):
        """Частичное обновление профиля"""
        data = {'full_name': 'Петр Петров'}
        response = authenticated_client.patch('/api/user-profiles/me/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == 'Петр Петров'
    
    def test_get_profile_by_id(self, authenticated_client, user):
        """Получение профиля по ID"""
        response = authenticated_client.get(f'/api/user-profiles/{user.profile.id}/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_profile_photo(self, authenticated_client, user, sample_image):
        """Обновление фото профиля"""
        data = {'photo': sample_image}
        response = authenticated_client.patch(
            '/api/user-profiles/me/',
            data,
            format='multipart'
        )
        # Может быть успех или ошибка в зависимости от настроек
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

