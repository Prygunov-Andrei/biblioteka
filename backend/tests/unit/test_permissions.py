"""
Тесты для permissions
"""
import pytest
from rest_framework.test import APIRequestFactory

from books.models import Book, Library, BookReview, Hashtag
from books.permissions import (
    IsOwnerOrReadOnly,
    IsLibraryOwner,
    IsReviewOwner,
    IsHashtagCreatorOrReadOnly,
    IsBookOwnerAction
)

from django.contrib.auth import get_user_model

User = get_user_model()


class TestIsOwnerOrReadOnly:
    """Тесты IsOwnerOrReadOnly"""
    
    def test_read_permission_all(self, book, user2):
        """Чтение разрешено всем"""
        factory = APIRequestFactory()
        request = factory.get('/api/books/')
        request.user = user2
        
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, book) is True
    
    def test_write_permission_owner(self, book, user):
        """Запись разрешена владельцу"""
        factory = APIRequestFactory()
        request = factory.put('/api/books/1/')
        request.user = user
        
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, book) is True
    
    def test_write_permission_not_owner(self, book, user2):
        """Запись запрещена не владельцу"""
        factory = APIRequestFactory()
        request = factory.put('/api/books/1/')
        request.user = user2
        
        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, book) is False


class TestIsLibraryOwner:
    """Тесты IsLibraryOwner"""
    
    def test_read_permission_all(self, library, user2):
        """Чтение разрешено всем"""
        factory = APIRequestFactory()
        request = factory.get('/api/libraries/1/')
        request.user = user2
        
        permission = IsLibraryOwner()
        assert permission.has_object_permission(request, None, library) is True
    
    def test_write_permission_owner(self, library, user):
        """Запись разрешена владельцу"""
        factory = APIRequestFactory()
        request = factory.put('/api/libraries/1/')
        request.user = user
        
        permission = IsLibraryOwner()
        assert permission.has_object_permission(request, None, library) is True
    
    def test_write_permission_not_owner(self, library, user2):
        """Запись запрещена не владельцу"""
        factory = APIRequestFactory()
        request = factory.put('/api/libraries/1/')
        request.user = user2
        
        permission = IsLibraryOwner()
        assert permission.has_object_permission(request, None, library) is False


class TestIsReviewOwner:
    """Тесты IsReviewOwner"""
    
    def test_read_permission_all(self, book, user, user2):
        """Чтение разрешено всем"""
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отзыв'
        )
        
        factory = APIRequestFactory()
        request = factory.get('/api/reviews/1/')
        request.user = user2
        
        permission = IsReviewOwner()
        assert permission.has_object_permission(request, None, review) is True
    
    def test_write_permission_owner(self, book, user):
        """Запись разрешена автору отзыва"""
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отзыв'
        )
        
        factory = APIRequestFactory()
        request = factory.put('/api/reviews/1/')
        request.user = user
        
        permission = IsReviewOwner()
        assert permission.has_object_permission(request, None, review) is True
    
    def test_write_permission_not_owner(self, book, user, user2):
        """Запись запрещена не автору"""
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отзыв'
        )
        
        factory = APIRequestFactory()
        request = factory.put('/api/reviews/1/')
        request.user = user2
        
        permission = IsReviewOwner()
        assert permission.has_object_permission(request, None, review) is False


class TestIsHashtagCreatorOrReadOnly:
    """Тесты IsHashtagCreatorOrReadOnly"""
    
    def test_read_permission_all(self, user, user2):
        """Чтение разрешено всем"""
        hashtag = Hashtag.objects.create(
            name='#тест',
            slug='test',
            creator=user
        )
        
        factory = APIRequestFactory()
        request = factory.get('/api/hashtags/test/')
        request.user = user2
        
        permission = IsHashtagCreatorOrReadOnly()
        assert permission.has_object_permission(request, None, hashtag) is True
    
    def test_delete_permission_creator(self, user):
        """Удаление разрешено создателю"""
        hashtag = Hashtag.objects.create(
            name='#тест',
            slug='test',
            creator=user
        )
        
        factory = APIRequestFactory()
        request = factory.delete('/api/hashtags/test/')
        request.user = user
        
        permission = IsHashtagCreatorOrReadOnly()
        assert permission.has_object_permission(request, None, hashtag) is True
    
    def test_delete_permission_not_creator(self, user, user2):
        """Удаление запрещено не создателю"""
        hashtag = Hashtag.objects.create(
            name='#тест',
            slug='test',
            creator=user
        )
        
        factory = APIRequestFactory()
        request = factory.delete('/api/hashtags/test/')
        request.user = user2
        
        permission = IsHashtagCreatorOrReadOnly()
        assert permission.has_object_permission(request, None, hashtag) is False
    
    def test_delete_general_hashtag_admin(self, user):
        """Удаление общего хэштега только админом"""
        hashtag = Hashtag.objects.create(
            name='#общий',
            slug='obshtii',
            creator=None
        )
        
        # Обычный пользователь
        factory = APIRequestFactory()
        request = factory.delete('/api/hashtags/obshtii/')
        request.user = user
        request.user.is_staff = False
        
        permission = IsHashtagCreatorOrReadOnly()
        assert permission.has_object_permission(request, None, hashtag) is False
        
        # Админ
        request.user.is_staff = True
        assert permission.has_object_permission(request, None, hashtag) is True


class TestIsBookOwnerAction:
    """Тесты IsBookOwnerAction"""
    
    def test_permission_owner(self, book, user):
        """Разрешение для владельца"""
        factory = APIRequestFactory()
        request = factory.post('/api/books/1/transfer/')
        request.user = user
        
        permission = IsBookOwnerAction()
        assert permission.has_object_permission(request, None, book) is True
    
    def test_permission_not_owner(self, book, user2):
        """Запрет для не владельца"""
        factory = APIRequestFactory()
        request = factory.post('/api/books/1/transfer/')
        request.user = user2
        
        permission = IsBookOwnerAction()
        assert permission.has_object_permission(request, None, book) is False
    
    def test_permission_no_owner_attribute(self, user):
        """Объект без атрибута owner"""
        factory = APIRequestFactory()
        request = factory.post('/api/test/')
        request.user = user
        
        permission = IsBookOwnerAction()
        obj = type('obj', (object,), {})()  # Объект без owner
        assert permission.has_object_permission(request, None, obj) is False

