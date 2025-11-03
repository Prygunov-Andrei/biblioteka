"""
Проверка состояния схемы БД и создание отсутствующих таблиц.
Использовать только в крайних случаях, когда миграции не могут быть применены.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Проверяет и создает отсутствующие таблицы из миграции 0005_add_user_system'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Проверка таблиц из миграции 0005_add_user_system...')
            
            # Проверяем наличие таблиц
            tables_to_check = [
                'books_hashtag',
                'books_bookhashtag',
                'books_bookreview',
                'books_userprofile',
                'books_library',
            ]
            
            missing_tables = []
            for table in tables_to_check:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, [table])
                exists = cursor.fetchone()[0]
                if not exists:
                    missing_tables.append(table)
                    self.stdout.write(self.style.WARNING(f'  ❌ Отсутствует: {table}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Найдена: {table}'))
            
            if not missing_tables:
                self.stdout.write(self.style.SUCCESS('\n✅ Все таблицы существуют!'))
                return
            
            self.stdout.write(self.style.WARNING(f'\n⚠️  Найдено {len(missing_tables)} отсутствующих таблиц.'))
            self.stdout.write(self.style.ERROR(
                '\n⚠️  ВНИМАНИЕ: Это указывает на проблему с применением миграций.\n'
                'Рекомендуется:\n'
                '1. Проверить состояние миграций: python manage.py showmigrations\n'
                '2. Применить миграции: python manage.py migrate\n'
                '3. Если проблема сохраняется, проверьте логи миграций\n\n'
                'Автоматическое создание таблиц следует использовать только в крайних случаях.'
            ))
            
            if input('\nСоздать отсутствующие таблицы автоматически? (yes/no): ') != 'yes':
                self.stdout.write('Отменено.')
                return
            
            # Создаем отсутствующие таблицы
            if 'books_hashtag' in missing_tables:
                self.stdout.write('Создание books_hashtag...')
                cursor.execute("""
                    CREATE TABLE books_hashtag (
                        id BIGSERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        slug VARCHAR(100) NOT NULL UNIQUE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        creator_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
                    );
                    CREATE UNIQUE INDEX books_hashtag_name_creator_uniq ON books_hashtag(name, creator_id);
                """)
            
            if 'books_bookhashtag' in missing_tables:
                self.stdout.write('Создание books_bookhashtag...')
                cursor.execute("""
                    CREATE TABLE books_bookhashtag (
                        id BIGSERIAL PRIMARY KEY,
                        book_id BIGINT NOT NULL REFERENCES books_book(id) ON DELETE CASCADE,
                        hashtag_id BIGINT NOT NULL REFERENCES books_hashtag(id) ON DELETE CASCADE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        UNIQUE(book_id, hashtag_id)
                    );
                """)
            
            if 'books_bookreview' in missing_tables:
                self.stdout.write('Создание books_bookreview...')
                cursor.execute("""
                    CREATE TABLE books_bookreview (
                        id BIGSERIAL PRIMARY KEY,
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        review_text TEXT,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        book_id BIGINT NOT NULL REFERENCES books_book(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                        UNIQUE(book_id, user_id)
                    );
                """)
            
            self.stdout.write(self.style.SUCCESS('\n✅ Все отсутствующие таблицы созданы!'))
            self.stdout.write('⚠️  НЕ ЗАБУДЬТЕ: Отметьте миграцию как примененную:')
            self.stdout.write('   python manage.py migrate books 0005_add_user_system --fake')

