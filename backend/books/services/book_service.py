"""
Сервис для работы с книгами
"""
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from ..models import Book, BookAuthor, Author, BookPage
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
    
    @staticmethod
    def process_normalized_pages(book: Book, normalized_image_urls: List[str]) -> None:
        """
        Обрабатывает нормализованные страницы: перемещает из временной директории в постоянное хранилище
        и создает BookPage записи.
        
        Args:
            book: Созданная книга
            normalized_image_urls: Список путей к нормализованным изображениям (например, ["/media/temp/normalized/normalized_uuid1.jpg", ...])
        """
        if not normalized_image_urls:
            return
        
        # Директории
        media_root = Path(settings.MEDIA_ROOT)
        temp_dir = media_root / 'temp' / 'normalized'
        processed_dir = media_root / 'books' / 'pages' / 'processed'
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Обрабатываем каждое нормализованное изображение
        for page_number, image_url in enumerate(normalized_image_urls, start=1):
            try:
                # Извлекаем путь к файлу из URL
                # URL может быть:
                # - "http://localhost:8000/media/temp/normalized/normalized_uuid.jpg" (абсолютный)
                # - "/media/temp/normalized/normalized_uuid.jpg" (относительный с /media/)
                # - "temp/normalized/normalized_uuid.jpg" (относительный без /media/)
                
                relative_path = None
                
                # Если это абсолютный URL (http:// или https://)
                if image_url.startswith('http://') or image_url.startswith('https://'):
                    # Извлекаем путь после /media/
                    media_index = image_url.find('/media/')
                    if media_index != -1:
                        relative_path = image_url[media_index + 7:]  # Убираем "/media/"
                # Если начинается с /media/
                elif image_url.startswith('/media/'):
                    relative_path = image_url[7:]  # Убираем "/media/"
                # Если начинается с /temp/
                elif image_url.startswith('/temp/'):
                    relative_path = image_url[1:]  # Убираем начальный /
                # Если начинается с temp/
                elif image_url.startswith('temp/'):
                    relative_path = image_url
                else:
                    # Пробуем как есть
                    relative_path = image_url
                
                # Полный путь к временному файлу
                temp_file_path = media_root / relative_path
                
                print(f"🔵 Обрабатываем страницу {page_number}: {image_url} -> {temp_file_path}", file=sys.stderr)
                
                # Проверяем, что файл существует
                if not temp_file_path.exists():
                    print(f"⚠️ Файл не найден: {temp_file_path}", file=sys.stderr)
                    continue
                
                # Генерируем имя для постоянного файла
                file_extension = temp_file_path.suffix
                new_filename = f"book_{book.id}_page_{page_number}{file_extension}"
                permanent_file_path = processed_dir / new_filename
                
                # Перемещаем файл из временной директории в постоянную
                shutil.move(str(temp_file_path), str(permanent_file_path))
                
                # Относительный путь для сохранения в модели (относительно MEDIA_ROOT)
                relative_processed_path = f"books/pages/processed/{new_filename}"
                
                # Получаем размеры изображения (опционально, можно использовать PIL или OpenCV)
                width = None
                height = None
                try:
                    from PIL import Image
                    with Image.open(permanent_file_path) as img:
                        width, height = img.size
                except Exception:
                    # Если не удалось получить размеры, оставляем None
                    pass
                
                # Создаем BookPage запись
                # Для original_image используем то же изображение (так как оно уже нормализовано)
                BookPage.objects.create(
                    book=book,
                    page_number=page_number,
                    original_image=relative_processed_path,  # Используем нормализованное изображение как оригинал
                    processed_image=relative_processed_path,  # И как обработанное
                    processing_status='completed',
                    processed_at=timezone.now(),
                    width=width,
                    height=height
                )
                
                print(f"✅ Страница {page_number} обработана: {new_filename}", file=sys.stderr)
                
            except Exception as e:
                import traceback
                print(f"❌ Ошибка обработки страницы {page_number}: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                # Продолжаем обработку остальных страниц
                continue

