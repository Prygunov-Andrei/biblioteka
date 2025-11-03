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
    queryset = Category.objects.all()
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
        """
        parent_categories = Category.objects.filter(
            parent_category__isnull=True
        ).order_by('order', 'name')
        
        serializer = CategoryTreeSerializer(parent_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        """Возвращает подкатегории для данной категории"""
        category = self.get_object()
        subcategories = category.subcategories.all().order_by('order', 'name')
        serializer = CategorySerializer(subcategories, many=True)
        return Response(serializer.data)

