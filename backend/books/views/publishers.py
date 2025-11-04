"""
ViewSet для издательств
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Publisher
from ..serializers import PublisherSerializer, BookSerializer


class PublisherViewSet(viewsets.ModelViewSet):
    """API для издательств"""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Сортировка
        ordering = self.request.query_params.get('ordering', 'name')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Получить все книги издательства"""
        from .books import BookViewSet
        publisher = self.get_object()
        # Используем оптимизированный queryset из BookViewSet
        books_queryset = BookViewSet.queryset.filter(publisher=publisher)
        serializer = BookSerializer(books_queryset, many=True, context={'request': request})
        return Response(serializer.data)

