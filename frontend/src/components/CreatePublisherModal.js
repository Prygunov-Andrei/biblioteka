import { useState, useEffect } from 'react';
import { publishersAPI } from '../services/api';
import './CreatePublisherModal.css';

const CreatePublisherModal = ({ isOpen, initialName = '', onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: initialName,
    city: '',
    website: '',
    description: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: initialName,
        city: '',
        website: '',
        description: '',
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

    if (!formData.name || formData.name.trim().length === 0) {
      newErrors.name = 'Название издательства обязательно';
    } else if (formData.name.trim().length > 300) {
      newErrors.name = 'Название не должно превышать 300 символов';
    }

    if (formData.city && formData.city.length > 200) {
      newErrors.city = 'Название города не должно превышать 200 символов';
    }

    if (formData.website && formData.website.trim()) {
      try {
        new URL(formData.website);
      } catch {
        newErrors.website = 'Введите корректный URL';
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
      console.log('CreatePublisherModal: создаем издательство:', formData);
      
      // Формируем данные для отправки - не отправляем пустые поля
      const publisherData = {
        name: formData.name.trim(),
      };
      
      if (formData.city && formData.city.trim()) {
        publisherData.city = formData.city.trim();
      }
      
      if (formData.website && formData.website.trim()) {
        publisherData.website = formData.website.trim();
      }
      
      if (formData.description && formData.description.trim()) {
        publisherData.description = formData.description.trim();
      }
      
      console.log('CreatePublisherModal: отправляем данные:', publisherData);
      const newPublisher = await publishersAPI.create(publisherData);

      console.log('CreatePublisherModal: издательство успешно создано:', newPublisher);
      
      // Вызываем onSuccess ПЕРЕД закрытием модального окна
      if (onSuccess) {
        console.log('CreatePublisherModal: вызываем onSuccess с издательством:', newPublisher);
        onSuccess(newPublisher);
      } else {
        console.warn('CreatePublisherModal: onSuccess не определен!');
      }
      
      // Закрываем модальное окно после вызова onSuccess
      console.log('CreatePublisherModal: закрываем модальное окно');
      onClose();
    } catch (error) {
      console.error('CreatePublisherModal: ошибка создания издательства:', error);
      if (error.response?.data) {
        const serverErrors = error.response.data;
        setErrors(serverErrors);
      } else {
        setErrors({ general: 'Не удалось создать издательство. Попробуйте еще раз.' });
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
      className="create-publisher-modal-overlay"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="create-publisher-modal" onClick={(e) => e.stopPropagation()}>
        <div className="create-publisher-modal-header">
          <h2>Создать новое издательство</h2>
          <button
            className="create-publisher-modal-close"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <div 
          className="create-publisher-modal-body"
          onClick={(e) => e.stopPropagation()}
        >
          {errors.general && (
            <div className="create-publisher-modal-error">{errors.general}</div>
          )}

          <div className="form-group">
            <label htmlFor="publisher-name">
              Название издательства <span className="required">*</span>
            </label>
            <input
              type="text"
              id="publisher-name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="Например: АСТ, Эксмо"
              className={`form-input ${errors.name ? 'form-input-error' : ''}`}
              disabled={loading}
              autoFocus
            />
            {errors.name && (
              <div className="form-error">{errors.name}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="publisher-city">Город</label>
            <input
              type="text"
              id="publisher-city"
              value={formData.city}
              onChange={(e) => handleChange('city', e.target.value)}
              placeholder="Например: Москва"
              className={`form-input ${errors.city ? 'form-input-error' : ''}`}
              disabled={loading}
            />
            {errors.city && (
              <div className="form-error">{errors.city}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="publisher-website">Сайт</label>
            <input
              type="url"
              id="publisher-website"
              value={formData.website}
              onChange={(e) => handleChange('website', e.target.value)}
              placeholder="https://example.com"
              className={`form-input ${errors.website ? 'form-input-error' : ''}`}
              disabled={loading}
            />
            {errors.website && (
              <div className="form-error">{errors.website}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="publisher-description">Описание</label>
            <textarea
              id="publisher-description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Дополнительная информация об издательстве"
              rows="3"
              className="form-textarea"
              disabled={loading}
            />
          </div>

          <div className="create-publisher-modal-footer">
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
              disabled={loading || !formData.name.trim()}
            >
              {loading ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatePublisherModal;

