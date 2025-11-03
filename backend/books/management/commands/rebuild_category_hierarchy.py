"""
Команда для перестройки иерархии категорий на основе двоеточий в названиях

Эта команда:
1. Находит все категории с двоеточием в названии
2. Определяет родительскую категорию (часть до двоеточия)
3. Создает или находит родительскую категорию
4. Создает подкатегорию (часть после двоеточия)
5. Связывает их через parent_category

Пример:
  "Антикварные: Оригиналы..." -> Родитель: "Антикварные", Подкатегория: "Оригиналы..."
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from books.models import Category
from collections import defaultdict


class Command(BaseCommand):
    help = 'Перестраивает иерархию категорий на основе двоеточий в названиях'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без реальных изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ПРОВЕРКИ - изменения не будут сохранены'))
        
        # Находим все категории с двоеточием
        categories_with_colon = Category.objects.filter(name__contains=':')
        
        self.stdout.write(f'Найдено {categories_with_colon.count()} категорий с двоеточием')
        
        # Группируем по родительским категориям
        parent_groups = defaultdict(list)
        # Словарь для нормализации имен (объединение вариантов написания)
        parent_name_map = {}
        
        for category in categories_with_colon:
            if ':' in category.name:
                parts = category.name.split(':', 1)
                parent_name = parts[0].strip()
                subcategory_name = parts[1].strip()
                
                # Нормализуем имя родителя (исправляем опечатки и варианты написания)
                normalized_name = parent_name
                
                # Словарь для объединения похожих названий
                name_normalizations = {
                    'Детская лит-ра': 'Детская литература',
                    'Детская лит-ра:': 'Детская литература',
                }
                
                # Проверяем словарь нормализаций
                if parent_name in name_normalizations:
                    normalized_name = name_normalizations[parent_name]
                elif len(parent_name) > 1:
                    # Проверяем, есть ли уже существующая родительская категория с похожим именем
                    # (различается только последним символом - латинская vs кириллическая буква)
                    last_char = parent_name[-1]
                    alternative_names = []
                    
                    # Если последняя буква похожа на латинскую "o", пробуем кириллическую "о"
                    if last_char in ['o', 'O']:
                        alternative_names.append(parent_name[:-1] + 'о')
                        alternative_names.append(parent_name[:-1] + 'О')
                    # Если последняя буква похожа на кириллическую "о", пробуем латинскую "o"
                    elif last_char in ['о', 'О']:
                        alternative_names.append(parent_name[:-1] + 'o')
                        alternative_names.append(parent_name[:-1] + 'O')
                    
                    # Проверяем, есть ли уже родительская категория с таким именем
                    for alt_name in alternative_names:
                        existing = Category.objects.filter(
                            name=alt_name,
                            parent_category__isnull=True
                        ).first()
                        if existing:
                            normalized_name = alt_name
                            break
                
                # Сохраняем маппинг для последующего использования
                if parent_name != normalized_name:
                    parent_name_map[parent_name] = normalized_name
                    self.stdout.write(self.style.WARNING(f'  Нормализовано имя родителя: "{parent_name}" -> "{normalized_name}"'))
                
                parent_groups[normalized_name].append({
                    'category': category,
                    'subcategory_name': subcategory_name
                })
        
        self.stdout.write(f'Найдено {len(parent_groups)} уникальных родительских категорий')
        
        created_parents = 0
        updated_categories = 0
        
        with transaction.atomic():
            for parent_name, subcategories in parent_groups.items():
                # Создаем или находим родительскую категорию
                # Сначала пробуем найти по точному совпадению имени (без parent_category)
                parent_category = None
                
                # Ищем существующую категорию по точному имени
                existing_parent = Category.objects.filter(
                    name=parent_name,
                    parent_category__isnull=True
                ).first()
                
                if existing_parent:
                    parent_category = existing_parent
                    self.stdout.write(f'  Найдена родительская категория по имени: "{parent_name}" (ID: {parent_category.id})')
                else:
                    # Если не найдено по имени, пробуем по slug (но только если slug не пустой)
                    parent_slug = slugify(parent_name)
                    if parent_slug:  # Проверяем, что slug не пустой
                        try:
                            found_by_slug = Category.objects.get(
                                slug=parent_slug,
                                parent_category__isnull=True
                            )
                            # Дополнительная проверка: имя должно совпадать или быть похожим
                            if found_by_slug.name == parent_name:
                                parent_category = found_by_slug
                                self.stdout.write(f'  Найдена родительская категория по slug: "{parent_name}" (ID: {parent_category.id})')
                            else:
                                # Slug совпадает, но имя не совпадает - не используем эту категорию
                                parent_category = None
                                self.stdout.write(self.style.WARNING(f'  Категория с slug "{parent_slug}" найдена, но имя не совпадает ("{found_by_slug.name}" != "{parent_name}")'))
                        except Category.DoesNotExist:
                            parent_category = None
                    else:
                        parent_category = None
                    
                    if not parent_category:
                        # Создаем новую родительскую категорию
                        # Нужно сгенерировать уникальный code и slug
                        base_code = slugify(parent_name)[:15] or f"parent-{parent_name[:10]}"
                        code = base_code
                        counter = 1
                        while Category.objects.filter(code=code).exists():
                            code = f"{base_code}{counter}"
                            counter += 1
                        
                        # Убеждаемся что slug не пустой
                        if not parent_slug:
                            parent_slug = slugify(parent_name) or f"parent-{parent_name[:10]}"
                        # Проверяем уникальность slug
                        original_slug = parent_slug
                        slug_counter = 1
                        while Category.objects.filter(slug=parent_slug).exists():
                            parent_slug = f"{original_slug}-{slug_counter}"
                            slug_counter += 1
                        
                        if not dry_run:
                            parent_category = Category.objects.create(
                                name=parent_name,
                                slug=parent_slug,
                                code=code,
                                icon='📚',
                                order=0
                            )
                            created_parents += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Создана родительская категория: "{parent_name}" (ID: {parent_category.id})'))
                        else:
                            self.stdout.write(self.style.WARNING(f'  [DRY-RUN] Будет создана родительская категория: "{parent_name}"'))
                            # Создаем фиктивный объект для dry-run
                            parent_category = type('obj', (object,), {'id': 'NEW', 'name': parent_name})()
                
                # Обновляем подкатегории
                for item in subcategories:
                    category = item['category']
                    subcategory_name = item['subcategory_name']
                    
                    # Обновляем название подкатегории (убираем родительскую часть)
                    if category.name != subcategory_name:
                        if not dry_run:
                            category.name = subcategory_name
                            category.slug = slugify(subcategory_name)
                            # Проверяем уникальность slug
                            original_slug = category.slug
                            counter = 1
                            while Category.objects.filter(slug=category.slug).exclude(id=category.id).exists():
                                category.slug = f"{original_slug}-{counter}"
                                counter += 1
                        
                        self.stdout.write(f'    Обновлено название: "{category.name}" -> "{subcategory_name}"')
                    
                    # Устанавливаем parent_category
                    if category.parent_category != parent_category:
                        if not dry_run:
                            category.parent_category = parent_category
                            category.save()
                            updated_categories += 1
                            self.stdout.write(self.style.SUCCESS(f'    ✓ Связана подкатегория: "{subcategory_name}" с родителем "{parent_name}"'))
                        else:
                            self.stdout.write(self.style.WARNING(f'    [DRY-RUN] Будет связана: "{subcategory_name}" с родителем "{parent_name}"'))
                    else:
                        self.stdout.write(f'    Подкатегория "{subcategory_name}" уже связана с родителем')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\nРЕЖИМ ПРОВЕРКИ - откатываем транзакцию'))
                raise Exception('Dry run - rollback')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Готово!'))
        self.stdout.write(f'  Создано родительских категорий: {created_parents}')
        self.stdout.write(f'  Обновлено подкатегорий: {updated_categories}')

