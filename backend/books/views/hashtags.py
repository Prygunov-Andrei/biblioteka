"""
ViewSet для хэштегов
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Hashtag
from ..serializers import HashtagSerializer
from ..services.hashtag_service import HashtagService


class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    """API для хэштегов (только чтение, создание через добавление к книге)"""
    queryset = Hashtag.objects.select_related('creator').prefetch_related('books')
    serializer_class = HashtagSerializer
    lookup_field = 'slug'
    permission_classes = []  # Чтение для всех
    
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

