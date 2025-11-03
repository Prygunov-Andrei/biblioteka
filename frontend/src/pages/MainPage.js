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

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadAllBooksForStats(); // Загружаем все книги для статистики (без фильтров)
  }, []);

  useEffect(() => {
    loadBooks();
  }, [selectedCategory, searchQuery, filters]);

  const loadData = async () => {
    try {
      const [categoriesData, hashtagsData] = await Promise.all([
        categoriesAPI.getAll(),
        hashtagsAPI.getAll(),
      ]);
      // Обработка пагинации: если есть results, используем их, иначе весь ответ
      setCategories(Array.isArray(categoriesData) ? categoriesData : (categoriesData.results || []));
      setHashtags(Array.isArray(hashtagsData) ? hashtagsData : (hashtagsData.results || []));
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    }
  };

  const loadAllBooksForStats = async () => {
    try {
      // Загружаем все книги для статистики (с пагинацией, увеличиваем размер страницы)
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

    // Фильтруем книги по выбранной категории
    const booksToCount = selectedCategory
      ? allBooks.filter(book => {
          // Проверяем все возможные варианты поля категории
          const bookCategoryId = book.category || book.category_id;
          return bookCategoryId === selectedCategory.id;
        })
      : allBooks;

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
      const params = {};
      
      if (selectedCategory) {
        params.category = selectedCategory.id;
      }
      
      if (searchQuery) {
        params.search = searchQuery;
      }
      
      if (filters.status) {
        params.status = filters.status;
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
      
      setBooks(booksList);
    } catch (error) {
      console.error('Ошибка загрузки книг:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
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
    navigate('/login');
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
      />
      <div className="main-content">
        <Sidebar
          categories={categories}
          hashtags={hashtags}
          selectedCategory={selectedCategory}
          onCategorySelect={handleCategorySelect}
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

