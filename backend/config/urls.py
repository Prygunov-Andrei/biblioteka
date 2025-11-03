"""
URL маршруты
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from books.views import (
    CategoryViewSet,
    AuthorViewSet,
    PublisherViewSet,
    BookViewSet,
    BookImageViewSet,
    BookElectronicViewSet,
    BookPageViewSet,
    UserProfileViewSet,
    LibraryViewSet,
    HashtagViewSet,
    BookReviewViewSet
)

# API Router
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'books', BookViewSet, basename='book')
router.register(r'book-images', BookImageViewSet, basename='book-image')
router.register(r'book-electronic', BookElectronicViewSet, basename='book-electronic')
router.register(r'book-pages', BookPageViewSet, basename='book-page')
router.register(r'user-profiles', UserProfileViewSet, basename='user-profile')
router.register(r'libraries', LibraryViewSet, basename='library')
router.register(r'hashtags', HashtagViewSet, basename='hashtag')
router.register(r'book-reviews', BookReviewViewSet, basename='book-review')

urlpatterns = [
    # JWT аутентификация
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
