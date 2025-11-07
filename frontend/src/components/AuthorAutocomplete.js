import { useState, useEffect, useRef } from 'react';
import { authorsAPI } from '../services/api';
import CreateAuthorModal from './CreateAuthorModal';
import './AuthorAutocomplete.css';

const AuthorAutocomplete = ({ selectedAuthors = [], onChange, maxAuthors = 3, placeholder = 'Введите автора' }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [debounceTimer, setDebounceTimer] = useState(null);
  const wrapperRef = useRef(null);

  // Поиск авторов с debounce
  useEffect(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await authorsAPI.search(searchQuery.trim());
        // Фильтруем уже выбранных авторов
        const filteredResults = (Array.isArray(results) ? results : (results.results || []))
          .filter(author => !selectedAuthors.some(selected => selected.id === author.id));
        setSuggestions(filteredResults);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Ошибка поиска авторов:', error);
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
  }, [searchQuery, selectedAuthors]);

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
    setShowSuggestions(true);
  };

  const handleSelectAuthor = (author) => {
    if (selectedAuthors.length >= maxAuthors) {
      return; // Не добавляем, если достигнут максимум
    }
    
    // Проверяем, не выбран ли уже этот автор (сравниваем по id или по full_name)
    const isAlreadySelected = selectedAuthors.some(selected => 
      selected.id === author.id || 
      (selected.full_name && author.full_name && selected.full_name.toLowerCase() === author.full_name.toLowerCase())
    );
    
    if (isAlreadySelected) {
      return;
    }

    const newAuthors = [...selectedAuthors, author];
    setSearchQuery('');
    setShowSuggestions(false);
    onChange && onChange(newAuthors);
  };

  const handleRemoveAuthor = (authorId) => {
    if (!authorId) return;
    const newAuthors = selectedAuthors.filter(author => {
      // Сравниваем по id, если он есть, иначе по full_name
      if (author.id) {
        return author.id !== authorId;
      }
      // Если id нет, но есть full_name, сравниваем по нему (для обратной совместимости)
      return true; // Оставляем авторов без id (не должны удаляться по authorId)
    });
    onChange && onChange(newAuthors);
  };

  const handleCreateNew = () => {
    setShowCreateModal(true);
    setShowSuggestions(false);
  };

  const handleAuthorCreated = (newAuthor) => {
    console.log('AuthorAutocomplete: handleAuthorCreated вызван с:', newAuthor);
    console.log('AuthorAutocomplete: текущие selectedAuthors:', selectedAuthors);
    
    // Заменяем временного автора на созданного, если есть временный с таким же именем
    const updatedAuthors = selectedAuthors.map(author => {
      const isTemporary = author.isTemporary || (author.id && String(author.id).startsWith('temp-'));
      const nameMatches = author.full_name && newAuthor.full_name && 
        author.full_name.toLowerCase().trim() === newAuthor.full_name.toLowerCase().trim();
      
      console.log(`AuthorAutocomplete: проверяем автора ${author.full_name}:`, {
        isTemporary,
        nameMatches,
        authorName: author.full_name,
        newAuthorName: newAuthor.full_name
      });
      
      if (isTemporary && nameMatches) {
        console.log(`AuthorAutocomplete: заменяем временного автора ${author.full_name} на созданного`);
        return newAuthor; // Заменяем временного на созданного
      }
      return author;
    });
    
    // Если временного автора не было (создали нового), добавляем
    const wasReplaced = updatedAuthors.some(a => a.id === newAuthor.id);
    console.log('AuthorAutocomplete: был ли заменен автор?', wasReplaced);
    
    if (!wasReplaced && updatedAuthors.length < maxAuthors) {
      console.log('AuthorAutocomplete: добавляем нового автора в список');
      updatedAuthors.push(newAuthor);
    }
    
    console.log('AuthorAutocomplete: обновленный список авторов:', updatedAuthors);
    setSearchQuery('');
    onChange && onChange(updatedAuthors);
    setShowCreateModal(false);
  };

  const handleInputFocus = () => {
    // Показываем выпадающий список при фокусе, если есть текст для поиска
    if (searchQuery.trim().length >= 2) {
      setShowSuggestions(true);
    }
  };

  const canAddMore = selectedAuthors.length < maxAuthors;

  return (
    <div className="author-autocomplete" ref={wrapperRef}>
      {/* Список выбранных авторов (чипсы) */}
      {selectedAuthors.length > 0 && (
        <div className="author-autocomplete-selected">
          {selectedAuthors.map((author, index) => {
            const isTemporary = author.isTemporary || (author.id && String(author.id).startsWith('temp-'));
            return (
              <div 
                key={author.id || `author-chip-${index}`} 
                className={`author-chip ${isTemporary ? 'author-chip-temporary' : ''}`}
                title={isTemporary ? 'Автор не найден в базе. Нажмите, чтобы создать.' : ''}
              >
                <span className="author-chip-name">{author.full_name}</span>
                {isTemporary && (
                  <button
                    type="button"
                    className="author-chip-create"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('AuthorAutocomplete: нажата кнопка создания для временного автора:', author.full_name);
                      setSearchQuery(author.full_name);
                      handleCreateNew();
                    }}
                    aria-label={`Создать автора ${author.full_name}`}
                    title="Создать автора в базе"
                  >
                    +
                  </button>
                )}
                <button
                  type="button"
                  className="author-chip-remove"
                  onClick={() => handleRemoveAuthor(author.id || `author-chip-${index}`)}
                  aria-label={`Удалить ${author.full_name}`}
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Поле ввода (показывается только если можно добавить еще) */}
      {canAddMore && (
        <>
          <input
            type="text"
            value={searchQuery}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            placeholder={placeholder}
            className="author-autocomplete-input form-input"
            disabled={!canAddMore}
          />
          
          {loading && (
            <div className="author-autocomplete-loading">
              Поиск...
            </div>
          )}

          {showSuggestions && !loading && searchQuery.trim().length >= 2 && (
            <div className="author-autocomplete-dropdown">
              {suggestions.length > 0 ? (
                <>
                  {suggestions.map((author, index) => (
                    <div
                      key={author.id || `author-${index}`}
                      className="author-autocomplete-item"
                      onClick={() => handleSelectAuthor(author)}
                    >
                      <div className="author-autocomplete-name">{author.full_name}</div>
                      {author.birth_year && (
                        <div className="author-autocomplete-meta">
                          {author.birth_year}
                          {author.death_year && ` - ${author.death_year}`}
                        </div>
                      )}
                    </div>
                  ))}
                  <div
                    className="author-autocomplete-item author-autocomplete-create"
                    onClick={handleCreateNew}
                  >
                    <span className="author-autocomplete-create-icon">+</span>
                    <span>Создать нового автора</span>
                  </div>
                </>
              ) : (
                <div className="author-autocomplete-item author-autocomplete-create" onClick={handleCreateNew}>
                  <span className="author-autocomplete-create-icon">+</span>
                  <span>Создать нового автора "{searchQuery}"</span>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {!canAddMore && (
        <div className="author-autocomplete-limit">
          Достигнут максимум авторов ({maxAuthors})
        </div>
      )}

      {showCreateModal && (
        <CreateAuthorModal
          isOpen={true}
          initialName={searchQuery}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleAuthorCreated}
        />
      )}
    </div>
  );
};

export default AuthorAutocomplete;

