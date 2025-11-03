"""
Экспорт всех ViewSets для обратной совместимости
"""
from .categories import CategoryViewSet
from .authors import AuthorViewSet
from .publishers import PublisherViewSet
from .books import BookViewSet
from .book_images import BookImageViewSet
from .book_electronic import BookElectronicViewSet
from .book_pages import BookPageViewSet
from .users import UserProfileViewSet
from .libraries import LibraryViewSet
from .hashtags import HashtagViewSet
from .reviews import BookReviewViewSet

__all__ = [
    'CategoryViewSet',
    'AuthorViewSet',
    'PublisherViewSet',
    'BookViewSet',
    'BookImageViewSet',
    'BookElectronicViewSet',
    'BookPageViewSet',
    'UserProfileViewSet',
    'LibraryViewSet',
    'HashtagViewSet',
    'BookReviewViewSet',
]

