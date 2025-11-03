"""
API тесты для BookImageViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestBookImageAPI:
    """Тесты API изображений книг"""
    
    def test_list_book_images(self, authenticated_client, book, sample_image):
        """Получение списка изображений"""
        from books.models import BookImage
        BookImage.objects.create(book=book, image=sample_image, order=1)
        
        response = authenticated_client.get('/api/book-images/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_book_images_by_book(self, authenticated_client, book, sample_image):
        """Фильтрация изображений по книге"""
        from books.models import BookImage
        BookImage.objects.create(book=book, image=sample_image, order=1)
        
        response = authenticated_client.get(f'/api/book-images/?book={book.id}')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_book_image(self, authenticated_client, book, sample_image):
        """Создание изображения книги"""
        # Используем custom action в BookViewSet
        data = {'image': sample_image, 'order': 1}
        response = authenticated_client.post(
            f'/api/books/{book.id}/images/',
            data,
            format='multipart'
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_update_book_image(self, authenticated_client, book, sample_image):
        """Обновление изображения"""
        from books.models import BookImage
        book_image = BookImage.objects.create(book=book, image=sample_image, order=1)
        
        data = {'order': 2}
        response = authenticated_client.patch(
            f'/api/book-images/{book_image.id}/',
            data
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_book_image(self, authenticated_client, book, sample_image):
        """Удаление изображения"""
        from books.models import BookImage
        book_image = BookImage.objects.create(book=book, image=sample_image, order=1)
        
        response = authenticated_client.delete(f'/api/book-images/{book_image.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

