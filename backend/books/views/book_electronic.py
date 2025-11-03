"""
ViewSet для электронных версий книг
"""
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from ..models import BookElectronic
from ..serializers import BookElectronicSerializer


class BookElectronicViewSet(viewsets.ModelViewSet):
    """API для электронных версий книг"""
    queryset = BookElectronic.objects.select_related('book')
    serializer_class = BookElectronicSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по книге
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        # Фильтр по формату
        format_type = self.request.query_params.get('format')
        if format_type:
            queryset = queryset.filter(format=format_type)
        
        return queryset.order_by('book', 'format')

