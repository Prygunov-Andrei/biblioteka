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
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ошибок авторизации
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Если ошибка 401 и мы еще не пытались обновить токен
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

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
        }
      } catch (refreshError) {
        // Если не удалось обновить токен, удаляем токены и перенаправляем на авторизацию
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
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
};

// API методы для книг
export const booksAPI = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/books/', { params });
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
};

// API методы для пользователя
export const userAPI = {
  getProfile: async () => {
    const response = await apiClient.get('/user-profiles/me/');
    return response.data;
  },
};

export default apiClient;

