import { useState, useEffect } from 'react';
import { booksAPI, librariesAPI } from '../services/api';
import ConfirmModal from './ConfirmModal';
import './BookTransferModal.css';

const BookTransferModal = ({ book, isOpen, onClose, onTransfer }) => {
  const [libraries, setLibraries] = useState([]);
  const [loadingLibraries, setLoadingLibraries] = useState(true);
  const [selectedLibraryId, setSelectedLibraryId] = useState('');
  const [transferring, setTransferring] = useState(false);
  const [error, setError] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);

  useEffect(() => {
    if (isOpen && book) {
      loadLibraries();
      // Сбрасываем состояние при открытии
      setSelectedLibraryId('');
      setError(null);
      setShowErrorModal(false);
    }
  }, [isOpen, book]);

  const loadLibraries = async () => {
    try {
      setLoadingLibraries(true);
      // Загружаем все библиотеки (не только свои)
      const librariesData = await librariesAPI.getAll();
      const librariesList = Array.isArray(librariesData) ? librariesData : (librariesData.results || []);
      
      // Если у книги уже есть библиотека, исключаем её из списка
      const filteredLibraries = book?.library 
        ? librariesList.filter(lib => lib.id !== book.library)
        : librariesList;
      
      setLibraries(filteredLibraries);
    } catch (err) {
      console.error('Ошибка загрузки библиотек:', err);
      setError('Не удалось загрузить список библиотек');
      setShowErrorModal(true);
    } finally {
      setLoadingLibraries(false);
    }
  };

  const handleTransfer = async () => {
    if (!selectedLibraryId) {
      setError('Выберите библиотеку для передачи');
      setShowErrorModal(true);
      return;
    }

    try {
      setTransferring(true);
      setError(null);
      
      const result = await booksAPI.transferBook(book.id, selectedLibraryId);
      
      if (onTransfer) {
        onTransfer(result.book);
      }
      
      // Закрываем модальное окно после успешной передачи
      handleClose();
    } catch (err) {
      console.error('Ошибка передачи книги:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Не удалось передать книгу';
      setError(errorMessage);
      setShowErrorModal(true);
    } finally {
      setTransferring(false);
    }
  };

  const handleClose = () => {
    setSelectedLibraryId('');
    setError(null);
    setShowErrorModal(false);
    onClose();
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleClose();
    }
  };

  if (!isOpen || !book) return null;

  return (
    <div
      className="book-transfer-modal-overlay"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="book-transfer-modal" onClick={(e) => e.stopPropagation()}>
        <div className="book-transfer-modal-header">
          <h2>Передать книгу</h2>
          <button
            className="book-transfer-modal-close"
            onClick={handleClose}
            aria-label="Закрыть"
            disabled={transferring}
          >
            ×
          </button>
        </div>

        <div className="book-transfer-modal-body">
          <div className="book-transfer-info">
            <p>Выберите библиотеку, в которую хотите передать книгу:</p>
            <div className="book-transfer-book-info">
              <strong>{book.title}</strong>
              {book.authors && book.authors.length > 0 && (
                <span> — {book.authors.map(a => a.full_name).join(', ')}</span>
              )}
            </div>
          </div>

          {loadingLibraries ? (
            <div className="book-transfer-loading">Загрузка библиотек...</div>
          ) : libraries.length === 0 ? (
            <div className="book-transfer-error">
              Нет доступных библиотек для передачи книги
            </div>
          ) : (
            <div className="book-transfer-form">
              <div className="form-group">
                <label htmlFor="library-select" className="required">
                  Библиотека *
                </label>
                <select
                  id="library-select"
                  className="form-input"
                  value={selectedLibraryId}
                  onChange={(e) => setSelectedLibraryId(e.target.value)}
                  disabled={transferring}
                >
                  <option value="">Выберите библиотеку</option>
                  {libraries.map((library) => (
                    <option key={library.id} value={library.id}>
                      {library.name}
                      {library.city && ` (${library.city})`}
                      {library.owner_username && ` — ${library.owner_username}`}
                    </option>
                  ))}
                </select>
              </div>

              {error && !showErrorModal && (
                <div className="book-transfer-form-error">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="book-transfer-modal-actions">
          <button
            type="button"
            className="book-transfer-modal-button book-transfer-modal-button-cancel"
            onClick={handleClose}
            disabled={transferring}
          >
            Отмена
          </button>
          {libraries.length > 0 && (
            <button
              type="button"
              className="book-transfer-modal-button book-transfer-modal-button-transfer"
              onClick={handleTransfer}
              disabled={transferring || !selectedLibraryId}
            >
              {transferring ? 'Передача...' : 'Передать'}
            </button>
          )}
        </div>
      </div>

      {/* Модальное окно для ошибок */}
      {showErrorModal && (
        <ConfirmModal
          isOpen={true}
          title="Ошибка"
          message={error || 'Произошла ошибка'}
          confirmText="ОК"
          cancelText={null}
          onConfirm={() => setShowErrorModal(false)}
          onCancel={() => setShowErrorModal(false)}
        />
      )}
    </div>
  );
};

export default BookTransferModal;

