"""
ViewSet для библиотек
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..models import Library
from ..serializers import LibrarySerializer, BookSerializer
from ..permissions import IsLibraryOwner


class LibraryViewSet(viewsets.ModelViewSet):
    """API для библиотек"""
    queryset = Library.objects.select_related('owner')
    serializer_class = LibrarySerializer
    permission_classes = [IsLibraryOwner]
    
    def get_permissions(self):
        """
        Переопределяем права доступа для разных действий.
        Для list, retrieve - AllowAny (все могут просматривать)
        Для остальных действий - IsLibraryOwner (только владелец может редактировать)
        """
        if self.action in ['list', 'retrieve', 'my_libraries']:
            return [AllowAny()]
        return [IsLibraryOwner()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по владельцу
        owner = self.request.query_params.get('owner')
        if owner:
            try:
                owner_id = int(owner)
                queryset = queryset.filter(owner_id=owner_id)
            except ValueError:
                queryset = queryset.filter(owner__username__icontains=owner)
        
        return queryset
    
    def perform_create(self, serializer):
        """При создании автоматически устанавливаем владельца"""
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_libraries(self, request):
        """Получить свои библиотеки"""
        libraries = self.get_queryset().filter(owner=request.user)
        serializer = self.get_serializer(libraries, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Получить книги в библиотеке"""
        library = self.get_object()
        books = library.books.all()
        serializer = BookSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)

