import { useState, useEffect } from 'react';
import { booksAPI, reviewsAPI } from '../services/api';
import ReviewItem from './ReviewItem';
import StarRating from './StarRating';
import EditReviewModal from './EditReviewModal';
import ConfirmModal from './ConfirmModal';
import './BookDetailModal.css';

const BookDetailModal = ({ bookId, isOpen, onClose, onEdit, onTransfer, onDelete }) => {
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [editingReview, setEditingReview] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  useEffect(() => {
    if (isOpen && bookId) {
      loadBookDetails();
      loadCurrentUser();
      setSelectedPageIndex(0); // Сбрасываем выбранную страницу при открытии
    }
  }, [isOpen, bookId]);

  const loadCurrentUser = async () => {
    try {
      // Пытаемся получить ID текущего пользователя из токена или через API
      const token = localStorage.getItem('access_token');
      if (token) {
        // Простой способ - декодировать JWT токен (только для получения user_id)
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.user_id) {
            setCurrentUserId(payload.user_id);
          }
        } catch (e) {
          // Если не удалось декодировать, пробуем через API
          // Можно добавить endpoint для получения текущего пользователя
        }
      }
    } catch (err) {
      console.error('Ошибка получения текущего пользователя:', err);
    }
  };

  const loadBookDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await booksAPI.getById(bookId);
      console.log('📖 Загружена книга:', data);
      console.log('📄 Страницы книги:', data.pages);
      console.log('📄 Количество страниц:', data.pages ? data.pages.length : 0);
      if (data.pages && data.pages.length > 0) {
        console.log('📄 Первая страница:', data.pages[0]);
        console.log('📄 URL первой страницы:', {
          processed_url: data.pages[0].processed_url,
          original_url: data.pages[0].original_url
        });
      }
      setBook(data);
    } catch (err) {
      console.error('Ошибка загрузки деталей книги:', err);
      setError('Не удалось загрузить информацию о книге');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  const handleEdit = () => {
    if (onEdit && book) {
      onEdit(book);
    }
  };

  const handleTransfer = () => {
    if (onTransfer && book) {
      onTransfer(book);
    }
  };

  const handleDelete = () => {
    if (onDelete && book) {
      onDelete(book);
    }
  };

  const handleEditReview = (review) => {
    setEditingReview(review);
  };

  const handleDeleteReview = (reviewId) => {
    // Показываем модальное окно подтверждения
    setConfirmDelete({
      reviewId,
      message: 'Вы уверены, что хотите удалить этот отзыв?'
    });
  };

  const handleConfirmDeleteReview = async () => {
    if (!confirmDelete) return;
    
    try {
      await reviewsAPI.delete(confirmDelete.reviewId);
      setConfirmDelete(null);
      // Перезагружаем данные книги
      await loadBookDetails();
    } catch (err) {
      console.error('Ошибка удаления отзыва:', err);
      setConfirmDelete(null);
      // Показываем ошибку через модальное окно
      setConfirmDelete({
        error: true,
        message: 'Не удалось удалить отзыв. Попробуйте позже.'
      });
    }
  };

  const handleCancelDeleteReview = () => {
    setConfirmDelete(null);
  };

  const handleSaveReview = async (reviewData) => {
    if (!book || !book.id) {
      console.error('Книга не загружена');
      return;
    }
    try {
      if (editingReview && editingReview.id) {
        // Обновление существующего отзыва
        // При обновлении не отправляем book, так как он не может измениться
        await reviewsAPI.update(editingReview.id, reviewData);
      } else {
        // Создание нового отзыва
        await reviewsAPI.createOrUpdate(book.id, reviewData);
      }
      setEditingReview(null);
      // Перезагружаем данные книги
      await loadBookDetails();
    } catch (err) {
      console.error('Ошибка сохранения отзыва:', err);
      console.error('Детали ошибки:', err.response?.data);
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Не удалось сохранить отзыв';
      // Показываем ошибку через модальное окно
      setConfirmDelete({
        error: true,
        message: errorMessage
      });
    }
  };

  const handleCancelEditReview = () => {
    setEditingReview(null);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleClose();
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const formatField = (value, defaultValue = 'Не указано') => {
    if (value === null || value === undefined || value === '') {
      return defaultValue;
    }
    return value;
  };

  const formatAuthors = () => {
    if (!book || !book.authors || book.authors.length === 0) {
      return 'Автор не указан';
    }
    // API возвращает массив объектов {id, full_name} или строк
    return book.authors.map(a => {
      if (typeof a === 'string') return a;
      return a.full_name || a.name || a;
    }).join(', ');
  };

  const formatCategory = () => {
    if (!book) {
      return 'Не указана';
    }
    // API может возвращать category_name или category.name
    if (book.category_name) {
      return book.category_name;
    }
    if (book.category) {
      return typeof book.category === 'string' ? book.category : book.category.name;
    }
    return 'Не указана';
  };

  const formatPublisher = () => {
    if (!book) {
      return 'Не указано';
    }
    // API может возвращать publisher_name или publisher.name
    if (book.publisher_name) {
      return book.publisher_name;
    }
    if (book.publisher) {
      return typeof book.publisher === 'string' ? book.publisher : book.publisher.name;
    }
    return 'Не указано';
  };

  const formatLanguage = () => {
    if (!book) {
      return 'Не указан';
    }
    // API может возвращать language_name или language.name
    if (book.language_name) {
      return book.language_name;
    }
    if (book.language) {
      return typeof book.language === 'string' ? book.language : book.language.name;
    }
    return 'Не указан';
  };

  const formatStatus = () => {
    if (!book || !book.status) {
      return 'Без статуса';
    }
    const statusMap = {
      'none': 'Без статуса',
      'reading': 'Читаю',
      'read': 'Прочитано',
      'want_to_read': 'Буду читать',
      'want_to_reread': 'Буду перечитывать'
    };
    return statusMap[book.status] || book.status;
  };

  const getFirstReadingDate = () => {
    // Получаем первую дату прочтения (самую раннюю) для прочитанных книг
    if (!book || book.status !== 'read' || !book.reading_dates || book.reading_dates.length === 0) {
      return null;
    }
    
    // Сортируем даты по возрастанию (первая дата - самая ранняя)
    const dates = book.reading_dates
      .map(d => {
        if (typeof d === 'string') return d;
        return d.date || d;
      })
      .filter(d => d)
      .sort();
    
    return dates.length > 0 ? dates[0] : null;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    if (isNaN(date.getTime())) return dateString; // Если невалидная дата, возвращаем как есть
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatBindingType = () => {
    if (!book || !book.binding_type) {
      return 'Не указан';
    }
    const bindingMap = {
      'paper': 'Бумажный (обложка)',
      'selfmade': 'Самодельный',
      'cardboard': 'Картонный',
      'hard': 'Твердый',
      'fabric': 'Тканевый',
      'owner': 'Владельческий',
      'halfleather': 'Полукожаный',
      'composite': 'Составной',
      'leather': 'Кожаный'
    };
    return bindingMap[book.binding_type] || book.binding_type;
  };

  const formatFormat = () => {
    if (!book || !book.format) {
      return 'Не указан';
    }
    const formatMap = {
      'very_large': 'Очень большой (свыше 28 см)',
      'encyclopedic': 'Энциклопедический (25-27 см)',
      'increased': 'Увеличенный (22-24 см)',
      'regular': 'Обычный (19-21 см)',
      'reduced': 'Уменьшенный (11-18 см)',
      'miniature': 'Миниатюрный (менее 10 см)'
    };
    return formatMap[book.format] || book.format;
  };

  const formatCondition = () => {
    if (!book || !book.condition) {
      return 'Не указано';
    }
    const conditionMap = {
      'ideal': 'Идеальное',
      'excellent': 'Отличное',
      'good': 'Хорошее',
      'satisfactory': 'Удовлетворительное',
      'poor': 'Плохое'
    };
    return conditionMap[book.condition] || book.condition;
  };

  return (
    <div className="book-detail-modal-overlay" onClick={handleBackdropClick}>
      <div className="book-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="book-detail-modal-header">
          <h2>{book && !loading && !error ? book.title : 'Информация о книге'}</h2>
          <button className="book-detail-modal-close" onClick={handleClose}>
            ×
          </button>
        </div>

        <div className="book-detail-modal-content">
          {loading && (
            <div className="book-detail-modal-loading">
              <div className="loading-spinner">Загрузка...</div>
            </div>
          )}

          {error && (
            <div className="book-detail-modal-error">
              <p>{error}</p>
              <button onClick={loadBookDetails}>Повторить</button>
            </div>
          )}

          {!loading && !error && book && (
            <div className="book-detail-modal-body">
              {/* Страницы книги */}
              {book.pages && book.pages.length > 0 ? (
                <section className="book-detail-section book-pages-section">
                  <div className="book-pages-container">
                    <div className="book-pages-main">
                      {book.pages[selectedPageIndex] && (
                        <img
                          src={book.pages[selectedPageIndex].processed_url || book.pages[selectedPageIndex].original_url}
                          alt={`Страница ${book.pages[selectedPageIndex].page_number}`}
                          className="book-pages-main-image"
                          onError={(e) => {
                            console.error('❌ Ошибка загрузки главной картинки:', e.target.src);
                            // Если processed_url не загрузился, пробуем original_url
                            const currentPage = book.pages[selectedPageIndex];
                            if (currentPage && currentPage.original_url && e.target.src !== currentPage.original_url) {
                              console.log('🔄 Пробуем original_url:', currentPage.original_url);
                              e.target.src = currentPage.original_url;
                            }
                          }}
                          onLoad={() => {
                            console.log('✅ Главная картинка загружена:', book.pages[selectedPageIndex].processed_url || book.pages[selectedPageIndex].original_url);
                          }}
                        />
                      )}
                    </div>
                    <div className="book-pages-thumbnails">
                      {book.pages.map((page, index) => {
                        const pageUrl = page.processed_url || page.original_url;
                        return (
                          <div
                            key={page.id || index}
                            className={`book-pages-thumbnail ${index === selectedPageIndex ? 'active' : ''}`}
                            onClick={() => {
                              console.log('🖱️ Клик по миниатюре:', index, page);
                              setSelectedPageIndex(index);
                            }}
                            title={`Страница ${page.page_number || index + 1}`}
                          >
                            <img
                              src={pageUrl}
                              alt={`Страница ${page.page_number || index + 1}`}
                              className="book-pages-thumbnail-image"
                              onError={(e) => {
                                console.error('❌ Ошибка загрузки миниатюры:', e.target.src);
                                // Если processed_url не загрузился, пробуем original_url
                                if (page.original_url && e.target.src !== page.original_url) {
                                  console.log('🔄 Пробуем original_url для миниатюры:', page.original_url);
                                  e.target.src = page.original_url;
                                }
                              }}
                              onLoad={() => {
                                console.log('✅ Миниатюра загружена:', pageUrl);
                              }}
                            />
                            <span className="book-pages-thumbnail-number">{page.page_number || index + 1}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </section>
              ) : (
                <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                  <p>Изображения страниц не загружены</p>
                  <p style={{ fontSize: '12px', marginTop: '8px', color: '#999' }}>
                    {book.pages === undefined 
                      ? 'Данные о страницах отсутствуют' 
                      : 'У этой книги нет загруженных изображений страниц. Для загрузки страниц используйте функцию создания книги.'}
                  </p>
                  {book.pages_info && (
                    <p style={{ fontSize: '12px', marginTop: '8px', fontStyle: 'italic' }}>
                      Информация о количестве страниц: {book.pages_info}
                    </p>
                  )}
                </div>
              )}

              {/* Основная информация */}
              <section className="book-detail-section">
                <div className="book-detail-field">
                  <span className="book-detail-label">Название:</span>
                  <span className="book-detail-value">{formatField(book.title)}</span>
                </div>
                {book.subtitle && (
                  <div className="book-detail-field">
                    <span className="book-detail-label">Подзаголовок:</span>
                    <span className="book-detail-value">{book.subtitle}</span>
                  </div>
                )}
                <div className="book-detail-field">
                  <span className="book-detail-label">Категория:</span>
                  <span className="book-detail-value">{formatCategory()}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Авторы:</span>
                  <span className="book-detail-value">{formatAuthors()}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Издательство:</span>
                  <span className="book-detail-value">{formatPublisher()}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Место издания:</span>
                  <span className="book-detail-value">{formatField(book.publication_place)}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Год издания:</span>
                  <span className="book-detail-value">
                    {book.year ? book.year : (book.year_approx || 'Не указан')}
                  </span>
                </div>
              </section>

              {/* Физические характеристики */}
              <section className="book-detail-section">
                <div className="book-detail-field">
                  <span className="book-detail-label">Тираж:</span>
                  <span className="book-detail-value">{formatField(book.circulation, 'Не указан')}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Язык текста:</span>
                  <span className="book-detail-value">{formatLanguage()}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Количество страниц:</span>
                  <span className="book-detail-value">{formatField(book.pages_info)}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Тип переплета:</span>
                  <span className="book-detail-value">{formatBindingType()}</span>
                </div>
                {book.binding_details && (
                  <div className="book-detail-field">
                    <span className="book-detail-label">Детали переплета:</span>
                    <span className="book-detail-value">{book.binding_details}</span>
                  </div>
                )}
                <div className="book-detail-field">
                  <span className="book-detail-label">Формат:</span>
                  <span className="book-detail-value">{formatFormat()}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Состояние:</span>
                  <span className="book-detail-value">{formatCondition()}</span>
                </div>
                {book.condition_details && (
                  <div className="book-detail-field">
                    <span className="book-detail-label">Детали состояния:</span>
                    <span className="book-detail-value">{book.condition_details}</span>
                  </div>
                )}
              </section>

              {/* Коммерческая информация */}
              <section className="book-detail-section">
                <div className="book-detail-field">
                  <span className="book-detail-label">Цена в рублях:</span>
                  <span className="book-detail-value">
                    {book.price_rub ? `${book.price_rub} ₽` : 'Не указана'}
                  </span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Код продавца:</span>
                  <span className="book-detail-value">{formatField(book.seller_code)}</span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">ISBN:</span>
                  <span className="book-detail-value">{formatField(book.isbn)}</span>
                </div>
              </section>

              {/* Дополнительная информация */}
              <section className="book-detail-section">
                {book.description && (
                  <div className="book-detail-field book-detail-field-full">
                    <span className="book-detail-label">Описание:</span>
                    <span className="book-detail-value">{book.description}</span>
                  </div>
                )}
                <div className="book-detail-field">
                  <span className="book-detail-label">Статус чтения:</span>
                  <span className="book-detail-value">
                    {formatStatus()}
                    {book.status === 'read' && getFirstReadingDate() && (
                      <span className="book-detail-reading-date">
                        {' '}(прочитано {formatDate(getFirstReadingDate())})
                      </span>
                    )}
                  </span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Библиотека:</span>
                  <span className="book-detail-value">
                    {book.library_name || (book.library ? (typeof book.library === 'string' ? book.library : book.library.name) : 'Не указана')}
                  </span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Владелец:</span>
                  <span className="book-detail-value">
                    {book.owner_username || (book.owner ? (typeof book.owner === 'string' ? book.owner : book.owner.username) : 'Не указан')}
                  </span>
                </div>
                <div className="book-detail-field">
                  <span className="book-detail-label">Дата размещения:</span>
                  <span className="book-detail-value">
                    {book.created_at ? new Date(book.created_at).toLocaleDateString('ru-RU') : 'Не указана'}
                  </span>
                </div>
              </section>

              {/* Связанные данные */}
              {((book.hashtags && book.hashtags.length > 0) || 
                (book.reading_dates && book.reading_dates.length > 0)) && (
                <section className="book-detail-section">
                  {book.hashtags && book.hashtags.length > 0 && (
                    <div className="book-detail-field book-detail-field-full">
                      <span className="book-detail-label">Хэштеги:</span>
                      <span className="book-detail-value">
                        {book.hashtags.map(h => {
                          if (typeof h === 'string') return h;
                          return h.name || h.slug || h;
                        }).join(', ')}
                      </span>
                    </div>
                  )}
                  {book.reading_dates && book.reading_dates.length > 0 && (
                    <div className="book-detail-field book-detail-field-full">
                      <span className="book-detail-label">Даты прочтения:</span>
                      <span className="book-detail-value">
                        {book.reading_dates.map(d => {
                          if (typeof d === 'string') return d;
                          return d.date || d;
                        }).join(', ')}
                      </span>
                    </div>
                  )}
                </section>
              )}
              
              {/* Электронные версии */}
              {book.electronic_versions && book.electronic_versions.length > 0 && (
                <section className="book-detail-section book-detail-section-electronic">
                  <div className="book-detail-field book-detail-field-full">
                    <span className="book-detail-label">Электронные версии:</span>
                    <div className="book-detail-electronic-versions">
                      {book.electronic_versions.map((version, index) => {
                        const downloadUrl = version.file_url || version.url;
                        if (!downloadUrl) return null;
                        
                        // Иконки для разных форматов
                        const formatIcons = {
                          'pdf': '📄',
                          'epub': '📖',
                          'mobi': '📱',
                          'fb2': '📚',
                          'djvu': '📑',
                          'txt': '📝',
                          'rtf': '📄',
                          'doc': '📄',
                          'docx': '📄'
                        };
                        
                        const formatLabels = {
                          'pdf': 'PDF',
                          'epub': 'EPUB',
                          'mobi': 'MOBI',
                          'fb2': 'FB2',
                          'djvu': 'DJVU',
                          'txt': 'TXT',
                          'rtf': 'RTF',
                          'doc': 'DOC',
                          'docx': 'DOCX'
                        };
                        
                        const icon = formatIcons[version.format] || '📄';
                        const label = formatLabels[version.format] || version.format.toUpperCase();
                        
                        return (
                          <a
                            key={version.id || index}
                            href={downloadUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="book-detail-electronic-version"
                            title={`Скачать ${label}`}
                          >
                            <span className="book-detail-electronic-icon">{icon}</span>
                            <span className="book-detail-electronic-label">{label}</span>
                          </a>
                        );
                      })}
                    </div>
                  </div>
                </section>
              )}

              {/* Отзывы */}
              <section className="book-detail-section book-detail-section-reviews">
                <div className="book-detail-field book-detail-field-full">
                  <div className="book-detail-reviews-header">
                    <span className="book-detail-label">
                      Отзывы {book.reviews && book.reviews.length > 0 ? `(${book.reviews.length})` : ''}:
                    </span>
                    {book.average_rating !== null && book.average_rating !== undefined && (
                      <div className="book-detail-average-rating">
                        <span className="book-detail-average-rating-label">Средний рейтинг:</span>
                        <StarRating rating={book.average_rating} size="medium" showValue={true} />
                      </div>
                    )}
                  </div>
                  {book.reviews && book.reviews.length > 0 ? (
                    <>
                      <div className="book-detail-reviews-list">
                        {book.reviews.map((review) => (
                          <ReviewItem
                            key={review.id}
                            review={review}
                            currentUserId={currentUserId}
                            onEdit={handleEditReview}
                            onDelete={handleDeleteReview}
                          />
                        ))}
                      </div>
                      {/* Проверяем, есть ли у текущего пользователя отзыв */}
                      {currentUserId && !book.reviews.some(review => {
                        const reviewUserId = typeof review.user === 'object' && review.user !== null 
                          ? review.user.id 
                          : review.user;
                        return reviewUserId === currentUserId;
                      }) && (
                        <div className="book-detail-add-review-section">
                          <button 
                            className="book-detail-add-review-button"
                            onClick={() => {
                              // Устанавливаем пустой объект для создания нового отзыва
                              setEditingReview({});
                            }}
                          >
                            Оставить отзыв
                          </button>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="book-detail-no-reviews">
                      <p>Пока нет отзывов. Будьте первым, кто оставит отзыв!</p>
                      {currentUserId && (
                        <button 
                          className="book-detail-add-review-button"
                          onClick={() => {
                            // Устанавливаем пустой объект для создания нового отзыва
                            setEditingReview({});
                          }}
                        >
                          Оставить отзыв
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </section>
            </div>
          )}
        </div>

        {!loading && !error && book && (
          <div className="book-detail-modal-footer">
            <button className="book-detail-button book-detail-button-edit" onClick={handleEdit}>
              Редактировать
            </button>
            <button className="book-detail-button book-detail-button-transfer" onClick={handleTransfer}>
              Передать
            </button>
            <button className="book-detail-button book-detail-button-delete" onClick={handleDelete}>
              Удалить
            </button>
            <button className="book-detail-button book-detail-button-close" onClick={handleClose}>
              Закрыть
            </button>
          </div>
        )}
      </div>

      {/* Модальное окно редактирования отзыва */}
      {editingReview !== null && editingReview !== undefined && (
        <EditReviewModal
          isOpen={true}
          review={editingReview.id ? editingReview : null}
          bookId={book?.id}
          onSave={handleSaveReview}
          onCancel={handleCancelEditReview}
        />
      )}

      {/* Модальное окно подтверждения удаления отзыва */}
      {confirmDelete && (
        <ConfirmModal
          isOpen={true}
          title={confirmDelete.error ? 'Ошибка' : 'Подтверждение удаления'}
          message={confirmDelete.message}
          confirmText={confirmDelete.error ? 'ОК' : 'Удалить'}
          cancelText={confirmDelete.error ? null : 'Отмена'}
          danger={!confirmDelete.error}
          onConfirm={confirmDelete.error ? handleCancelDeleteReview : handleConfirmDeleteReview}
          onCancel={confirmDelete.error ? handleCancelDeleteReview : handleCancelDeleteReview}
        />
      )}
    </div>
  );
};

export default BookDetailModal;

