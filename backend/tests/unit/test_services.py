"""
Тесты для сервисов
"""
import pytest
from django.contrib.auth import get_user_model

from books.models import Book, Hashtag, BookHashtag, Library, Author, BookAuthor
from books.services.hashtag_service import HashtagService
from books.services.transfer_service import TransferService
from books.services.book_service import BookService
from books.exceptions import HashtagLimitExceeded, TransferError
from books.constants import MAX_HASHTAGS_PER_BOOK, MAX_AUTHORS_PER_BOOK

User = get_user_model()


class TestHashtagService:
    """Тесты HashtagService"""
    
    def test_normalize_name(self):
        """Нормализация названия хэштега"""
        assert HashtagService.normalize_name('#фантастика') == 'фантастика'
        assert HashtagService.normalize_name('  #фантастика  ') == 'фантастика'
        assert HashtagService.normalize_name('фантастика') == 'фантастика'
        assert HashtagService.normalize_name('') == ''
    
    def test_create_slug(self):
        """Создание slug"""
        slug = HashtagService.create_slug('#Тестовая Название')
        assert slug is not None
        assert len(slug) > 0
    
    def test_get_or_create_hashtag_new(self, user):
        """Создание нового хэштега"""
        hashtag, created = HashtagService.get_or_create_hashtag('фантастика', user)
        assert created is True
        assert hashtag.name == '#фантастика'
        assert hashtag.creator == user
    
    def test_get_or_create_hashtag_existing(self, user):
        """Получение существующего хэштега"""
        hashtag1, created1 = HashtagService.get_or_create_hashtag('фантастика', user)
        hashtag2, created2 = HashtagService.get_or_create_hashtag('фантастика', user)
        
        assert created1 is True
        assert created2 is False
        assert hashtag1.id == hashtag2.id
    
    def test_get_or_create_hashtag_empty_name(self, user):
        """Пустое название хэштега"""
        with pytest.raises(ValueError):
            HashtagService.get_or_create_hashtag('', user)
    
    def test_add_hashtags_to_book(self, book, user):
        """Добавление хэштегов к книге"""
        hashtag_names = ['фантастика', 'приключения']
        added = HashtagService.add_hashtags_to_book(book, hashtag_names, user)
        
        assert len(added) == 2
        assert book.hashtags.count() == 2
    
    def test_add_hashtags_limit_exceeded(self, book, user):
        """Превышение лимита хэштегов"""
        # Добавляем до лимита
        existing = []
        for i in range(MAX_HASHTAGS_PER_BOOK):
            hashtag = Hashtag.objects.create(
                name=f'#тест{i}',
                slug=f'test{i}',
                creator=user
            )
            BookHashtag.objects.create(book=book, hashtag=hashtag)
            existing.append(hashtag)
        
        # Пытаемся добавить еще один
        with pytest.raises(HashtagLimitExceeded):
            HashtagService.add_hashtags_to_book(book, ['новый'], user)
    
    def test_add_hashtags_duplicate(self, book, user):
        """Добавление дублирующегося хэштега"""
        hashtag = Hashtag.objects.create(name='#тест', slug='test', creator=user)
        BookHashtag.objects.create(book=book, hashtag=hashtag)
        
        # Пытаемся добавить тот же хэштег
        added = HashtagService.add_hashtags_to_book(book, ['тест'], user)
        # Не должен быть добавлен повторно
        assert book.hashtags.count() == 1


class TestTransferService:
    """Тесты TransferService"""
    
    def test_transfer_to_library(self, book, library):
        """Передача книги в библиотеку"""
        original_library = book.library
        TransferService.transfer_to_library(book, library)
        
        book.refresh_from_db()
        assert book.library == library
    
    def test_transfer_to_library_none(self, book):
        """Передача в None библиотеку"""
        with pytest.raises(TransferError):
            TransferService.transfer_to_library(book, None)
    
    def test_transfer_to_user(self, book, user2):
        """Передача книги другому пользователю"""
        original_owner = book.owner
        TransferService.transfer_to_user(book, user2)
        
        book.refresh_from_db()
        assert book.owner == user2
    
    def test_transfer_to_user_none(self, book):
        """Передача None пользователю"""
        with pytest.raises(TransferError):
            TransferService.transfer_to_user(book, None)
    
    def test_transfer_book_to_library(self, book, library):
        """Передача через transfer_book в библиотеку"""
        book, message = TransferService.transfer_book(book, library_id=library.id)
        
        assert book.library == library
        assert 'библиотеку' in message.lower()
    
    def test_transfer_book_to_user(self, book, user2):
        """Передача через transfer_book пользователю"""
        book, message = TransferService.transfer_book(book, user_id=user2.id)
        
        assert book.owner == user2
        assert 'пользователю' in message.lower()
    
    def test_transfer_book_library_not_found(self, book):
        """Передача в несуществующую библиотеку"""
        with pytest.raises(TransferError):
            TransferService.transfer_book(book, library_id=99999)
    
    def test_transfer_book_user_not_found(self, book):
        """Передача несуществующему пользователю"""
        with pytest.raises(TransferError):
            TransferService.transfer_book(book, user_id=99999)
    
    def test_transfer_book_no_params(self, book):
        """Передача без указания library или user"""
        with pytest.raises(TransferError):
            TransferService.transfer_book(book)


class TestBookService:
    """Тесты BookService"""
    
    def test_create_book_with_relations(self, db, user, category, author, publisher, library):
        """Создание книги со связями"""
        validated_data = {
            'category': category,
            'title': 'Новая книга',
            'library': library,
            'publisher': publisher,
            'year': 2020
        }
        author_ids = [author.id]
        
        book = BookService.create_book_with_relations(
            validated_data,
            author_ids,
            None,
            user
        )
        
        assert book.title == 'Новая книга'
        assert book.owner == user
        assert book.authors.count() == 1
        assert author in book.authors.all()
    
    def test_create_book_with_hashtags(self, db, user, category, author, publisher, library):
        """Создание книги с хэштегами"""
        validated_data = {
            'category': category,
            'title': 'Книга с хэштегами',
            'library': library,
            'publisher': publisher
        }
        
        book = BookService.create_book_with_relations(
            validated_data,
            [author.id],
            ['фантастика', 'приключения'],
            user
        )
        
        assert book.hashtags.count() == 2
    
    def test_create_book_max_authors(self, db, user, category, publisher, library):
        """Создание книги с максимальным количеством авторов"""
        authors = [Author.objects.create(full_name=f'Автор {i}') 
                  for i in range(MAX_AUTHORS_PER_BOOK)]
        author_ids = [a.id for a in authors]
        
        validated_data = {
            'category': category,
            'title': 'Книга',
            'library': library,
            'publisher': publisher
        }
        
        book = BookService.create_book_with_relations(
            validated_data,
            author_ids,
            None,
            user
        )
        
        assert book.authors.count() == MAX_AUTHORS_PER_BOOK
    
    def test_update_book_authors(self, book, author):
        """Обновление авторов книги"""
        author2 = Author.objects.create(full_name='Второй Автор')
        author3 = Author.objects.create(full_name='Третий Автор')
        
        # Обновляем авторов
        BookService.update_book_authors(book, [author2.id, author3.id])
        
        book.refresh_from_db()
        assert book.authors.count() == 2
        assert author2 in book.authors.all()
        assert author3 in book.authors.all()
        assert author not in book.authors.all()
    
    def test_update_book_authors_none(self, book):
        """Обновление авторов None (не меняем)"""
        original_count = book.authors.count()
        BookService.update_book_authors(book, None)
        
        book.refresh_from_db()
        assert book.authors.count() == original_count
    
    def test_update_book_authors_empty_list(self, book):
        """Обновление авторов пустым списком"""
        BookService.update_book_authors(book, [])
        
        book.refresh_from_db()
        assert book.authors.count() == 0

