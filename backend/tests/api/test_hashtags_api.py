"""
API тесты для HashtagViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestHashtagAPI:
    """Тесты API хэштегов"""
    
    def test_list_hashtags(self, authenticated_client, user):
        """Получение списка хэштегов"""
        from books.models import Hashtag
        Hashtag.objects.create(name='#тест', slug='test', creator=user)
        
        response = authenticated_client.get('/api/hashtags/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_retrieve_hashtag_by_slug(self, authenticated_client, user):
        """Получение хэштега по slug"""
        from books.models import Hashtag
        hashtag = Hashtag.objects.create(name='#тест', slug='test', creator=user)
        
        response = authenticated_client.get(f'/api/hashtags/{hashtag.slug}/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_hashtags(self, authenticated_client, user):
        """Поиск хэштегов"""
        from books.models import Hashtag
        Hashtag.objects.create(name='#фантастика', slug='fantastika', creator=user)
        
        response = authenticated_client.get('/api/hashtags/?search=фантастика')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_hashtag(self, authenticated_client, user):
        """Создание хэштега"""
        data = {'name': 'новый_тег'}
        response = authenticated_client.post('/api/hashtags/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '#новый_тег'
    
    def test_create_hashtag_empty_name(self, authenticated_client):
        """Создание хэштега с пустым именем"""
        data = {'name': ''}
        response = authenticated_client.post('/api/hashtags/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

