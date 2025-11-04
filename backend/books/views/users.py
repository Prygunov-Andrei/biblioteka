"""
ViewSet для профилей пользователей
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from ..models import UserProfile
from ..serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """API для профилей пользователей"""
    queryset = UserProfile.objects.select_related('user').prefetch_related(
        'user__libraries',
        'user__owned_books'
    )
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]  # Профиль доступен только авторизованным
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Пользователь видит все профили, но может редактировать только свой
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Получить или обновить свой профиль"""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile, context={'request': request})
            return Response(serializer.data)
        
        # PUT/PATCH - обновление
        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

