"""
Кастомная аутентификация для опционального JWT токена
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class OptionalJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация, которая не возвращает ошибку при невалидном токене.
    
    Это позволяет публичным эндпоинтам (AllowAny) работать даже с невалидными токенами.
    Если токен валидный - пользователь будет авторизован.
    Если токен невалидный - запрос продолжится как анонимный.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, AuthenticationFailed) as e:
            # Невалидный токен - просто возвращаем None, не поднимаем исключение
            # Это позволит AllowAny permissions работать для публичных эндпоинтов
            # Логируем для отладки, но не поднимаем исключение
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f'Невалидный JWT токен проигнорирован для публичного эндпоинта: {str(e)}')
            return None
        except Exception as e:
            # Другие ошибки тоже игнорируем для публичных эндпоинтов
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f'Ошибка JWT аутентификации проигнорирована: {str(e)}')
            return None

