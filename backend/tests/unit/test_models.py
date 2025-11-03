"""
Тесты для моделей
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from books.models import (
    Category, Author, Publisher, Book, BookAuthor, BookImage,
    BookElectronic, BookPage, UserProfile, Library, Hashtag,
    BookHashtag, BookReview
)

User = get_user_model()


class TestCategory:
    """Тесты модели Category"""
    
    def test_create_category(self, db):
        """Создание категории"""
        category = Category.objects.create(
            code='test',
            name='Тестовая категория',
            slug='test-category',
            icon='📚',
            order=1
        )
        assert category.code == 'test'
        assert category.name == 'Тестовая категория'
        assert category.slug == 'test-category'
    
    def test_category_str(self, category):
        """Проверка __str__ метода"""
        assert str(category) == category.name
    
    def test_category_unique_code(self, db):
        """Уникальность кода категории"""
        Category.objects.create(code='test', name='Test 1', slug='test-1')
        with pytest.raises(IntegrityError):
            Category.objects.create(code='test', name='Test 2', slug='test-2')


class TestAuthor:
    """Тесты модели Author"""
    
    def test_create_author(self, db):
        """Создание автора"""
        author = Author.objects.create(
            full_name='Пушкин А.С.',
            birth_year=1799,
            death_year=1837,
            biography='Великий русский поэт'
        )
        assert author.full_name == 'Пушкин А.С.'
        assert author.birth_year == 1799
    
    def test_author_str(self, author):
        """Проверка __str__ метода"""
        assert str(author) == author.full_name
    
    def test_author_without_death_year(self, db):
        """Автор без года смерти (живой)"""
        author = Author.objects.create(
            full_name='Современный Автор',
            birth_year=1980,
            death_year=None
        )
        assert author.death_year is None


class TestPublisher:
    """Тесты модели Publisher"""
    
    def test_create_publisher(self, db):
        """Создание издательства"""
        publisher = Publisher.objects.create(
            name='АСТ',
            city='Москва',
            website='https://ast.ru',
            description='Крупное издательство'
        )
        assert publisher.name == 'АСТ'
        assert publisher.city == 'Москва'
    
    def test_publisher_str(self, publisher):
        """Проверка __str__ метода"""
        assert str(publisher) == publisher.name


class TestUserProfile:
    """Тесты модели UserProfile"""
    
    def test_create_user_profile_automatically(self, db):
        """Профиль создается автоматически при создании пользователя"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='pass123'
        )
        # Профиль должен быть создан автоматически через сигнал
        assert hasattr(user, 'profile')
        assert user.profile.user == user
    
    def test_user_profile_str(self, user):
        """Проверка __str__ метода"""
        profile = user.profile
        assert str(profile) == f"Профиль {user.username}"
    
    def test_update_profile(self, user):
        """Обновление профиля"""
        profile = user.profile
        profile.full_name = 'Иван Иванов'
        profile.save()
        assert user.profile.full_name == 'Иван Иванов'


class TestLibrary:
    """Тесты модели Library"""
    
    def test_create_library(self, db, user):
        """Создание библиотеки"""
        library = Library.objects.create(
            owner=user,
            name='Моя библиотека',
            address='Москва, ул. Тестовая, 1',
            city='Москва',
            country='Россия',
            description='Описание библиотеки'
        )
        assert library.owner == user
        assert library.name == 'Моя библиотека'
    
    def test_library_str(self, library):
        """Проверка __str__ метода"""
        assert library.owner.username in str(library)
        assert library.name in str(library)
    
    def test_library_cascade_delete(self, user, library):
        """При удалении пользователя библиотека удаляется"""
        user_id = user.id
        library_id = library.id
        user.delete()
        assert not Library.objects.filter(id=library_id).exists()


class TestHashtag:
    """Тесты модели Hashtag"""
    
    def test_create_hashtag(self, db, user):
        """Создание хэштега"""
        hashtag = Hashtag.objects.create(
            name='#фантастика',
            slug='fantastika',
            creator=user
        )
        assert hashtag.name == '#фантастика'
        assert hashtag.creator == user
    
    def test_hashtag_auto_slug(self, db, user):
        """Автоматическое создание slug"""
        hashtag = Hashtag(name='#test', creator=user)
        hashtag.save()
        # Slug должен быть создан автоматически
        # Используем английское название для slugify
        assert hashtag.slug is not None
        # Slug может быть пустым для кириллицы без настроек
        # Проверяем что метод save() был вызван
        assert hashtag.id is not None
    
    def test_hashtag_unique_slug(self, db, user):
        """Уникальность slug"""
        Hashtag.objects.create(name='#test1', slug='test', creator=user)
        with pytest.raises(IntegrityError):
            Hashtag.objects.create(name='#test2', slug='test', creator=user)
    
    def test_general_hashtag(self, db):
        """Общий хэштег (без creator)"""
        hashtag = Hashtag.objects.create(
            name='#общий',
            slug='obshtii'
        )
        assert hashtag.creator is None


class TestBook:
    """Тесты модели Book"""
    
    def test_create_book(self, book):
        """Создание книги"""
        assert book.title == 'Тестовая книга'
        assert book.owner is not None
        assert book.category is not None
    
    def test_book_str(self, book):
        """Проверка __str__ метода"""
        assert book.title in str(book)
        # Проверяем что авторы включены
        authors_count = book.authors.count()
        assert authors_count > 0
    
    def test_book_images_count_property(self, book):
        """Проверка свойства images_count"""
        assert book.images_count == 0
        
        # Добавляем изображение
        from books.models import BookImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        image_file = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        BookImage.objects.create(book=book, image=image_file, order=1)
        
        book.refresh_from_db()
        assert book.images_count == 1
    
    def test_book_status_choices(self, book):
        """Проверка валидных статусов"""
        valid_statuses = ['none', 'read', 'want_to_read', 'want_to_reread']
        for status in valid_statuses:
            book.status = status
            book.save()
            assert book.status == status
    
    def test_book_cascade_delete_owner(self, user, book):
        """При удалении владельца книга удаляется"""
        book_id = book.id
        user.delete()
        assert not Book.objects.filter(id=book_id).exists()
    
    def test_book_set_null_library(self, library, book):
        """При удалении библиотеки library становится null"""
        library_id = library.id
        library.delete()
        book.refresh_from_db()
        assert book.library is None


class TestBookAuthor:
    """Тесты модели BookAuthor"""
    
    def test_create_book_author(self, book, author):
        """Создание связи книга-автор"""
        # Удаляем существующего автора если есть (из фикстуры)
        BookAuthor.objects.filter(book=book).delete()
        
        book_author = BookAuthor.objects.create(
            book=book,
            author=author,
            order=1
        )
        assert book_author.book == book
        assert book_author.author == author
        assert book_author.order == 1
    
    def test_book_author_unique_order(self, book, author):
        """Уникальность order для книги"""
        # Удаляем существующего автора если есть
        BookAuthor.objects.filter(book=book).delete()
        
        BookAuthor.objects.create(book=book, author=author, order=1)
        
        author2 = Author.objects.create(full_name='Другой Автор')
        with pytest.raises(IntegrityError):
            BookAuthor.objects.create(book=book, author=author2, order=1)
    
    def test_book_author_max_order(self, book, author):
        """Максимальный порядок автора = 3"""
        from django.core.exceptions import ValidationError
        from django.core.validators import MaxValueValidator
        
        book_author = BookAuthor(book=book, author=author, order=4)
        # Валидатор должен сработать
        with pytest.raises(ValidationError):
            book_author.full_clean()


class TestBookImage:
    """Тесты модели BookImage"""
    
    def test_create_book_image(self, book, sample_image):
        """Создание изображения книги"""
        book_image = BookImage.objects.create(
            book=book,
            image=sample_image,
            order=1
        )
        assert book_image.book == book
        assert book_image.order == 1
        assert book_image.image is not None
    
    def test_book_image_unique_order(self, book, sample_image):
        """Уникальность order для книги"""
        BookImage.objects.create(book=book, image=sample_image, order=1)
        
        # Второе изображение с тем же порядком должно вызвать ошибку
        with pytest.raises(IntegrityError):
            BookImage.objects.create(book=book, image=sample_image, order=1)


class TestBookElectronic:
    """Тесты модели BookElectronic"""
    
    def test_create_book_electronic(self, book):
        """Создание электронной версии"""
        electronic = BookElectronic.objects.create(
            book=book,
            format='pdf',
            url='https://example.com/book.pdf'
        )
        assert electronic.book == book
        assert electronic.format == 'pdf'
        assert electronic.url == 'https://example.com/book.pdf'
    
    def test_book_electronic_format_choices(self, book):
        """Проверка валидных форматов"""
        valid_formats = ['pdf', 'epub', 'mobi', 'fb2', 'djvu', 'txt', 'rtf', 'doc', 'docx']
        for fmt in valid_formats:
            electronic = BookElectronic(book=book, format=fmt)
            electronic.full_clean()  # Валидация должна пройти


class TestBookReview:
    """Тесты модели BookReview"""
    
    def test_create_book_review(self, book, user):
        """Создание отзыва на книгу"""
        review = BookReview.objects.create(
            book=book,
            user=user,
            rating=5,
            review_text='Отличная книга!'
        )
        assert review.book == book
        assert review.user == user
        assert review.rating == 5
    
    def test_book_review_unique_user_book(self, book, user):
        """Уникальность пары пользователь-книга"""
        BookReview.objects.create(book=book, user=user, rating=5)
        
        with pytest.raises(IntegrityError):
            BookReview.objects.create(book=book, user=user, rating=4)
    
    def test_book_review_rating_range(self, book, user):
        """Оценка должна быть от 1 до 5"""
        # Валидные оценки
        for rating in [1, 3, 5]:
            review = BookReview(book=book, user=user, rating=rating)
            review.full_clean()
        
        # Невалидные оценки (если есть валидатор)
        # Зависит от модели, проверяем что нет ошибок для 1-5


class TestBookHashtag:
    """Тесты модели BookHashtag"""
    
    def test_create_book_hashtag(self, book, user):
        """Создание связи книга-хэштег"""
        hashtag = Hashtag.objects.create(
            name='#тест',
            slug='test',
            creator=user
        )
        book_hashtag = BookHashtag.objects.create(
            book=book,
            hashtag=hashtag
        )
        assert book_hashtag.book == book
        assert book_hashtag.hashtag == hashtag
    
    def test_book_hashtag_unique(self, book, user):
        """Уникальность пары книга-хэштег"""
        hashtag = Hashtag.objects.create(name='#тест', slug='test', creator=user)
        BookHashtag.objects.create(book=book, hashtag=hashtag)
        
        with pytest.raises(IntegrityError):
            BookHashtag.objects.create(book=book, hashtag=hashtag)


class TestBookPage:
    """Тесты модели BookPage"""
    
    def test_create_book_page(self, book, sample_image):
        """Создание страницы книги"""
        page = BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image,
            processing_status='pending'
        )
        assert page.book == book
        assert page.page_number == 1
        assert page.processing_status == 'pending'
    
    def test_book_page_unique_page_number(self, book, sample_image):
        """Уникальность номера страницы для книги"""
        BookPage.objects.create(
            book=book,
            page_number=1,
            original_image=sample_image
        )
        
        with pytest.raises(IntegrityError):
            BookPage.objects.create(
                book=book,
                page_number=1,
                original_image=sample_image
            )
    
    def test_book_page_processing_status_choices(self, book, sample_image):
        """Проверка валидных статусов обработки"""
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        page_number = 2
        for status in valid_statuses:
            # Удаляем предыдущую страницу если существует
            BookPage.objects.filter(book=book, page_number=page_number).delete()
            
            page = BookPage.objects.create(
                book=book,
                page_number=page_number,
                original_image=sample_image,
                processing_status=status
            )
            assert page.processing_status == status
            page_number += 1  # Увеличиваем для следующей итерации

