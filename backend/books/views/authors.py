"""
ViewSet для авторов
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Author
from ..serializers import AuthorSerializer, BookSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """API для авторов"""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Поиск по ФИО
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(full_name__icontains=search)
        
        # Фильтр по году рождения
        birth_year_min = self.request.query_params.get('birth_year_min')
        birth_year_max = self.request.query_params.get('birth_year_max')
        if birth_year_min:
            queryset = queryset.filter(birth_year__gte=birth_year_min)
        if birth_year_max:
            queryset = queryset.filter(birth_year__lte=birth_year_max)
        
        # Сортировка
        ordering = self.request.query_params.get('ordering', 'full_name')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Получить все книги автора"""
        author = self.get_object()
        books = author.books.all()
        serializer = BookSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)

