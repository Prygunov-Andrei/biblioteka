import { useState, useEffect, useRef } from 'react';
import { publishersAPI } from '../services/api';
import CreatePublisherModal from './CreatePublisherModal';
import './PublisherAutocomplete.css';

const PublisherAutocomplete = ({ value, onChange, placeholder = 'Введите издательство' }) => {
  const [searchQuery, setSearchQuery] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedPublisher, setSelectedPublisher] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [debounceTimer, setDebounceTimer] = useState(null);
  const [hasBeenFocused, setHasBeenFocused] = useState(false);
  const [userHasTyped, setUserHasTyped] = useState(false);
  const wrapperRef = useRef(null);

  // Инициализация при получении value извне
  useEffect(() => {
    if (value && typeof value === 'object' && value.id) {
      // Если передан объект издательства
      setSelectedPublisher(value);
      setSearchQuery(value.name);
      setShowSuggestions(false); // Не показываем список при инициализации
      setUserHasTyped(false);
      setHasBeenFocused(false); // Сбрасываем флаг фокуса при инициализации
    } else if (value && typeof value === 'string' && value.trim()) {
      // Если передан просто текст (название издательства)
      setSearchQuery(value);
      setSelectedPublisher(null);
      setShowSuggestions(false); // Не показываем список при инициализации
      setUserHasTyped(false);
      setHasBeenFocused(false); // Сбрасываем флаг фокуса при инициализации
    } else if (!value) {
      setSearchQuery('');
      setSelectedPublisher(null);
      setShowSuggestions(false);
      setUserHasTyped(false);
      setHasBeenFocused(false); // Сбрасываем флаг фокуса при очистке
    }
  }, [value]);

  // Поиск издательств с debounce (только если пользователь взаимодействовал с полем)
  useEffect(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Не запускаем поиск автоматически при инициализации
    // Только если пользователь ввел текст или сфокусировался на поле
    if (!hasBeenFocused && !userHasTyped) {
      return;
    }

    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await publishersAPI.search(searchQuery.trim());
        setSuggestions(Array.isArray(results) ? results : (results.results || []));
        // Показываем список только если пользователь взаимодействовал с полем
        if (hasBeenFocused || userHasTyped) {
          setShowSuggestions(true);
        }
      } catch (error) {
        console.error('Ошибка поиска издательств:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    setDebounceTimer(timer);

    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [searchQuery, hasBeenFocused, userHasTyped]);

  // Закрытие выпадающего списка при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setSearchQuery(newValue);
    setSelectedPublisher(null);
    setUserHasTyped(true); // Пользователь начал вводить текст
    setShowSuggestions(true);
    
    // Если поле очищено, передаем пустую строку
    if (!newValue.trim()) {
      onChange && onChange('');
      setShowSuggestions(false);
    }
  };

  const handleSelectPublisher = (publisher) => {
    setSelectedPublisher(publisher);
    setSearchQuery(publisher.name);
    setShowSuggestions(false);
    setUserHasTyped(false); // Сбрасываем флаг после выбора
    onChange && onChange(publisher);
  };

  const handleCreateNew = () => {
    setShowCreateModal(true);
    setShowSuggestions(false);
  };

  const handlePublisherCreated = (newPublisher) => {
    setSelectedPublisher(newPublisher);
    setSearchQuery(newPublisher.name);
    onChange && onChange(newPublisher);
    setShowCreateModal(false);
  };

  const handleInputFocus = () => {
    setHasBeenFocused(true); // Пользователь сфокусировался на поле
    
    // Показываем выпадающий список при фокусе, если есть текст для поиска
    if (searchQuery.trim().length >= 2) {
      // Если уже есть результаты - показываем их
      if (suggestions.length > 0) {
        setShowSuggestions(true);
      } else {
        // Если результатов нет, но есть текст - запускаем поиск
        // (это сработает через useEffect с debounce)
        setShowSuggestions(true);
      }
    }
  };

  return (
    <div className="publisher-autocomplete" ref={wrapperRef}>
      <input
        type="text"
        value={searchQuery}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        placeholder={placeholder}
        className="publisher-autocomplete-input form-input"
      />
      
      {loading && (
        <div className="publisher-autocomplete-loading">
          Поиск...
        </div>
      )}

      {showSuggestions && !loading && searchQuery.trim().length >= 2 && (
        <div className="publisher-autocomplete-dropdown">
          {suggestions.length > 0 ? (
            <>
              {suggestions.map((publisher) => (
                <div
                  key={publisher.id}
                  className="publisher-autocomplete-item"
                  onClick={() => handleSelectPublisher(publisher)}
                >
                  <div className="publisher-autocomplete-name">{publisher.name}</div>
                  {publisher.city && (
                    <div className="publisher-autocomplete-city">{publisher.city}</div>
                  )}
                </div>
              ))}
              <div
                className="publisher-autocomplete-item publisher-autocomplete-create"
                onClick={handleCreateNew}
              >
                <span className="publisher-autocomplete-create-icon">+</span>
                <span>Создать новое издательство</span>
              </div>
            </>
          ) : (
            <div className="publisher-autocomplete-item publisher-autocomplete-create" onClick={handleCreateNew}>
              <span className="publisher-autocomplete-create-icon">+</span>
              <span>Создать новое издательство "{searchQuery}"</span>
            </div>
          )}
        </div>
      )}

      {showCreateModal && (
        <CreatePublisherModal
          isOpen={true}
          initialName={searchQuery}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handlePublisherCreated}
        />
      )}
    </div>
  );
};

export default PublisherAutocomplete;

