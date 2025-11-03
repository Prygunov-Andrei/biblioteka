"""
Кастомные исключения для операций с книгами
"""


class BookException(Exception):
    """Базовое исключение для операций с книгами"""
    pass


class HashtagLimitExceeded(BookException):
    """Превышен лимит хэштегов на книгу"""
    pass


class TransferError(BookException):
    """Ошибка передачи книги"""
    pass


class BookValidationError(BookException):
    """Ошибка валидации книги"""
    pass

