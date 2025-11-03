"""
Кастомные permissions для разграничения доступа
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Только владелец может редактировать книгу"""
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Редактирование только владельцу
        return obj.owner == request.user


class IsLibraryOwner(permissions.BasePermission):
    """Только владелец библиотеки может редактировать"""
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Редактирование только владельцу
        return obj.owner == request.user


class IsReviewOwner(permissions.BasePermission):
    """Только автор отзыва может редактировать"""
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Редактирование только автору
        return obj.user == request.user


class IsHashtagCreatorOrReadOnly(permissions.BasePermission):
    """Только создатель хэштега может удалять (общие может только админ)"""
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Удаление
        if request.method == 'DELETE':
            # Общие хэштеги (creator=null) удалять может только админ
            if obj.creator is None:
                return request.user.is_staff
            return obj.creator == request.user
        # Редактирование только создателю
        if obj.creator is None:
            return request.user.is_staff
        return obj.creator == request.user


class IsBookOwnerAction(permissions.BasePermission):
    """Для кастомных actions, требует что пользователь - владелец книги"""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False

