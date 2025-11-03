"""
Сериализаторы для книг
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Book, BookPage, Author, Publisher, BookImage, BookElectronic, BookAuthor,
    UserProfile, Library, Hashtag, BookHashtag, BookReview
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
        return obj.user.libraries.count()
    
    def get_books_count(self, obj):
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
        return obj.books.count()


class HashtagSerializer(serializers.ModelSerializer):
    """Сериализатор хэштега"""
    creator_username = serializers.CharField(source='creator.username', read_only=True, allow_null=True)
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'slug', 'creator', 'creator_username', 'books_count', 'created_at']
    
    def get_books_count(self, obj):
        return obj.books.count()


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
        count = obj.books.count()
        # Добавляем книги из всех подкатегорий
        for subcategory in obj.subcategories.all():
            count += subcategory.books.count()
        return count
    
    def get_subcategories(self, obj):
        """Возвращает подкатегории"""
        subcategories = obj.subcategories.all().order_by('order', 'name')
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
        subcategories = obj.subcategories.all().order_by('order', 'name')
        # Используем простой сериализатор для подкатегорий (без вложенности)
        return [
            {
                'id': sub.id,
                'code': sub.code,
                'name': sub.name,
                'slug': sub.slug,
                'icon': sub.icon,
                'order': sub.order,
                'books_count': sub.books.count()
            }
            for sub in subcategories
        ]
    
    def get_books_count(self, obj):
        """Подсчитывает книги включая подкатегории"""
        count = obj.books.count()
        # Добавляем книги из всех подкатегорий
        for subcategory in obj.subcategories.all():
            count += subcategory.books.count()
        return count


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


class BookSerializer(serializers.ModelSerializer):
    """Сериализатор книги для списка"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    library_name = serializers.CharField(source='library.name', read_only=True, allow_null=True)
    authors = AuthorSerializer(many=True, read_only=True)
    hashtags = HashtagSerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(read_only=True)
    images = BookImageSerializer(many=True, read_only=True, source='images.all')
    reviews_count = serializers.IntegerField(source='reviews.count', read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'category', 'category_name', 'category_code', 'category_icon',
            'owner', 'owner_username', 'library', 'library_name', 'status',
            'authors', 'hashtags', 'publication_place', 'publisher', 'publisher_name',
            'year', 'year_approx', 'pages_info',
            'binding_type', 'binding_details', 'format',
            'price_rub', 'description', 'condition', 'condition_details',
            'seller_code', 'isbn',
            'images_count', 'images', 'reviews_count',
            'created_at', 'updated_at'
        ]


class BookDetailSerializer(BookSerializer):
    """Детальный сериализатор книги"""
    electronic_versions = BookElectronicSerializer(many=True, read_only=True, source='electronic_versions.all')
    pages = BookPageSerializer(source='pages_set', many=True, read_only=True)
    reviews = BookReviewSerializer(many=True, read_only=True)
    
    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['electronic_versions', 'pages', 'reviews']


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
    
    class Meta:
        model = Book
        fields = [
            'category', 'title', 'subtitle',
            'library', 'status',
            'publication_place', 'publisher',
            'year', 'year_approx', 'pages_info',
            'binding_type', 'binding_details', 'format',
            'price_rub', 'description',
            'condition', 'condition_details',
            'seller_code', 'isbn',
            'author_ids', 'hashtag_names'
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
        current_user = self.context['request'].user
        
        # Используем сервис для создания книги со всеми связями
        book = BookService.create_book_with_relations(
            validated_data=validated_data,
            author_ids=author_ids,
            hashtag_names=hashtag_names if hashtag_names else None,
            creator=current_user
        )
        
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
            'year', 'year_approx', 'pages_info',
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
