import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import BookGrid from '../components/BookGrid';
import Filters from '../components/Filters';
import { authAPI, categoriesAPI, booksAPI, hashtagsAPI } from '../services/api';
import './MainPage.css';

const MainPage = () => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedHashtag, setSelectedHashtag] = useState(null);
  const [selectedLibraries, setSelectedLibraries] = useState(() => {
    // Загружаем из localStorage при инициализации
    const saved = localStorage.getItem('selectedLibraries');
    return saved ? JSON.parse(saved) : [];
  });
  const [categories, setCategories] = useState([]);
  const [hashtags, setHashtags] = useState([]);
  const [books, setBooks] = useState([]);
  const [allBooks, setAllBooks] = useState([]); // Все книги для статистики
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    status: null,
    has_reviews: false,
    has_electronic: false,
    recently_added: false,
  });
  const navigate = useNavigate();

  // Сохраняем выбранные библиотеки в localStorage
  useEffect(() => {
    if (selectedLibraries.length > 0) {
      localStorage.setItem('selectedLibraries', JSON.stringify(selectedLibraries));
    } else {
      localStorage.removeItem('selectedLibraries');
    }
  }, [selectedLibraries]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadAllBooksForStats(); // Загружаем все книги для статистики (без фильтров)
  }, []);

  useEffect(() => {
    loadHashtags();
  }, [selectedCategory]);

  useEffect(() => {
    loadBooks();
  }, [selectedCategory, selectedHashtag, searchQuery, filters, selectedLibraries]);

  const loadData = async () => {
    try {
      const categoriesData = await categoriesAPI.getTree();
      // Обработка пагинации: если есть results, используем их, иначе весь ответ
      setCategories(Array.isArray(categoriesData) ? categoriesData : (categoriesData.results || []));
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    }
  };

  const loadHashtags = async () => {
    try {
      const categoryId = selectedCategory ? selectedCategory.id : null;
      const data = await hashtagsAPI.getByCategory(categoryId);
      setHashtags(data.hashtags || []);
    } catch (error) {
      console.error('Ошибка загрузки хэштегов:', error);
      setHashtags([]);
    }
  };

  const loadAllBooksForStats = async () => {
    try {
      // Загружаем все книги для статистики (с пагинацией, увеличиваем размер страницы)
      // Загружаем без фильтра по библиотекам, чтобы иметь полную картину для подсчета
      let allBooksList = [];
      let page = 1;
      let hasMore = true;
      
      while (hasMore) {
        const params = { page, page_size: 100 }; // Увеличиваем размер страницы
        const data = await booksAPI.getAll(params);
        
        if (Array.isArray(data)) {
          allBooksList = [...allBooksList, ...data];
          hasMore = false;
        } else {
          const results = data.results || [];
          allBooksList = [...allBooksList, ...results];
          hasMore = !!data.next; // Проверяем наличие следующей страницы
          page++;
        }
      }
      
      setAllBooks(allBooksList);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  };

  // Вычисляем количество книг с учетом выбранных библиотек для категорий
  const calculateCategoryBooksCount = (category) => {
    if (selectedLibraries.length === 0) {
      return 0;
    }
    
    // Фильтруем книги по выбранным библиотекам
    let filteredBooks = allBooks.filter(book => {
      const bookLibraryId = book.library || book.library_id;
      return bookLibraryId && selectedLibraries.includes(bookLibraryId);
    });
    
    // Фильтруем по категории
    if (category.subcategories && category.subcategories.length > 0) {
      // Родительская категория - считаем книги из всех подкатегорий
      const subcategoryIds = category.subcategories.map(sub => sub.id);
      return filteredBooks.filter(book => {
        const bookCategoryId = book.category || book.category_id;
        return bookCategoryId === category.id || subcategoryIds.includes(bookCategoryId);
      }).length;
    } else {
      // Обычная категория
      return filteredBooks.filter(book => {
        const bookCategoryId = book.category || book.category_id;
        return bookCategoryId === category.id;
      }).length;
    }
  };

  // Общее количество книг с учетом выбранных библиотек
  const getFilteredBooksCount = () => {
    if (selectedLibraries.length === 0) {
      return 0;
    }
    return allBooks.filter(book => {
      const bookLibraryId = book.library || book.library_id;
      return bookLibraryId && selectedLibraries.includes(bookLibraryId);
    }).length;
  };

  const calculateStats = () => {
    const stats = {
      status: {
        none: 0,
        reading: 0,
        read: 0,
        want_to_read: 0,
        want_to_reread: 0,
      },
      with_reviews: 0,
      with_electronic: 0,
      recently_added: 0,
    };

    // Фильтруем книги по выбранным библиотекам
    // Если не выбрана ни одна библиотека - возвращаем нулевые статистики
    if (selectedLibraries.length === 0) {
      return stats;
    }
    
    let booksToCount = allBooks.filter(book => {
      const bookLibraryId = book.library || book.library_id;
      return bookLibraryId && selectedLibraries.includes(bookLibraryId);
    });

    // Фильтруем книги по выбранной категории
    if (selectedCategory) {
      booksToCount = booksToCount.filter(book => {
        // Проверяем все возможные варианты поля категории
        const bookCategoryId = book.category || book.category_id;
        // Если выбрана родительская категория с подкатегориями, считаем книги из всех её подкатегорий
        if (selectedCategory.subcategories && selectedCategory.subcategories.length > 0) {
          const subcategoryIds = selectedCategory.subcategories.map(sub => sub.id);
          return bookCategoryId === selectedCategory.id || subcategoryIds.includes(bookCategoryId);
        }
        return bookCategoryId === selectedCategory.id;
      });
    }

    booksToCount.forEach(book => {
      // Статусы
      if (book.status && stats.status[book.status] !== undefined) {
        stats.status[book.status]++;
      }
      
      // Отзывы
      if (book.reviews_count > 0) {
        stats.with_reviews++;
      }
      
      // Электронные версии
      if (book.electronic_versions_count > 0) {
        stats.with_electronic++;
      }
      
      // Недавно добавленные
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      if (book.created_at) {
        const createdDate = new Date(book.created_at);
        if (createdDate >= sevenDaysAgo) {
          stats.recently_added++;
        }
      }
    });

    return stats;
  };

  const loadBooks = async () => {
    setLoading(true);
    try {
      // Если не выбрана ни одна библиотека - не показываем книги
      if (selectedLibraries.length === 0) {
        setBooks([]);
        setLoading(false);
        return;
      }
      
      const params = {};
      
      // Фильтрация по выбранным библиотекам
      params.libraries = selectedLibraries;
      
      if (selectedCategory) {
        // Если выбрана родительская категория с подкатегориями, фильтруем по всем
        if (selectedCategory.subcategories && selectedCategory.subcategories.length > 0) {
          // Фильтруем по родительской категории или её подкатегориям
          const categoryIds = [selectedCategory.id, ...selectedCategory.subcategories.map(sub => sub.id)];
          // API может не поддерживать множественный фильтр, используем фильтр по родительской
          // или можно сделать несколько запросов и объединить
          params.category = selectedCategory.id;
        } else {
          params.category = selectedCategory.id;
        }
      }
      
      if (searchQuery) {
        params.search = searchQuery;
      }
      
      if (filters.status) {
        params.status = filters.status;
      }

      if (selectedHashtag) {
        // Фильтрация по хэштегу будет на клиенте, так как API может не поддерживать это напрямую
      }
      
      if (filters.has_reviews) {
        // Нужно будет добавить этот фильтр на бэкенде или фильтровать на клиенте
      }
      
      if (filters.has_electronic) {
        // Нужно будет добавить этот фильтр на бэкенде
      }
      
      // Увеличиваем размер страницы для лучшей производительности
      params.page_size = 100;
      const data = await booksAPI.getAll(params);
      // Обработка пагинации: если есть results, используем их, иначе весь ответ
      let booksList = Array.isArray(data) ? data : (data.results || []);
      
      // Если есть пагинация и мы используем фильтры, загружаем все страницы
      if (data.next && (filters.status || filters.has_reviews || filters.has_electronic || filters.recently_added)) {
        let page = 2;
        let hasMore = true;
        while (hasMore) {
          const nextParams = { ...params, page, page_size: 100 };
          const nextData = await booksAPI.getAll(nextParams);
          if (Array.isArray(nextData)) {
            booksList = [...booksList, ...nextData];
            hasMore = false;
          } else {
            const nextResults = nextData.results || [];
            booksList = [...booksList, ...nextResults];
            hasMore = !!nextData.next;
            page++;
          }
        }
      }
      
      // Клиентская фильтрация для полей, которые пока не поддерживаются на бэкенде
      if (filters.has_electronic) {
        booksList = booksList.filter(book => book.electronic_versions_count > 0);
      }
      
      if (filters.has_reviews) {
        booksList = booksList.filter(book => book.reviews_count > 0);
      }
      
      if (filters.recently_added) {
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        booksList = booksList.filter(book => {
          const createdDate = new Date(book.created_at);
          return createdDate >= sevenDaysAgo;
        });
      }

      // Фильтрация по хэштегу
      if (selectedHashtag) {
        booksList = booksList.filter(book => {
          return book.hashtags && book.hashtags.some(ht => ht.id === selectedHashtag.id);
        });
      }
      
      setBooks(booksList);
    } catch (error) {
      console.error('Ошибка загрузки книг:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setSelectedHashtag(null); // Сбрасываем выбранный хэштег при смене категории
  };

  const handleHashtagSelect = (hashtag) => {
    setSelectedHashtag(hashtag);
  };

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const handleFilterChange = (filterName, value) => {
    setFilters((prev) => ({
      ...prev,
      [filterName]: value,
    }));
  };

  const handleLogout = () => {
    authAPI.logout();
    // Используем window.location для принудительного перехода, чтобы избежать проблем с кэшированием состояния
    window.location.href = '/login';
  };

  const handleAddBook = () => {
    // Пока просто консольный лог, позже добавим модальное окно
    console.log('Добавить книгу');
  };

  return (
    <div className="main-page">
      <Header 
        onLogout={handleLogout}
        searchQuery={searchQuery}
        onSearch={handleSearch}
        selectedLibraries={selectedLibraries}
        onLibrariesChange={setSelectedLibraries}
      />
      <div className="main-content">
              <Sidebar
                categories={categories}
                hashtags={hashtags}
                selectedCategory={selectedCategory}
                selectedHashtag={selectedHashtag}
                onCategorySelect={handleCategorySelect}
                onHashtagSelect={handleHashtagSelect}
                totalBooksCount={getFilteredBooksCount()}
                calculateCategoryBooksCount={calculateCategoryBooksCount}
              />
        <div className="content-area">
          <Filters
            filters={filters}
            onFilterChange={handleFilterChange}
            stats={calculateStats()}
          />
          <BookGrid
            books={books}
            loading={loading}
            onAddBook={handleAddBook}
          />
        </div>
      </div>
    </div>
  );
};

export default MainPage;

