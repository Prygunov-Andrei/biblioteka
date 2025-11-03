"""
Сервис для передачи книг между библиотеками и пользователями
"""
from django.contrib.auth import get_user_model
from ..models import Book, Library
from ..exceptions import TransferError

User = get_user_model()


class TransferService:
    """Сервис для передачи книг между библиотеками и пользователями"""
    
    @staticmethod
    def transfer_to_library(book: Book, library: Library) -> Book:
        """Передает книгу в библиотеку"""
        if not library:
            raise TransferError("Библиотека не указана")
        
        book.library = library
        book.save(update_fields=['library', 'updated_at'])
        return book
    
    @staticmethod
    def transfer_to_user(book: Book, new_owner: User) -> Book:
        """Передает книгу другому пользователю (меняет owner)"""
        if not new_owner:
            raise TransferError("Пользователь не указан")
        
        book.owner = new_owner
        book.save(update_fields=['owner', 'updated_at'])
        return book
    
    @staticmethod
    def transfer_book(
        book: Book,
        library_id: int = None,
        user_id: int = None
    ) -> tuple[Book, str]:
        """
        Передает книгу в библиотеку или пользователю.
        Returns: (book, message)
        """
        if library_id:
            try:
                library = Library.objects.get(id=library_id)
                TransferService.transfer_to_library(book, library)
                return book, f'Книга передана в библиотеку "{library.name}"'
            except Library.DoesNotExist:
                raise TransferError("Библиотека не найдена")
        
        elif user_id:
            try:
                new_owner = User.objects.get(id=user_id)
                TransferService.transfer_to_user(book, new_owner)
                return book, f'Книга передана пользователю {new_owner.username}'
            except User.DoesNotExist:
                raise TransferError("Пользователь не найден")
        
        raise TransferError("Необходимо указать library или user")

