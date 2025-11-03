"""
ViewSet для отзывов на книги
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import BookReview
from ..serializers import BookReviewSerializer
from ..permissions import IsReviewOwner


class BookReviewViewSet(viewsets.ModelViewSet):
    """API для отзывов на книги"""
    queryset = BookReview.objects.select_related('book', 'user')
    serializer_class = BookReviewSerializer
    permission_classes = [IsReviewOwner]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтр по книге
        book = self.request.query_params.get('book')
        if book:
            try:
                book_id = int(book)
                queryset = queryset.filter(book_id=book_id)
            except ValueError:
                queryset = queryset.filter(book__title__icontains=book)
        
        # Фильтр по пользователю
        user = self.request.query_params.get('user')
        if user:
            try:
                user_id = int(user)
                queryset = queryset.filter(user_id=user_id)
            except ValueError:
                queryset = queryset.filter(user__username__icontains=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """При создании автоматически устанавливаем пользователя"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Создание или обновление отзыва (upsert)"""
        book_id = request.data.get('book')
        if not book_id:
            return Response(
                {'error': 'Необходимо указать book'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем существующий отзыв
        try:
            review = BookReview.objects.get(book_id=book_id, user=request.user)
            # Обновляем существующий отзыв
            serializer = self.get_serializer(
                review,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except BookReview.DoesNotExist:
            # Создаем новый отзыв
            return super().create(request, *args, **kwargs)

