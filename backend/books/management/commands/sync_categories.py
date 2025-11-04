"""
Management команда для синхронизации категорий из канонического JSON файла
Простая загрузка категорий с иерархией из categories_canonical.json
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from books.models import Category


class Command(BaseCommand):
    help = 'Синхронизирует категории из канонического JSON файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='categories_canonical.json',
            help='Имя JSON файла в books/data/ (по умолчанию: categories_canonical.json)',
        )

    def handle(self, *args, **options):
        file_name = options.get('file', 'categories_canonical.json')
        json_path = Path(__file__).resolve().parent.parent.parent / 'data' / file_name
        
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
        
        self.stdout.write(f'📖 Загружено {len(categories_data)} категорий из канонического JSON')
        
        created_count = 0
        updated_count = 0
        
        # Словарь для хранения всех категорий по коду
        all_categories = {}
        
        with transaction.atomic():
            # Проход 1: Создаем/обновляем все категории (сначала родительские, потом подкатегории)
            categories_to_process = []
            
            # Сортируем: сначала родительские (parent=null), потом подкатегории
            for cat_data in categories_data:
                parent_code = cat_data.get('parent')
                if parent_code is None:
                    categories_to_process.insert(0, cat_data)  # В начало
                else:
                    categories_to_process.append(cat_data)  # В конец
            
            for cat_data in categories_to_process:
                code = cat_data['code']
                name = cat_data['name']
                slug = cat_data.get('slug', '')
                if not slug:
                    slug = slugify(name) or code
                icon = cat_data.get('icon', '📚')
                order = cat_data.get('order', 0)
                
                # Пытаемся найти по коду
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
                
                # Сохраняем для установки parent_category во втором проходе
                all_categories[code] = category
                
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Создана: {code} - {name}'))
                else:
                    updated_count += 1
                    if updated_count <= 10:  # Показываем только первые 10
                        self.stdout.write(f'🔄 Обновлена: {code} - {name}')
            
            # Проход 2: Устанавливаем parent_category для подкатегорий
            linked_count = 0
            for cat_data in categories_data:
                parent_code = cat_data.get('parent')
                if parent_code:
                    category = all_categories[cat_data['code']]
                    parent_category = all_categories.get(parent_code)
                    
                    if parent_category:
                        if category.parent_category != parent_category:
                            category.parent_category = parent_category
                            category.save()
                            linked_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️  Родительская категория с кодом "{parent_code}" не найдена для "{category.name}"'
                        ))
            
            if linked_count > 0:
                self.stdout.write(f'🔗 Установлено связей parent_category: {linked_count}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n📊 Итого: создано {created_count}, обновлено {updated_count} категорий'
        ))

