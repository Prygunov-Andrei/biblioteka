/**
 * Утилиты для работы с аутентификацией
 */

export const getStoredTokens = () => {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
};

export const setStoredTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
  }
};

export const clearStoredTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

