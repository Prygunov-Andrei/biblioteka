"""
Главная фабрика тестовых данных
"""
import os
import sys
import random
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files import File

from books.models import Category, Author, Publisher, Language, Book, BookAuthor, BookImage, BookReview, Library, Hashtag, BookPage

# Добавляем путь к фабрике для импорта
factory_path = Path(__file__).parent
if str(factory_path) not in sys.path:
    sys.path.insert(0, str(factory_path))

from test_data_factory.generators.publishers_loader import load_publishers_from_json
from test_data_factory.generators.authors_loader import load_authors_from_json
from test_data_factory.generators.book_generator import BookGenerator
from test_data_factory.generators.image_generator import generate_book_images, generate_book_pages

User = get_user_model()


class TestDataFactory:
    """Фабрика для генерации тестовых данных"""
    
    def __init__(self, base_dir: Path = None):
        """
        Инициализация фабрики
        
        Args:
            base_dir: Базовая директория проекта (для поиска файлов)
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = base_dir
        
        self.output_images_dir = self.base_dir / 'test_data_factory' / 'generated_images'
        self.authors_data = None
        self.publishers_data = None
        self.categories = None
        self.authors = []
        self.publishers = []
        self.languages = []
        self.hashtags = []
        self.user = None
        self.library = None
        self.all_libraries = []  # Список всех библиотек для распределения книг
        
        # Список хэштегов для использования в книгах
        self.HASHTAGS_LIST = [
            'классика',
            'фантастика',
            'детектив',
            'роман',
            'история',
            'биография',
            'поэзия',
            'драма',
            'комедия',
            'триллер',
            'ужасы',
            'приключения',
            'философия',
            'наука',
            'психология',
            'путешествия',
            'любовный_роман',
            'военный_роман',
            'современная_литература',
            'антиквариат',
        ]
    
    def ensure_user_and_library(self, user_id: Optional[int] = None, library_id: Optional[int] = None):
        """
        Создает или получает пользователя и библиотеку
        
        Args:
            user_id: ID пользователя (если указан, используется он)
            library_id: ID библиотеки (если указан, используется она)
        """
        # Получаем или создаем пользователя
        if user_id:
            self.user = User.objects.get(id=user_id)
        else:
            # Ищем первого пользователя или создаем тестового
            self.user = User.objects.first()
            if not self.user:
                self.user = User.objects.create_user(
                    username='test_user',
                    email='test@example.com',
                    password='testpass123'
                )
        
        # Получаем или создаем библиотеку
        if library_id:
            self.library = Library.objects.get(id=library_id)
        else:
            # Ищем библиотеку пользователя или создаем
            self.library = Library.objects.filter(owner=self.user).first()
            if not self.library:
                self.library = Library.objects.create(
                    owner=self.user,
                    name='Тестовая библиотека',
                    address='Адрес библиотеки',
                    city='Москва',
                    country='Россия',
                    description='Библиотека для тестирования'
                )
    
    def create_multiple_users_and_libraries(self, num_users: int = 4, libraries_per_user: int = 2):
        """
        Создает несколько пользователей с библиотеками
        
        Args:
            num_users: Количество пользователей для создания (включая уже существующих)
            libraries_per_user: Количество библиотек на пользователя
        """
        print(f"\n👥 Создание пользователей и библиотек...")
        print(f"   Пользователей: {num_users}, библиотек на пользователя: {libraries_per_user}\n")
        
        # Получаем существующих пользователей
        existing_users = list(User.objects.all())
        existing_count = len(existing_users)
        
        # Создаем недостающих пользователей
        users_to_create = num_users - existing_count
        if users_to_create > 0:
            print(f"  Создание {users_to_create} новых пользователей...")
            for i in range(users_to_create):
                user_num = existing_count + i + 1
                username = f'user_{user_num}'
                email = f'user{user_num}@example.com'
                
                # Проверяем, что пользователь не существует
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='testpass123'
                    )
                    existing_users.append(user)
                    print(f"    ✓ Создан пользователь: {username}")
                else:
                    user = User.objects.get(username=username)
                    existing_users.append(user)
                    print(f"    ✓ Использован существующий пользователь: {username}")
        
        # Ограничиваем список пользователей до num_users
        users = existing_users[:num_users]
        
        # Создаем библиотеки для каждого пользователя
        all_libraries = []
        cities = ['Москва', 'Санкт-Петербург', 'Екатеринбург', 'Новосибирск', 'Казань', 'Нижний Новгород']
        addresses = [
            'ул. Ленина, д. 10',
            'пр. Мира, д. 25',
            'ул. Пушкина, д. 5',
            'ул. Гагарина, д. 15',
            'пр. Победы, д. 30',
            'ул. Советская, д. 8',
        ]
        
        print(f"\n  📚 Создание библиотек...")
        for user_index, user in enumerate(users):
            user_libraries = Library.objects.filter(owner=user)
            
            # Создаем недостающие библиотеки
            libraries_to_create = libraries_per_user - user_libraries.count()
            if libraries_to_create > 0:
                for lib_index in range(libraries_to_create):
                    city = cities[user_index % len(cities)]
                    address = addresses[(user_index * libraries_per_user + lib_index) % len(addresses)]
                    
                    library = Library.objects.create(
                        owner=user,
                        name=f'Библиотека {user.username} #{lib_index + 1}',
                        address=address,
                        city=city,
                        country='Россия',
                        description=f'Библиотека пользователя {user.username}'
                    )
                    all_libraries.append(library)
                    print(f"    ✓ Создана библиотека: {library.name} (владелец: {user.username})")
            else:
                # Добавляем существующие библиотеки
                all_libraries.extend(list(user_libraries))
                print(f"    ✓ Использованы существующие библиотеки пользователя {user.username}")
        
        self.all_libraries = all_libraries
        print(f"\n  ✅ Итого библиотек: {len(all_libraries)}")
        
        # Устанавливаем первого пользователя как текущего (для совместимости)
        if users:
            self.user = users[0]
            self.library = Library.objects.filter(owner=self.user).first()
    
    def load_data(self):
        """Загружает данные из JSON файлов"""
        print("📚 Загрузка данных из JSON...")
        self.authors_data = load_authors_from_json()
        self.publishers_data = load_publishers_from_json()
        print(f"  ✓ Загружено авторов: {len(self.authors_data)}")
        print(f"  ✓ Загружено издательств: {len(self.publishers_data)}")
        
        # Загружаем категории
        # Загружаем все категории, включая подкатегории
        # Фабрика будет генерировать книги как для родительских, так и для подкатегорий
        self.categories = list(Category.objects.all().order_by('order', 'name'))
        print(f"  ✓ Загружено категорий: {len(self.categories)}")
        
        # Создаем хэштеги в БД, если их нет
        self._ensure_hashtags_in_db()
        
        # Создаем языки в БД, если их нет
        self._ensure_languages_in_db()
    
    def ensure_authors_and_publishers_in_db(self) -> tuple[list, list]:
        """
        Создает авторов и издательства в БД, если их нет
        
        Returns:
            (authors, publishers) - списки созданных объектов
        """
        if not self.authors_data:
            self.load_data()
        
        print("\n📝 Проверка авторов в БД...")
        created_authors = 0
        existing_authors = 0
        
        for author_data in self.authors_data:
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
            self.authors.append(author)
        
        print(f"  ✓ Создано авторов: {created_authors}")
        print(f"  ✓ Уже существует: {existing_authors}")
        
        print("\n📝 Проверка издательств в БД...")
        created_publishers = 0
        existing_publishers = 0
        
        for publisher_data in self.publishers_data:
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
            self.publishers.append(publisher)
        
        print(f"  ✓ Создано издательств: {created_publishers}")
        print(f"  ✓ Уже существует: {existing_publishers}")
        
        return self.authors, self.publishers
    
    def _ensure_hashtags_in_db(self):
        """Создает хэштеги в БД, если их нет"""
        if not self.user:
            raise ValueError("Необходимо сначала создать пользователя (ensure_user_and_library)")
        
        print("\n🏷️  Проверка хэштегов в БД...")
        created_hashtags = 0
        existing_hashtags = 0
        
        for hashtag_name in self.HASHTAGS_LIST:
            # Создаем slug из названия
            from django.utils.text import slugify
            base_slug = slugify(hashtag_name)
            
            # Убеждаемся что slug не пустой
            if not base_slug:
                base_slug = f"hashtag-{hashtag_name[:10]}"
                base_slug = slugify(base_slug)
            
            # Проверяем уникальность slug и при необходимости добавляем суффикс
            slug = base_slug
            counter = 1
            while Hashtag.objects.filter(slug=slug).exclude(name=hashtag_name, creator=self.user).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Проверяем уникальность по name и creator
            hashtag, created = Hashtag.objects.get_or_create(
                name=hashtag_name,
                creator=self.user,
                defaults={
                    'slug': slug,
                }
            )
            
            # Если хэштег уже существует, обновляем slug если он пустой или дублируется
            if not created and (not hashtag.slug or Hashtag.objects.filter(slug=hashtag.slug).exclude(id=hashtag.id).exists()):
                if not hashtag.slug or Hashtag.objects.filter(slug=hashtag.slug).exclude(id=hashtag.id).exists():
                    # Ищем уникальный slug
                    new_slug = base_slug
                    counter = 1
                    while Hashtag.objects.filter(slug=new_slug).exclude(id=hashtag.id).exists():
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1
                    hashtag.slug = new_slug
                    hashtag.save()
            
            if created:
                created_hashtags += 1
            else:
                existing_hashtags += 1
            self.hashtags.append(hashtag)
        
        print(f"  ✓ Создано хэштегов: {created_hashtags}")
        print(f"  ✓ Уже существует: {existing_hashtags}")
    
    def _ensure_languages_in_db(self):
        """Создает языки в БД, если их нет"""
        print("\n🌍 Проверка языков в БД...")
        
        # Список основных языков
        languages_data = [
            {'name': 'Русский', 'code': 'ru'},
            {'name': 'Английский', 'code': 'en'},
            {'name': 'Немецкий', 'code': 'de'},
            {'name': 'Французский', 'code': 'fr'},
            {'name': 'Испанский', 'code': 'es'},
            {'name': 'Итальянский', 'code': 'it'},
            {'name': 'Польский', 'code': 'pl'},
            {'name': 'Чешский', 'code': 'cs'},
            {'name': 'Украинский', 'code': 'uk'},
            {'name': 'Белорусский', 'code': 'be'},
            {'name': 'Латинский', 'code': 'la'},
            {'name': 'Древнегреческий', 'code': 'grc'},
            {'name': 'Японский', 'code': 'ja'},
            {'name': 'Китайский', 'code': 'zh'},
            {'name': 'Арабский', 'code': 'ar'},
        ]
        
        created_languages = 0
        existing_languages = 0
        
        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                name=lang_data['name'],
                defaults={
                    'code': lang_data['code'],
                }
            )
            if created:
                created_languages += 1
            else:
                existing_languages += 1
            self.languages.append(language)
        
        print(f"  ✓ Создано языков: {created_languages}")
        print(f"  ✓ Уже существует: {existing_languages}")
    
    def _distribute_resources(self, total_books: int) -> tuple[list, list]:
        """
        Распределяет авторов и издательства так, чтобы все были использованы
        
        Args:
            total_books: Общее количество книг для генерации
        
        Returns:
            (authors_list, publishers_list) - списки авторов и издательств для каждой книги
        """
        authors_list = []
        publishers_list = []
        
        # Перемешиваем для случайности
        authors_pool = self.authors.copy()
        publishers_pool = self.publishers.copy()
        random.shuffle(authors_pool)
        random.shuffle(publishers_pool)
        
        # Отслеживаем использованные
        used_authors = set()
        used_publishers = set()
        
        # Сначала гарантируем использование ВСЕХ авторов хотя бы один раз
        # Создаем список для первых N книг с уникальными авторами
        author_index = 0
        publishers_index = 0
        
        # Проходим по всем авторам и создаем для каждого хотя бы одну книгу
        for i in range(len(authors_pool)):
            if i >= total_books:
                break  # Если авторов больше чем книг, останавливаемся
                
            # Выбираем авторов (1-3 автора на книгу, но приоритет неиспользованным)
            num_authors = random.randint(1, min(3, len(authors_pool)))
            book_authors = []
            
            # Обязательно добавляем текущего автора (если он еще не использован)
            if author_index < len(authors_pool):
                current_author = authors_pool[author_index]
                if current_author.id not in used_authors:
                    book_authors.append(current_author)
                    used_authors.add(current_author.id)
                author_index += 1
            
            # Если нужно больше авторов, добавляем неиспользованных
            unused_authors = [a for a in authors_pool if a.id not in used_authors]
            while len(book_authors) < num_authors and unused_authors:
                author = random.choice(unused_authors)
                book_authors.append(author)
                used_authors.add(author.id)
                unused_authors.remove(author)
            
            # Если все еще не хватило, добавляем любых случайных
            while len(book_authors) < num_authors:
                author = random.choice(authors_pool)
                if author not in book_authors:
                    book_authors.append(author)
            
            authors_list.append(book_authors)
            
            # Выбираем издательство
            if publishers_index < len(publishers_pool):
                publisher = publishers_pool[publishers_index]
                publishers_index += 1
                used_publishers.add(publisher.id)
            else:
                # Все использованы, берем случайное
                publisher = random.choice(publishers_pool)
            
            publishers_list.append(publisher)
        
        # Если книг больше чем авторов, заполняем остальные случайными авторами
        while len(authors_list) < total_books:
            num_authors = random.randint(1, min(3, len(authors_pool)))
            book_authors = random.sample(authors_pool, min(num_authors, len(authors_pool)))
            authors_list.append(book_authors)
            
            # Издательство
            if publishers_index < len(publishers_pool):
                publisher = publishers_pool[publishers_index]
                publishers_index += 1
            else:
                publisher = random.choice(publishers_pool)
            publishers_list.append(publisher)
        
        print(f"  ✓ Всего авторов использовано: {len(used_authors)} из {len(authors_pool)}")
        print(f"  ✓ Всего издательств использовано: {len(used_publishers)} из {len(publishers_pool)}")
        
        return authors_list, publishers_list
    
    def generate_books_for_all_categories(self, books_per_category: int = 3, distribute_to_all_libraries: bool = True):
        """
        Генерирует книги для всех категорий
        
        Args:
            books_per_category: Количество книг на категорию
            distribute_to_all_libraries: Если True, распределяет книги равномерно между всеми библиотеками
        """
        if not self.categories:
            self.load_data()
        
        # Проверяем наличие библиотек
        if distribute_to_all_libraries and self.all_libraries:
            libraries_to_use = self.all_libraries
            print(f"\n📚 Распределение книг между {len(libraries_to_use)} библиотеками...")
        else:
            if not self.user or not self.library:
                raise ValueError("Необходимо вызвать ensure_user_and_library() перед генерацией")
            libraries_to_use = [self.library]
        
        if not self.authors or not self.publishers:
            self.ensure_authors_and_publishers_in_db()
        
        # Убеждаемся, что хэштеги созданы для всех пользователей
        if not self.hashtags:
            # Создаем хэштеги для всех уникальных пользователей
            unique_users = list(set([lib.owner for lib in libraries_to_use]))
            first_user = unique_users[0] if unique_users else None
            
            # Временно устанавливаем пользователя для создания хэштегов
            old_user = self.user
            self.user = first_user if first_user else self.user
            self._ensure_hashtags_in_db()
            # Восстанавливаем старого пользователя
            self.user = old_user if old_user else first_user
        
        total_books = len(self.categories) * books_per_category
        print(f"\n📖 Генерация {total_books} книг для {len(self.categories)} категорий...")
        print(f"   ({books_per_category} книг на категорию)")
        if distribute_to_all_libraries:
            books_per_library = total_books / len(libraries_to_use) if libraries_to_use else 0
            print(f"   (~{books_per_library:.1f} книг на библиотеку)\n")
        else:
            print()
        
        # Распределяем ресурсы
        authors_list, publishers_list = self._distribute_resources(total_books)
        
        # Распределяем библиотеки для каждой книги
        library_index = 0
        book_index = 0
        created_count = 0
        
        for category in self.categories:
            print(f"  📚 {category.name}...")
            
            for _ in range(books_per_category):
                # Получаем назначенных авторов и издательство
                book_authors = authors_list[book_index]
                publisher = publishers_list[book_index]
                
                # Выбираем библиотеку (равномерное распределение)
                selected_library = libraries_to_use[library_index % len(libraries_to_use)]
                library_owner = selected_library.owner
                library_index += 1
                book_index += 1
                
                try:
                    with transaction.atomic():
                        # Генерируем данные книги
                        book_data = BookGenerator.generate_book_data(
                            category=category,
                            authors=book_authors,
                            publisher=publisher,
                            library=selected_library,
                            owner=library_owner,
                            category_name=category.name,
                            languages=self.languages
                        )
                        
                        # Создаем книгу
                        book = Book.objects.create(**book_data)
                        created_count += 1
                        
                        # Добавляем авторов
                        for order, author in enumerate(book_authors, start=1):
                            BookAuthor.objects.create(
                                book=book,
                                author=author,
                                order=order
                            )
                        
                        # Генерируем изображения
                        try:
                            image_paths = generate_book_images(
                                title=book.title,
                                count=3,
                                output_dir=self.output_images_dir
                            )
                            
                            # Создаем записи BookImage
                            for order, img_path in enumerate(image_paths, start=1):
                                with open(img_path, 'rb') as img_file:
                                    book_image = BookImage(
                                        book=book,
                                        order=order
                                    )
                                    book_image.image.save(
                                        img_path.name,
                                        File(img_file),
                                        save=True
                                    )
                            
                        except Exception as e:
                            print(f"    ⚠️  Ошибка генерации изображений: {e}")
                        
                        # Генерируем страницы книги (от 1 до 5 страниц)
                        try:
                            num_pages = random.randint(1, 5)
                            page_paths = generate_book_pages(
                                title=book.title,
                                count=num_pages,
                                output_dir=self.output_images_dir
                            )
                            
                            # Создаем записи BookPage
                            first_page = None
                            for page_number, page_path in enumerate(page_paths, start=1):
                                with open(page_path, 'rb') as page_file:
                                    book_page = BookPage(
                                        book=book,
                                        page_number=page_number,
                                        processing_status='pending',
                                        width=1200,  # Стандартная ширина страницы
                                        height=1600  # Стандартная высота страницы
                                    )
                                    book_page.original_image.save(
                                        page_path.name,
                                        File(page_file),
                                        save=True
                                    )
                                    # Сохраняем первую страницу как обложку
                                    if page_number == 1:
                                        first_page = book_page
                            
                            # Назначаем первую страницу как обложку
                            if first_page:
                                book.cover_page = first_page
                                book.save(update_fields=['cover_page'])
                            
                        except Exception as e:
                            print(f"    ⚠️  Ошибка генерации страниц: {e}")
                        
                        # Добавляем хэштеги к половине книг (50% вероятность)
                        if random.random() < 0.5 and self.hashtags:
                            try:
                                # Количество хэштегов для этой книги (от 1 до 20, но не больше доступных)
                                num_hashtags = random.randint(1, min(20, len(self.hashtags)))
                                
                                # Выбираем случайные хэштеги
                                selected_hashtags = random.sample(self.hashtags, num_hashtags)
                                
                                # Добавляем хэштеги к книге
                                for hashtag in selected_hashtags:
                                    book.hashtags.add(hashtag)
                                
                            except Exception as e:
                                print(f"    ⚠️  Ошибка добавления хэштегов: {e}")
                        
                        # Генерируем отзыв для части книг (40% вероятность)
                        if random.random() < 0.4:
                            try:
                                # Генерируем оценку (1-5)
                                rating = random.randint(1, 5)
                                
                                # Генерируем текст отзыва (70% вероятность)
                                review_text = ""
                                if random.random() < 0.7:
                                    review_texts = [
                                        "Отличная книга, рекомендую!",
                                        "Очень интересное произведение.",
                                        "Неожиданный поворот сюжета.",
                                        "Классика, которую стоит прочитать.",
                                        "Интересно, но не без недостатков.",
                                        "Прекрасное произведение, впечатлен.",
                                        "На любителя, но мне понравилось.",
                                        "Сложное, но стоящее чтение.",
                                        "Легко читается, рекомендую.",
                                        "Не самое лучшее произведение автора.",
                                    ]
                                    review_text = random.choice(review_texts)
                                
                                BookReview.objects.create(
                                    book=book,
                                    user=library_owner,
                                    rating=rating,
                                    review_text=review_text
                                )
                            except Exception as e:
                                print(f"    ⚠️  Ошибка создания отзыва: {e}")
                    
                except Exception as e:
                    print(f"    ❌ Ошибка создания книги: {e}")
                    continue
        
        print(f"\n✅ Создано книг: {created_count}")
        return created_count
    
    def cleanup(self):
        """Удаляет временные файлы"""
        import shutil
        if self.output_images_dir.exists():
            shutil.rmtree(self.output_images_dir, ignore_errors=True)
            print(f"\n🧹 Очистка: удалена директория {self.output_images_dir}")


if __name__ == '__main__':
    # Тест (требует настройки Django)
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    factory = TestDataFactory()
    factory.ensure_user_and_library()
    factory.load_data()
    factory.ensure_authors_and_publishers_in_db()
    factory.generate_books_for_all_categories(books_per_category=2)
    factory.cleanup()
