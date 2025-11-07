"""
ViewSet для книг (основной, самый сложный)
"""
import os
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from ..models import Book, BookPage, BookImage, BookElectronic, Category, Hashtag, BookReview
from ..serializers import (
    BookSerializer, BookListSerializer, BookDetailSerializer,
    BookCreateSerializer, BookUpdateSerializer,
    BookPageSerializer, BookImageSerializer,
    BookElectronicSerializer, HashtagSerializer, LibrarySerializer
)
from ..permissions import IsOwnerOrReadOnly
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..services.document_processor import process_document, normalize_pages_batch
from ..services.hashtag_service import HashtagService
from ..services.transfer_service import TransferService
from ..services.llm_service import auto_fill_book_data
from ..exceptions import HashtagLimitExceeded, TransferError
from ..constants import MIN_IMAGE_ORDER, MAX_IMAGE_ORDER
from ..pagination import ConditionalBookPagination


class BookViewSet(viewsets.ModelViewSet):
    """API для книг"""
    queryset = Book.objects.select_related(
        'category', 'publisher', 'owner', 'library', 'language'
    ).prefetch_related(
        'authors',
        Prefetch('hashtags', queryset=Hashtag.objects.select_related('creator'))
    ).annotate(
        reviews_count_annotated=Count('reviews', distinct=True),
        electronic_versions_count_annotated=Count('electronic_versions', distinct=True),
        images_count_annotated=Count('images', distinct=True)
    )
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    # Разрешаем чтение всем, редактирование только владельцам
    permission_classes = [IsOwnerOrReadOnly]
    # Используем условную пагинацию: если книг > 30, применяется пагинация
    pagination_class = ConditionalBookPagination
    
    def get_permissions(self):
        """
        Переопределяем права доступа для разных действий.
        Для list и retrieve - AllowAny (все могут просматривать)
        Для normalize_pages - IsAuthenticated (требуется авторизация, но не проверка владельца)
        Для остальных действий - IsOwnerOrReadOnly (только владелец может редактировать)
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'normalize_pages':
            return [IsAuthenticated()]
        return [IsOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        elif self.action == 'create':
            return BookCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookUpdateSerializer
        elif self.action == 'list':
            # Используем упрощенный сериализатор для списка для лучшей производительности
            from ..serializers import BookListSerializer
            return BookListSerializer
        return BookSerializer
    
    def list(self, request, *args, **kwargs):
        """
        Переопределяем метод list для явного использования пагинатора
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Пагинация применена
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Пагинация не применена (книг <= 30) - возвращаем все книги
        serializer = self.get_serializer(queryset, many=True)
        # Используем пагинатор для формирования ответа даже без пагинации
        paginator = self.pagination_class()
        paginator.count = queryset.count()
        return paginator.get_paginated_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Создание книги с авторами и хэштегами"""
        import sys
        import json
        
        # Логируем входящие данные для отладки
        print(f"🔵 BookViewSet.create вызван", file=sys.stderr)
        print(f"🔵 Данные запроса: {json.dumps(request.data, indent=2, default=str)}", file=sys.stderr)
        sys.stderr.flush()
        
        serializer = self.get_serializer(data=request.data)
        
        # Логируем ошибки валидации перед raise_exception
        if not serializer.is_valid():
            print(f"🔴 Ошибки валидации: {json.dumps(serializer.errors, indent=2, default=str)}", file=sys.stderr)
            sys.stderr.flush()
        
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        
        # Возвращаем с ID используя BookSerializer
        response_serializer = BookSerializer(book, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def get_queryset(self):
        """Оптимизированный queryset с аннотациями и фильтрацией"""
        queryset = super().get_queryset()
        
        # Для detail view загружаем все связи
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'images', 'electronic_versions', 'pages_set',
                Prefetch('reviews', queryset=BookReview.objects.select_related('user').order_by('-created_at')),
                'reading_dates'
            )
        # Для list загружаем обложку (cover_page) и первую страницу каждой книги для отображения в карточке
        elif self.action == 'list':
            queryset = queryset.select_related('cover_page').prefetch_related(
                Prefetch(
                    'pages_set', 
                    queryset=BookPage.objects.order_by('page_number'),
                    to_attr='all_pages'
                )
            )
        # Для list НЕ загружаем изображения через prefetch - это слишком медленно для большого количества книг
        # Изображения будут загружены лениво через сериализатор только для первой страницы
        # Для остальных страниц images будет пустым массивом (карточки будут без изображений)
        
        # Фильтрация по категории (slug или ID)
        category = self.request.query_params.get('category')
        if category:
            try:
                category_id = int(category)
                category_obj = Category.objects.prefetch_related('subcategories').get(id=category_id)
                # Если это родительская категория, включаем все её подкатегории
                if category_obj.subcategories.exists():
                    subcategory_ids = list(category_obj.subcategories.values_list('id', flat=True))
                    subcategory_ids.append(category_obj.id)  # Включаем и саму родительскую
                    queryset = queryset.filter(category_id__in=subcategory_ids)
                else:
                    queryset = queryset.filter(category_id=category_id)
            except (ValueError, Category.DoesNotExist):
                # Если не ID, пробуем slug
                queryset = queryset.filter(category__slug=category)
        
        # Фильтрация по владельцу
        owner = self.request.query_params.get('owner')
        if owner:
            try:
                owner_id = int(owner)
                queryset = queryset.filter(owner_id=owner_id)
            except ValueError:
                queryset = queryset.filter(owner__username__icontains=owner)
        
        # Фильтрация по библиотеке (поддержка множественного выбора)
        from ..utils import parse_library_ids
        library_ids = parse_library_ids(self.request)
        if library_ids:
            queryset = queryset.filter(library_id__in=library_ids)
        else:
            # Если не удалось распарсить как ID, пробуем фильтровать по имени
            libraries = self.request.query_params.getlist('libraries') or self.request.query_params.getlist('library')
            if libraries:
                queryset = queryset.filter(library__name__in=libraries)
        
        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтрация по хэштегу (ID или имя)
        hashtag = self.request.query_params.get('hashtag')
        if hashtag:
            try:
                hashtag_id = int(hashtag)
                queryset = queryset.filter(hashtags__id=hashtag_id)
            except ValueError:
                queryset = queryset.filter(hashtags__name__icontains=hashtag)
        
        # Фильтрация по наличию отзывов
        has_reviews = self.request.query_params.get('has_reviews')
        if has_reviews and has_reviews.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(reviews__isnull=False)
        
        # Фильтрация по наличию электронных версий
        has_electronic = self.request.query_params.get('has_electronic')
        if has_electronic and has_electronic.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(electronic_versions__isnull=False)
        
        # Фильтрация по недавно добавленным (за последние 7 дней)
        recently_added = self.request.query_params.get('recently_added')
        if recently_added and recently_added.lower() in ('true', '1', 'yes'):
            from datetime import timedelta
            seven_days_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=seven_days_ago)
        
        # Фильтрация по автору
        author = self.request.query_params.get('author')
        if author:
            try:
                author_id = int(author)
                queryset = queryset.filter(authors__id=author_id)
            except ValueError:
                queryset = queryset.filter(authors__full_name__icontains=author)
        
        # Фильтрация по издательству
        publisher = self.request.query_params.get('publisher')
        if publisher:
            try:
                publisher_id = int(publisher)
                queryset = queryset.filter(publisher_id=publisher_id)
            except ValueError:
                queryset = queryset.filter(publisher__name__icontains=publisher)
        
        # Фильтрация по году издания (диапазон)
        year_min = self.request.query_params.get('year_min')
        year_max = self.request.query_params.get('year_max')
        if year_min:
            try:
                queryset = queryset.filter(year__gte=int(year_min))
            except ValueError:
                pass
        if year_max:
            try:
                queryset = queryset.filter(year__lte=int(year_max))
            except ValueError:
                pass
        
        # Поиск по названию, подзаголовку, ISBN (нечувствительный к регистру)
        search = self.request.query_params.get('search')
        if search:
            # В PostgreSQL с локалью C icontains может быть чувствителен к регистру
            # Используем поиск по нескольким вариантам регистра для надежности
            search_variants = [
                search.lower(),      # нижний регистр
                search.capitalize(),  # с заглавной первой буквой
                search.upper(),      # верхний регистр
                search,              # исходный вариант
            ]
            # Убираем дубликаты
            search_variants = list(dict.fromkeys(search_variants))
            
            # Создаем Q объект для поиска по всем вариантам
            search_q = Q()
            for variant in search_variants:
                search_q |= (
                    Q(title__icontains=variant) |
                    Q(subtitle__icontains=variant) |
                    Q(isbn__icontains=variant) |
                    Q(authors__full_name__icontains=variant)
                )
            queryset = queryset.filter(search_q)
        
        # Фильтрация по типу переплета
        binding_type = self.request.query_params.get('binding_type')
        if binding_type:
            queryset = queryset.filter(binding_type=binding_type)
        
        # Фильтрация по формату
        format_type = self.request.query_params.get('format')
        if format_type:
            queryset = queryset.filter(format=format_type)
        
        # Фильтрация по состоянию
        condition = self.request.query_params.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition)
        
        # Фильтрация по диапазону цены
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        if price_min:
            try:
                queryset = queryset.filter(price_rub__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(price_rub__lte=float(price_max))
            except ValueError:
                pass
        
        # Сортировка
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Применяем distinct() только в конце, если были фильтры по ManyToMany
        # Это нужно для избежания дубликатов при фильтрации по authors, hashtags и т.д.
        # Проверяем все возможные фильтры, которые могут вызвать дубликаты
        has_manytomany_filters = (
            self.request.query_params.get('search') or
            self.request.query_params.get('hashtag') or
            self.request.query_params.get('author') or
            self.request.query_params.get('has_reviews') or
            self.request.query_params.get('has_electronic')
        )
        if has_manytomany_filters:
            queryset = queryset.distinct()
        
        return queryset
    
    @action(detail=False, methods=['post'], url_path='normalize-pages', parser_classes=[MultiPartParser, FormParser])
    def normalize_pages(self, request):
        """
        Нормализация страниц для мастера создания книги
        POST /api/books/normalize-pages/
        Content-Type: multipart/form-data
        
        Body:
        - files: List[File] - загруженные изображения
        
        Response:
        {
            "normalized_images": [
                {
                    "id": "uuid",
                    "original_filename": "page1.jpg",
                    "normalized_url": "/media/temp/normalized/normalized_uuid.jpg",
                    "width": 1920,
                    "height": 2560
                },
                ...
            ],
            "total": 5,
            "processed": 5
        }
        """
        import sys
        print("=" * 80, file=sys.stderr)
        print("🔵 normalize_pages ENDPOINT ВЫЗВАН!", file=sys.stderr)
        print(f"🔵 request.method: {request.method}", file=sys.stderr)
        print(f"🔵 request.FILES: {list(request.FILES.keys())}", file=sys.stderr)
        print(f"🔵 request.data: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}", file=sys.stderr)
        sys.stderr.flush()
        
        files = request.FILES.getlist('files')
        
        if not files:
            return Response(
                {'error': 'Файлы не найдены'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import sys
            print(f"🔵 normalize_pages endpoint вызван с {len(files)} файлами", file=sys.stderr)
            for i, f in enumerate(files):
                print(f"  Файл {i+1}: {f.name}, размер: {f.size} байт, тип: {f.content_type}", file=sys.stderr)
            sys.stderr.flush()
            
            # Обрабатываем файлы
            normalized_images = normalize_pages_batch(files)
            
            print(f"🔵 normalize_pages_batch вернул {len(normalized_images)} результатов")
            
            # Фильтруем успешно обработанные изображения
            successful = [img for img in normalized_images if img.get('normalized_url')]
            failed = [img for img in normalized_images if img.get('error')]
            
            print(f"🔵 Успешно: {len(successful)}, Ошибок: {len(failed)}")
            
            return Response({
                'normalized_images': normalized_images,
                'total': len(normalized_images),
                'processed': len(successful),
                'failed': len(failed),
                'errors': [{'filename': img['original_filename'], 'error': img.get('error')} 
                          for img in failed] if failed else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"🔴 ОШИБКА в normalize_pages endpoint: {str(e)}")
            print(f"🔴 Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Ошибка обработки: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='auto-fill')
    def auto_fill(self, request):
        """
        Автозаполнение данных книги через OpenAI GPT-4o
        POST /api/books/auto-fill/
        Content-Type: application/json
        
        Body:
        {
            "normalized_image_urls": [
                "/media/temp/normalized/normalized_uuid1.jpg",
                "/media/temp/normalized/normalized_uuid2.jpg",
                ...
            ]
        }
        
        Response:
        {
            "success": true,
            "data": {
                "title": "...",
                "subtitle": "...",
                "category_id": 1,
                "authors": ["...", "..."],
                ...
            },
            "confidence": 0.85,
            "error": null
        }
        """
        import sys
        
        normalized_image_urls = request.data.get('normalized_image_urls', [])
        
        if not normalized_image_urls:
            return Response(
                {'error': 'Необходимо указать normalized_image_urls'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(normalized_image_urls, list):
            return Response(
                {'error': 'normalized_image_urls должен быть массивом'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"🔵 auto_fill endpoint вызван с {len(normalized_image_urls)} изображениями", file=sys.stderr)
        sys.stderr.flush()
        
        try:
            result = auto_fill_book_data(normalized_image_urls)
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(
                    {
                        'success': False,
                        'data': None,
                        'error': result.get('error', 'Неизвестная ошибка'),
                        'confidence': None
                    },
                    status=status.HTTP_200_OK  # 200, но с success=false для фронтенда
                )
                
        except ValueError as e:
            # Ошибка конфигурации (нет API ключа)
            return Response(
                {
                    'success': False,
                    'data': None,
                    'error': str(e),
                    'confidence': None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"🔴 ОШИБКА в auto_fill endpoint: {str(e)}", file=sys.stderr)
            print(f"🔴 Traceback: {error_trace}", file=sys.stderr)
            sys.stderr.flush()
            
            return Response(
                {
                    'success': False,
                    'data': None,
                    'error': f'Ошибка обработки: {str(e)}',
                    'confidence': None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Возвращает статистику по фильтрам для всех книг в выбранных категориях и библиотеках.
        Используется для отображения счетчиков в фильтрах.
        """
        from datetime import timedelta
        from django.utils import timezone
        from ..utils import parse_library_ids, get_category_queryset
        
        # Получаем параметры фильтрации
        library_ids = parse_library_ids(request)
        
        # Если не выбраны библиотеки, возвращаем нулевые статистики
        if not library_ids:
            return Response({
                'status': {
                    'none': 0,
                    'reading': 0,
                    'read': 0,
                    'want_to_read': 0,
                    'want_to_reread': 0,
                },
                'with_reviews': 0,
                'with_electronic': 0,
                'recently_added': 0,
            })
        
        # Получаем базовый queryset (без фильтров из get_queryset, чтобы избежать конфликтов)
        queryset = Book.objects.all()
        
        # Фильтрация по библиотекам
        queryset = queryset.filter(library_id__in=library_ids)
        
        # Получаем query параметры (поддержка как DRF Request, так и Django WSGIRequest)
        query_params = getattr(request, 'query_params', request.GET)
        
        # Фильтрация по категории (если указана)
        category_id = query_params.get('category')
        if category_id:
            try:
                category_id = int(category_id)
                queryset = get_category_queryset(category_id, include_subcategories=True)
                queryset = queryset.filter(library_id__in=library_ids)
            except (ValueError, Category.DoesNotExist):
                pass
        
        # Фильтрация по хэштегу (если указан)
        hashtag_id = query_params.get('hashtag')
        if hashtag_id:
            try:
                hashtag_id = int(hashtag_id)
                queryset = queryset.filter(hashtags__id=hashtag_id).distinct()
            except ValueError:
                pass
        
        # Фильтрация по поисковому запросу (если указан)
        search = query_params.get('search')
        if search:
            search_variants = [
                search.lower(),
                search.capitalize(),
                search.upper(),
                search,
            ]
            search_variants = list(dict.fromkeys(search_variants))
            
            search_q = Q()
            for variant in search_variants:
                search_q |= (
                    Q(title__icontains=variant) |
                    Q(subtitle__icontains=variant) |
                    Q(isbn__icontains=variant) |
                    Q(authors__full_name__icontains=variant)
                )
            queryset = queryset.filter(search_q).distinct()
        
        # Подсчитываем статистику
        stats = {
            'status': {
                'none': queryset.filter(status='none').count(),
                'reading': queryset.filter(status='reading').count(),
                'read': queryset.filter(status='read').count(),
                'want_to_read': queryset.filter(status='want_to_read').count(),
                'want_to_reread': queryset.filter(status='want_to_reread').count(),
            },
            'with_reviews': queryset.filter(reviews__isnull=False).distinct().count(),
            'with_electronic': queryset.filter(electronic_versions__isnull=False).distinct().count(),
            'recently_added': queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def my_books(self, request):
        """Получить свои книги"""
        books = self.get_queryset().filter(owner=request.user)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-books/read')
    def my_books_read(self, request):
        """Получить прочитанные книги"""
        books = self.get_queryset().filter(owner=request.user, status='read')
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-books/want-to-read')
    def my_books_want_to_read(self, request):
        """Получить книги "Буду читать" """
        books = self.get_queryset().filter(owner=request.user, status='want_to_read')
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Передать книгу в библиотеку или другому пользователю"""
        book = self.get_object()
        
        # Проверяем что это владелец книги
        if book.owner != request.user:
            return Response(
                {'error': 'Только владелец может передать книгу'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        library_id = request.data.get('library')
        user_id = request.data.get('user')
        
        try:
            book, message = TransferService.transfer_book(
                book,
                library_id=library_id,
                user_id=user_id
            )
            
            serializer = BookSerializer(book, context={'request': request})
            return Response({
                'message': message,
                'book': serializer.data
            })
        except TransferError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def hashtags(self, request, pk=None):
        """Добавить хэштеги к книге"""
        # Используем get_object() для получения книги (DRF правильно обрабатывает pk)
        # Затем перезагружаем объект из БД для актуального состояния хэштегов
        book_obj = self.get_object()
        from books.models import Book
        book = Book.objects.select_related('owner', 'library').get(pk=book_obj.pk)
        
        # Проверяем что это владелец
        if book.owner != request.user:
            return Response(
                {'error': 'Только владелец может добавлять хэштеги'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        hashtag_names = request.data.get('hashtag_names', [])
        
        # Убеждаемся что hashtag_names - это список
        if not isinstance(hashtag_names, list):
            # Если это строка, преобразуем в список с одним элементом
            hashtag_names = [hashtag_names] if hashtag_names else []
        
        if not hashtag_names:
            return Response(
                {'error': 'Необходимо указать hashtag_names'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            added_hashtags = HashtagService.add_hashtags_to_book(
                book,
                hashtag_names,
                request.user
            )
            
            # Обновляем объект из БД чтобы получить актуальные хэштеги
            book.refresh_from_db()
            
            serializer = HashtagSerializer(
                book.hashtags.all(),
                many=True,
                context={'request': request}
            )
            
            return Response({
                'message': f'Добавлено {len(added_hashtags)} хэштегов',
                'hashtags': serializer.data
            })
        except HashtagLimitExceeded as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get', 'post'])
    def images(self, request, pk=None):
        """Управление изображениями книги"""
        book = self.get_object()
        
        if request.method == 'GET':
            # Получить все изображения
            images = book.images.all()
            serializer = BookImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Добавить изображение
            image_file = request.FILES.get('image')
            order = request.data.get('order', 0)
            
            if not image_file:
                return Response(
                    {'error': 'Файл изображения не предоставлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                order = int(order)
                if order < MIN_IMAGE_ORDER or order > MAX_IMAGE_ORDER:
                    return Response(
                        {'error': f'Порядок должен быть от {MIN_IMAGE_ORDER} до {MAX_IMAGE_ORDER}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {'error': 'Порядок должен быть числом'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверка уникальности порядка
            if book.images.filter(order=order).exists():
                return Response(
                    {'error': f'Изображение с порядком {order} уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            book_image = BookImage.objects.create(
                book=book,
                image=image_file,
                order=order
            )
            
            serializer = BookImageSerializer(book_image, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def electronic_versions(self, request, pk=None):
        """Управление электронными версиями книги"""
        book = self.get_object()
        
        if request.method == 'GET':
            # Получить все электронные версии
            versions = book.electronic_versions.all()
            serializer = BookElectronicSerializer(versions, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Добавить электронную версию
            format_type = request.data.get('format')
            url = request.data.get('url', '')
            file = request.FILES.get('file')
            
            if not format_type:
                return Response(
                    {'error': 'Формат не указан'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not url and not file:
                return Response(
                    {'error': 'Необходимо указать либо URL, либо загрузить файл'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            electronic = BookElectronic.objects.create(
                book=book,
                format=format_type,
                url=url,
                file=file if file else None
            )
            
            serializer = BookElectronicSerializer(electronic, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def pages(self, request, pk=None):
        """Получить все страницы книги"""
        book = self.get_object()
        
        # Фильтр по статусу обработки
        status_filter = request.query_params.get('status')
        pages = book.pages_set.all()
        
        if status_filter:
            pages = pages.filter(processing_status=status_filter)
        
        serializer = BookPageSerializer(pages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_pages(self, request, pk=None):
        """Загрузка страниц книги"""
        book = self.get_object()
        files = request.FILES.getlist('pages')
        
        if not files:
            return Response(
                {'error': 'Файлы не найдены'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_pages = []
        
        for idx, file in enumerate(files):
            # Определяем номер страницы
            page_number = book.pages_set.count() + idx + 1
            
            # Создаем страницу
            page = BookPage.objects.create(
                book=book,
                page_number=page_number,
                original_image=file,
                processing_status='pending'
            )
            
            created_pages.append(page)
        
        serializer = BookPageSerializer(
            created_pages, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            'message': f'Загружено {len(created_pages)} страниц',
            'pages': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def process_pages(self, request, pk=None):
        """Обработка страниц книги"""
        book = self.get_object()
        
        # Получаем ID страниц для обработки
        page_ids = request.data.get('page_ids', [])
        
        if page_ids:
            pages = book.pages_set.filter(id__in=page_ids, processing_status='pending')
        else:
            # Обрабатываем все необработанные страницы
            pages = book.pages_set.filter(processing_status='pending')
        
        if not pages:
            return Response(
                {'message': 'Нет страниц для обработки'},
                status=status.HTTP_200_OK
            )
        
        processed_count = 0
        errors = []
        
        for page in pages:
            try:
                page.processing_status = 'processing'
                page.save()
                
                # Входной файл
                input_path = page.original_image.path
                
                # Выходной файл
                output_filename = f"processed_{page.id}_{os.path.basename(input_path)}"
                output_dir = Path(settings.MEDIA_ROOT) / 'books' / 'pages' / 'processed'
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / output_filename
                
                # Обрабатываем документ через сервис
                width, height = process_document(input_path, output_path)
                
                # Сохраняем относительный путь
                rel_path = str(output_path.relative_to(settings.MEDIA_ROOT))
                page.processed_image = rel_path
                page.width = width
                page.height = height
                page.processing_status = 'completed'
                page.processed_at = timezone.now()
                page.save()
                
                processed_count += 1
                    
            except Exception as e:
                page.processing_status = 'failed'
                page.error_message = str(e)
                page.save()
                errors.append({
                    'page_id': page.id,
                    'page_number': page.page_number,
                    'error': str(e)
                })
        
        return Response({
            'message': f'Обработано страниц: {processed_count}',
            'processed': processed_count,
            'errors': errors
        })

