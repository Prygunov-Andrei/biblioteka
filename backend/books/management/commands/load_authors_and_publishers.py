"""
Management команда для загрузки авторов и издательств из JSON в БД
Используется при деплое для наполнения базы справочными данными
"""
import sys
from pathlib import Path

from django.core.management.base import BaseCommand

# Добавляем путь к фабрике в sys.path
base_dir = Path(__file__).parent.parent.parent.parent.parent
test_factory_dir = base_dir / 'test_data_factory'
sys.path.insert(0, str(base_dir))

from books.models import Author, Publisher
from test_data_factory.generators.publishers_loader import load_publishers_from_json
from test_data_factory.generators.authors_loader import load_authors_from_json


class Command(BaseCommand):
    help = 'Загружает авторов и издательства из JSON файлов в базу данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📚 Загрузка авторов и издательств...\n'))
        
        # Определяем путь к JSON файлам
        json_dir = base_dir / 'test_data_factory' / 'data'
        
        # Загружаем авторов
        self.stdout.write('📝 Загрузка авторов...')
        authors_data = load_authors_from_json()
        
        created_authors = 0
        existing_authors = 0
        
        for author_data in authors_data:
            author, created = Author.objects.get_or_create(
                full_name=author_data['full_name'],
                defaults={
                    'birth_year': author_data.get('birth_year'),
                    'death_year': author_data.get('death_year'),
                    'biography': author_data.get('biography', ''),
                }
            )
            if created:
                created_authors += 1
            else:
                existing_authors += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✅ Авторы: создано {created_authors}, уже существует {existing_authors}'
            )
        )
        
        # Загружаем издательства
        self.stdout.write('\n📝 Загрузка издательств...')
        publishers_data = load_publishers_from_json()
        
        created_publishers = 0
        existing_publishers = 0
        
        for publisher_data in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=publisher_data['name'],
                defaults={
                    'city': publisher_data.get('city', ''),
                    'website': publisher_data.get('website', ''),
                    'description': publisher_data.get('description', ''),
                }
            )
            if created:
                created_publishers += 1
            else:
                existing_publishers += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✅ Издательства: создано {created_publishers}, уже существует {existing_publishers}'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✨ Готово! Всего авторов в БД: {Author.objects.count()}, '
                f'издательств: {Publisher.objects.count()}'
            )
        )

