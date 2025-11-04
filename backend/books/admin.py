from django.contrib import admin
from .models import (
    UserProfile,
    Library,
    Hashtag,
    BookHashtag,
    BookReview,
    Category,
    Author,
    Publisher,
    Language,
    Book,
    BookAuthor,
    BookImage,
    BookElectronic,
    BookPage,
    BookReadingDate,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'created_at']
    search_fields = ['user__username', 'full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'country', 'created_at']
    list_filter = ['city', 'country', 'created_at']
    search_fields = ['name', 'address', 'city', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'creator', 'created_at']
    list_filter = ['creator', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BookHashtag)
class BookHashtagAdmin(admin.ModelAdmin):
    list_display = ['book', 'hashtag', 'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title', 'hashtag__name']
    readonly_fields = ['created_at']


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__title', 'user__username', 'review_text']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'slug', 'parent_category', 'order', 'created_at']
    list_filter = ['parent_category', 'created_at']
    search_fields = ['name', 'code', 'slug']
    readonly_fields = ['created_at']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_year', 'death_year', 'created_at']
    list_filter = ['birth_year', 'death_year', 'created_at']
    search_fields = ['full_name', 'biography']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['name', 'city', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'status', 'year', 'language', 'cover_page', 'created_at']
    list_filter = ['status', 'category', 'binding_type', 'format', 'condition', 'year', 'language', 'created_at']
    search_fields = ['title', 'subtitle', 'isbn', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['cover_page']
    filter_horizontal = ['authors', 'hashtags']
    # ManyToMany поля с through моделями нельзя включать в fieldsets
    # Они будут автоматически добавлены Django admin через filter_horizontal
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'subtitle', 'category', 'status', 'cover_page')
        }),
        ('Владелец и библиотека', {
            'fields': ('owner', 'library')
        }),
        ('Издательская информация', {
            'fields': ('publication_place', 'publisher', 'year', 'year_approx', 'pages_info', 'circulation', 'language')
        }),
        ('Физические характеристики', {
            'fields': ('binding_type', 'binding_details', 'format')
        }),
        ('Описание и состояние', {
            'fields': ('description', 'condition', 'condition_details')
        }),
        ('Цена и коды', {
            'fields': ('price_rub', 'seller_code', 'isbn')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ['book', 'author', 'order']
    list_filter = ['order']
    search_fields = ['book__title', 'author__full_name']
    ordering = ['book', 'order']


@admin.register(BookImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ['book', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title']
    readonly_fields = ['created_at']
    ordering = ['book', 'order']


@admin.register(BookElectronic)
class BookElectronicAdmin(admin.ModelAdmin):
    list_display = ['book', 'format', 'created_at']
    list_filter = ['format', 'created_at']
    search_fields = ['book__title']
    readonly_fields = ['created_at']


@admin.register(BookPage)
class BookPageAdmin(admin.ModelAdmin):
    list_display = ['book', 'page_number', 'processing_status', 'processed_at']
    list_filter = ['processing_status', 'processed_at', 'created_at']
    search_fields = ['book__title']
    readonly_fields = ['created_at', 'processed_at']
    ordering = ['book', 'page_number']


@admin.register(BookReadingDate)
class BookReadingDateAdmin(admin.ModelAdmin):
    list_display = ['book', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['book__title', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['book', '-date']
