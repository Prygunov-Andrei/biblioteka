"""
ViewSet для изображений книг
"""
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from ..models import BookImage
from ..serializers import BookImageSerializer


class BookImageViewSet(viewsets.ModelViewSet):
    """API для изображений книг"""
    queryset = BookImage.objects.select_related('book')
    serializer_class = BookImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по книге
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        return queryset.order_by('book', 'order')

