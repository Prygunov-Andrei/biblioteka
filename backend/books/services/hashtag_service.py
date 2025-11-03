"""
Сервис для работы с хэштегами
"""
from typing import List
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from ..models import Hashtag, BookHashtag, Book
from ..exceptions import HashtagLimitExceeded
from ..constants import MAX_HASHTAGS_PER_BOOK

User = get_user_model()


class HashtagService:
    """Сервис для работы с хэштегами"""
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Нормализует название хэштега.
        Убирает пробелы, # в начале, приводит к нижнему регистру.
        """
        if not name:
            return ""
        name = name.strip()
        if name.startswith('#'):
            name = name[1:]
        return name.strip()
    
    @staticmethod
    def create_slug(name: str) -> str:
        """Создает slug из названия хэштега"""
        normalized = HashtagService.normalize_name(name)
        return slugify(normalized) or normalized.lower().replace(' ', '-')
    
    @staticmethod
    def get_or_create_hashtag(name: str, creator: User) -> tuple[Hashtag, bool]:
        """
        Создает или получает хэштег.
        Returns: (hashtag, created)
        """
        normalized = HashtagService.normalize_name(name)
        if not normalized:
            raise ValueError("Название хэштега не может быть пустым")
        
        hashtag_name = f"#{normalized}"
        slug = HashtagService.create_slug(normalized)
        
        hashtag, created = Hashtag.objects.get_or_create(
            name=hashtag_name,
            creator=creator,
            defaults={'slug': slug}
        )
        
        return hashtag, created
    
    @staticmethod
    def add_hashtags_to_book(
        book: Book,
        hashtag_names: List[str],
        creator: User
    ) -> List[Hashtag]:
        """
        Добавляет хэштеги к книге с валидацией лимита.
        Returns: список добавленных хэштегов
        """
        if not hashtag_names:
            return []
        
        # Убеждаемся что hashtag_names - это список
        if not isinstance(hashtag_names, list):
            # Если это строка, преобразуем в список с одним элементом
            hashtag_names = [hashtag_names] if hashtag_names else []
        
        # Проверка лимита - используем прямую проверку через BookHashtag для актуальности
        # Важно: получаем свежий объект книги из БД, чтобы избежать проблем с кэшированием
        from ..models import BookHashtag, Book
        # Получаем ID книги - используем int() для явного преобразования
        book_id = int(book.pk)
        # Используем прямой запрос к БД для получения актуального количества
        # Важно: используем book_id, а не объект book, чтобы избежать проблем с кэшированием
        current_count = BookHashtag.objects.filter(book_id=book_id).count()
        
        if current_count + len(hashtag_names) > MAX_HASHTAGS_PER_BOOK:
            raise HashtagLimitExceeded(
                f"Нельзя добавить более "
                f"{MAX_HASHTAGS_PER_BOOK - current_count} хэштегов"
            )
        
        added_hashtags = []
        
        for hashtag_name in hashtag_names[:MAX_HASHTAGS_PER_BOOK]:
            try:
                hashtag, created = HashtagService.get_or_create_hashtag(
                    hashtag_name,
                    creator
                )
                
                # Создаем связь (если еще не существует)
                # Используем book_id напрямую для избежания проблем с кэшированием
                book_hashtag, link_created = BookHashtag.objects.get_or_create(
                    book_id=book_id,
                    hashtag=hashtag
                )
                
                if link_created:
                    added_hashtags.append(hashtag)
                    
            except ValueError:
                # Пропускаем невалидные хэштеги
                continue
        
        return added_hashtags

