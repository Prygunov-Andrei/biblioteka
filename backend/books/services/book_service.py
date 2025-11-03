"""
Сервис для работы с книгами
"""
from typing import List, Optional
from django.contrib.auth import get_user_model
from ..models import Book, BookAuthor, Author
from ..services.hashtag_service import HashtagService
from ..constants import MAX_AUTHORS_PER_BOOK

User = get_user_model()


class BookService:
    """Сервис для работы с книгами"""
    
    @staticmethod
    def create_book_with_relations(
        validated_data: dict,
        author_ids: List[int],
        hashtag_names: Optional[List[str]],
        creator: User
    ) -> Book:
        """
        Создает книгу со всеми связями (авторы, хэштеги).
        Returns: созданная книга
        """
        # Автоматически устанавливаем владельца
        if 'owner' not in validated_data:
            validated_data['owner'] = creator
        
        # Создаем книгу
        book = Book.objects.create(**validated_data)
        
        # Создаем связи с авторами
        BookService._create_book_authors(book, author_ids)
        
        # Создаем связи с хэштегами
        if hashtag_names:
            HashtagService.add_hashtags_to_book(book, hashtag_names, creator)
        
        return book
    
    @staticmethod
    def _create_book_authors(book: Book, author_ids: List[int]) -> None:
        """Создает связи книги с авторами"""
        if not author_ids:
            return
        
        for idx, author_id in enumerate(author_ids[:MAX_AUTHORS_PER_BOOK], 1):
            try:
                BookAuthor.objects.create(
                    book=book,
                    author_id=author_id,
                    order=idx
                )
            except Author.DoesNotExist:
                # Пропускаем несуществующих авторов
                continue
    
    @staticmethod
    def update_book_authors(book: Book, author_ids: Optional[List[int]]) -> None:
        """Обновляет авторов книги"""
        if author_ids is None:
            return
        
        # Удаляем старые связи
        BookAuthor.objects.filter(book=book).delete()
        
        # Создаем новые
        BookService._create_book_authors(book, author_ids)

