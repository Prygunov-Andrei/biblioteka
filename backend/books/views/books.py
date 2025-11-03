"""
ViewSet для книг (основной, самый сложный)
"""
import os
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from ..models import Book, BookPage, BookImage, BookElectronic, Category
from ..serializers import (
    BookSerializer, BookDetailSerializer,
    BookCreateSerializer, BookUpdateSerializer,
    BookPageSerializer, BookImageSerializer,
    BookElectronicSerializer, HashtagSerializer, LibrarySerializer
)
from ..permissions import IsOwnerOrReadOnly
from rest_framework.permissions import AllowAny
from ..services.document_processor import process_document
from ..services.hashtag_service import HashtagService
from ..services.transfer_service import TransferService
from ..exceptions import HashtagLimitExceeded, TransferError
from ..constants import MIN_IMAGE_ORDER, MAX_IMAGE_ORDER


class BookViewSet(viewsets.ModelViewSet):
    """API для книг"""
    queryset = Book.objects.select_related(
        'category', 'publisher', 'owner', 'library'
    ).prefetch_related(
        'authors', 'images', 'electronic_versions', 'pages_set',
        'hashtags', 'reviews'
    )
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    # Разрешаем чтение всем, редактирование только владельцам
    permission_classes = [IsOwnerOrReadOnly]
    
    def get_permissions(self):
        """
        Переопределяем права доступа для разных действий.
        Для list и retrieve - AllowAny (все могут просматривать)
        Для остальных действий - IsOwnerOrReadOnly (только владелец может редактировать)
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        elif self.action == 'create':
            return BookCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookUpdateSerializer
        return BookSerializer
    
    def create(self, request, *args, **kwargs):
        """Создание книги с авторами и хэштегами"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        
        # Возвращаем с ID используя BookSerializer
        response_serializer = BookSerializer(book, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по категории (slug или ID)
        category = self.request.query_params.get('category')
        if category:
            try:
                category_id = int(category)
                category_obj = Category.objects.get(id=category_id)
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
        libraries = self.request.query_params.getlist('libraries') or self.request.query_params.getlist('library')
        if libraries:
            try:
                library_ids = [int(lib_id) for lib_id in libraries if lib_id]
                if library_ids:
                    queryset = queryset.filter(library_id__in=library_ids)
            except (ValueError, TypeError):
                # Если не удалось распарсить как ID, пробуем фильтровать по имени
                queryset = queryset.filter(library__name__in=libraries).distinct()
        
        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтрация по хэштегу
        hashtag = self.request.query_params.get('hashtag')
        if hashtag:
            queryset = queryset.filter(hashtags__name__icontains=hashtag).distinct()
        
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
        
        # Поиск по названию, подзаголовку, ISBN
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(subtitle__icontains=search) |
                Q(isbn__icontains=search) |
                Q(authors__full_name__icontains=search)
            ).distinct()
        
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
        
        return queryset
    
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

