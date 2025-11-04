"""
Утилиты для работы с книгами и категориями
"""
from typing import List, Optional
from django.db.models import QuerySet
from .models import Category, Book


def get_category_queryset(category_id: int, include_subcategories: bool = True) -> QuerySet:
    """
    Получает queryset книг для категории с учетом подкатегорий
    
    Args:
        category_id: ID категории
        include_subcategories: Включать ли подкатегории (по умолчанию True)
    
    Returns:
        QuerySet книг для категории
    """
    try:
        category = Category.objects.prefetch_related('subcategories').get(id=category_id)
        
        if include_subcategories and category.subcategories.exists():
            # Получаем ID подкатегорий одним запросом
            subcategory_ids = list(category.subcategories.values_list('id', flat=True))
            subcategory_ids.append(category.id)
            return Book.objects.filter(category_id__in=subcategory_ids)
        else:
            return Book.objects.filter(category_id=category_id)
    except Category.DoesNotExist:
        return Book.objects.none()


def parse_library_ids(request) -> List[int]:
    """
    Парсит список ID библиотек из query параметров request
    
    Args:
        request: DRF Request или Django WSGIRequest объект
    
    Returns:
        Список ID библиотек (пустой список если не указаны)
    """
    # Поддержка как DRF Request, так и обычного Django request
    if hasattr(request, 'query_params'):
        # DRF Request
        libraries = request.query_params.getlist('libraries') or request.query_params.getlist('library')
    else:
        # Django WSGIRequest
        libraries = request.GET.getlist('libraries') or request.GET.getlist('library')
    
    library_ids = []
    if libraries:
        try:
            library_ids = [int(lib_id) for lib_id in libraries if lib_id]
        except (ValueError, TypeError):
            pass
    return library_ids

