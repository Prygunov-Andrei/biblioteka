"""
Сериализаторы для книг
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Book, BookPage, Author, Publisher, Language, BookImage, BookElectronic, BookAuthor,
    UserProfile, Library, Hashtag, BookHashtag, BookReview, BookReadingDate
)
from .constants import MAX_HASHTAGS_PER_BOOK, MAX_AUTHORS_PER_BOOK
from .services.hashtag_service import HashtagService
from .services.book_service import BookService

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя (краткий)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя"""
    user = UserSerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()
    libraries_count = serializers.SerializerMethodField()
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'photo', 'photo_url',
            'description', 'libraries_count', 'books_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user']
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None
    
    def get_libraries_count(self, obj):
        # Используем prefetch_related если доступен, иначе count()
        if hasattr(obj.user, '_prefetched_objects_cache') and 'libraries' in obj.user._prefetched_objects_cache:
            return len(obj.user.libraries.all())
        return obj.user.libraries.count()
    
    def get_books_count(self, obj):
        # Используем prefetch_related если доступен, иначе count()
        if hasattr(obj.user, '_prefetched_objects_cache') and 'owned_books' in obj.user._prefetched_objects_cache:
            return len(obj.user.owned_books.all())
        return obj.user.owned_books.count()


class LibrarySerializer(serializers.ModelSerializer):
    """Сериализатор библиотеки"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Library
        fields = [
            'id', 'owner', 'owner_username', 'name', 'address',
            'city', 'country', 'description', 'books_count',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'owner': {'required': False}  # Устанавливается через perform_create
        }
    
    def get_books_count(self, obj):
        # Используем аннотацию если есть, иначе count()
        return getattr(obj, 'books_count_annotated', obj.books.count())


class HashtagSerializer(serializers.ModelSerializer):
    """Сериализатор хэштега"""
    creator_username = serializers.SerializerMethodField()
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'slug', 'creator', 'creator_username', 'books_count', 'created_at']
    
    def get_creator_username(self, obj):
        # Используем prefetch_related creator если доступен
        if obj.creator:
            return obj.creator.username
        return None
    
    def get_books_count(self, obj):
        # Используем аннотацию если есть, иначе возвращаем 0 (не вызываем count() чтобы избежать N+1)
        return getattr(obj, 'books_count_annotated', 0)


class BookReviewSerializer(serializers.ModelSerializer):
    """Сериализатор отзыва на книгу"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = BookReview
        fields = [
            'id', 'book', 'book_title', 'user', 'user_username',
            'rating', 'review_text', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории"""
    books_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    is_parent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'code', 'name', 'slug', 'icon', 'order', 
            'books_count', 'parent_category', 'subcategories', 'is_parent'
        ]
    
    def get_books_count(self, obj):
        """Подсчитывает книги включая подкатегории"""
        # Используем аннотации если доступны
        books_count = getattr(obj, 'books_count_annotated', 0)
        subcategories_count = getattr(obj, 'subcategories_books_count_annotated', 0)
        
        if books_count > 0 or subcategories_count > 0:
            return books_count + subcategories_count
        
        # Fallback: если аннотации нет, используем старый метод (но это медленнее)
        count = obj.books.count()
        if hasattr(obj, '_prefetched_objects_cache') and 'subcategories' in obj._prefetched_objects_cache:
            for subcategory in obj.subcategories.all():
                count += subcategory.books.count()
        else:
            # Если нет prefetch, делаем один запрос для всех подкатегорий
            from django.db.models import Count
            subcategories_count = obj.subcategories.aggregate(
                total=Count('books')
            )['total'] or 0
            count += subcategories_count
        return count
    
    def get_subcategories(self, obj):
        """Возвращает подкатегории"""
        subcategories = obj.subcategories.all().order_by('name')  # Сортировка по алфавиту
        return CategorySerializer(subcategories, many=True).data


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Сериализатор для дерева категорий (только родительские с подкатегориями)"""
    subcategories = serializers.SerializerMethodField()
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'code', 'name', 'slug', 'icon', 'order', 'subcategories', 'books_count']
    
    def get_subcategories(self, obj):
        """Возвращает подкатегории"""
        from django.db.models import Count, Q
        from books.models import Book
        
        library_ids = self.context.get('library_ids', [])
        subcategories = obj.subcategories.all().order_by('name')  # Сортировка по алфавиту
        
        # Если указаны библиотеки, фильтруем книги для подсчета
        if library_ids:
            subcategories = subcategories.annotate(
                books_count=Count(
                    'books',
                    filter=Q(books__library_id__in=library_ids),
                    distinct=True
                )
            )
        
        # Используем простой сериализатор для подкатегорий (без вложенности)
        # Фильтруем подкатегории с нулевым количеством книг
        result = []
        for sub in subcategories:
            books_count = getattr(sub, 'books_count', 0)
            # Показываем только подкатегории с книгами
            if books_count > 0:
                result.append({
                    'id': sub.id,
                    'code': sub.code,
                    'name': sub.name,
                    'slug': sub.slug,
                    'icon': sub.icon,
                    'order': sub.order,
                    'books_count': books_count
                })
        return result
    
    def get_books_count(self, obj):
        """Подсчитывает книги включая подкатегории"""
        library_ids = self.context.get('library_ids', [])
        
        # Используем аннотации если доступны
        books_count = getattr(obj, 'books_count_annotated', 0)
        subcategories_count = getattr(obj, 'subcategories_books_count_annotated', 0)
        
        if books_count > 0 or subcategories_count > 0:
            return books_count + subcategories_count
        
        # Fallback: если аннотации нет и библиотеки не указаны, возвращаем 0
        if not library_ids:
            return 0
        
        # Если библиотеки указаны, но аннотации нет - делаем запрос
        from django.db.models import Count, Q
        count = obj.books.filter(library_id__in=library_ids).count()
        subcategories_count = obj.subcategories.aggregate(
            total=Count('books', filter=Q(books__library_id__in=library_ids))
        )['total'] or 0
        return count + subcategories_count


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор автора"""
    
    class Meta:
        model = Author
        fields = ['id', 'full_name', 'birth_year', 'death_year', 'biography', 'notes']


class PublisherSerializer(serializers.ModelSerializer):
    """Сериализатор издательства"""
    
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'city', 'website', 'description']


class LanguageSerializer(serializers.ModelSerializer):
    """Сериализатор языка"""
    
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']


class BookReadingDateSerializer(serializers.ModelSerializer):
    """Сериализатор даты прочтения книги"""
    
    class Meta:
        model = BookReadingDate
        fields = ['id', 'book', 'date', 'notes', 'created_at', 'updated_at']


class BookImageSerializer(serializers.ModelSerializer):
    """Сериализатор изображения книги"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BookImage
        fields = ['id', 'book', 'image_url', 'order', 'created_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class BookElectronicSerializer(serializers.ModelSerializer):
    """Сериализатор электронной версии"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BookElectronic
        fields = ['id', 'format', 'url', 'file_url', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class BookPageSerializer(serializers.ModelSerializer):
    """Сериализатор страницы книги"""
    original_url = serializers.SerializerMethodField()
    processed_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BookPage
        fields = [
            'id', 'book', 'page_number', 'original_url', 'processed_url',
            'processing_status', 'width', 'height', 'created_at'
        ]
    
    def get_original_url(self, obj):
        if obj.original_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.original_image.url) if request else obj.original_image.url
        return None
    
    def get_processed_url(self, obj):
        if obj.processed_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.processed_image.url) if request else obj.processed_image.url
        return None


class BookListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор книги для списка (минимум данных для быстрой загрузки)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    library_name = serializers.CharField(source='library.name', read_only=True, allow_null=True)
    language_name = serializers.CharField(source='language.name', read_only=True, allow_null=True)
    
    # Упрощенные сериализаторы для авторов и хэштегов
    authors = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()
    
    images_count = serializers.IntegerField(read_only=True, source='images_count_annotated')
    first_page_url = serializers.SerializerMethodField()
    reviews_count = serializers.IntegerField(read_only=True, source='reviews_count_annotated')
    electronic_versions_count = serializers.IntegerField(read_only=True, source='electronic_versions_count_annotated')
    average_rating = serializers.SerializerMethodField()
    
    def get_average_rating(self, obj):
        """Возвращает средний рейтинг книги"""
        return obj.average_rating
    
    def get_authors(self, obj):
        # Возвращаем только имена авторов для списка
        return [{'id': a.id, 'full_name': a.full_name} for a in obj.authors.all()[:3]]
    
    def get_hashtags(self, obj):
        # Возвращаем только имена хэштегов для списка
        return [{'id': h.id, 'name': h.name, 'slug': h.slug} for h in obj.hashtags.all()]
    
    def get_first_page_url(self, obj):
        """Возвращает URL обложки книги (cover_page) для отображения в списке"""
        try:
            # Сначала проверяем, есть ли назначенная обложка
            cover_page = obj.cover_page
            if not cover_page:
                # Если обложка не назначена, используем первую страницу
                if hasattr(obj, 'all_pages') and obj.all_pages:
                    cover_page = obj.all_pages[0] if obj.all_pages else None
                else:
                    # Иначе делаем запрос - используем order_by для получения первой страницы
                    cover_page = obj.pages_set.order_by('page_number').first()
            
            if cover_page:
                request = self.context.get('request')
                # Приоритет: processed_image, затем original_image
                if cover_page.processed_image:
                    url = cover_page.processed_image.url
                    return request.build_absolute_uri(url) if request else url
                elif cover_page.original_image:
                    url = cover_page.original_image.url
                    return request.build_absolute_uri(url) if request else url
        except Exception as e:
            # Логируем ошибку для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f'Ошибка получения обложки для книги {obj.id}: {e}')
        return None
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'category', 'category_name', 'category_code', 'category_icon',
            'owner', 'owner_username', 'library', 'library_name', 'status',
            'authors', 'hashtags', 'publication_place', 'publisher', 'publisher_name',
            'year', 'year_approx', 'pages_info', 'circulation',
            'language', 'language_name',
            'binding_type', 'format',
            'price_rub', 'condition',
            'seller_code', 'isbn',
            'images_count', 'first_page_url', 'reviews_count', 'electronic_versions_count',
            'average_rating',
            'created_at', 'updated_at'
        ]
        # Убраны поля: description, binding_details, condition_details для уменьшения размера


class BookSerializer(serializers.ModelSerializer):
    """Сериализатор книги для списка"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    library_name = serializers.CharField(source='library.name', read_only=True, allow_null=True)
    language_name = serializers.CharField(source='language.name', read_only=True, allow_null=True)
    authors = AuthorSerializer(many=True, read_only=True)
    hashtags = HashtagSerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(read_only=True, source='images_count_annotated')
    images = serializers.SerializerMethodField()
    first_page_url = serializers.SerializerMethodField()
    reviews_count = serializers.IntegerField(read_only=True, source='reviews_count_annotated')
    electronic_versions_count = serializers.IntegerField(read_only=True, source='electronic_versions_count_annotated')
    
    def get_images(self, obj):
        # Для оптимизации скорости загрузки списка НЕ загружаем изображения
        # Они могут быть загружены отдельно по требованию через detail endpoint
        # Это значительно ускоряет загрузку списка книг
        return []
    
    def get_first_page_url(self, obj):
        """Возвращает URL обложки книги (cover_page) для отображения в списке"""
        try:
            # Сначала проверяем, есть ли назначенная обложка
            cover_page = obj.cover_page
            if not cover_page:
                # Если обложка не назначена, используем первую страницу
                if hasattr(obj, 'all_pages') and obj.all_pages:
                    cover_page = obj.all_pages[0] if obj.all_pages else None
                else:
                    # Иначе делаем запрос - используем order_by для получения первой страницы
                    cover_page = obj.pages_set.order_by('page_number').first()
            
            if cover_page:
                request = self.context.get('request')
                # Приоритет: processed_image, затем original_image
                if cover_page.processed_image:
                    url = cover_page.processed_image.url
                    return request.build_absolute_uri(url) if request else url
                elif cover_page.original_image:
                    url = cover_page.original_image.url
                    return request.build_absolute_uri(url) if request else url
        except Exception as e:
            # Логируем ошибку для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f'Ошибка получения обложки для книги {obj.id}: {e}')
        return None
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'category', 'category_name', 'category_code', 'category_icon',
            'owner', 'owner_username', 'library', 'library_name', 'status',
            'authors', 'hashtags', 'publication_place', 'publisher', 'publisher_name',
            'year', 'year_approx', 'pages_info', 'circulation',
            'language', 'language_name',
            'binding_type', 'binding_details', 'format',
            'price_rub', 'description', 'condition', 'condition_details',
            'seller_code', 'isbn',
            'images_count', 'images', 'first_page_url', 'reviews_count', 'electronic_versions_count',
            'created_at', 'updated_at'
        ]


class BookDetailSerializer(BookSerializer):
    """Детальный сериализатор книги"""
    electronic_versions = BookElectronicSerializer(many=True, read_only=True, source='electronic_versions.all')
    pages = serializers.SerializerMethodField()
    reviews = BookReviewSerializer(many=True, read_only=True)
    reading_dates = BookReadingDateSerializer(many=True, read_only=True, source='reading_dates.all')
    average_rating = serializers.SerializerMethodField()
    
    def get_average_rating(self, obj):
        """Возвращает средний рейтинг книги"""
        return obj.average_rating
    
    def get_pages(self, obj):
        """Получаем страницы, отсортированные по номеру страницы"""
        # Используем prefetch_related кэш, если он есть, иначе делаем запрос
        if hasattr(obj, '_prefetched_objects_cache') and 'pages_set' in obj._prefetched_objects_cache:
            pages = list(obj._prefetched_objects_cache['pages_set'])
            pages.sort(key=lambda x: x.page_number)
        else:
            pages = list(obj.pages_set.all().order_by('page_number'))
        
        return BookPageSerializer(pages, many=True, context=self.context).data
    
    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['electronic_versions', 'pages', 'reviews', 'reading_dates', 'average_rating']


class BookCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания книги"""
    author_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='Список ID авторов (до 3-х)'
    )
    hashtag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text='Список названий хэштегов (до 20)'
    )
    language_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text='Название языка (например, "Русский"). Если язык не найден, будет создан новый.'
    )
    normalized_image_urls = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text='Список путей к нормализованным изображениям из временной директории (например, ["/media/temp/normalized/normalized_uuid1.jpg", ...])'
    )
    
    class Meta:
        model = Book
        fields = [
            'category', 'title', 'subtitle',
            'library', 'status',
            'publication_place', 'publisher',
            'year', 'year_approx', 'pages_info', 'circulation',
            'language', 'language_name',
            'binding_type', 'binding_details', 'format',
            'price_rub', 'description',
            'condition', 'condition_details',
            'seller_code', 'isbn',
            'author_ids', 'hashtag_names', 'normalized_image_urls'
        ]
    
    def validate_author_ids(self, value):
        if len(value) > MAX_AUTHORS_PER_BOOK:
            raise serializers.ValidationError(f"Не более {MAX_AUTHORS_PER_BOOK} авторов")
        return value
    
    def validate_hashtag_names(self, value):
        if len(value) > MAX_HASHTAGS_PER_BOOK:
            raise serializers.ValidationError(f"Не более {MAX_HASHTAGS_PER_BOOK} хэштегов")
        return value
    
    def create(self, validated_data):
        author_ids = validated_data.pop('author_ids', [])
        hashtag_names = validated_data.pop('hashtag_names', [])
        language_name = validated_data.pop('language_name', None)
        normalized_image_urls = validated_data.pop('normalized_image_urls', [])
        current_user = self.context['request'].user
        
        # Обрабатываем language_name: ищем язык по имени или создаем новый
        if language_name and not validated_data.get('language'):
            language_name_clean = language_name.strip()
            if language_name_clean:
                language, created = Language.objects.get_or_create(
                    name=language_name_clean,
                    defaults={'code': language_name_clean.lower()[:10]}  # Используем первые 10 символов как код
                )
                validated_data['language'] = language
        
        # Используем сервис для создания книги со всеми связями
        book = BookService.create_book_with_relations(
            validated_data=validated_data,
            author_ids=author_ids,
            hashtag_names=hashtag_names if hashtag_names else None,
            creator=current_user
        )
        
        # Обрабатываем нормализованные страницы: перемещаем из temp в постоянное хранилище и создаем BookPage записи
        if normalized_image_urls:
            BookService.process_normalized_pages(book, normalized_image_urls)
        
        return book


class BookUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления книги"""
    author_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='Список ID авторов (до 3-х)'
    )
    
    class Meta:
        model = Book
        fields = [
            'category', 'title', 'subtitle',
            'library', 'status',
            'publication_place', 'publisher',
            'year', 'year_approx', 'pages_info', 'circulation',
            'language',
            'binding_type', 'binding_details', 'format',
            'price_rub', 'description',
            'condition', 'condition_details',
            'seller_code', 'isbn',
            'author_ids'
        ]
        extra_kwargs = {
            'title': {'required': False},
        }
    
    def validate_author_ids(self, value):
        if len(value) > MAX_AUTHORS_PER_BOOK:
            raise serializers.ValidationError(f"Не более {MAX_AUTHORS_PER_BOOK} авторов")
        return value
    
    def update(self, instance, validated_data):
        author_ids = validated_data.pop('author_ids', None)
        
        # Обновляем поля книги
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем авторов если указаны
        BookService.update_book_authors(instance, author_ids)
        
        return instance
