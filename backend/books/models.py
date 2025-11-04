"""
Модели для книг
"""
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MaxValueValidator, MinValueValidator


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    full_name = models.CharField(
        'ФИО',
        max_length=500,
        blank=True,
        help_text='Полное имя пользователя'
    )
    photo = models.ImageField(
        'Фото',
        upload_to='users/photos/',
        blank=True,
        null=True,
        help_text='Фото профиля'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Описание или биография пользователя'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль при создании пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Library(models.Model):
    """Библиотека пользователя"""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='libraries',
        verbose_name='Владелец',
        help_text='Владелец библиотеки'
    )
    name = models.CharField(
        'Название',
        max_length=200,
        help_text='Название библиотеки (например, "Библиотека в Москве")'
    )
    address = models.TextField(
        'Адрес',
        help_text='Физический адрес библиотеки'
    )
    city = models.CharField(
        'Город',
        max_length=200,
        blank=True,
        help_text='Город'
    )
    country = models.CharField(
        'Страна',
        max_length=200,
        blank=True,
        help_text='Страна'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Описание библиотеки'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Библиотека'
        verbose_name_plural = 'Библиотеки'
        ordering = ['owner', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class Hashtag(models.Model):
    """Хэштег для книг"""
    name = models.CharField(
        'Название',
        max_length=100,
        help_text='Название хэштега (например, "#фантастика")'
    )
    slug = models.SlugField(
        'Slug',
        max_length=100,
        unique=True,
        help_text='URL-дружественное имя'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_hashtags',
        verbose_name='Создатель',
        help_text='Пользователь, создавший хэштег (null = общий хэштег)'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Хэштег'
        verbose_name_plural = 'Хэштеги'
        ordering = ['name']
        unique_together = ['name', 'creator']  # Один хэштег с одним именем у пользователя
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        creator_str = f" ({self.creator.username})" if self.creator else " (общий)"
        return f"{self.name}{creator_str}"


class BookHashtag(models.Model):
    """Связь книги и хэштега"""
    book = models.ForeignKey(
        'Book',
        on_delete=models.CASCADE,
        related_name='book_hashtags',
        verbose_name='Книга'
    )
    hashtag = models.ForeignKey(
        Hashtag,
        on_delete=models.CASCADE,
        related_name='book_hashtags',
        verbose_name='Хэштег'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Хэштег книги'
        verbose_name_plural = 'Хэштеги книг'
        unique_together = ['book', 'hashtag']
        ordering = ['book', 'created_at']
    
    def __str__(self):
        return f"{self.book.title} - {self.hashtag.name}"


class BookReview(models.Model):
    """Отзыв пользователя на книгу"""
    book = models.ForeignKey(
        'Book',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Книга'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='book_reviews',
        verbose_name='Пользователь',
        help_text='Автор отзыва'
    )
    rating = models.IntegerField(
        'Оценка',
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Оценка книги от 1 до 5'
    )
    review_text = models.TextField(
        'Текст отзыва',
        blank=True,
        help_text='Текст отзыва'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Отзыв на книгу'
        verbose_name_plural = 'Отзывы на книги'
        unique_together = ['book', 'user']  # Один отзыв на книгу от пользователя
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв {self.user.username} на {self.book.title}"


class Category(models.Model):
    """Категория книг"""
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='Родительская категория',
        help_text='Родительская категория (если категория является подкатегорией)'
    )
    code = models.CharField('Код', max_length=20, unique=True, default='', help_text='Буквенный код категории')
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Иконка', max_length=50, default='📚')
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def is_parent(self):
        """Возвращает True, если категория является родительской (имеет подкатегории)"""
        return self.subcategories.exists()


class Author(models.Model):
    """Автор книги"""
    full_name = models.CharField(
        'ФИО',
        max_length=500,
        help_text='ФИО автора'
    )
    birth_year = models.IntegerField(
        'Год рождения',
        null=True,
        blank=True,
        validators=[MaxValueValidator(2100)],
        help_text='Год рождения'
    )
    death_year = models.IntegerField(
        'Год смерти',
        null=True,
        blank=True,
        validators=[MaxValueValidator(2100)],
        help_text='Год смерти'
    )
    biography = models.TextField(
        'Биография',
        blank=True,
        help_text='Биография'
    )
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Заметки'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['full_name']
    
    def __str__(self):
        return self.full_name


class Publisher(models.Model):
    """Издательство"""
    name = models.CharField(
        'Название',
        max_length=300,
        help_text='Название издательства. Допустимы сокращения: Худ. лит-ра, Омское изд-во.'
    )
    city = models.CharField(
        'Город',
        max_length=200,
        blank=True,
        help_text='Город'
    )
    website = models.URLField(
        'Ссылка на сайт',
        blank=True,
        help_text='Ссылка на сайт'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        help_text='Описание'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Language(models.Model):
    """Язык текста книги"""
    name = models.CharField(
        'Название',
        max_length=100,
        unique=True,
        help_text='Название языка (например, "Русский", "Английский")'
    )
    code = models.CharField(
        'Код языка',
        max_length=10,
        unique=True,
        blank=True,
        help_text='ISO код языка (например, "ru", "en", "de")'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга"""
    
    # Владелец и библиотека
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_books',
        verbose_name='Владелец',
        help_text='Владелец книги (создатель)',
        null=True,  # Временно nullable для миграции
        blank=True
    )
    library = models.ForeignKey(
        'Library',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='Библиотека',
        help_text='Библиотека, в которой находится книга'
    )
    
    # Статус книги
    STATUS_CHOICES = [
        ('none', 'Без статуса'),
        ('reading', 'Читаю'),
        ('read', 'Прочитано'),
        ('want_to_read', 'Буду читать'),
        ('want_to_reread', 'Буду перечитывать'),
    ]
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='none',
        help_text='Статус книги'
    )
    
    # Хэштеги
    hashtags = models.ManyToManyField(
        'Hashtag',
        through='BookHashtag',
        related_name='books',
        blank=True,
        verbose_name='Хэштеги',
        help_text='Хэштеги книги (до 20)'
    )
    
    # Рубрика
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='Рубрика',
        help_text='Рубрика. Допустимые коды рубрик'
    )
    
    # Авторы (через промежуточную модель для ограничения и порядка)
    authors = models.ManyToManyField(
        Author,
        through='BookAuthor',
        related_name='books',
        verbose_name='Авторы',
        help_text='Авторы. Начинается с фамилии, затем инициалы или имя. Не более трех авторов.'
    )
    
    # Основная информация
    title = models.CharField(
        'Название',
        max_length=500,
        help_text='Основное название книги.'
    )
    subtitle = models.TextField(
        'Второе название',
        blank=True,
        help_text='Данные о переводе, принадлежность к серии, редакторов издания, художника-иллюстратора надо указывать здесь. Если произведения, входящие в издание перечислены на титульном листе, их тоже можно здесь указать.'
    )
    
    # Издательская информация
    publication_place = models.CharField(
        'Место издания',
        max_length=200,
        blank=True,
        help_text='Место издания. Город'
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='Издательство',
        help_text='Издательство'
    )
    year = models.IntegerField(
        'Год издания',
        null=True,
        blank=True,
        validators=[MaxValueValidator(2100)],
        help_text='Год издания (точный, для поиска по диапазону)'
    )
    year_approx = models.CharField(
        'Год издания (приблизительно)',
        max_length=10,
        blank=True,
        help_text='Если год неизвестен точно, можно указать: 197?, 18??'
    )
    pages_info = models.CharField(
        'Страниц',
        max_length=200,
        blank=True,
        help_text='Страниц. Можно указать количество иллюстраций, схем, карт или их наличие.'
    )
    circulation = models.IntegerField(
        'Тираж',
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Тираж книги в штуках'
    )
    language = models.ForeignKey(
        'Language',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        verbose_name='Язык текста',
        help_text='Язык текста книги'
    )
    
    # Физические характеристики
    BINDING_CHOICES = [
        ('paper', 'Бумажный (обложка)'),
        ('selfmade', 'Самодельный'),
        ('cardboard', 'Картонный'),
        ('hard', 'Твердый'),
        ('fabric', 'Тканевый'),
        ('owner', 'Владельческий'),
        ('halfleather', 'Полукожаный'),
        ('composite', 'Составной'),
        ('leather', 'Кожаный'),
    ]
    binding_type = models.CharField(
        'Тип переплёта',
        max_length=20,
        choices=BINDING_CHOICES,
        blank=True,
        help_text='Бумажный (обложка), Самодельный, Картонный, Твердый - обычно достаточно, Тканевый, Владельческий, Полукожаный, Составной, Кожаный'
    )
    binding_details = models.CharField(
        'Детали переплёта',
        max_length=200,
        blank=True,
        help_text='Цвет, качество переплета'
    )
    
    FORMAT_CHOICES = [
        ('very_large', 'Очень большой (свыше 28 см)'),
        ('encyclopedic', 'Энциклопедический (25-27 см)'),
        ('increased', 'Увеличенный (22-24 см)'),
        ('regular', 'Обычный (19-21 см)'),
        ('reduced', 'Уменьшенный (11-18 см)'),
        ('miniature', 'Миниатюрный (менее 10 см)'),
    ]
    format = models.CharField(
        'Формат книги',
        max_length=20,
        choices=FORMAT_CHOICES,
        blank=True,
        help_text='Очень большой (свыше 28 см), Энциклопедический (25-27 см), Увеличенный (22-24 см), Обычный (19-21 см), Уменьшенный (11-18 см), Миниатюрный (менее 10 см)'
    )
    
    # Описание и состояние
    description = models.TextField(
        'Содержание',
        blank=True,
        help_text='Содержание. Аннотация.'
    )
    
    CONDITION_CHOICES = [
        ('ideal', 'Идеальное'),
        ('excellent', 'Отличное'),
        ('good', 'Хорошее'),
        ('satisfactory', 'Удовлетворительное'),
        ('poor', 'Плохое'),
    ]
    condition = models.CharField(
        'Состояние',
        max_length=20,
        choices=CONDITION_CHOICES,
        blank=True,
        help_text='Идеальное, отличное, хорошее, удовлетворительное, плохое'
    )
    condition_details = models.TextField(
        'Детали состояния',
        blank=True,
        help_text='Изъяны: отсутствие страниц, иллюстраций, загрязнения, изменения цвета, потертости, рассыпанный или "рыхлый" блок и проч.'
    )
    
    # Цена
    price_rub = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Цена в рублях, с автоматическим пересчетом в Евро и Доллары'
    )
    
    # Метаданные
    seller_code = models.CharField(
        'Учетный код продавца',
        max_length=50,
        blank=True,
        help_text='Когда книг много, они могут храниться на пронумерованных полках или в коробках. Напишите этот номер здесь.'
    )
    isbn = models.CharField(
        'ISBN',
        max_length=20,
        blank=True,
        help_text='ISBN. Если у книги два кода ISBN, указывать надо только первый.'
    )
    
    # Обложка книги
    cover_page = models.ForeignKey(
        'BookPage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cover_for_books',
        verbose_name='Обложка',
        help_text='Страница книги, используемая как обложка (для отображения в списках и карточках)'
    )
    
    # Автоматические поля (created_at = дата размещения)
    created_at = models.DateTimeField('Дата размещения', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='books_book_created_at_idx'),
            models.Index(fields=['library', 'category'], name='books_book_lib_cat_idx'),
            models.Index(fields=['owner', 'status'], name='books_book_owner_status_idx'),
        ]
    
    def __str__(self):
        authors_str = ', '.join([a.full_name for a in self.authors.all()[:3]])
        return f"{self.title} - {authors_str}" if authors_str else self.title
    
    @property
    def images_count(self):
        """Количество изображений"""
        return self.images.count()


class BookAuthor(models.Model):
    """Промежуточная модель для связи Book и Author с порядком"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_authors')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.IntegerField(
        'Порядок',
        default=0,
        validators=[MaxValueValidator(3)],
        help_text='Порядок автора (1-3, не более трех авторов)'
    )
    
    class Meta:
        verbose_name = 'Автор книги'
        verbose_name_plural = 'Авторы книг'
        ordering = ['book', 'order']
        unique_together = ['book', 'order']
    
    def __str__(self):
        return f"{self.book.title} - {self.author.full_name} (#{self.order})"


class BookImage(models.Model):
    """Изображение книги"""
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Книга'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='books/images/',
        help_text='Изображение книги'
    )
    order = models.IntegerField(
        'Порядок',
        default=0,
        validators=[MaxValueValidator(20)],
        help_text='Порядок отображения (1-20)'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Изображение книги'
        verbose_name_plural = 'Изображения книг'
        ordering = ['book', 'order']
        unique_together = ['book', 'order']
    
    def __str__(self):
        return f"{self.book.title} - изображение #{self.order}"


class BookElectronic(models.Model):
    """Электронная версия книги"""
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='electronic_versions',
        verbose_name='Книга'
    )
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('mobi', 'MOBI'),
        ('fb2', 'FB2'),
        ('djvu', 'DJVU'),
        ('txt', 'TXT'),
        ('rtf', 'RTF'),
        ('doc', 'DOC'),
        ('docx', 'DOCX'),
    ]
    format = models.CharField(
        'Формат',
        max_length=10,
        choices=FORMAT_CHOICES,
        help_text='Формат электронной версии'
    )
    url = models.URLField(
        'Ссылка',
        blank=True,
        help_text='Ссылка на электронную версию'
    )
    file = models.FileField(
        'Файл',
        upload_to='books/electronic/',
        blank=True,
        help_text='Файл электронной версии'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Электронная версия'
        verbose_name_plural = 'Электронные версии'
        ordering = ['book', 'format']
    
    def __str__(self):
        return f"{self.book.title} - {self.get_format_display()}"


class BookPage(models.Model):
    """Страница книги (для обработки документов)"""
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name='pages_set',
        verbose_name='Книга'
    )
    page_number = models.IntegerField('Номер страницы')
    
    # Оригинальное изображение
    original_image = models.ImageField('Оригинал', upload_to='books/pages/original/')
    
    # Обработанное изображение
    processed_image = models.ImageField('Обработанное', upload_to='books/pages/processed/', blank=True, null=True)
    
    # Метаданные обработки
    processed_at = models.DateTimeField('Обработано', blank=True, null=True)
    processing_status = models.CharField(
        'Статус',
        max_length=20,
        choices=[
            ('pending', 'Ожидает'),
            ('processing', 'Обрабатывается'),
            ('completed', 'Готово'),
            ('failed', 'Ошибка')
        ],
        default='pending'
    )
    error_message = models.TextField('Ошибка', blank=True, null=True)
    
    # Размеры изображения
    width = models.IntegerField('Ширина', blank=True, null=True)
    height = models.IntegerField('Высота', blank=True, null=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Страница книги'
        verbose_name_plural = 'Страницы книг'
        ordering = ['book', 'page_number']
        unique_together = ['book', 'page_number']
    
    def __str__(self):
        return f"{self.book.title} - стр. {self.page_number}"


class BookReadingDate(models.Model):
    """Дата прочтения книги (может быть несколько дат для одной книги)"""
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reading_dates',
        verbose_name='Книга',
        help_text='Книга, которую прочитали'
    )
    date = models.DateField(
        'Дата прочтения',
        help_text='Дата, когда книга была прочитана'
    )
    notes = models.TextField(
        'Заметки',
        blank=True,
        help_text='Дополнительные заметки о прочтении (например, где прочитали, впечатления)'
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Дата прочтения'
        verbose_name_plural = 'Даты прочтения'
        ordering = ['book', '-date']
        unique_together = ['book', 'date']  # Одна дата прочтения на книгу
    
    def __str__(self):
        return f"{self.book.title} - {self.date}"
