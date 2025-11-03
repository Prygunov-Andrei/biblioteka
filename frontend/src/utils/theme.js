// Утилиты для управления темой

const THEME_STORAGE_KEY = 'biblioteka-theme';
const DARK_THEME_CLASS = 'dark-theme';

export const getTheme = () => {
  return localStorage.getItem(THEME_STORAGE_KEY) || 'light';
};

export const setTheme = (theme) => {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  applyTheme(theme);
};

export const applyTheme = (theme) => {
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add(DARK_THEME_CLASS);
  } else {
    root.classList.remove(DARK_THEME_CLASS);
  }
};

export const toggleTheme = () => {
  const currentTheme = getTheme();
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  setTheme(newTheme);
  return newTheme;
};

// Применяем тему при загрузке страницы
if (typeof window !== 'undefined') {
  applyTheme(getTheme());
}

