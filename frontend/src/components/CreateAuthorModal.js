import { useState, useEffect } from 'react';
import { authorsAPI } from '../services/api';
import './CreateAuthorModal.css';

const CreateAuthorModal = ({ isOpen, initialName = '', onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    full_name: initialName,
    birth_year: '',
    death_year: '',
    biography: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        full_name: initialName,
        birth_year: '',
        death_year: '',
        biography: '',
        notes: '',
      });
      setErrors({});
    }
  }, [isOpen, initialName]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Очищаем ошибку для этого поля
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.full_name || formData.full_name.trim().length === 0) {
      newErrors.full_name = 'ФИО автора обязательно';
    } else if (formData.full_name.trim().length > 500) {
      newErrors.full_name = 'ФИО не должно превышать 500 символов';
    }

    if (formData.birth_year) {
      const birthYear = parseInt(formData.birth_year);
      if (isNaN(birthYear) || birthYear < 0 || birthYear > 2100) {
        newErrors.birth_year = 'Год рождения должен быть от 0 до 2100';
      }
    }

    if (formData.death_year) {
      const deathYear = parseInt(formData.death_year);
      if (isNaN(deathYear) || deathYear < 0 || deathYear > 2100) {
        newErrors.death_year = 'Год смерти должен быть от 0 до 2100';
      }
      if (formData.birth_year && parseInt(formData.birth_year) >= deathYear) {
        newErrors.death_year = 'Год смерти должен быть больше года рождения';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation(); // Предотвращаем всплытие события

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      console.log('CreateAuthorModal: создаем автора:', formData);
      
      // Формируем данные для отправки - не отправляем пустые поля
      const authorData = {
        full_name: formData.full_name.trim(),
      };
      
      if (formData.birth_year && formData.birth_year.trim()) {
        const birthYear = parseInt(formData.birth_year);
        if (!isNaN(birthYear)) {
          authorData.birth_year = birthYear;
        }
      }
      
      if (formData.death_year && formData.death_year.trim()) {
        const deathYear = parseInt(formData.death_year);
        if (!isNaN(deathYear)) {
          authorData.death_year = deathYear;
        }
      }
      
      if (formData.biography && formData.biography.trim()) {
        authorData.biography = formData.biography.trim();
      }
      
      if (formData.notes && formData.notes.trim()) {
        authorData.notes = formData.notes.trim();
      }
      
      console.log('CreateAuthorModal: отправляем данные:', authorData);
      const newAuthor = await authorsAPI.create(authorData);

      console.log('CreateAuthorModal: автор успешно создан:', newAuthor);
      
      // Вызываем onSuccess ПЕРЕД закрытием модального окна
      if (onSuccess) {
        console.log('CreateAuthorModal: вызываем onSuccess с автором:', newAuthor);
        onSuccess(newAuthor);
      } else {
        console.warn('CreateAuthorModal: onSuccess не определен!');
      }
      
      // Закрываем модальное окно после вызова onSuccess
      console.log('CreateAuthorModal: закрываем модальное окно');
      onClose();
    } catch (error) {
      console.error('CreateAuthorModal: ошибка создания автора:', error);
      if (error.response?.data) {
        const serverErrors = error.response.data;
        setErrors(serverErrors);
      } else {
        setErrors({ general: 'Не удалось создать автора. Попробуйте еще раз.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="create-author-modal-overlay"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div 
        className="create-author-modal" 
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.stopPropagation();
            onClose();
          }
        }}
      >
        <div className="create-author-modal-header">
          <h2>Создать нового автора</h2>
          <button
            className="create-author-modal-close"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <div 
          className="create-author-modal-body"
          onClick={(e) => e.stopPropagation()}
        >
          {errors.general && (
            <div className="create-author-modal-error">{errors.general}</div>
          )}

          <div className="form-group">
            <label htmlFor="author-full_name">
              ФИО автора <span className="required">*</span>
            </label>
            <input
              type="text"
              id="author-full_name"
              value={formData.full_name}
              onChange={(e) => handleChange('full_name', e.target.value)}
              placeholder="Например: Пушкин Александр Сергеевич"
              className={`form-input ${errors.full_name ? 'form-input-error' : ''}`}
              disabled={loading}
              autoFocus
            />
            {errors.full_name && (
              <div className="form-error">{errors.full_name}</div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="author-birth_year">Год рождения</label>
              <input
                type="number"
                id="author-birth_year"
                value={formData.birth_year}
                onChange={(e) => handleChange('birth_year', e.target.value)}
                placeholder="Например: 1799"
                min="0"
                max="2100"
                className={`form-input ${errors.birth_year ? 'form-input-error' : ''}`}
                disabled={loading}
              />
              {errors.birth_year && (
                <div className="form-error">{errors.birth_year}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="author-death_year">Год смерти</label>
              <input
                type="number"
                id="author-death_year"
                value={formData.death_year}
                onChange={(e) => handleChange('death_year', e.target.value)}
                placeholder="Например: 1837"
                min="0"
                max="2100"
                className={`form-input ${errors.death_year ? 'form-input-error' : ''}`}
                disabled={loading}
              />
              {errors.death_year && (
                <div className="form-error">{errors.death_year}</div>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="author-biography">Биография</label>
            <textarea
              id="author-biography"
              value={formData.biography}
              onChange={(e) => handleChange('biography', e.target.value)}
              placeholder="Краткая биография автора"
              rows="3"
              className="form-textarea"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="author-notes">Заметки</label>
            <textarea
              id="author-notes"
              value={formData.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              placeholder="Дополнительные заметки"
              rows="2"
              className="form-textarea"
              disabled={loading}
            />
          </div>

          <div className="create-author-modal-footer">
            <button
              type="button"
              onClick={onClose}
              className="wizard-button wizard-button-back"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="wizard-button wizard-button-next"
              disabled={loading || !formData.full_name.trim()}
            >
              {loading ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAuthorModal;

