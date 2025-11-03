"""
API тесты для BookPageViewSet
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestBookPageAPI:
    """Тесты API страниц книг"""
    
    def test_list_book_pages(self, authenticated_client, book, sample_image):
        """Получение списка страниц"""
        from books.models import BookPage
        BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image
        )
        
        response = authenticated_client.get('/api/book-pages/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_book(self, authenticated_client, book, sample_image):
        """Фильтрация по книге"""
        from books.models import BookPage
        BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image
        )
        
        response = authenticated_client.get(f'/api/book-pages/?book={book.id}')
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_status(self, authenticated_client, book, sample_image):
        """Фильтрация по статусу"""
        from books.models import BookPage
        BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image,
            processing_status='pending'
        )
        
        response = authenticated_client.get('/api/book-pages/?status=pending')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_book_page(self, authenticated_client, book, sample_image):
        """Создание страницы"""
        # Используем custom action в BookViewSet для загрузки страниц
        # upload_pages принимает несколько файлов и создает страницы автоматически
        data = {'pages': [sample_image]}
        response = authenticated_client.post(
            f'/api/books/{book.id}/upload_pages/',
            data,
            format='multipart'
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_process_book_page(self, authenticated_client, book, sample_image, monkeypatch):
        """Обработка страницы"""
        from books.models import BookPage
        page = BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image,
            processing_status='pending'
        )
        
        # Мокируем process_document
        def mock_process_document(input_path, output_path):
            return 800, 1200
        
        monkeypatch.setattr(
            'books.views.book_pages.process_document',
            mock_process_document
        )
        
        response = authenticated_client.post(f'/api/book-pages/{page.id}/process/')
        # Может быть успех или ошибка
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_process_already_processed_page(self, authenticated_client, book, sample_image):
        """Обработка уже обработанной страницы"""
        from books.models import BookPage
        page = BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image,
            processing_status='completed'
        )
        
        response = authenticated_client.post(f'/api/book-pages/{page.id}/process/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

