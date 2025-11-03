"""
Management команда для синхронизации категорий из JSON файла
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from books.models import Category


class Command(BaseCommand):
    help = 'Синхронизирует категории из books/data/categories.json в базу данных'

    def handle(self, *args, **options):
        # Путь к JSON файлу
        json_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'categories.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'Файл {json_path} не найден!'))
            return
        
        # Загружаем JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        categories_data = data.get('categories', [])
        
        if not categories_data:
            self.stdout.write(self.style.ERROR('Категории не найдены в JSON файле!'))
            return
        
        self.stdout.write(f'📖 Загружено {len(categories_data)} категорий из JSON')
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for cat_data in categories_data:
                code = cat_data['code']
                name = cat_data['name']
                slug = cat_data['slug']
                icon = cat_data.get('icon', '📚')
                order = cat_data.get('order', 0)
                
                # Пытаемся найти по коду или slug
                try:
                    category = Category.objects.get(code=code)
                    # Обновляем существующую
                    category.name = name
                    category.slug = slug
                    category.icon = icon
                    category.order = order
                    category.save()
                    created = False
                except Category.DoesNotExist:
                    # Создаем новую
                    category = Category.objects.create(
                        code=code,
                        name=name,
                        slug=slug,
                        icon=icon,
                        order=order,
                    )
                    created = True
                
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Создана: {code} - {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'🔄 Обновлена: {code} - {name}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n📊 Итого: создано {created_count}, обновлено {updated_count} категорий'
        ))

