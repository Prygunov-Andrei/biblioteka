"""
ViewSet для страниц книг
"""
import os
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from ..models import BookPage
from ..serializers import BookPageSerializer
from ..services.document_processor import process_document


class BookPageViewSet(viewsets.ModelViewSet):
    """API для страниц книг"""
    queryset = BookPage.objects.select_related('book')
    serializer_class = BookPageSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по книге
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        # Фильтр по статусу обработки
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(processing_status=status_filter)
        
        return queryset.order_by('book', 'page_number')
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Обработать конкретную страницу"""
        page = self.get_object()
        
        if page.processing_status != 'pending':
            return Response(
                {'error': f'Страница уже обработана (статус: {page.processing_status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            
            # Обрабатываем документ
            width, height = process_document(input_path, output_path)
            
            # Сохраняем результат
            rel_path = str(output_path.relative_to(settings.MEDIA_ROOT))
            page.processed_image = rel_path
            page.width = width
            page.height = height
            page.processing_status = 'completed'
            page.processed_at = timezone.now()
            page.save()
            
            serializer = self.get_serializer(page)
            return Response(serializer.data)
            
        except Exception as e:
            page.processing_status = 'failed'
            page.error_message = str(e)
            page.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

