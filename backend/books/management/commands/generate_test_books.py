"""
Management команда для генерации тестовых книг
"""
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# Добавляем путь к фабрике в sys.path
base_dir = Path(__file__).parent.parent.parent.parent.parent
test_factory_dir = base_dir / 'test_data_factory'
sys.path.insert(0, str(base_dir))

from django.contrib.auth import get_user_model
from books.models import Library

from test_data_factory.factory import TestDataFactory

User = get_user_model()


class Command(BaseCommand):
    help = 'Генерирует тестовые книги для всех категорий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count-per-category',
            type=int,
            default=3,
            help='Количество книг на категорию (по умолчанию: 3)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя (если не указан, используется первый или создается тестовый)',
        )
        parser.add_argument(
            '--library-id',
            type=int,
            help='ID библиотеки (если не указан, используется библиотека пользователя или создается)',
        )
        parser.add_argument(
            '--create-users',
            type=int,
            default=4,
            help='Создать указанное количество пользователей с библиотеками (по умолчанию: 4)',
        )
        parser.add_argument(
            '--libraries-per-user',
            type=int,
            default=2,
            help='Количество библиотек на пользователя (по умолчанию: 2)',
        )
        parser.add_argument(
            '--distribute-books',
            action='store_true',
            help='Распределять книги равномерно между всеми библиотеками',
        )

    def handle(self, *args, **options):
        count_per_category = options['count_per_category']
        user_id = options.get('user_id')
        library_id = options.get('library_id')
        create_users = options.get('create_users', 4)
        libraries_per_user = options.get('libraries_per_user', 2)
        distribute_books = options.get('distribute_books', False)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🏭 Генерация тестовых книг...\n'
                f'   Книг на категорию: {count_per_category}\n'
            )
        )
        
        try:
            # Инициализируем фабрику
            factory = TestDataFactory(base_dir=base_dir)
            
            # Если не указаны конкретные user_id и library_id, создаем несколько пользователей
            if not user_id and not library_id and (create_users > 0 or distribute_books):
                factory.create_multiple_users_and_libraries(
                    num_users=create_users,
                    libraries_per_user=libraries_per_user
                )
                distribute_books = True  # Автоматически включаем распределение
            else:
                # Настраиваем одного пользователя и библиотеку (старый режим)
                factory.ensure_user_and_library(user_id=user_id, library_id=library_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'👤 Пользователь: {factory.user.username}\n'
                        f'📚 Библиотека: {factory.library.name}\n'
                    )
                )
            
            # Загружаем данные
            factory.load_data()
            
            # Создаем авторов и издательства в БД
            factory.ensure_authors_and_publishers_in_db()
            
            # Генерируем книги
            created_count = factory.generate_books_for_all_categories(
                books_per_category=count_per_category,
                distribute_to_all_libraries=distribute_books
            )
            
            # Очищаем временные файлы
            factory.cleanup()
            
            # Показываем статистику по библиотекам
            if distribute_books and factory.all_libraries:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n📊 Статистика по библиотекам:\n'
                    )
                )
                for library in factory.all_libraries:
                    books_count = library.books.count()
                    self.stdout.write(
                        f'   {library.name} ({library.owner.username}): {books_count} книг\n'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✨ Готово! Создано {created_count} книг.\n'
                    f'💡 После тестирования книги можно удалить через Django Admin или API.'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Ошибка при генерации: {e}')

