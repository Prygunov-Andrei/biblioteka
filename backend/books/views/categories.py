"""
ViewSet для категорий
"""
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import Category
from ..serializers import CategorySerializer, CategoryTreeSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """API для категорий"""
    from django.db.models import Count, Prefetch
    from ..models import Book
    queryset = Category.objects.prefetch_related(
        'subcategories',
        Prefetch('subcategories__books', queryset=Book.objects.all())
    ).annotate(
        books_count_annotated=Count('books', distinct=True),
        subcategories_books_count_annotated=Count('subcategories__books', distinct=True)
    )
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]  # Категории доступны для чтения всем
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Поиск по названию или коду
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        # Фильтр по типу категории
        parent_only = self.request.query_params.get('parent_only', '').lower() == 'true'
        if parent_only:
            # Возвращаем только категории без родителя (родительские категории)
            queryset = queryset.filter(parent_category__isnull=True)
        
        subcategories_only = self.request.query_params.get('subcategories_only', '').lower() == 'true'
        if subcategories_only:
            # Возвращаем только подкатегории
            queryset = queryset.filter(parent_category__isnull=False)
        
        # Фильтр по родительской категории
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(parent_category_id=parent_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Возвращает дерево категорий:
        - Только родительские категории (без parent_category)
        - С вложенными подкатегориями
        - Поддерживает фильтрацию по библиотекам для подсчета книг
        - ВАЖНО: Если библиотеки не указаны, возвращает пустой список
        """
        from django.db.models import Count, Q
        from books.models import Book
        
        # Получаем список библиотек из query параметра
        from ..utils import parse_library_ids
        library_ids = parse_library_ids(request)
        
        # ВАЖНО: Если библиотеки не указаны, возвращаем пустой список категорий
        # (не показываем все категории, если библиотеки не выбраны)
        if not library_ids:
            return Response([])
        
        # Аннотируем подкатегории для каждой родительской категории
        from django.db.models import Prefetch
        subcategories_queryset = Category.objects.filter(
            parent_category__isnull=False
        ).annotate(
            books_count=Count(
                'books',
                filter=Q(books__library_id__in=library_ids),
                distinct=True
            )
        ).order_by('name')
        
        # Формируем queryset для родительских категорий
        parent_categories = Category.objects.filter(
            parent_category__isnull=True
        ).order_by('name')  # Сортировка по алфавиту
        
        # Аннотируем количество книг с фильтрацией по библиотекам
        parent_categories = parent_categories.annotate(
            books_count_annotated=Count(
                'books',
                filter=Q(books__library_id__in=library_ids),
                distinct=True
            ),
            subcategories_books_count_annotated=Count(
                'subcategories__books',
                filter=Q(subcategories__books__library_id__in=library_ids),
                distinct=True
            )
        )
        
        # Добавляем prefetch для подкатегорий (должно быть ПОСЛЕ аннотаций)
        parent_categories = parent_categories.prefetch_related(
            Prefetch('subcategories', queryset=subcategories_queryset)
        )
        
        # Фильтруем родительские категории: показываем только если есть книги
        # (либо в самой категории, либо в подкатегориях)
        parent_categories = parent_categories.filter(
            Q(books_count_annotated__gt=0) | Q(subcategories_books_count_annotated__gt=0)
        )
        
        serializer = CategoryTreeSerializer(
            parent_categories, 
            many=True,
            context={'request': request, 'library_ids': library_ids}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='tree/all')
    def tree_all(self, request):
        """
        Возвращает ВСЕ категории в виде дерева (для выбора при создании книги).
        Не фильтрует по библиотекам - возвращает все категории независимо от наличия книг.
        """
        from django.db.models import Count, Prefetch
        
        # Аннотируем подкатегории (все, без фильтрации)
        subcategories_queryset = Category.objects.filter(
            parent_category__isnull=False
        ).annotate(
            books_count=Count('books', distinct=True)
        ).order_by('name')
        
        # Формируем queryset для родительских категорий (все, без фильтрации)
        parent_categories = Category.objects.filter(
            parent_category__isnull=True
        ).annotate(
            books_count_annotated=Count('books', distinct=True),
            subcategories_books_count_annotated=Count('subcategories__books', distinct=True)
        ).order_by('name')
        
        # Добавляем prefetch для подкатегорий
        parent_categories = parent_categories.prefetch_related(
            Prefetch('subcategories', queryset=subcategories_queryset)
        )
        
        # НЕ фильтруем - возвращаем все категории
        serializer = CategoryTreeSerializer(
            parent_categories, 
            many=True,
            context={'request': request, 'library_ids': None}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        """Возвращает подкатегории для данной категории"""
        category = self.get_object()
        # Используем prefetch если доступен
        if hasattr(category, '_prefetched_objects_cache') and 'subcategories' in category._prefetched_objects_cache:
            subcategories = category.subcategories.all().order_by('name')
        else:
            subcategories = category.subcategories.all().order_by('name')
        serializer = CategorySerializer(subcategories, many=True)
        return Response(serializer.data)

