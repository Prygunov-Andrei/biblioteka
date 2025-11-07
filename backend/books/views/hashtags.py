"""
ViewSet для хэштегов
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from ..models import Hashtag, Book, Category
from ..serializers import HashtagSerializer
from ..services.hashtag_service import HashtagService


class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    """API для хэштегов (только чтение, создание через добавление к книге)"""
    queryset = Hashtag.objects.select_related('creator').prefetch_related('books')
    serializer_class = HashtagSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]  # Чтение для всех
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по создателю
        creator = self.request.query_params.get('creator')
        if creator:
            try:
                creator_id = int(creator)
                queryset = queryset.filter(creator_id=creator_id)
            except ValueError:
                queryset = queryset.filter(creator__username__icontains=creator)
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Возвращает хэштеги с частотой упоминания для выбранной категории
        
        Query params:
            category_id - ID категории (если не указан, используются все категории)
            libraries - ID библиотек (можно передать несколько через запятую или массивом)
        """
        category_id = request.query_params.get('category_id')
        
        # Получаем список библиотек из параметров запроса
        libraries_param = request.query_params.getlist('libraries')
        if not libraries_param:
            # Пробуем получить как строку с запятыми
            libraries_str = request.query_params.get('libraries')
            if libraries_str:
                libraries_param = [lib.strip() for lib in libraries_str.split(',') if lib.strip()]
        
        # Базовый queryset для книг
        books_queryset = Book.objects.all()
        
        # ВАЖНО: Фильтруем по библиотекам ТОЛЬКО если они указаны
        # Если библиотеки не указаны, возвращаем пустой список (не все хэштеги!)
        if libraries_param:
            try:
                library_ids = [int(lib_id) for lib_id in libraries_param if lib_id]
                if library_ids:
                    books_queryset = books_queryset.filter(library_id__in=library_ids)
                else:
                    # Если библиотеки указаны, но не валидны, возвращаем пустой список
                    return Response({
                        'hashtags': [],
                        'max_count': 1,
                        'min_count': 1,
                    })
            except (ValueError, TypeError):
                # Если не удалось преобразовать в числа, возвращаем пустой список
                return Response({
                    'hashtags': [],
                    'max_count': 1,
                    'min_count': 1,
                })
        else:
            # Если библиотеки НЕ указаны, возвращаем пустой список
            # (не показываем все хэштеги, если библиотеки не выбраны)
            return Response({
                'hashtags': [],
                'max_count': 1,
                'min_count': 1,
            })
        
        if category_id:
            try:
                # Используем утилиту для получения queryset категории
                from ..utils import get_category_queryset
                category_queryset = get_category_queryset(category_id, include_subcategories=True)
                # Применяем фильтр категории к уже отфильтрованному по библиотекам queryset
                books_queryset = books_queryset.filter(id__in=category_queryset.values_list('id', flat=True))
            except Category.DoesNotExist:
                return Response(
                    {'error': 'Категория не найдена'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Получаем хэштеги с подсчетом частоты для книг в категории и библиотеках
        hashtags = Hashtag.objects.filter(
            books__in=books_queryset
        ).annotate(
            count=Count('books', filter=Q(books__in=books_queryset))
        ).distinct().order_by('-count', 'name')
        
        # Формируем ответ с частотой
        result = []
        max_count = 0
        min_count = float('inf')
        
        for hashtag in hashtags:
            count = hashtag.count
            max_count = max(max_count, count)
            min_count = min(min_count, count)
            result.append({
                'id': hashtag.id,
                'name': hashtag.name,
                'slug': hashtag.slug,
                'count': count,
            })
        
        # Добавляем информацию о диапазоне для расчета размера шрифта
        response_data = {
            'hashtags': result,
            'max_count': max_count if max_count > 0 else 1,
            'min_count': min_count if min_count != float('inf') else 1,
        }
        
        return Response(response_data)
    
    def create(self, request, *args, **kwargs):
        """Создать новый хэштег"""
        name = request.data.get('name', '').strip()
        if not name:
            return Response(
                {'error': 'Необходимо указать name'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            hashtag, created = HashtagService.get_or_create_hashtag(
                name,
                request.user
            )
            
            serializer = self.get_serializer(hashtag, context={'request': request})
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=status_code)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

