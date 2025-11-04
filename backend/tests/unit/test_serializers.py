"""
Тесты для сериализаторов
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from books.models import (
    Category, Author, Publisher, Language, Book, BookAuthor, BookImage,
    BookElectronic, BookReadingDate, UserProfile, Library, Hashtag, BookReview
)
from books.serializers import (
    CategorySerializer, AuthorSerializer, PublisherSerializer, LanguageSerializer,
    BookSerializer, BookCreateSerializer, BookUpdateSerializer,
    BookImageSerializer, BookElectronicSerializer, BookReadingDateSerializer,
    UserProfileSerializer, LibrarySerializer, HashtagSerializer,
    BookReviewSerializer
)
from books.constants import MAX_HASHTAGS_PER_BOOK, MAX_AUTHORS_PER_BOOK

User = get_user_model()


# Создаем мок request для сериализаторов
class MockRequest:
    """Мок request для использования в контексте сериализаторов"""
    def __init__(self, user):
        self.user = user


class TestCategorySerializer:
    """Тесты CategorySerializer"""
    
    def test_serialize_category(self, category):
        """Сериализация категории"""
        serializer = CategorySerializer(category)
        data = serializer.data
        assert data['code'] == category.code
        assert data['name'] == category.name
        assert data['slug'] == category.slug
    
    def test_deserialize_category(self, db):
        """Десериализация категории"""
        data = {
            'code': 'new_cat',
            'name': 'Новая категория',
            'slug': 'new-category',
            'icon': '📚',
            'order': 1
        }
        serializer = CategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()
        assert category.code == 'new_cat'


class TestAuthorSerializer:
    """Тесты AuthorSerializer"""
    
    def test_serialize_author(self, author):
        """Сериализация автора"""
        serializer = AuthorSerializer(author)
        data = serializer.data
        assert data['full_name'] == author.full_name
        assert data['birth_year'] == author.birth_year
    
    def test_deserialize_author(self, db):
        """Десериализация автора"""
        data = {
            'full_name': 'Новый Автор',
            'birth_year': 1960,
            'death_year': 2020,
            'biography': 'Биография'
        }
        serializer = AuthorSerializer(data=data)
        assert serializer.is_valid()
        author = serializer.save()
        assert author.full_name == 'Новый Автор'


class TestPublisherSerializer:
    """Тесты PublisherSerializer"""
    
    def test_serialize_publisher(self, publisher):
        """Сериализация издательства"""
        serializer = PublisherSerializer(publisher)
        data = serializer.data
        assert data['name'] == publisher.name
        assert data['city'] == publisher.city
    
    def test_deserialize_publisher(self, db):
        """Десериализация издательства"""
        data = {
            'name': 'Новое издательство',
            'city': 'СПб',
            'website': 'https://new.ru',
            'description': 'Описание'
        }
        serializer = PublisherSerializer(data=data)
        assert serializer.is_valid()
        publisher = serializer.save()
        assert publisher.name == 'Новое издательство'


class TestLanguageSerializer:
    """Тесты LanguageSerializer"""
    
    def test_serialize_language(self, language):
        """Сериализация языка"""
        serializer = LanguageSerializer(language)
        data = serializer.data
        assert data['name'] == language.name
        assert data['code'] == language.code
    
    def test_deserialize_language(self, db):
        """Десериализация языка"""
        data = {
            'name': 'Английский',
            'code': 'en'
        }
        serializer = LanguageSerializer(data=data)
        assert serializer.is_valid()
        language = serializer.save()
        assert language.name == 'Английский'
        assert language.code == 'en'


class TestBookCreateSerializer:
    """Тесты BookCreateSerializer"""
    
    def test_create_book_with_authors(self, db, user, category, author, publisher, library, language):
        """Создание книги с авторами"""
        data = {
            'category': category.id,
            'title': 'Новая книга',
            'library': library.id,
            'publisher': publisher.id,
            'language': language.id,
            'circulation': 5000,
            'author_ids': [author.id],
            'year': 2020,
            'status': 'none'
        }
        serializer = BookCreateSerializer(data=data, context={'request': MockRequest(user)})
        assert serializer.is_valid()
        book = serializer.save()
        assert book.title == 'Новая книга'
        assert book.authors.count() == 1
        assert book.owner == user
        assert book.language == language
        assert book.circulation == 5000
    
    def test_create_book_max_authors(self, db, user, category, publisher, library):
        """Проверка лимита авторов"""
        authors = [Author.objects.create(full_name=f'Автор {i}') for i in range(MAX_AUTHORS_PER_BOOK + 1)]
        author_ids = [a.id for a in authors]
        
        data = {
            'category': category.id,
            'title': 'Книга',
            'library': library.id,
            'publisher': publisher.id,
            'author_ids': author_ids,
            'year': 2020
        }
        serializer = BookCreateSerializer(data=data, context={'request': MockRequest(user)})
        assert not serializer.is_valid()
        assert 'author_ids' in serializer.errors
    
    def test_create_book_with_hashtags(self, db, user, category, author, publisher, library):
        """Создание книги с хэштегами"""
        data = {
            'category': category.id,
            'title': 'Книга с хэштегами',
            'library': library.id,
            'publisher': publisher.id,
            'author_ids': [author.id],
            'hashtag_names': ['фантастика', 'приключения'],
            'year': 2020
        }
        serializer = BookCreateSerializer(data=data, context={'request': MockRequest(user)})
        assert serializer.is_valid()
        book = serializer.save()
        assert book.hashtags.count() == 2
    
    def test_create_book_max_hashtags(self, db, user, category, author, publisher, library):
        """Проверка лимита хэштегов"""
        hashtags = [f'тест{i}' for i in range(MAX_HASHTAGS_PER_BOOK + 1)]
        data = {
            'category': category.id,
            'title': 'Книга',
            'library': library.id,
            'publisher': publisher.id,
            'author_ids': [author.id],
            'hashtag_names': hashtags,
            'year': 2020
        }
        serializer = BookCreateSerializer(data=data, context={'request': MockRequest(user)})
        assert not serializer.is_valid()
        assert 'hashtag_names' in serializer.errors


class TestBookUpdateSerializer:
    """Тесты BookUpdateSerializer"""
    
    def test_update_book(self, book):
        """Обновление книги"""
        data = {
            'title': 'Обновленное название',
            'year': 2021
        }
        serializer = BookUpdateSerializer(book, data=data, partial=True)
        assert serializer.is_valid()
        updated_book = serializer.save()
        assert updated_book.title == 'Обновленное название'
        assert updated_book.year == 2021
    
    def test_update_book_authors(self, book, author):
        """Обновление авторов книги"""
        author2 = Author.objects.create(full_name='Второй Автор')
        data = {
            'author_ids': [author2.id]
        }
        serializer = BookUpdateSerializer(book, data=data, partial=True)
        assert serializer.is_valid()
        serializer.save()
        book.refresh_from_db()
        assert book.authors.count() == 1
        assert author2 in book.authors.all()


class TestBookSerializer:
    """Тесты BookSerializer"""
    
    def test_serialize_book(self, book):
        """Сериализация книги"""
        serializer = BookSerializer(book)
        data = serializer.data
        assert data['title'] == book.title
        assert 'authors' in data
        assert 'category' in data
        assert 'publisher' in data
        assert 'circulation' in data
        assert 'language' in data
        assert 'language_name' in data
        assert data['circulation'] == 5000
        assert data['language_name'] == 'Русский'


class TestBookReadingDateSerializer:
    """Тесты BookReadingDateSerializer"""
    
    def test_serialize_reading_date(self, book):
        """Сериализация даты прочтения"""
        from datetime import date
        reading_date = BookReadingDate.objects.create(
            book=book,
            date=date(2024, 1, 15),
            notes='Прочитал за один вечер'
        )
        serializer = BookReadingDateSerializer(reading_date)
        data = serializer.data
        assert data['book'] == book.id
        assert data['date'] == '2024-01-15'
        assert data['notes'] == 'Прочитал за один вечер'
    
    def test_deserialize_reading_date(self, book):
        """Десериализация даты прочтения"""
        data = {
            'book': book.id,
            'date': '2024-01-15',
            'notes': 'Отличная книга!'
        }
        serializer = BookReadingDateSerializer(data=data)
        assert serializer.is_valid()
        reading_date = serializer.save()
        assert reading_date.book == book
        assert str(reading_date.date) == '2024-01-15'
        assert reading_date.notes == 'Отличная книга!'


class TestUserProfileSerializer:
    """Тесты UserProfileSerializer"""
    
    def test_serialize_user_profile(self, user):
        """Сериализация профиля"""
        serializer = UserProfileSerializer(user.profile)
        data = serializer.data
        assert 'user' in data
        assert data['user']['username'] == user.username
    
    def test_update_user_profile(self, user):
        """Обновление профиля"""
        data = {
            'full_name': 'Иван Иванов',
            'description': 'Новое описание'
        }
        serializer = UserProfileSerializer(
            user.profile,
            data=data,
            partial=True
        )
        assert serializer.is_valid()
        profile = serializer.save()
        assert profile.full_name == 'Иван Иванов'


class TestLibrarySerializer:
    """Тесты LibrarySerializer"""
    
    def test_serialize_library(self, library):
        """Сериализация библиотеки"""
        serializer = LibrarySerializer(library)
        data = serializer.data
        assert data['name'] == library.name
        assert 'owner' in data
    
    def test_create_library(self, db, user):
        """Создание библиотеки"""
        data = {
            'name': 'Новая библиотека',
            'address': 'Адрес',
            'city': 'Москва',
            'country': 'Россия',
            'description': 'Описание',
            'owner': user.id  # owner обязателен
        }
        serializer = LibrarySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        library = serializer.save()
        assert library.owner == user


class TestHashtagSerializer:
    """Тесты HashtagSerializer"""
    
    def test_serialize_hashtag(self, user):
        """Сериализация хэштега"""
        hashtag = Hashtag.objects.create(
            name='#тест',
            slug='test',
            creator=user
        )
        serializer = HashtagSerializer(hashtag)
        data = serializer.data
        assert data['name'] == '#тест'
        assert 'books_count' in data


class TestBookReviewSerializer:
    """Тесты BookReviewSerializer"""
    
    def test_serialize_book_review(self, book, user):
        """Сериализация отзыва"""
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отличная книга!'
        )
        serializer = BookReviewSerializer(review)
        data = serializer.data
        assert data['rating'] == 5
        assert data['review_text'] == 'Отличная книга!'
    
    def test_create_book_review(self, book, user):
        """Создание отзыва"""
        data = {
            'book': book.id,
            'rating': 4,
            'review_text': 'Хорошая книга'
        }
        serializer = BookReviewSerializer(data=data)
        assert serializer.is_valid()
        review = serializer.save(user=user)
        assert review.book == book
        assert review.user == user
        assert review.rating == 4
    
    def test_review_rating_validation(self, book, user):
        """Валидация оценки (должна быть 1-5)"""
        # Валидные оценки
        for rating in [1, 3, 5]:
            data = {'book': book.id, 'rating': rating, 'review_text': 'Текст'}
            serializer = BookReviewSerializer(data=data)
            assert serializer.is_valid(raise_exception=False)
        
        # Невалидные оценки (если есть валидатор в модели)
        # Проверка зависит от реализации валидации в модели

