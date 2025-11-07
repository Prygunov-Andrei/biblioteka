import { useState, useEffect, useRef } from 'react';
import { booksAPI, categoriesAPI, publishersAPI, authorsAPI, librariesAPI } from '../services/api';
import PublisherAutocomplete from './PublisherAutocomplete';
import AuthorAutocomplete from './AuthorAutocomplete';
import ConfirmModal from './ConfirmModal';
import './BookEditModal.css';

const BookEditModal = ({ book, isOpen, onClose, onSave }) => {
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [libraries, setLibraries] = useState([]);
  const [loadingLibraries, setLoadingLibraries] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const isSearchingAuthorsRef = useRef(false);
  const initialFormDataRef = useRef(null);
  
  // Состояние для дат прочтения
  const [readingDates, setReadingDates] = useState([]);
  const [loadingReadingDates, setLoadingReadingDates] = useState(false);
  const [newReadingDate, setNewReadingDate] = useState('');
  const [newReadingDateNotes, setNewReadingDateNotes] = useState('');
  const [confirmDeleteReadingDate, setConfirmDeleteReadingDate] = useState(null);
  
  // Состояние для страниц
  const [bookPages, setBookPages] = useState([]);
  const [loadingPages, setLoadingPages] = useState(false);
  const [uploadingPages, setUploadingPages] = useState(false);
  const [confirmDeletePage, setConfirmDeletePage] = useState(null);
  const fileInputRef = useRef(null);
  
  // Состояние для электронных версий
  const [electronicVersions, setElectronicVersions] = useState([]);
  const [loadingElectronicVersions, setLoadingElectronicVersions] = useState(false);
  const [confirmDeleteElectronicVersion, setConfirmDeleteElectronicVersion] = useState(null);
  const [addingElectronicVersion, setAddingElectronicVersion] = useState(false);
  const [newElectronicVersion, setNewElectronicVersion] = useState({
    format: '',
    url: '',
    file: null
  });
  const electronicFileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    title: '',
    subtitle: '',
    authors: [],
    author_ids: [],
    publisher: null,
    publisher_name: '',
    publisher_website: '',
    publication_place: '',
    year: '',
    year_approx: '',
    category_id: null,
    category_name: null,
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
    status: 'none',
    library: null,
  });

  // Загружаем категории при монтировании
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setLoadingCategories(true);
        const categoriesData = await categoriesAPI.getTree();
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

  // Загружаем библиотеки пользователя при монтировании
  useEffect(() => {
    const loadLibraries = async () => {
      try {
        setLoadingLibraries(true);
        const librariesData = await librariesAPI.getMyLibraries();
        setLibraries(Array.isArray(librariesData) ? librariesData : (librariesData.results || []));
      } catch (error) {
        console.error('Ошибка загрузки библиотек:', error);
      } finally {
        setLoadingLibraries(false);
      }
    };
    loadLibraries();
  }, []);

  // Загружаем данные книги при открытии модального окна
  useEffect(() => {
    if (isOpen && book) {
      // Сбрасываем состояние при открытии
      setHasChanges(false);
      setError(null);
      initialFormDataRef.current = null;
      loadBookData();
    } else if (!isOpen) {
      // Сбрасываем состояние при закрытии
      setHasChanges(false);
      initialFormDataRef.current = null;
      setFormData({
        title: '',
        subtitle: '',
        authors: [],
        author_ids: [],
        publisher: null,
        publisher_name: '',
        publisher_website: '',
        publication_place: '',
        year: '',
        year_approx: '',
        category_id: null,
        category_name: null,
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
        status: 'none',
        library: null,
      });
      // Сбрасываем состояние электронных версий
      setNewElectronicVersion({
        format: '',
        url: '',
        file: null
      });
      if (electronicFileInputRef.current) {
        electronicFileInputRef.current.value = '';
      }
    }
  }, [isOpen, book]);

  const loadBookData = async () => {
    if (!book) return;

    try {
      setLoading(true);
      setError(null);

      // Загружаем полные данные книги
      const bookData = await booksAPI.getById(book.id);
      
      // Загружаем дополнительные данные (даты прочтения, страницы, электронные версии)
      loadAdditionalData(book.id, bookData.status);

      // Преобразуем данные книги в формат формы
      const authors = bookData.authors || [];
      const authorsList = authors.map(author => ({
        id: author.id,
        full_name: author.full_name,
        isTemporary: false
      }));

      const initialData = {
        title: bookData.title || '',
        subtitle: bookData.subtitle || '',
        authors: authorsList,
        author_ids: authors.map(a => a.id),
        publisher: bookData.publisher || null,
        publisher_name: bookData.publisher_name || '',
        publisher_website: bookData.publisher?.website || '',
        publication_place: bookData.publication_place || '',
        year: bookData.year ? String(bookData.year) : '',
        year_approx: bookData.year_approx || '',
        category_id: bookData.category || null,
        category_name: bookData.category_name || null,
        language_name: bookData.language_name || '',
        pages_info: bookData.pages_info || '',
        circulation: bookData.circulation ? String(bookData.circulation) : '',
        binding_type: bookData.binding_type || '',
        binding_details: bookData.binding_details || '',
        format: bookData.format || '',
        condition: bookData.condition || '',
        condition_details: bookData.condition_details || '',
        isbn: bookData.isbn || '',
        description: bookData.description || '',
        status: bookData.status || 'none',
        library: bookData.library || null,
      };

      initialFormDataRef.current = JSON.stringify(initialData);
      setFormData(initialData);
      setHasChanges(false);
    } catch (err) {
      console.error('Ошибка загрузки данных книги:', err);
      setError('Не удалось загрузить данные книги');
    } finally {
      setLoading(false);
    }
  };

  const loadAdditionalData = async (bookId, status) => {
    // Загружаем даты прочтения только для статусов 'read' и 'want_to_reread'
    if (status === 'read' || status === 'want_to_reread') {
      try {
        setLoadingReadingDates(true);
        const dates = await booksAPI.getReadingDates(bookId);
        setReadingDates(dates || []);
      } catch (err) {
        console.error('Ошибка загрузки дат прочтения:', err);
      } finally {
        setLoadingReadingDates(false);
      }
    } else {
      setReadingDates([]);
    }
    
    // Загружаем страницы книги
    try {
      setLoadingPages(true);
      const pages = await booksAPI.getPages(bookId);
      setBookPages(pages || []);
    } catch (err) {
      console.error('Ошибка загрузки страниц:', err);
      // Если страниц нет или произошла ошибка, используем данные из bookData
      try {
        const bookData = await booksAPI.getById(bookId);
        setBookPages(bookData.pages_set || bookData.pages || []);
      } catch (e) {
        setBookPages([]);
      }
    } finally {
      setLoadingPages(false);
    }
    
    // Загружаем электронные версии
    try {
      setLoadingElectronicVersions(true);
      // Электронные версии уже загружены в bookData
      // Но можно загрузить отдельно, если нужно
      const bookData = await booksAPI.getById(bookId);
      setElectronicVersions(bookData.electronic_versions || []);
    } catch (err) {
      console.error('Ошибка загрузки электронных версий:', err);
    } finally {
      setLoadingElectronicVersions(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      // Проверяем, есть ли изменения
      const currentDataStr = JSON.stringify(updated);
      setHasChanges(currentDataStr !== initialFormDataRef.current);
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.target.closest('.create-author-modal') || e.target.closest('.create-publisher-modal')) {
      return;
    }

    if (!formData.title || formData.title.trim() === '') {
      setError('Название книги обязательно для заполнения');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Подготавливаем данные для отправки
      const updateData = {
        title: formData.title,
        subtitle: formData.subtitle || null,
        category: formData.category_id || null,
        author_ids: formData.author_ids || [],
        publisher: formData.publisher || null,
        publication_place: formData.publication_place || null,
        year: formData.year ? (isNaN(parseInt(formData.year)) ? null : parseInt(formData.year)) : null,
        year_approx: formData.year_approx || null,
        pages_info: formData.pages_info || null,
        circulation: formData.circulation ? (isNaN(parseInt(formData.circulation)) ? null : parseInt(formData.circulation)) : null,
        // language_name передаем только если он не пустой
        binding_type: formData.binding_type || null,
        binding_details: formData.binding_details || null,
        format: formData.format || null,
        condition: formData.condition || null,
        condition_details: formData.condition_details || null,
        isbn: formData.isbn ? (formData.isbn.includes(',') ? formData.isbn.split(',')[0].trim() : formData.isbn.trim()).substring(0, 20) : null,
        description: formData.description || null,
        status: formData.status || 'none',
        library: formData.library || null,
      };

      // Добавляем language_name только если он не пустой
      if (formData.language_name && formData.language_name.trim()) {
        updateData.language_name = formData.language_name.trim();
      }

      // Удаляем null и undefined значения
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === null || updateData[key] === undefined || updateData[key] === '') {
          if (key !== 'status' && key !== 'library') {
            delete updateData[key];
          }
        }
      });

      console.log('BookEditModal: отправляем данные для обновления:', JSON.stringify(updateData, null, 2));

      const updatedBook = await booksAPI.update(book.id, updateData);
      
      console.log('✅ BookEditModal: книга успешно обновлена:', updatedBook);

      // Обновляем initialFormDataRef, чтобы при следующем открытии не было ложного предупреждения
      // Перезагружаем данные книги для получения актуального состояния
      // Небольшая задержка, чтобы сервер точно обработал изменения
      await new Promise(resolve => setTimeout(resolve, 100));
      const refreshedBookData = await booksAPI.getById(book.id);
      console.log('🔄 BookEditModal: перезагружены данные книги после сохранения:', refreshedBookData);
      const authors = refreshedBookData.authors || [];
      const authorsList = authors.map(author => ({
        id: author.id,
        full_name: author.full_name,
        isTemporary: false
      }));

      const refreshedData = {
        title: refreshedBookData.title || '',
        subtitle: refreshedBookData.subtitle || '',
        authors: authorsList,
        author_ids: authors.map(a => a.id),
        publisher: refreshedBookData.publisher || null,
        publisher_name: refreshedBookData.publisher_name || '',
        publisher_website: refreshedBookData.publisher?.website || '',
        publication_place: refreshedBookData.publication_place || '',
        year: refreshedBookData.year ? String(refreshedBookData.year) : '',
        year_approx: refreshedBookData.year_approx || '',
        category_id: refreshedBookData.category || null,
        category_name: refreshedBookData.category_name || null,
        language_name: refreshedBookData.language_name || '',
        pages_info: refreshedBookData.pages_info || '',
        circulation: refreshedBookData.circulation ? String(refreshedBookData.circulation) : '',
        binding_type: refreshedBookData.binding_type || '',
        binding_details: refreshedBookData.binding_details || '',
        format: refreshedBookData.format || '',
        condition: refreshedBookData.condition || '',
        condition_details: refreshedBookData.condition_details || '',
        isbn: refreshedBookData.isbn || '',
        description: refreshedBookData.description || '',
        status: refreshedBookData.status || 'none',
        library: refreshedBookData.library || null,
      };
      initialFormDataRef.current = JSON.stringify(refreshedData);
      setHasChanges(false);

      if (onSave) {
        // Передаем ID книги, чтобы MainPage мог обновить BookDetailModal
        onSave({ id: book.id, ...updatedBook });
      }

      // Закрываем без показа предупреждения, так как изменения сохранены
      onClose();
    } catch (err) {
      console.error('Ошибка обновления книги:', err);
      console.error('Детали ошибки:', err.response?.data);

      let errorMessage = 'Не удалось обновить книгу';
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (typeof errorData === 'object') {
          const fieldErrors = [];
          for (const [field, messages] of Object.entries(errorData)) {
            if (Array.isArray(messages)) {
              fieldErrors.push(`${field}: ${messages.join(', ')}`);
            } else if (typeof messages === 'string') {
              fieldErrors.push(`${field}: ${messages}`);
            }
          }
          if (fieldErrors.length > 0) {
            errorMessage = 'Ошибки валидации:\n' + fieldErrors.join('\n');
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Примечание: язык обрабатывается на бэкенде через language_name
  // В BookUpdateSerializer нет поддержки language_name, поэтому нужно использовать language (ID)
  // Но для простоты пока передаем null, если язык не найден - бэкенд не обновит поле

  const handleClose = () => {
    // Если есть несохраненные изменения, показываем подтверждение
    // Но только если модальное окно действительно было открыто и пользователь что-то менял
    if (hasChanges && initialFormDataRef.current !== null) {
      setShowCancelConfirm(true);
    } else {
      // Если изменений нет или данные еще не загружены, просто закрываем
      onClose();
    }
  };

  const handleConfirmCancel = () => {
    setShowCancelConfirm(false);
    setHasChanges(false);
    // Восстанавливаем исходные данные
    if (initialFormDataRef.current) {
      try {
        const originalData = JSON.parse(initialFormDataRef.current);
        setFormData(originalData);
      } catch (e) {
        console.error('Ошибка восстановления данных:', e);
      }
    }
    onClose();
  };

  const handleCancelConfirmCancel = () => {
    setShowCancelConfirm(false);
  };

  // Обработчики для дат прочтения
  const handleAddReadingDate = async () => {
    if (!newReadingDate) {
      setError('Укажите дату прочтения');
      return;
    }

    try {
      const addedDate = await booksAPI.addReadingDate(book.id, newReadingDate, newReadingDateNotes);
      setReadingDates(prev => [...prev, addedDate].sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return dateB - dateA; // Сортировка по убыванию (новые первыми)
      }));
      setNewReadingDate('');
      setNewReadingDateNotes('');
      setError(null);
    } catch (err) {
      console.error('Ошибка добавления даты прочтения:', err);
      setError(err.response?.data?.error || 'Не удалось добавить дату прочтения');
    }
  };

  const handleDeleteReadingDate = async (dateId) => {
    try {
      await booksAPI.deleteReadingDate(book.id, dateId);
      setReadingDates(prev => prev.filter(d => d.id !== dateId));
      setConfirmDeleteReadingDate(null);
      setError(null);
    } catch (err) {
      console.error('Ошибка удаления даты прочтения:', err);
      setError(err.response?.data?.error || 'Не удалось удалить дату прочтения');
    }
  };

  // Обработчики для страниц
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleUploadPages(files);
    }
    // Сбрасываем значение input, чтобы можно было выбрать те же файлы снова
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadPages = async (files) => {
    if (!book || !files || files.length === 0) {
      return;
    }

    try {
      setUploadingPages(true);
      setError(null);

      // Проверяем форматы файлов
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
      const invalidFiles = files.filter(file => !allowedTypes.includes(file.type));
      
      if (invalidFiles.length > 0) {
        setError('Поддерживаются только изображения: JPEG, PNG, WebP');
        setUploadingPages(false);
        return;
      }

      // Проверяем размер файлов (максимум 10MB на файл)
      const maxSize = 10 * 1024 * 1024; // 10MB
      const largeFiles = files.filter(file => file.size > maxSize);
      
      if (largeFiles.length > 0) {
        setError(`Размер некоторых файлов превышает 10MB`);
        setUploadingPages(false);
        return;
      }

      const response = await booksAPI.uploadPages(book.id, files);
      
      // Перезагружаем список страниц
      const pages = await booksAPI.getPages(book.id);
      setBookPages(pages || []);
      
      setError(null);
    } catch (err) {
      console.error('Ошибка загрузки страниц:', err);
      setError(err.response?.data?.error || 'Не удалось загрузить страницы');
    } finally {
      setUploadingPages(false);
    }
  };

  const handleDeletePage = async (pageId) => {
    try {
      await booksAPI.deletePage(book.id, pageId);
      setBookPages(prev => prev.filter(p => p.id !== pageId));
      setConfirmDeletePage(null);
      setError(null);
    } catch (err) {
      console.error('Ошибка удаления страницы:', err);
      setError(err.response?.data?.error || 'Не удалось удалить страницу');
    }
  };

  // Обработчики для электронных версий
  const handleAddElectronicVersion = async () => {
    if (!newElectronicVersion.format) {
      setError('Выберите формат электронной версии');
      return;
    }

    if (!newElectronicVersion.url && !newElectronicVersion.file) {
      setError('Укажите URL или загрузите файл');
      return;
    }

    try {
      setAddingElectronicVersion(true);
      setError(null);

      const formData = new FormData();
      formData.append('format', newElectronicVersion.format);
      if (newElectronicVersion.url) {
        formData.append('url', newElectronicVersion.url);
      }
      if (newElectronicVersion.file) {
        formData.append('file', newElectronicVersion.file);
      }

      const addedVersion = await booksAPI.addElectronicVersion(book.id, formData);
      setElectronicVersions(prev => [...prev, addedVersion]);
      
      // Сбрасываем форму
      setNewElectronicVersion({
        format: '',
        url: '',
        file: null
      });
      if (electronicFileInputRef.current) {
        electronicFileInputRef.current.value = '';
      }
    } catch (err) {
      console.error('Ошибка добавления электронной версии:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Не удалось добавить электронную версию';
      setError(errorMessage);
    } finally {
      setAddingElectronicVersion(false);
    }
  };

  const handleDeleteElectronicVersion = async (versionId) => {
    try {
      await booksAPI.deleteElectronicVersion(book.id, versionId);
      setElectronicVersions(prev => prev.filter(v => v.id !== versionId));
      setConfirmDeleteElectronicVersion(null);
      setError(null);
    } catch (err) {
      console.error('Ошибка удаления электронной версии:', err);
      setError(err.response?.data?.error || 'Не удалось удалить электронную версию');
    }
  };

  const handleElectronicFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setNewElectronicVersion(prev => ({ ...prev, file }));
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr;
    }
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

  if (!isOpen || !book) return null;

  return (
    <div
      className="book-edit-modal-overlay"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="book-edit-modal" onClick={(e) => e.stopPropagation()}>
        <div className="book-edit-modal-header">
          <h2>Редактировать книгу</h2>
          <button
            className="book-edit-modal-close"
            onClick={handleClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <div className="book-edit-modal-body">
          {loading ? (
            <div className="book-edit-modal-loading">Загрузка данных...</div>
          ) : error ? (
            <div className="book-edit-modal-error">{error}</div>
          ) : (
            <form onSubmit={handleSubmit} className="book-edit-form">
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
                    handleChange('authors', authors);
                    const realAuthorIds = authors
                      .filter(a => a.id && !String(a.id).startsWith('temp-'))
                      .map(a => a.id);
                    handleChange('author_ids', realAuthorIds);
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
                        handleChange('publisher', publisher.id);
                        handleChange('publisher_name', publisher.name);
                        handleChange('publisher_website', publisher.website || '');
                      } else if (typeof publisher === 'string') {
                        handleChange('publisher_name', publisher);
                        handleChange('publisher', null);
                        handleChange('publisher_website', '');
                      } else {
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
                      const selectedCategory = selectedId ? categories.find(cat => cat.id === selectedId) : null;
                      handleChange('category_id', selectedId);
                      handleChange('category_name', selectedCategory ? (selectedCategory.fullName || selectedCategory.name) : null);
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

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="status">Статус книги</label>
                  <select
                    id="status"
                    value={formData.status || 'none'}
                    onChange={(e) => {
                      handleChange('status', e.target.value);
                      // При изменении статуса загружаем или очищаем даты прочтения
                      if (e.target.value === 'read' || e.target.value === 'want_to_reread') {
                        loadAdditionalData(book.id, e.target.value);
                      } else {
                        setReadingDates([]);
                      }
                    }}
                    className="form-input"
                  >
                    <option value="none">Не указан</option>
                    <option value="reading">Читаю</option>
                    <option value="read">Прочитано</option>
                    <option value="want_to_read">Хочу прочитать</option>
                    <option value="want_to_reread">Хочу перечитать</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="library">Библиотека</label>
                  {loadingLibraries ? (
                    <div className="form-input" style={{ color: '#666', fontStyle: 'italic', padding: '10px 12px' }}>
                      Загрузка библиотек...
                    </div>
                  ) : (
                    <select
                      id="library"
                      value={formData.library || ''}
                      onChange={(e) => handleChange('library', e.target.value ? parseInt(e.target.value) : null)}
                      className="form-input"
                    >
                      <option value="">Не указана</option>
                      {libraries.map(library => (
                        <option key={library.id} value={library.id}>
                          {library.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {/* Управление датами прочтения (только для статусов 'read' и 'want_to_reread') */}
              {(formData.status === 'read' || formData.status === 'want_to_reread') && (
                <div className="form-group" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #e0e0e0' }}>
                  <label>Даты прочтения</label>
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                      <input
                        type="date"
                        value={newReadingDate}
                        onChange={(e) => setNewReadingDate(e.target.value)}
                        className="form-input"
                        style={{ flex: '1' }}
                      />
                      <button
                        type="button"
                        onClick={handleAddReadingDate}
                        className="book-edit-modal-button book-edit-modal-button-save"
                        style={{ padding: '10px 20px', whiteSpace: 'nowrap' }}
                        disabled={!newReadingDate}
                      >
                        Добавить
                      </button>
                    </div>
                    <textarea
                      value={newReadingDateNotes}
                      onChange={(e) => setNewReadingDateNotes(e.target.value)}
                      placeholder="Заметки (необязательно)"
                      rows="2"
                      className="form-textarea"
                      style={{ marginBottom: '8px' }}
                    />
                  </div>
                  {loadingReadingDates ? (
                    <div style={{ color: '#666', fontStyle: 'italic' }}>Загрузка дат прочтения...</div>
                  ) : readingDates.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {readingDates.map((readingDate) => (
                        <div
                          key={readingDate.id}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '8px 12px',
                            background: '#f5f5f5',
                            borderRadius: '6px',
                            border: '1px solid #e0e0e0'
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: '500' }}>{formatDate(readingDate.date)}</div>
                            {readingDate.notes && (
                              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                {readingDate.notes}
                              </div>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() => setConfirmDeleteReadingDate(readingDate.id)}
                            style={{
                              background: '#ff5252',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '4px 12px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            Удалить
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: '#666', fontStyle: 'italic' }}>Нет дат прочтения</div>
                  )}
                </div>
              )}

              {/* Управление страницами */}
              <div className="form-group" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #e0e0e0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <label style={{ margin: 0 }}>Страницы книги</label>
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/webp"
                      multiple
                      onChange={handleFileSelect}
                      style={{ display: 'none' }}
                      disabled={uploadingPages || !book}
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingPages || !book}
                      className="book-edit-modal-button book-edit-modal-button-save"
                      style={{
                        padding: '8px 16px',
                        fontSize: '14px',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {uploadingPages ? 'Загрузка...' : '+ Добавить страницы'}
                    </button>
                  </div>
                </div>
                
                {loadingPages ? (
                  <div style={{ color: '#666', fontStyle: 'italic', padding: '20px', textAlign: 'center' }}>
                    Загрузка страниц...
                  </div>
                ) : bookPages.length > 0 ? (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                    gap: '12px',
                    marginTop: '12px'
                  }}>
                    {bookPages.map((page) => (
                      <div
                        key={page.id}
                        style={{
                          position: 'relative',
                          border: '1px solid #e0e0e0',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          background: '#f5f5f5'
                        }}
                      >
                        <img
                          src={page.processed_url || page.original_url}
                          alt={`Страница ${page.page_number}`}
                          style={{
                            width: '100%',
                            height: '150px',
                            objectFit: 'cover',
                            display: 'block'
                          }}
                        />
                        <div style={{
                          position: 'absolute',
                          top: '4px',
                          right: '4px',
                          background: 'rgba(255, 82, 82, 0.9)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '50%',
                          width: '24px',
                          height: '24px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '14px',
                          lineHeight: '1'
                        }}
                        onClick={() => setConfirmDeletePage(page.id)}
                        title="Удалить страницу"
                      >
                        ×
                      </div>
                        <div style={{
                          padding: '4px 8px',
                          fontSize: '12px',
                          textAlign: 'center',
                          background: 'rgba(0, 0, 0, 0.7)',
                          color: 'white',
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0
                        }}>
                          Страница {page.page_number}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{
                    padding: '40px 20px',
                    textAlign: 'center',
                    color: '#666',
                    fontStyle: 'italic',
                    border: '2px dashed #e0e0e0',
                    borderRadius: '8px',
                    background: '#fafafa'
                  }}>
                    Нет загруженных страниц
                  </div>
                )}
              </div>

              {/* Управление электронными версиями */}
              <div className="form-group" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid #e0e0e0' }}>
                <label>Электронные версии</label>
                
                {/* Форма добавления новой электронной версии */}
                <div className="electronic-version-add-form">
                  <div className="electronic-version-add-form-content">
                    <div className="electronic-version-add-field">
                      <label htmlFor="electronic_format" className="electronic-version-add-label">
                        Формат *
                      </label>
                      <select
                        id="electronic_format"
                        className="electronic-version-add-select"
                        value={newElectronicVersion.format}
                        onChange={(e) => setNewElectronicVersion(prev => ({ ...prev, format: e.target.value }))}
                        disabled={addingElectronicVersion}
                      >
                        <option value="">Выберите формат</option>
                        <option value="pdf">PDF</option>
                        <option value="epub">EPUB</option>
                        <option value="mobi">MOBI</option>
                        <option value="fb2">FB2</option>
                        <option value="djvu">DJVU</option>
                        <option value="txt">TXT</option>
                        <option value="rtf">RTF</option>
                        <option value="doc">DOC</option>
                        <option value="docx">DOCX</option>
                      </select>
                    </div>

                    <div className="electronic-version-add-field">
                      <label htmlFor="electronic_url" className="electronic-version-add-label">
                        URL (опционально)
                      </label>
                      <input
                        type="url"
                        id="electronic_url"
                        className="electronic-version-add-input"
                        value={newElectronicVersion.url}
                        onChange={(e) => setNewElectronicVersion(prev => ({ ...prev, url: e.target.value }))}
                        placeholder="https://example.com/book.pdf"
                        disabled={addingElectronicVersion}
                      />
                    </div>

                    <div className="electronic-version-add-field">
                      <label htmlFor="electronic_file" className="electronic-version-add-label">
                        Или загрузите файл (опционально)
                      </label>
                      <input
                        type="file"
                        id="electronic_file"
                        className="electronic-version-add-input"
                        ref={electronicFileInputRef}
                        onChange={handleElectronicFileSelect}
                        accept=".pdf,.epub,.mobi,.fb2,.djvu,.txt,.rtf,.doc,.docx"
                        disabled={addingElectronicVersion}
                      />
                      {newElectronicVersion.file && (
                        <div className="electronic-version-file-info">
                          Выбран файл: {newElectronicVersion.file.name}
                        </div>
                      )}
                    </div>

                    <button
                      type="button"
                      className="electronic-version-add-button"
                      onClick={handleAddElectronicVersion}
                      disabled={addingElectronicVersion || !newElectronicVersion.format || (!newElectronicVersion.url && !newElectronicVersion.file)}
                    >
                      {addingElectronicVersion ? 'Добавление...' : 'Добавить электронную версию'}
                    </button>
                  </div>
                </div>

                {/* Список существующих электронных версий */}
                {electronicVersions.length > 0 && (
                  <div className="electronic-version-list">
                    {electronicVersions.map((version) => (
                      <div
                        key={version.id}
                        className="electronic-version-item"
                      >
                        <div className="electronic-version-item-info">
                          <div className="electronic-version-item-format">
                            {version.format?.toUpperCase() || 'Неизвестный формат'}
                          </div>
                          {version.url && (
                            <div className="electronic-version-item-link">
                              <a href={version.url} target="_blank" rel="noopener noreferrer">
                                {version.url}
                              </a>
                            </div>
                          )}
                          {version.file_url && (
                            <div className="electronic-version-item-link">
                              <a href={version.file_url} target="_blank" rel="noopener noreferrer">
                                Скачать файл
                              </a>
                            </div>
                          )}
                        </div>
                        <button
                          type="button"
                          className="electronic-version-delete-button"
                          onClick={() => setConfirmDeleteElectronicVersion(version.id)}
                        >
                          Удалить
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {error && (
                <div className="book-edit-form-error" style={{
                  background: '#ffebee',
                  border: '1px solid #f44336',
                  borderRadius: '6px',
                  padding: '12px 16px',
                  marginBottom: '16px',
                  color: '#c62828',
                  whiteSpace: 'pre-line'
                }}>
                  {error}
                </div>
              )}

              <div className="book-edit-modal-actions">
                <button
                  type="button"
                  className="book-edit-modal-button book-edit-modal-button-cancel"
                  onClick={handleClose}
                  disabled={saving}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="book-edit-modal-button book-edit-modal-button-save"
                  disabled={!formData.title || formData.title.trim() === '' || saving}
                >
                  {saving ? 'Сохранение...' : 'Сохранить изменения'}
                </button>
              </div>
            </form>
          )}
        </div>

        {showCancelConfirm && (
          <ConfirmModal
            isOpen={true}
            title="Отменить изменения?"
            message="У вас есть несохраненные изменения. Вы уверены, что хотите закрыть окно редактирования? Все несохраненные изменения будут потеряны."
            confirmText="Да, отменить"
            cancelText="Продолжить редактирование"
            danger={true}
            onConfirm={handleConfirmCancel}
            onCancel={handleCancelConfirmCancel}
          />
        )}

        {confirmDeleteReadingDate && (
          <ConfirmModal
            isOpen={true}
            title="Удалить дату прочтения?"
            message="Вы уверены, что хотите удалить эту дату прочтения? Это действие нельзя отменить."
            confirmText="Да, удалить"
            cancelText="Отмена"
            danger={true}
            onConfirm={() => handleDeleteReadingDate(confirmDeleteReadingDate)}
            onCancel={() => setConfirmDeleteReadingDate(null)}
          />
        )}

        {confirmDeletePage && (
          <ConfirmModal
            isOpen={true}
            title="Удалить страницу?"
            message="Вы уверены, что хотите удалить эту страницу? Это действие нельзя отменить."
            confirmText="Да, удалить"
            cancelText="Отмена"
            danger={true}
            onConfirm={() => handleDeletePage(confirmDeletePage)}
            onCancel={() => setConfirmDeletePage(null)}
          />
        )}

        {confirmDeleteElectronicVersion && (
          <ConfirmModal
            isOpen={true}
            title="Удалить электронную версию?"
            message="Вы уверены, что хотите удалить эту электронную версию? Это действие нельзя отменить."
            confirmText="Да, удалить"
            cancelText="Отмена"
            danger={true}
            onConfirm={() => handleDeleteElectronicVersion(confirmDeleteElectronicVersion)}
            onCancel={() => setConfirmDeleteElectronicVersion(null)}
          />
        )}
      </div>
    </div>
  );
};

export default BookEditModal;

