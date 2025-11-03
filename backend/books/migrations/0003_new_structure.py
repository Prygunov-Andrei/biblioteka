"""
Миграция на новую структуру моделей Book
"""
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_category_code'),
    ]

    operations = [
        # Создаем новые модели
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(help_text='ФИО автора', max_length=500, verbose_name='ФИО')),
                ('birth_year', models.IntegerField(blank=True, help_text='Год рождения', null=True, validators=[django.core.validators.MaxValueValidator(2100)], verbose_name='Год рождения')),
                ('death_year', models.IntegerField(blank=True, help_text='Год смерти', null=True, validators=[django.core.validators.MaxValueValidator(2100)], verbose_name='Год смерти')),
                ('biography', models.TextField(blank=True, help_text='Биография', verbose_name='Биография')),
                ('notes', models.TextField(blank=True, help_text='Заметки', verbose_name='Заметки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
            ],
            options={
                'verbose_name': 'Автор',
                'verbose_name_plural': 'Авторы',
                'ordering': ['full_name'],
            },
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Название издательства. Допустимы сокращения: Худ. лит-ра, Омское изд-во.', max_length=300, verbose_name='Название')),
                ('city', models.CharField(blank=True, help_text='Город', max_length=200, verbose_name='Город')),
                ('website', models.URLField(blank=True, help_text='Ссылка на сайт', verbose_name='Ссылка на сайт')),
                ('description', models.TextField(blank=True, help_text='Описание', verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
            ],
            options={
                'verbose_name': 'Издательство',
                'verbose_name_plural': 'Издательства',
                'ordering': ['name'],
            },
        ),
        # Удаляем старые поля Book (если они есть)
        migrations.RemoveField(
            model_name='book',
            name='author',
        ),
        migrations.RemoveField(
            model_name='book',
            name='binding',
        ),
        migrations.RemoveField(
            model_name='book',
            name='circulation',
        ),
        migrations.RemoveField(
            model_name='book',
            name='cover_image',
        ),
        migrations.RemoveField(
            model_name='book',
            name='edition',
        ),
        migrations.RemoveField(
            model_name='book',
            name='language',
        ),
        migrations.RemoveField(
            model_name='book',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='book',
            name='pages',
        ),
        migrations.RemoveField(
            model_name='book',
            name='weight',
        ),
        # Обновляем существующие поля
        migrations.AlterField(
            model_name='book',
            name='description',
            field=models.TextField(blank=True, default='', help_text='Содержание. Аннотация.', verbose_name='Содержание'),
        ),
        # Добавляем новые поля
        migrations.AddField(
            model_name='book',
            name='subtitle',
            field=models.TextField(blank=True, default='', help_text='Данные о переводе, принадлежность к серии, редакторов издания, художника-иллюстратора надо указывать здесь. Если произведения, входящие в издание перечислены на титульном листе, их тоже можно здесь указать.', verbose_name='Второе название'),
        ),
        migrations.AddField(
            model_name='book',
            name='publication_place',
            field=models.CharField(blank=True, default='', help_text='Место издания. Город', max_length=200, verbose_name='Место издания'),
        ),
        migrations.AddField(
            model_name='book',
            name='year_approx',
            field=models.CharField(blank=True, default='', help_text='Если год неизвестен точно, можно указать: 197?, 18??', max_length=10, verbose_name='Год издания (приблизительно)'),
        ),
        migrations.AddField(
            model_name='book',
            name='pages_info',
            field=models.CharField(blank=True, default='', help_text='Страниц. Можно указать количество иллюстраций, схем, карт или их наличие.', max_length=200, verbose_name='Страниц'),
        ),
        migrations.AddField(
            model_name='book',
            name='binding_type',
            field=models.CharField(blank=True, choices=[('paper', 'Бумажный (обложка)'), ('selfmade', 'Самодельный'), ('cardboard', 'Картонный'), ('hard', 'Твердый'), ('fabric', 'Тканевый'), ('owner', 'Владельческий'), ('halfleather', 'Полукожаный'), ('composite', 'Составной'), ('leather', 'Кожаный')], help_text='Бумажный (обложка), Самодельный, Картонный, Твердый - обычно достаточно, Тканевый, Владельческий, Полукожаный, Составной, Кожаный', max_length=20, verbose_name='Тип переплёта'),
        ),
        migrations.AddField(
            model_name='book',
            name='binding_details',
            field=models.CharField(blank=True, default='', help_text='Цвет, качество переплета', max_length=200, verbose_name='Детали переплёта'),
        ),
        migrations.AddField(
            model_name='book',
            name='condition',
            field=models.CharField(blank=True, choices=[('ideal', 'Идеальное'), ('excellent', 'Отличное'), ('good', 'Хорошее'), ('satisfactory', 'Удовлетворительное'), ('poor', 'Плохое')], help_text='Идеальное, отличное, хорошее, удовлетворительное, плохое', max_length=20, verbose_name='Состояние'),
        ),
        migrations.AddField(
            model_name='book',
            name='condition_details',
            field=models.TextField(blank=True, default='', help_text='Изъяны: отсутствие страниц, иллюстраций, загрязнения, изменения цвета, потертости, рассыпанный или "рыхлый" блок и проч.', verbose_name='Детали состояния'),
        ),
        migrations.AddField(
            model_name='book',
            name='price_rub',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Цена в рублях, с автоматическим пересчетом в Евро и Доллары', max_digits=10, null=True, verbose_name='Цена'),
        ),
        migrations.AddField(
            model_name='book',
            name='seller_code',
            field=models.CharField(blank=True, default='', help_text='Когда книг много, они могут храниться на пронумерованных полках или в коробках. Напишите этот номер здесь.', max_length=50, verbose_name='Учетный код продавца'),
        ),
        # Обновляем существующие поля
        migrations.AlterField(
            model_name='book',
            name='publisher',
            field=models.ForeignKey(blank=True, help_text='Издательство', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='books', to='books.publisher', verbose_name='Издательство'),
        ),
        migrations.AlterField(
            model_name='book',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Рубрика. Допустимые коды рубрик', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='books', to='books.category', verbose_name='Рубрика'),
        ),
        migrations.AlterField(
            model_name='book',
            name='format',
            field=models.CharField(blank=True, choices=[('very_large', 'Очень большой (свыше 28 см)'), ('encyclopedic', 'Энциклопедический (25-27 см)'), ('increased', 'Увеличенный (22-24 см)'), ('regular', 'Обычный (19-21 см)'), ('reduced', 'Уменьшенный (11-18 см)'), ('miniature', 'Миниатюрный (менее 10 см)')], help_text='Очень большой (свыше 28 см), Энциклопедический (25-27 см), Увеличенный (22-24 см), Обычный (19-21 см), Уменьшенный (11-18 см), Миниатюрный (менее 10 см)', max_length=20, verbose_name='Формат книги'),
        ),
        migrations.AlterField(
            model_name='book',
            name='year',
            field=models.IntegerField(blank=True, help_text='Год издания (точный, для поиска по диапазону)', null=True, validators=[django.core.validators.MaxValueValidator(2100)], verbose_name='Год издания'),
        ),
        migrations.AlterField(
            model_name='book',
            name='isbn',
            field=models.CharField(blank=True, default='', help_text='ISBN. Если у книги два кода ISBN, указывать надо только первый.', max_length=20, verbose_name='ISBN'),
        ),
        migrations.AlterField(
            model_name='book',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата размещения'),
        ),
        # Создаем промежуточные модели
        migrations.CreateModel(
            name='BookAuthor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0, help_text='Порядок автора (1-3, не более трех авторов)', validators=[django.core.validators.MaxValueValidator(3)], verbose_name='Порядок')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.author')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='book_authors', to='books.book')),
            ],
            options={
                'verbose_name': 'Автор книги',
                'verbose_name_plural': 'Авторы книг',
                'ordering': ['book', 'order'],
                'unique_together': {('book', 'order')},
            },
        ),
        migrations.CreateModel(
            name='BookImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Изображение книги', upload_to='books/images/', verbose_name='Изображение')),
                ('order', models.IntegerField(default=0, help_text='Порядок отображения (1-20)', validators=[django.core.validators.MaxValueValidator(20)], verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='books.book', verbose_name='Книга')),
            ],
            options={
                'verbose_name': 'Изображение книги',
                'verbose_name_plural': 'Изображения книг',
                'ordering': ['book', 'order'],
                'unique_together': {('book', 'order')},
            },
        ),
        migrations.CreateModel(
            name='BookElectronic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('format', models.CharField(choices=[('pdf', 'PDF'), ('epub', 'EPUB'), ('mobi', 'MOBI'), ('fb2', 'FB2'), ('djvu', 'DJVU'), ('txt', 'TXT'), ('rtf', 'RTF'), ('doc', 'DOC'), ('docx', 'DOCX')], help_text='Формат электронной версии', max_length=10, verbose_name='Формат')),
                ('url', models.URLField(blank=True, help_text='Ссылка на электронную версию', verbose_name='Ссылка')),
                ('file', models.FileField(blank=True, help_text='Файл электронной версии', upload_to='books/electronic/', verbose_name='Файл')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='electronic_versions', to='books.book', verbose_name='Книга')),
            ],
            options={
                'verbose_name': 'Электронная версия',
                'verbose_name_plural': 'Электронные версии',
                'ordering': ['book', 'format'],
            },
        ),
        # Добавляем связь авторов
        migrations.AddField(
            model_name='book',
            name='authors',
            field=models.ManyToManyField(help_text='Авторы. Начинается с фамилии, затем инициалы или имя. Не более трех авторов.', related_name='books', through='books.BookAuthor', to='books.author', verbose_name='Авторы'),
        ),
    ]
