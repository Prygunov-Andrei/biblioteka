"""
API тесты для BookReviewViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestBookReviewAPI:
    """Тесты API отзывов"""
    
    def test_create_review(self, authenticated_client, book, user):
        """Создание отзыва"""
        data = {
            'book': book.id,
            'rating': 5,
            'review_text': 'Отличная книга!'
        }
        response = authenticated_client.post('/api/book-reviews/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 5
    
    def test_create_review_upsert(self, authenticated_client, book, user):
        """Создание/обновление отзыва (upsert)"""
        # Создаем первый отзыв
        data1 = {
            'book': book.id,
            'rating': 4,
            'review_text': 'Хорошая книга'
        }
        response1 = authenticated_client.post('/api/book-reviews/', data1)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Обновляем тот же отзыв
        data2 = {
            'book': book.id,
            'rating': 5,
            'review_text': 'Отличная книга!'
        }
        response2 = authenticated_client.post('/api/book-reviews/', data2)
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data['rating'] == 5
    
    def test_list_reviews(self, authenticated_client, book, user):
        """Получение списка отзывов"""
        from books.models import BookReview
        BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отзыв'
        )
        
        response = authenticated_client.get('/api/book-reviews/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_filter_reviews_by_book(self, authenticated_client, book, user):
        """Фильтрация отзывов по книге"""
        from books.models import BookReview
        BookReview.objects.create(
            book=book,
            user=user,
            rating=5
        )
        
        response = authenticated_client.get(f'/api/book-reviews/?book={book.id}')
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_review_owner(self, authenticated_client, book, user):
        """Обновление отзыва автором"""
        from books.models import BookReview
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=4,
            review_text='Хорошая'
        )
        
        data = {'review_text': 'Обновленный отзыв'}
        response = authenticated_client.patch(f'/api/book-reviews/{review.id}/', data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_review_not_owner(self, book, user, user2):
        """Обновление отзыва не автором"""
        from books.models import BookReview
        from rest_framework.test import APIClient
        
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=4
        )
        
        client = APIClient()
        client.force_authenticate(user=user2)
        
        data = {'review_text': 'Попытка изменить'}
        response = client.patch(f'/api/book-reviews/{review.id}/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_review(self, authenticated_client, book, user):
        """Удаление отзыва"""
        from books.models import BookReview
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5
        )
        
        response = authenticated_client.delete(f'/api/book-reviews/{review.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

