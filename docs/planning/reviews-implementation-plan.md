# План реализации отзывов и рейтингов

## Обзор

Реализация системы отзывов и рейтингов для книг:
- Отображение отзывов в BookDetailModal
- Отображение среднего рейтинга в списке книг (BookCard)
- Возможность создания/редактирования/удаления отзывов
- Обновление фабрики для генерации 5-20 отзывов на каждую книгу

## Backend (Django)

### 1. Модель Book - добавить вычисление среднего рейтинга

**Файл:** `backend/books/models.py`

Добавить `@property` метод:
```python
@property
def average_rating(self):
    """Средний рейтинг книги из всех отзывов с оценками"""
    from django.db.models import Avg
    result = self.reviews.exclude(rating__isnull=True).aggregate(Avg('rating'))
    return round(result['rating__avg'], 2) if result['rating__avg'] else None
```

### 2. Сериализатор BookDetailSerializer - добавить average_rating

**Файл:** `backend/books/serializers.py`

Добавить поле:
```python
average_rating = serializers.SerializerMethodField()

def get_average_rating(self, obj):
    return obj.average_rating
```

### 3. Сериализатор BookListSerializer - добавить average_rating

**Файл:** `backend/books/serializers.py`

Добавить поле в `BookListSerializer`:
```python
average_rating = serializers.SerializerMethodField()

def get_average_rating(self, obj):
    return obj.average_rating
```

Добавить в `fields`:
```python
fields = [
    # ... existing fields ...
    'average_rating',
    # ... existing fields ...
]
```

### 4. ViewSet - оптимизация запросов

**Файл:** `backend/books/views/books.py`

Убедиться, что в `retrieve` action:
```python
queryset = queryset.prefetch_related(
    'images', 'electronic_versions', 'pages_set',
    Prefetch('reviews', queryset=BookReview.objects.select_related('user'), to_attr='all_reviews'),
    'reading_dates'
)
```

### 5. Permissions - проверка

**Файл:** `backend/books/permissions.py`

`IsReviewOwner` уже корректно реализован:
- Чтение разрешено всем (включая неавторизованных)
- Редактирование/удаление только автору отзыва

## Frontend (React)

### 1. Компонент BookCard - добавить средний рейтинг

**Файл:** `frontend/src/components/BookCard.js`

Добавить:
- Компонент `StarRating` для отображения звезд
- Отображение среднего рейтинга в карточке (если есть)

**Файл:** `frontend/src/components/BookCard.css`

Добавить стили для звездного рейтинга

### 2. Компонент StarRating

**Файл:** `frontend/src/components/StarRating.js` (новый)

Компонент для отображения звезд:
- Принимает `rating` (0-5 или null)
- Отображает заполненные и пустые звезды
- Поддержка темной темы

**Файл:** `frontend/src/components/StarRating.css` (новый)

### 3. Компонент BookDetailModal - секция отзывов

**Файл:** `frontend/src/components/BookDetailModal.js`

Добавить секцию отзывов:
- Отображение среднего рейтинга (если есть)
- Список всех отзывов:
  - Имя пользователя
  - Дата создания
  - Звезды (1-5)
  - Текст отзыва
  - Кнопки "Редактировать" / "Удалить" (только для своего отзыва)

**Файл:** `frontend/src/components/BookDetailModal.css`

Добавить стили для секции отзывов

### 4. Компонент ReviewItem

**Файл:** `frontend/src/components/ReviewItem.js` (новый)

Компонент для отдельного отзыва:
- Отображение звезд
- Текст отзыва
- Информация о пользователе и дате
- Кнопки редактирования/удаления

**Файл:** `frontend/src/components/ReviewItem.css` (новый)

### 5. Компонент EditReviewModal

**Файл:** `frontend/src/components/EditReviewModal.js` (новый)

Модальное окно для редактирования отзыва:
- Форма с полями:
  - Звезды (1-5, опционально)
  - Текст отзыва (опционально)
- Валидация: хотя бы одно поле должно быть заполнено
- Кнопки "Сохранить" и "Отмена"

**Файл:** `frontend/src/components/EditReviewModal.css` (новый)

### 6. API сервис - методы для отзывов

**Файл:** `frontend/src/services/api.js`

Добавить методы:
```javascript
reviewsAPI: {
  createOrUpdate: (bookId, data) => {
    // POST /api/reviews/ с book_id и данными
  },
  update: (reviewId, data) => {
    // PUT /api/reviews/{id}/
  },
  delete: (reviewId) => {
    // DELETE /api/reviews/{id}/
  }
}
```

## Фабрика тестовых данных

### Обновить генерацию отзывов

**Файл:** `test_data_factory/factory.py`

Заменить текущую логику (40% вероятность, 1 отзыв) на:
- Для каждой книги: 5-20 отзывов от случайных пользователей
- Варианты отзывов:
  - Только звезды (1-5) - 30%
  - Только текст - 30%
  - И звезды, и текст - 35%
  - Пустой отзыв (только для тестирования) - 5%

## Структура данных

### BookDetailSerializer
```javascript
{
  // ... existing fields ...
  reviews: [
    {
      id: 1,
      user: 1,
      user_username: "test_user",
      rating: 4, // или null
      review_text: "Отличная книга!", // или пусто
      created_at: "2025-01-27T10:00:00Z",
      updated_at: "2025-01-27T10:00:00Z"
    }
  ],
  average_rating: 4.2 // или null
}
```

### BookListSerializer
```javascript
{
  // ... existing fields ...
  average_rating: 4.2 // или null
}
```

## API Endpoints

### Существующие (уже реализованы)
- `GET /api/books/{id}/` - возвращает reviews и нужно добавить average_rating
- `POST /api/reviews/` - upsert (создание/обновление отзыва)
- `PUT /api/reviews/{id}/` - обновление отзыва
- `DELETE /api/reviews/{id}/` - удаление отзыва

## Логика работы

1. **Любой пользователь может оставить отзыв к любой книге**
   - Проверка: `unique_together = ['book', 'user']` - один отзыв на книгу от пользователя
   - `POST /api/reviews/` делает upsert: если отзыв существует - обновляется, если нет - создается

2. **Отображение отзывов**
   - В BookDetailModal: список всех отзывов с полной информацией
   - В BookCard: только средний рейтинг (звездами)

3. **Редактирование/удаление**
   - Пользователь видит кнопки только для своего отзыва
   - Редактирование через `EditReviewModal`
   - Удаление через `DELETE /api/reviews/{id}/`

4. **Средний рейтинг**
   - Вычисляется на бэкенде из всех отзывов с оценками (rating не null)
   - Отображается только если есть отзывы с оценками
   - Обновляется автоматически при изменении отзывов

## Порядок реализации

1. **Backend:**
   - Добавить `average_rating` в модель Book
   - Добавить `average_rating` в сериализаторы
   - Оптимизировать запросы

2. **Фабрика:**
   - Обновить генерацию отзывов (5-20 на книгу)
   - Удалить все книги и перегенерировать

3. **Frontend:**
   - Создать компонент `StarRating`
   - Обновить `BookCard` для отображения среднего рейтинга
   - Обновить `BookDetailModal` для отображения списка отзывов
   - Создать компонент `ReviewItem`
   - Создать компонент `EditReviewModal`
   - Добавить методы в API сервис

4. **Тестирование:**
   - Проверить отображение отзывов в BookDetailModal
   - Проверить отображение среднего рейтинга в списке книг
   - Проверить создание/редактирование/удаление отзывов
   - Проверить обновление среднего рейтинга после изменений

## Тестирование

- [ ] Средний рейтинг вычисляется корректно
- [ ] Средний рейтинг отображается в BookCard (звездами)
- [ ] Средний рейтинг отображается в BookDetailModal
- [ ] Список отзывов отображается в BookDetailModal
- [ ] Отзывы с только звездами отображаются корректно
- [ ] Отзывы с только текстом отображаются корректно
- [ ] Отзывы с звездами и текстом отображаются корректно
- [ ] Кнопки редактирования/удаления видны только для своего отзыва
- [ ] Создание отзыва работает (upsert)
- [ ] Редактирование отзыва работает
- [ ] Удаление отзыва работает
- [ ] Средний рейтинг обновляется после изменения отзывов
- [ ] Фабрика генерирует 5-20 отзывов на каждую книгу
