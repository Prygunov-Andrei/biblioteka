"""
Генератор данных книг
"""
import random
from decimal import Decimal
from typing import Optional

from .titles_generator import generate_book_title


# Варианты для разных полей
STATUS_CHOICES = ['none', 'reading', 'read', 'want_to_read', 'want_to_reread']
BINDING_CHOICES = ['paper', 'selfmade', 'cardboard', 'hard', 'fabric', 'owner', 'halfleather', 'composite', 'leather']
FORMAT_CHOICES = ['very_large', 'encyclopedic', 'increased', 'regular', 'reduced', 'miniature']
CONDITION_CHOICES = ['ideal', 'excellent', 'good', 'satisfactory', 'poor']

BINDING_COLORS = ['красный', 'синий', 'зеленый', 'коричневый', 'черный', 'бежевый', 'серый']
BINDING_QUALITIES = ['обычный', 'хороший', 'отличный', 'премиум']

CONDITION_DETAILS = [
    'Небольшие потертости на обложке',
    'Легкие загрязнения страниц',
    'Незначительные дефекты переплета',
    'Хорошее состояние, минимальные следы использования',
    'Отличное состояние, как новое',
    'Идеальное состояние',
]


class BookGenerator:
    """Генератор данных для книг"""
    
    @staticmethod
    def generate_isbn() -> Optional[str]:
        """Генерирует случайный ISBN (опционально, 50% chance)"""
        if random.random() < 0.5:
            # Простой формат: 978-5-XXXXX-XX-X
            part1 = random.randint(10000, 99999)
            part2 = random.randint(10, 99)
            part3 = random.randint(0, 9)
            return f"978-5-{part1}-{part2}-{part3}"
        return None
    
    @staticmethod
    def generate_seller_code() -> str:
        """Генерирует учетный код продавца"""
        shelf = random.randint(1, 50)
        box = random.randint(1, 20)
        return f"S{shelf:02d}B{box:02d}"
    
    @staticmethod
    def generate_year(author_death_year: Optional[int] = None) -> tuple[Optional[int], Optional[str]]:
        """
        Генерирует год издания
        
        Returns:
            (year, year_approx) - точный год или приблизительный
        """
        # Если указан год смерти автора, книга не может быть позже
        if author_death_year is not None:
            max_year = min(author_death_year, 2024)
        else:
            max_year = 2024
        
        # Минимальный год для генерации
        min_year = 1700
        
        # Если максимальный год меньше минимального, используем приблизительный год
        if max_year < min_year:
            # Приблизительный год на основе года смерти автора
            if author_death_year:
                century = author_death_year // 100
                decade = (author_death_year % 100) // 10
                year_approx = f"{century}{decade}?"
            else:
                century = random.randint(17, 20)
                if random.random() < 0.5:
                    year_approx = f"{century}??"
                else:
                    decade = random.randint(0, 9)
                    year_approx = f"{century}{decade}?"
            return (None, year_approx)
        
        # 80% chance точного года, 20% приблизительного
        if random.random() < 0.8:
            year = random.randint(min_year, max_year)
            return (year, None)
        else:
            # Приблизительный год
            century = random.randint(17, 20)
            if random.random() < 0.5:
                year_approx = f"{century}??"
            else:
                decade = random.randint(0, 9)
                year_approx = f"{century}{decade}?"
            return (None, year_approx)
    
    @staticmethod
    def generate_pages_info() -> str:
        """Генерирует информацию о страницах"""
        pages = random.randint(100, 800)
        extras = []
        
        if random.random() < 0.3:
            extras.append(f"{random.randint(8, 32)} иллюстраций")
        
        if random.random() < 0.2:
            extras.append("схемы и карты")
        
        if random.random() < 0.15:
            extras.append("цветные вклейки")
        
        result = f"{pages} стр."
        if extras:
            result += f", {', '.join(extras)}"
        
        return result
    
    @staticmethod
    def generate_price() -> Optional[Decimal]:
        """Генерирует цену в рублях (80% chance)"""
        if random.random() < 0.8:
            # Цены от 100 до 5000 рублей
            price = random.randint(100, 5000)
            # Округляем до десятков
            price = (price // 10) * 10
            return Decimal(str(price))
        return None
    
    @staticmethod
    def generate_circulation() -> Optional[int]:
        """Генерирует тираж книги (70% chance)"""
        if random.random() < 0.7:
            # Тираж от 500 до 100000 экземпляров
            # Используем логарифмическое распределение для более реалистичных значений
            circulation = random.choice([
                random.randint(500, 2000),      # Малый тираж
                random.randint(2000, 10000),    # Средний тираж
                random.randint(10000, 50000),   # Большой тираж
                random.randint(50000, 100000),  # Очень большой тираж
            ])
            return circulation
        return None
    
    @classmethod
    def generate_book_data(
        cls,
        category,
        authors: list,
        publisher,
        library,
        owner,
        category_name: str = None,
        languages: list = None
    ) -> dict:
        """
        Генерирует полные данные для книги
        
        Args:
            category: Объект Category
            authors: Список объектов Author (1-3)
            publisher: Объект Publisher
            library: Объект Library
            owner: Объект User
            category_name: Название категории (для генерации названия)
            languages: Список объектов Language для выбора языка книги
        
        Returns:
            Словарь с данными для создания Book
        """
        if not authors:
            raise ValueError("Необходимо указать хотя бы одного автора")
        
        # Генерируем название
        title_data = generate_book_title(category_name or (category.name if category else None))
        
        # Определяем год смерти последнего автора (для ограничения года издания)
        death_years = [a.death_year for a in authors if a.death_year]
        max_death_year = max(death_years) if death_years else None
        
        # Генерируем год
        year, year_approx = cls.generate_year(max_death_year)
        
        # Генерируем место издания из города издательства
        publication_place = publisher.city if publisher and publisher.city else ""
        
        # Генерируем тип переплета
        binding_type = random.choice(BINDING_CHOICES)
        binding_details = None
        if random.random() < 0.7:
            color = random.choice(BINDING_COLORS)
            quality = random.choice(BINDING_QUALITIES)
            binding_details = f"{quality}, {color}"
        
        # Генерируем состояние
        condition = random.choice(CONDITION_CHOICES)
        condition_details = None
        if random.random() < 0.5:
            condition_details = random.choice(CONDITION_DETAILS)
        
        # Статус - распределяем более равномерно
        # 20% none, 15% reading, 25% read, 20% want_to_read, 20% want_to_reread
        status_weights = [0.20, 0.15, 0.25, 0.20, 0.20]
        status = random.choices(STATUS_CHOICES, weights=status_weights, k=1)[0]
        
        # Формируем данные книги
        book_data = {
            # Обязательные поля
            'title': title_data['title'],
            'category': category,
            'owner': owner,
            'library': library,
            
            # Авторы будут добавлены отдельно через BookAuthor
            
            # Статус
            'status': status,
            
            # Издательская информация
            'publisher': publisher,
            'publication_place': publication_place,
            'year': year,
            'year_approx': year_approx or '',
            'pages_info': cls.generate_pages_info(),
            
            # Физические характеристики
            'binding_type': binding_type,
            'binding_details': binding_details or '',
            'format': random.choice(FORMAT_CHOICES),
            
            # Описание
            'subtitle': title_data.get('subtitle') or '',
            'description': title_data.get('description') or '',
            
            # Состояние
            'condition': condition,
            'condition_details': condition_details or '',
            
            # Цена
            'price_rub': cls.generate_price(),
            
            # Метаданные
            'seller_code': cls.generate_seller_code(),
            'isbn': cls.generate_isbn() or '',
            
            # Новые поля
            'circulation': cls.generate_circulation(),
            'language': random.choice(languages) if languages and random.random() < 0.8 else None,  # 80% chance языка
        }
        
        return book_data


if __name__ == '__main__':
    # Тест генерации
    print("Примеры данных книги:\n")
    
    # Создаем моковые объекты для теста
    class MockCategory:
        name = "История России"
    
    class MockAuthor:
        def __init__(self, name, death_year=None):
            self.full_name = name
            self.death_year = death_year
    
    class MockPublisher:
        city = "Москва"
    
    class MockLibrary:
        pass
    
    class MockOwner:
        pass
    
    category = MockCategory()
    authors = [MockAuthor("Пушкин А.С.", 1837)]
    publisher = MockPublisher()
    library = MockLibrary()
    owner = MockOwner()
    
    for i in range(3):
        data = BookGenerator.generate_book_data(
            category, authors, publisher, library, owner, category.name
        )
        print(f"Книга {i+1}:")
        print(f"  Название: {data['title']}")
        print(f"  Год: {data['year'] or data['year_approx']}")
        print(f"  Переплет: {data['binding_type']}")
        print(f"  Цена: {data['price_rub']}")
        print()

