import { useState, useEffect, useRef } from 'react';
import { librariesAPI } from '../services/api';
import './LibrarySelector.css';

const LibrarySelector = ({ selectedLibraries, onLibrariesChange }) => {
  const [libraries, setLibraries] = useState([]);
  const [myLibraries, setMyLibraries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadLibraries();
    
    // Закрываем dropdown при клике вне его
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadLibraries = async () => {
    try {
      setLoading(true);
      const [allLibrariesData, myLibrariesData] = await Promise.all([
        librariesAPI.getAll(),
        librariesAPI.getMyLibraries(),
      ]);
      
      const allLibraries = Array.isArray(allLibrariesData) 
        ? allLibrariesData 
        : (allLibrariesData.results || []);
      
      const myLibrariesList = Array.isArray(myLibrariesData)
        ? myLibrariesData
        : (myLibrariesData.results || []);
      
      setLibraries(allLibraries);
      setMyLibraries(myLibrariesList);
      
      // Если библиотеки еще не выбраны, выбираем все по умолчанию
      if (selectedLibraries.length === 0 && allLibraries.length > 0) {
        onLibrariesChange(allLibraries.map(lib => lib.id));
      }
    } catch (error) {
      console.error('Ошибка загрузки библиотек:', error);
    } finally {
      setLoading(false);
    }
  };

  const isMyLibrary = (libraryId) => {
    return myLibraries.some(lib => lib.id === libraryId);
  };

  const handleToggleLibrary = (libraryId) => {
    const newSelected = selectedLibraries.includes(libraryId)
      ? selectedLibraries.filter(id => id !== libraryId)
      : [...selectedLibraries, libraryId];
    onLibrariesChange(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedLibraries.length === libraries.length) {
      // Если все выбраны, снимаем выбор
      onLibrariesChange([]);
    } else {
      // Выбираем все
      onLibrariesChange(libraries.map(lib => lib.id));
    }
  };

  const allSelected = libraries.length > 0 && selectedLibraries.length === libraries.length;
  const someSelected = selectedLibraries.length > 0 && selectedLibraries.length < libraries.length;

  return (
    <div className="library-selector" ref={dropdownRef}>
      <button
        className="library-selector-button"
        onClick={() => setShowDropdown(!showDropdown)}
      >
        БИБЛИОТЕКИ
        <span className="selector-arrow">{showDropdown ? '▲' : '▼'}</span>
        {someSelected && (
          <span className="selector-count">({selectedLibraries.length})</span>
        )}
      </button>

      {showDropdown && (
        <div className="library-dropdown">
          {loading ? (
            <div className="dropdown-loading">Загрузка...</div>
          ) : (
            <>
              <div className="dropdown-header">
                <label className="select-all-checkbox">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(input) => {
                      if (input) {
                        input.indeterminate = someSelected && !allSelected;
                      }
                    }}
                    onChange={handleSelectAll}
                  />
                  <span>Выбрать все ({libraries.length})</span>
                </label>
              </div>
              <div className="dropdown-divider"></div>
              
              {/* Сначала показываем свои библиотеки */}
              {myLibraries.length > 0 && (
                <>
                  <div className="dropdown-section">
                    <div className="section-title">Мои библиотеки</div>
                    {myLibraries.map((library) => (
                      <label
                        key={library.id}
                        className={`library-item ${isMyLibrary(library.id) ? 'my-library' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedLibraries.includes(library.id)}
                          onChange={() => handleToggleLibrary(library.id)}
                        />
                        <span className="library-name">{library.name}</span>
                        <span className="library-meta">
                          {library.city && library.city + ', '}
                          {library.country || ''}
                        </span>
                      </label>
                    ))}
                  </div>
                  {libraries.some(lib => !isMyLibrary(lib.id)) && (
                    <div className="dropdown-divider"></div>
                  )}
                </>
              )}
              
              {/* Затем остальные библиотеки */}
              {libraries.filter(lib => !isMyLibrary(lib.id)).length > 0 && (
                <div className="dropdown-section">
                  {myLibraries.length > 0 && (
                    <div className="section-title">Другие библиотеки</div>
                  )}
                  {libraries
                    .filter(lib => !isMyLibrary(lib.id))
                    .map((library) => (
                      <label
                        key={library.id}
                        className="library-item"
                      >
                        <input
                          type="checkbox"
                          checked={selectedLibraries.includes(library.id)}
                          onChange={() => handleToggleLibrary(library.id)}
                        />
                        <span className="library-name">{library.name}</span>
                        <span className="library-meta">
                          {library.city && library.city + ', '}
                          {library.country || ''}
                        </span>
                        <span className="library-owner">
                          @{library.owner_username}
                        </span>
                      </label>
                    ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default LibrarySelector;

