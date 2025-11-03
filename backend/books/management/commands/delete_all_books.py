"""
Management команда для удаления всех книг (сохраняя категории, авторов, издательства)
"""
from django.core.management.base import BaseCommand
from books.models import Book, BookImage, BookPage, BookElectronic, BookAuthor, BookHashtag, BookReview


class Command(BaseCommand):
    help = 'Удаляет все книги из базы данных (сохраняя категории, авторов, издательства)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждение удаления (обязательно для выполнения)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  ВНИМАНИЕ: Эта команда удалит ВСЕ книги из базы данных!\n'
                    'Для подтверждения используйте флаг --confirm'
                )
            )
            return
        
        # Подсчитываем количество объектов для удаления
        books_count = Book.objects.count()
        images_count = BookImage.objects.count()
        pages_count = BookPage.objects.count()
        electronic_count = BookElectronic.objects.count()
        reviews_count = BookReview.objects.count()
        
        self.stdout.write(
            self.style.WARNING(
                f'\n🗑️  Удаление книг и связанных данных:\n'
                f'   Книг: {books_count}\n'
                f'   Изображений: {images_count}\n'
                f'   Страниц: {pages_count}\n'
                f'   Электронных версий: {electronic_count}\n'
                f'   Отзывов: {reviews_count}\n'
            )
        )
        
        # Удаляем все книги (связанные объекты удалятся автоматически благодаря CASCADE)
        deleted_books = Book.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Успешно удалено:\n'
                f'   Объектов удалено: {deleted_books[0]}\n'
                f'   Типов объектов: {len(deleted_books[1])}\n'
            )
        )
        
        # Показываем что осталось
        categories_count = Book.objects.count()  # Должно быть 0
        authors_count = Book.objects.count()  # Должно быть 0
        publishers_count = Book.objects.count()  # Должно быть 0
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Статус после удаления:\n'
                f'   Книги: {Book.objects.count()}\n'
                f'   Изображения: {BookImage.objects.count()}\n'
                f'   Страницы: {BookPage.objects.count()}\n'
                f'   Электронные версии: {BookElectronic.objects.count()}\n'
                f'   Отзывы: {BookReview.objects.count()}\n'
            )
        )
        
        # Проверяем что категории, авторы и издательства остались
        from books.models import Category, Author, Publisher
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Сохранено:\n'
                f'   Категорий: {Category.objects.count()}\n'
                f'   Авторов: {Author.objects.count()}\n'
                f'   Издательств: {Publisher.objects.count()}\n'
            )
        )

