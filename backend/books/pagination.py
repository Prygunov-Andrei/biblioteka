"""
Кастомные пагинаторы для книг
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ConditionalBookPagination(PageNumberPagination):
    """
    Условная пагинация для книг:
    - Если книг <= 30: возвращаем все книги без пагинации
    - Если книг > 30: применяем пагинацию с размером страницы 30
    """
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Пагинирует queryset только если количество объектов больше page_size
        """
        # Подсчитываем общее количество книг
        self.count = queryset.count()
        
        # Если книг меньше или равно page_size, не применяем пагинацию
        if self.count <= self.page_size:
            return None
        
        # Иначе применяем стандартную пагинацию
        return super().paginate_queryset(queryset, request, view)
    
    def get_paginated_response(self, data):
        """
        Возвращает пагинированный ответ или обычный список если пагинация не применена
        """
        # Если пагинация не была применена (count <= page_size), возвращаем простой список
        if self.count <= self.page_size:
            return Response({
                'count': self.count,
                'results': data,
                'paginated': False
            })
        
        # Иначе возвращаем стандартный пагинированный ответ
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'paginated': True
        })

