import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import BookGrid from '../components/BookGrid';
import Filters from '../components/Filters';
import BookDetailModal from '../components/BookDetailModal';
import BookCreateWizard from '../components/BookCreateWizard';
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
  // const [allBooks, setAllBooks] = useState([]); // Удалено - используем books_count из API
  const [loading, setLoading] = useState(true);
  // Состояние пагинации
  const [currentPage, setCurrentPage] = useState(1);
  const [paginationInfo, setPaginationInfo] = useState({
    count: 0,
    next: null,
    previous: null,
    paginated: false
  });
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
  }, [selectedLibraries]); // Перезагружаем категории при изменении библиотек

  // Удаляем загрузку всех книг для статистики - теперь используем books_count из API категорий
  // useEffect(() => {
  //   loadAllBooksForStats(); // Загружаем все книги для статистики (без фильтров)
  // }, []);

  const [stats, setStats] = useState({
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
  });

  // Состояние для модального окна просмотра книги
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [isBookDetailModalOpen, setIsBookDetailModalOpen] = useState(false);

  // Состояние для мастера создания книги
  const [isBookCreateWizardOpen, setIsBookCreateWizardOpen] = useState(false);

  useEffect(() => {
    loadHashtags();
  }, [selectedCategory]);

  useEffect(() => {
    // Сбрасываем страницу на 1 при изменении фильтров
    setCurrentPage(1);
  }, [selectedCategory, selectedHashtag, searchQuery, filters, selectedLibraries]);

  useEffect(() => {
    loadBooks();
  }, [selectedCategory, selectedHashtag, searchQuery, filters, selectedLibraries, currentPage]);

  useEffect(() => {
    loadStats();
  }, [selectedCategory, selectedHashtag, searchQuery, selectedLibraries]);

  const loadData = async () => {
    try {
      // Передаем выбранные библиотеки для правильного подсчета книг
      const params = {};
      if (selectedLibraries.length > 0) {
        params.libraries = selectedLibraries;
      }
      const categoriesData = await categoriesAPI.getTree(params);
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

  // Удалена функция loadAllBooksForStats - теперь используем books_count из API категорий

  // Удалено calculateCategoryBooksCount - теперь используем books_count из API категорий напрямую

  // Общее количество книг с учетом выбранных библиотек
  const getFilteredBooksCount = () => {
    if (selectedLibraries.length === 0) {
      return 0;
    }
    // Суммируем books_count из всех родительских категорий
    // Каждая категория уже включает книги из подкатегорий в books_count
    return categories.reduce((total, category) => {
      return total + (category.books_count || 0);
    }, 0);
  };

  const handleBookClick = (book) => {
    setSelectedBookId(book.id);
    setIsBookDetailModalOpen(true);
  };

  const handleCloseBookDetail = () => {
    setIsBookDetailModalOpen(false);
    setSelectedBookId(null);
  };

  const handleEditBook = (book) => {
    // TODO: Реализовать в Этапе 7
    console.log('Редактирование книги:', book);
    handleCloseBookDetail();
  };

  const handleTransferBook = (book) => {
    // TODO: Реализовать в Этапе 8
    console.log('Передача книги:', book);
    handleCloseBookDetail();
  };

  const handleDeleteBook = (book) => {
    // TODO: Реализовать в Этапе 9
    console.log('Удаление книги:', book);
    handleCloseBookDetail();
  };

  const loadStats = async () => {
    try {
      // Если не выбрана ни одна библиотека - сбрасываем статистику
      if (selectedLibraries.length === 0) {
        setStats({
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
        });
        return;
      }
      
      const params = {
        libraries: selectedLibraries,
      };
      
      if (selectedCategory) {
        params.category = selectedCategory.id;
      }
      
      if (selectedHashtag) {
        params.hashtag = selectedHashtag.id;
      }
      
      if (searchQuery) {
        params.search = searchQuery;
      }
      
      const statsData = await booksAPI.getStats(params);
      setStats(statsData);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
      // В случае ошибки сбрасываем статистику
      setStats({
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
      });
    }
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
        // Бэкенд сам обрабатывает родительские категории с подкатегориями
        // Просто передаем ID категории
        params.category = selectedCategory.id;
      }
      
      if (searchQuery) {
        params.search = searchQuery;
      }
      
      if (filters.status) {
        params.status = filters.status;
      }

      if (selectedHashtag) {
        // Фильтрация по хэштегу через бэкенд (ID)
        params.hashtag = selectedHashtag.id;
      }
      
      if (filters.has_reviews) {
        params.has_reviews = 'true';
      }
      
      if (filters.has_electronic) {
        params.has_electronic = 'true';
      }
      
      if (filters.recently_added) {
        params.recently_added = 'true';
      }
      
      // Добавляем параметр page для пагинации
      if (currentPage > 1) {
        params.page = currentPage;
      }
      
      // Не указываем page_size - пагинация применяется автоматически если книг > 30
      // Бэкенд сам решает применять пагинацию или нет
      const data = await booksAPI.getAll(params);
      
      // Сохраняем информацию о пагинации
      setPaginationInfo({
        count: data.count || 0,
        next: data.next || null,
        previous: data.previous || null,
        paginated: data.paginated || false
      });
      
      // Отображаем только текущую страницу
      const booksList = data.results || [];
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
    setIsBookCreateWizardOpen(true);
  };

  const handleCloseBookCreateWizard = () => {
    setIsBookCreateWizardOpen(false);
  };

  const handleBookCreateComplete = () => {
    setIsBookCreateWizardOpen(false);
    // Перезагружаем список книг после создания
    loadBooks();
  };

  return (
    <div className="main-page">
      <Header 
        onLogout={handleLogout}
        searchQuery={searchQuery}
        onSearch={handleSearch}
        selectedLibraries={selectedLibraries}
        onLibrariesChange={setSelectedLibraries}
        onAddBook={handleAddBook}
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
              />
        <div className="content-area">
          <Filters
            filters={filters}
            onFilterChange={handleFilterChange}
            stats={stats}
          />
          <BookGrid
            books={books}
            loading={loading}
            onBookClick={handleBookClick}
          />
          
          {/* Пагинация */}
          {paginationInfo.paginated && paginationInfo.count > 0 && (
            <div className="pagination">
              <div className="pagination-info">
                Страница {currentPage} из {Math.ceil(paginationInfo.count / 30)} 
                ({paginationInfo.count} книг всего)
              </div>
              <div className="pagination-controls">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={!paginationInfo.previous || currentPage === 1}
                  className="pagination-button"
                >
                  ← Предыдущая
                </button>
                <button
                  onClick={() => setCurrentPage(prev => prev + 1)}
                  disabled={!paginationInfo.next || currentPage >= Math.ceil(paginationInfo.count / 30)}
                  className="pagination-button"
                >
                  Следующая →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Модальное окно просмотра книги */}
      <BookDetailModal
        bookId={selectedBookId}
        isOpen={isBookDetailModalOpen}
        onClose={handleCloseBookDetail}
        onEdit={handleEditBook}
        onTransfer={handleTransferBook}
        onDelete={handleDeleteBook}
      />

      {/* Мастер создания книги */}
      <BookCreateWizard
        isOpen={isBookCreateWizardOpen}
        onClose={handleCloseBookCreateWizard}
        onComplete={handleBookCreateComplete}
      />
    </div>
  );
};

export default MainPage;

