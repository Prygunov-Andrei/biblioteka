import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Создаем экземпляр axios с базовой конфигурацией
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена к каждому запросу
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    // Добавляем токен только если он есть
    // Для публичных эндпоинтов токен не обязателен, но если он есть - добавим
    // OptionalJWTAuthentication на сервере проигнорирует невалидные токены
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Публичные эндпоинты, которые доступны без токена
const PUBLIC_ENDPOINTS = [
  '/categories/',
  '/categories/tree/',
  '/hashtags/',
  '/books/',  // GET запросы на список книг
  '/books/stats/',  // GET запросы на статистику фильтров
];

// Проверяем, является ли эндпоинт публичным
// Учитываем, что URL может содержать query параметры, поэтому проверяем начало пути
const isPublicEndpoint = (url) => {
  // Извлекаем путь из URL (убираем query параметры)
  const path = url.split('?')[0];
  return PUBLIC_ENDPOINTS.some(endpoint => {
    const cleanEndpoint = endpoint.replace(/\/$/, ''); // Убираем trailing slash
    const cleanPath = path.replace(/\/$/, '');
    return cleanPath.includes(cleanEndpoint) || cleanPath.endsWith(cleanEndpoint);
  });
};

// Интерцептор для обработки ошибок авторизации
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const url = originalRequest.url || '';

    // Если ошибка 401 и мы еще не пытались обновить токен
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Если это публичный эндпоинт и токен невалидный, пробуем запрос без токена
      if (isPublicEndpoint(url)) {
        // Создаем новый конфиг без токена
        const cleanHeaders = { ...originalRequest.headers };
        delete cleanHeaders.Authorization;
        
        // Формируем полный URL для запроса
        let requestUrl = originalRequest.url || url;
        // Если URL относительный, добавляем baseURL
        if (!requestUrl.startsWith('http')) {
          const baseUrl = originalRequest.baseURL || API_BASE_URL;
          requestUrl = `${baseUrl}${requestUrl.startsWith('/') ? '' : '/'}${requestUrl}`;
        }
        
        // Используем axios напрямую, чтобы обойти интерцептор запроса
        try {
          const response = await axios({
            method: originalRequest.method || 'get',
            url: requestUrl,
            params: originalRequest.params,
            data: originalRequest.data,
            headers: cleanHeaders,
          });
          return response;
        } catch (retryError) {
          // Если и без токена не работает, возвращаем ошибку
          return Promise.reject(retryError);
        }
      }

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        } else {
          // Если нет refresh токена и это не публичный эндпоинт, перенаправляем на логин
          if (!isPublicEndpoint(url)) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }
          return Promise.reject(error);
        }
      } catch (refreshError) {
        // Если не удалось обновить токен и это не публичный эндпоинт
        if (!isPublicEndpoint(url)) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API методы для авторизации
export const authAPI = {
  login: async (username, password) => {
    const response = await apiClient.post('/token/', {
      username,
      password,
    });
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
};

// API методы для категорий
export const categoriesAPI = {
  getAll: async () => {
    const response = await apiClient.get('/categories/');
    return response.data;
  },
  getTree: async (params = {}) => {
    // Возвращает дерево категорий (родительские с подкатегориями)
    // Поддерживает фильтрацию по библиотекам для подсчета книг
    const queryParams = new URLSearchParams();
    if (params.libraries && params.libraries.length > 0) {
      params.libraries.forEach(libId => {
        queryParams.append('libraries', libId);
      });
    }
    const queryString = queryParams.toString();
    const url = `/categories/tree/${queryString ? `?${queryString}` : ''}`;
    const response = await apiClient.get(url);
    return response.data;
  },
  getBySlug: async (slug) => {
    const response = await apiClient.get(`/categories/${slug}/`);
    return response.data;
  },
};

// API методы для хэштегов
export const hashtagsAPI = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/hashtags/', { params });
    return response.data;
  },
  getByCategory: async (categoryId = null) => {
    const params = categoryId ? { category_id: categoryId } : {};
    const response = await apiClient.get('/hashtags/by_category/', { params });
    return response.data;
  },
};

// API методы для книг
export const booksAPI = {
  getStats: async (params = {}) => {
    const requestParams = new URLSearchParams();
    
    // Обрабатываем все параметры
    Object.keys(params).forEach(key => {
      if (key === 'libraries' && Array.isArray(params[key])) {
        params[key].forEach(libId => {
          requestParams.append('libraries', libId);
        });
      } else if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        requestParams.append(key, params[key]);
      }
    });
    
    const response = await apiClient.get(`/books/stats/?${requestParams.toString()}`);
    return response.data;
  },
  getAll: async (params = {}) => {
    // Для множественных библиотек используем getlist
    const requestParams = new URLSearchParams();
    
    // Обрабатываем все параметры
    Object.keys(params).forEach(key => {
      if (key === 'libraries' && Array.isArray(params[key])) {
        // Для библиотек добавляем каждую отдельно
        params[key].forEach(libId => {
          requestParams.append('libraries', libId);
        });
      } else {
        requestParams.append(key, params[key]);
      }
    });
    
    const response = await apiClient.get(`/books/?${requestParams.toString()}`);
    return response.data;
  },
  getById: async (id) => {
    const response = await apiClient.get(`/books/${id}/`);
    return response.data;
  },
  search: async (query, params = {}) => {
    const response = await apiClient.get('/books/', {
      params: { ...params, search: query },
    });
    return response.data;
  },
  normalizePages: async (files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    const response = await apiClient.post('/books/normalize-pages/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  autoFill: async (normalizedImageUrls) => {
    const response = await apiClient.post('/books/auto-fill/', {
      normalized_image_urls: normalizedImageUrls,
    });
    return response.data;
  },
  create: async (bookData) => {
    // Отправляем данные как JSON (бэкенд обработает language_name и создаст связи)
    const response = await apiClient.post('/books/', bookData);
    return response.data;
  },
  update: async (bookId, bookData) => {
    // Обновление книги через PATCH (частичное обновление)
    const response = await apiClient.patch(`/books/${bookId}/`, bookData);
    return response.data;
  },
  // Управление страницами
  getPages: async (bookId) => {
    const response = await apiClient.get(`/books/${bookId}/pages/`);
    return response.data;
  },
  deletePage: async (bookId, pageId) => {
    const response = await apiClient.delete(`/books/${bookId}/pages/${pageId}/`);
    return response.data;
  },
  // Управление электронными версиями
  deleteElectronicVersion: async (bookId, versionId) => {
    const response = await apiClient.delete(`/books/${bookId}/electronic_versions/${versionId}/`);
    return response.data;
  },
  addElectronicVersion: async (bookId, electronicData) => {
    const response = await apiClient.post(`/books/${bookId}/electronic_versions/`, electronicData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  // Управление датами прочтения
  getReadingDates: async (bookId) => {
    const response = await apiClient.get(`/books/${bookId}/reading_dates/`);
    return response.data;
  },
  addReadingDate: async (bookId, date, notes = '') => {
    const response = await apiClient.post(`/books/${bookId}/reading_dates/`, {
      date: date, // Формат: YYYY-MM-DD
      notes: notes,
    });
    return response.data;
  },
  deleteReadingDate: async (bookId, dateId) => {
    const response = await apiClient.delete(`/books/${bookId}/reading_dates/${dateId}/`);
    return response.data;
  },
};

// API методы для авторов
export const authorsAPI = {
  search: async (query) => {
    const response = await apiClient.get('/authors/', {
      params: { search: query },
    });
    return response.data;
  },
  getAll: async () => {
    const response = await apiClient.get('/authors/');
    return response.data;
  },
  getById: async (id) => {
    const response = await apiClient.get(`/authors/${id}/`);
    return response.data;
  },
  create: async (authorData) => {
    const response = await apiClient.post('/authors/', authorData);
    return response.data;
  },
  update: async (id, authorData) => {
    const response = await apiClient.patch(`/authors/${id}/`, authorData);
    return response.data;
  },
  delete: async (id) => {
    const response = await apiClient.delete(`/authors/${id}/`);
    return response.data;
  },
};

// API методы для издательств
export const publishersAPI = {
  search: async (query) => {
    const response = await apiClient.get('/publishers/', {
      params: { search: query },
    });
    return response.data;
  },
  getAll: async () => {
    const response = await apiClient.get('/publishers/');
    return response.data;
  },
  getById: async (id) => {
    const response = await apiClient.get(`/publishers/${id}/`);
    return response.data;
  },
  create: async (publisherData) => {
    const response = await apiClient.post('/publishers/', publisherData);
    return response.data;
  },
  update: async (id, publisherData) => {
    const response = await apiClient.patch(`/publishers/${id}/`, publisherData);
    return response.data;
  },
  delete: async (id) => {
    const response = await apiClient.delete(`/publishers/${id}/`);
    return response.data;
  },
};

// API методы для пользователя
export const userAPI = {
  getProfile: async () => {
    const response = await apiClient.get('/user-profiles/me/');
    return response.data;
  },
  updateProfile: async (profileData) => {
    const formData = new FormData();
    if (profileData.full_name !== undefined) formData.append('full_name', profileData.full_name);
    if (profileData.description !== undefined) formData.append('description', profileData.description);
    if (profileData.photo) formData.append('photo', profileData.photo);
    
    const response = await apiClient.patch('/user-profiles/me/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// API методы для библиотек
export const librariesAPI = {
  getAll: async () => {
    const response = await apiClient.get('/libraries/');
    return response.data;
  },
  getMyLibraries: async () => {
    const response = await apiClient.get('/libraries/my_libraries/');
    return response.data;
  },
  getById: async (id) => {
    const response = await apiClient.get(`/libraries/${id}/`);
    return response.data;
  },
  create: async (libraryData) => {
    const response = await apiClient.post('/libraries/', libraryData);
    return response.data;
  },
  update: async (id, libraryData) => {
    const response = await apiClient.patch(`/libraries/${id}/`, libraryData);
    return response.data;
  },
  delete: async (id) => {
    const response = await apiClient.delete(`/libraries/${id}/`);
    return response.data;
  },
};

// API методы для отзывов
export const reviewsAPI = {
  createOrUpdate: async (bookId, reviewData) => {
    const response = await apiClient.post('/book-reviews/', {
      book: bookId,
      ...reviewData
    });
    return response.data;
  },
  update: async (reviewId, reviewData) => {
    // Используем PATCH для частичного обновления (не требуем все поля)
    const response = await apiClient.patch(`/book-reviews/${reviewId}/`, reviewData);
    return response.data;
  },
  delete: async (reviewId) => {
    const response = await apiClient.delete(`/book-reviews/${reviewId}/`);
    return response.data;
  },
  getByBook: async (bookId) => {
    const response = await apiClient.get('/book-reviews/', {
      params: { book: bookId }
    });
    return response.data;
  }
};

export default apiClient;

