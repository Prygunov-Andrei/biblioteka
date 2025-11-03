"""
ViewSet для категорий
"""
from django.db.models import Q
from rest_framework import viewsets
from ..models import Category
from ..serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """API для категорий"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Поиск по названию или коду
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        return queryset

