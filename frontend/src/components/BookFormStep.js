import { useState, useEffect } from 'react';
import { categoriesAPI, publishersAPI, authorsAPI } from '../services/api';
import PublisherAutocomplete from './PublisherAutocomplete';
import AuthorAutocomplete from './AuthorAutocomplete';
import './BookFormStep.css';

const BookFormStep = ({ autoFillData, onFormDataChange, onNext, onBack }) => {
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  // Загружаем категории при монтировании компонента
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setLoadingCategories(true);
        const categoriesData = await categoriesAPI.getTree();
        // Преобразуем дерево категорий в плоский список для select
        const flattenCategories = (cats, parentName = '') => {
          let result = [];
          cats.forEach(cat => {
            const fullName = parentName ? `${parentName} → ${cat.name}` : cat.name;
            result.push({
              id: cat.id,
              name: cat.name,
              fullName: fullName,
              code: cat.code
            });
            if (cat.subcategories && cat.subcategories.length > 0) {
              result = result.concat(flattenCategories(cat.subcategories, fullName));
            }
          });
          return result;
        };
        const flatCategories = flattenCategories(Array.isArray(categoriesData) ? categoriesData : (categoriesData.results || []));
        setCategories(flatCategories);
      } catch (error) {
        console.error('Ошибка загрузки категорий:', error);
      } finally {
        setLoadingCategories(false);
      }
    };
    loadCategories();
  }, []);

  const [formData, setFormData] = useState(() => {
    const initial = {
      title: '',
      subtitle: '',
      authors: [], // Массив объектов авторов {id, full_name}
      author_ids: [], // Массив ID авторов для отправки на сервер
      publisher: null, // ID издательства для отправки на сервер
      publisher_name: '', // Название для отображения
      publisher_website: '', // Сайт издательства для отображения ссылки
      publication_place: '',
      year: '',
      year_approx: '',
      category_id: null,
      language_name: '',
      pages_info: '',
      circulation: '',
      binding_type: '',
      binding_details: '',
      format: '',
      condition: '',
      condition_details: '',
      isbn: '',
      description: '',
      authors_display: ''
    };
    
    // Если есть данные от LLM, используем их для предзаполнения
    if (autoFillData) {
      return {
        ...initial,
        ...autoFillData,
        authors_display: Array.isArray(autoFillData.authors) 
          ? autoFillData.authors.join(', ') 
          : '',
        // Убеждаемся, что category_id правильно обработан
        category_id: autoFillData.category_id !== null && autoFillData.category_id !== undefined
          ? (typeof autoFillData.category_id === 'number' ? autoFillData.category_id : parseInt(autoFillData.category_id))
          : null
      };
    }
    
    return initial;
  });

  // Обновляем форму при изменении autoFillData
  useEffect(() => {
    if (autoFillData && categories.length > 0) {
      console.log('BookFormStep: получены данные от LLM:', autoFillData);
      setFormData(prev => {
        const categoryId = autoFillData.category_id !== null && autoFillData.category_id !== undefined
          ? (typeof autoFillData.category_id === 'number' ? autoFillData.category_id : parseInt(autoFillData.category_id))
          : null;
        
        // Находим категорию по ID для отображения
        const selectedCategory = categoryId ? categories.find(cat => cat.id === categoryId) : null;
        
        const updated = {
          ...prev,
          ...autoFillData,
          // Авторы будут обработаны отдельно после поиска
          authors: [],
          author_ids: [],
          // Убеждаемся, что category_id правильно обработан
          category_id: categoryId,
          // Для издательства: если LLM вернул publisher_name, ищем в базе
          publisher: null, // Будет установлено после поиска
        };
        console.log('BookFormStep: обновленные данные формы:', updated);
        console.log('BookFormStep: category_id:', updated.category_id, 'найдена категория:', selectedCategory);
        return updated;
      });

      // Если LLM вернул publisher_name, ищем издательство в базе
      if (autoFillData.publisher_name && autoFillData.publisher_name.trim()) {
        const searchPublisher = async () => {
          try {
            const results = await publishersAPI.search(autoFillData.publisher_name.trim());
            const publishers = Array.isArray(results) ? results : (results.results || []);
            if (publishers.length > 0) {
              // Находим точное совпадение или берем первое
              const exactMatch = publishers.find(p => 
                p.name.toLowerCase() === autoFillData.publisher_name.toLowerCase()
              );
              const selectedPublisher = exactMatch || publishers[0];
              setFormData(prev => ({
                ...prev,
                publisher: selectedPublisher.id, // Сохраняем ID для отправки на сервер
                publisher_name: selectedPublisher.name, // Название для отображения
                publisher_website: selectedPublisher.website || '', // Сайт для отображения ссылки
              }));
            }
          } catch (error) {
            console.error('Ошибка поиска издательства:', error);
            // Оставляем publisher_name как есть, пользователь сможет создать новое
          }
        };
        searchPublisher();
      }

      // Если LLM вернул авторов, ищем их в базе
      if (autoFillData.authors && Array.isArray(autoFillData.authors) && autoFillData.authors.length > 0) {
        console.log('BookFormStep: начинаем поиск авторов от LLM:', autoFillData.authors);
        const searchAuthors = async () => {
          try {
            const foundAuthors = [];
            // Ищем каждого автора по отдельности
            for (const authorName of autoFillData.authors.slice(0, 3)) {
              // authorName может быть строкой или объектом
              const nameToSearch = typeof authorName === 'string' 
                ? authorName.trim() 
                : (authorName.full_name || authorName.name || '').trim();
              
              if (nameToSearch) {
                console.log(`BookFormStep: ищем автора "${nameToSearch}"`);
                try {
                  const results = await authorsAPI.search(nameToSearch);
                  const authors = Array.isArray(results) ? results : (results.results || []);
                  console.log(`BookFormStep: найдено авторов для "${nameToSearch}":`, authors.length, authors);
                  
                  if (authors.length > 0) {
                    // Находим точное совпадение или берем первое
                    const exactMatch = authors.find(a => 
                      a.full_name.toLowerCase() === nameToSearch.toLowerCase()
                    );
                    const selectedAuthor = exactMatch || authors[0];
                    console.log(`BookFormStep: выбран автор:`, selectedAuthor);
                    foundAuthors.push(selectedAuthor);
                  } else {
                    console.log(`BookFormStep: автор "${nameToSearch}" не найден в базе`);
                  }
                } catch (error) {
                  console.error(`Ошибка поиска автора "${nameToSearch}":`, error);
                  // Пропускаем этого автора, пользователь сможет добавить вручную
                }
              }
            }
            
            console.log('BookFormStep: итоговый список найденных авторов:', foundAuthors);
            
            // Если авторы не найдены в базе, создаем временные объекты для отображения
            // (без id, чтобы пользователь мог их создать позже)
            const allAuthors = [...foundAuthors];
            const notFoundNames = autoFillData.authors
              .slice(0, 3)
              .map(name => typeof name === 'string' ? name.trim() : (name.full_name || name.name || '').trim())
              .filter(name => name && !foundAuthors.some(found => found.full_name.toLowerCase() === name.toLowerCase()));
            
            // Создаем временные объекты для авторов, которых нет в базе
            notFoundNames.forEach((name, index) => {
              allAuthors.push({
                id: `temp-${Date.now()}-${index}`, // Временный ID
                full_name: name,
                isTemporary: true // Флаг, что это временный автор
              });
            });
            
            if (allAuthors.length > 0) {
              console.log('BookFormStep: устанавливаем авторов (найденные + временные):', allAuthors);
              setFormData(prev => ({
                ...prev,
                authors: allAuthors,
                // Сохраняем только ID реальных авторов (не временных)
                author_ids: foundAuthors.map(a => a.id),
              }));
            } else {
              console.log('BookFormStep: авторы не найдены, оставляем пустой массив');
            }
          } catch (error) {
            console.error('Ошибка поиска авторов:', error);
          }
        };
        searchAuthors();
      } else {
        console.log('BookFormStep: авторы от LLM отсутствуют или не являются массивом:', autoFillData.authors);
      }
    }
  }, [autoFillData, categories]);

  const handleChange = (field, value) => {
    console.log(`BookFormStep: handleChange вызван для поля "${field}" со значением:`, value);
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      console.log(`BookFormStep: handleChange обновляет formData для "${field}":`, updated);
      if (onFormDataChange) {
        onFormDataChange(updated);
      }
      return updated;
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    e.stopPropagation(); // Предотвращаем всплытие события
    
    // Проверяем, не было ли это событие из модального окна
    if (e.target.closest('.create-author-modal') || e.target.closest('.create-publisher-modal')) {
      return; // Игнорируем submit из модальных окон
    }
    
    if (!formData.title || formData.title.trim() === '') {
      alert('Название книги обязательно для заполнения');
      return;
    }
    if (onNext) {
      onNext({ formData });
    }
  };

  return (
    <div className="book-form-step">
      <div className="book-form-header">
        <h3>Заполнение данных книги</h3>
        {autoFillData && (
          <p className="book-form-hint">
            Данные предзаполнены автоматически. Вы можете их отредактировать.
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="book-form">
        <div className="form-group">
          <label htmlFor="title" className="required">
            Название книги *
          </label>
          <input
            type="text"
            id="title"
            value={formData.title || ''}
            onChange={(e) => handleChange('title', e.target.value)}
            placeholder="Введите название книги"
            required
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="subtitle">Подзаголовок</label>
          <input
            type="text"
            id="subtitle"
            value={formData.subtitle || ''}
            onChange={(e) => handleChange('subtitle', e.target.value)}
            placeholder="Введите подзаголовок"
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="authors">Авторы</label>
          <AuthorAutocomplete
            selectedAuthors={formData.authors || []}
            onChange={(authors) => {
              console.log('BookFormStep: onChange вызван с авторами:', authors);
              handleChange('authors', authors);
              // Сохраняем только ID реальных авторов (не временных с temp- префиксом)
              const realAuthorIds = authors
                .filter(a => a.id && !String(a.id).startsWith('temp-'))
                .map(a => a.id);
              console.log('BookFormStep: realAuthorIds:', realAuthorIds);
              handleChange('author_ids', realAuthorIds);
              console.log('BookFormStep: formData после обновления:', { ...formData, authors, author_ids: realAuthorIds });
            }}
            maxAuthors={3}
            placeholder="Введите автора"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="publisher">Издательство</label>
            <PublisherAutocomplete
              value={formData.publisher_name || ''}
              onChange={(publisher) => {
                if (publisher && typeof publisher === 'object' && publisher.id) {
                  // Выбрано издательство из базы - сохраняем и объект (для отображения), и ID (для отправки)
                  handleChange('publisher', publisher.id); // ID для отправки на сервер
                  handleChange('publisher_name', publisher.name); // Название для отображения
                  handleChange('publisher_website', publisher.website || ''); // Сайт для отображения ссылки
                } else if (typeof publisher === 'string') {
                  // Введен текст вручную (для обратной совместимости)
                  handleChange('publisher_name', publisher);
                  handleChange('publisher', null);
                  handleChange('publisher_website', '');
                } else {
                  // Очищено
                  handleChange('publisher', null);
                  handleChange('publisher_name', '');
                  handleChange('publisher_website', '');
                }
              }}
              placeholder="Введите издательство"
            />
            {formData.publisher && formData.publisher_website && (
              <div className="form-hint">
                <a
                  href={formData.publisher_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="publisher-website-link"
                >
                  {formData.publisher_website}
                </a>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="publication_place">Место издания</label>
            <input
              type="text"
              id="publication_place"
              value={formData.publication_place || ''}
              onChange={(e) => handleChange('publication_place', e.target.value)}
              placeholder="Введите место издания"
              className="form-input"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="year">Год издания</label>
            <input
              type="number"
              id="year"
              value={formData.year || ''}
              onChange={(e) => handleChange('year', e.target.value)}
              placeholder="Год"
              min="0"
              max="2100"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="year_approx">Приблизительный год</label>
            <input
              type="text"
              id="year_approx"
              value={formData.year_approx || ''}
              onChange={(e) => handleChange('year_approx', e.target.value)}
              placeholder="Например: 197?, 18??"
              className="form-input"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="category_id">Рубрика (категория)</label>
          {loadingCategories ? (
            <div className="form-input" style={{ color: '#666', fontStyle: 'italic', padding: '10px 12px' }}>
              Загрузка категорий...
            </div>
          ) : (
            <select
              id="category_id"
              value={formData.category_id || ''}
              onChange={(e) => {
                const selectedId = e.target.value ? parseInt(e.target.value) : null;
                handleChange('category_id', selectedId);
              }}
              className="form-input"
            >
              <option value="">Не определено</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.fullName}
                </option>
              ))}
            </select>
          )}
          {formData.category_id && !loadingCategories && (
            (() => {
              const selectedCategory = categories.find(cat => cat.id === formData.category_id);
              return selectedCategory ? (
                <div className="form-hint">
                  Выбрана категория: {selectedCategory.fullName}
                </div>
              ) : null;
            })()
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="pages_info">Страниц</label>
            <input
              type="text"
              id="pages_info"
              value={formData.pages_info || ''}
              onChange={(e) => handleChange('pages_info', e.target.value)}
              placeholder="Например: 256 стр., 16 иллюстраций"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="circulation">Тираж</label>
            <input
              type="number"
              id="circulation"
              value={formData.circulation || ''}
              onChange={(e) => handleChange('circulation', e.target.value)}
              placeholder="Количество экземпляров"
              min="1"
              className="form-input"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="language_name">Язык текста</label>
          <input
            type="text"
            id="language_name"
            value={formData.language_name || ''}
            onChange={(e) => handleChange('language_name', e.target.value)}
            placeholder="Например: Русский, Английский"
            className="form-input"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="binding_type">Тип переплёта</label>
            <select
              id="binding_type"
              value={formData.binding_type || ''}
              onChange={(e) => handleChange('binding_type', e.target.value)}
              className="form-input"
            >
              <option value="">Не определено</option>
              <option value="paper">Бумажный (обложка)</option>
              <option value="selfmade">Самодельный</option>
              <option value="cardboard">Картонный</option>
              <option value="hard">Твердый</option>
              <option value="fabric">Тканевый</option>
              <option value="owner">Владельческий</option>
              <option value="halfleather">Полукожаный</option>
              <option value="composite">Составной</option>
              <option value="leather">Кожаный</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="format">Формат книги</label>
            <select
              id="format"
              value={formData.format || ''}
              onChange={(e) => handleChange('format', e.target.value)}
              className="form-input"
            >
              <option value="">Не определено</option>
              <option value="very_large">Очень большой (свыше 28 см)</option>
              <option value="encyclopedic">Энциклопедический (25-27 см)</option>
              <option value="increased">Увеличенный (22-24 см)</option>
              <option value="regular">Обычный (19-21 см)</option>
              <option value="reduced">Уменьшенный (11-18 см)</option>
              <option value="miniature">Миниатюрный (менее 10 см)</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="binding_details">Детали переплёта</label>
          <input
            type="text"
            id="binding_details"
            value={formData.binding_details || ''}
            onChange={(e) => handleChange('binding_details', e.target.value)}
            placeholder="Например: Синий, тканевый"
            className="form-input"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="condition">Состояние</label>
            <select
              id="condition"
              value={formData.condition || ''}
              onChange={(e) => handleChange('condition', e.target.value)}
              className="form-input"
            >
              <option value="">Не определено</option>
              <option value="ideal">Идеальное</option>
              <option value="excellent">Отличное</option>
              <option value="good">Хорошее</option>
              <option value="satisfactory">Удовлетворительное</option>
              <option value="poor">Плохое</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="isbn">ISBN</label>
            <input
              type="text"
              id="isbn"
              value={formData.isbn || ''}
              onChange={(e) => handleChange('isbn', e.target.value)}
              placeholder="Введите ISBN"
              className="form-input"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="condition_details">Детали состояния</label>
          <textarea
            id="condition_details"
            value={formData.condition_details || ''}
            onChange={(e) => handleChange('condition_details', e.target.value)}
            placeholder="Например: Отсутствуют страницы 5-8, загрязнения на обложке"
            rows="3"
            className="form-textarea"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Содержание/Аннотация</label>
          <textarea
            id="description"
            value={formData.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Введите описание содержания книги"
            rows="4"
            className="form-textarea"
          />
        </div>

        <div className="wizard-navigation">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="wizard-button wizard-button-back"
            >
              ← Назад
            </button>
          )}
          <button
            type="submit"
            className="wizard-button wizard-button-next"
            disabled={!formData.title || formData.title.trim() === ''}
          >
            Далее →
          </button>
        </div>
      </form>
    </div>
  );
};

export default BookFormStep;

