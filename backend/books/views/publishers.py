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
        from django.db.models import Case, When, Value, IntegerField, Q
        
        queryset = super().get_queryset()
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            search_clean = search.strip()
            
            # Разбиваем поисковый запрос на слова (разделители: запятая, пробел)
            # И ищем издательства, которые содержат хотя бы одно из слов
            search_words = [word.strip() for word in search_clean.replace(',', ' ').split() if word.strip()]
            
            if search_words:
                # Строим Q-объект для поиска по каждому слову
                q_objects = Q()
                for word in search_words:
                    q_objects |= Q(name__icontains=word)
                
                queryset = queryset.filter(q_objects).distinct()
                
                # Сортировка по точности совпадения:
                # 1. Точное совпадение всего запроса (без учета регистра)
                # 2. Начинается с первого слова запроса
                # 3. Содержит все слова запроса
                # 4. Содержит первое слово запроса
                # 5. Содержит любое слово запроса
                queryset = queryset.annotate(
                    match_priority=Case(
                        When(name__iexact=search_clean, then=Value(1)),
                        When(name__istartswith=search_words[0], then=Value(2)),
                        When(name__icontains=search_clean, then=Value(3)),
                        When(name__icontains=search_words[0], then=Value(4)),
                        default=Value(5),
                        output_field=IntegerField()
                    )
                ).order_by('match_priority', 'name')
            else:
                # Если после очистки не осталось слов, используем исходный запрос
                queryset = queryset.filter(name__icontains=search_clean).order_by('name')
        else:
            # Если нет поиска - обычная сортировка по названию
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

