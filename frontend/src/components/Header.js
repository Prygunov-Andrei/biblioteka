import { useState, useEffect } from 'react';
import { userAPI } from '../services/api';
import { getTheme, toggleTheme } from '../utils/theme';
import { isAuthenticated } from '../utils/auth';
import './Header.css';

const Header = ({ onLogout, searchQuery, onSearch }) => {
  const [user, setUser] = useState(null);
  const [showMenu, setShowMenu] = useState(false);
  const [theme, setTheme] = useState(getTheme());

  useEffect(() => {
    // Загружаем профиль только если пользователь авторизован
    if (isAuthenticated()) {
      loadUserProfile();
    }
  }, []);

  const loadUserProfile = async () => {
    try {
      const profile = await userAPI.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Ошибка загрузки профиля:', error);
    }
  };

  const handleSearchChange = (e) => {
    onSearch(e.target.value);
  };

  const handleThemeToggle = () => {
    const newTheme = toggleTheme();
    setTheme(newTheme);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="quote">
            "...книгу вообще нельзя читать – ее можно только перечитывать. В. Набоков."
          </div>
        </div>
        <div className="header-center">
          <div className="search-bar-container">
            <input
              type="text"
              placeholder="Поиск..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>
        </div>
        <div className="header-right">
          <button 
            className="theme-toggle-button"
            onClick={handleThemeToggle}
            title={theme === 'light' ? 'Переключить на темную тему' : 'Переключить на светлую тему'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <div className="user-menu" onClick={() => setShowMenu(!showMenu)}>
            {user?.photo_url ? (
              <img 
                src={user.photo_url} 
                alt={user.full_name || user.user?.username || 'Пользователь'} 
                className="user-avatar"
              />
            ) : (
              <div className="user-avatar-placeholder">
                {user?.full_name?.[0] || user?.user?.username?.[0] || 'U'}
              </div>
            )}
            <span className="user-name">
              {user?.full_name || user?.user?.username || 'Пользователь'}
            </span>
            <span className="dropdown-arrow">▼</span>
          </div>
          {showMenu && (
            <div className="user-dropdown">
              <button 
                className="dropdown-item"
                onClick={() => {
                  setShowMenu(false);
                  // TODO: перейти на страницу профиля
                }}
              >
                Моя страница
              </button>
              <button 
                className="dropdown-item"
                onClick={() => {
                  setShowMenu(false);
                  onLogout();
                }}
              >
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;

