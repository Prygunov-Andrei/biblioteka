import { useState } from 'react';
import ConfirmModal from './ConfirmModal';
import './ConfirmationStep.css';

const ConfirmationStep = ({ 
  formData, 
  normalizedPages, 
  pages, 
  onBack, 
  onCreate, 
  onCancel 
}) => {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);

  const handleCreate = async () => {
    if (!formData || !formData.title || formData.title.trim() === '') {
      setError('Название книги обязательно для заполнения');
      setShowErrorModal(true);
      return;
    }

    setCreating(true);
    setError(null);

    try {
      if (onCreate) {
        console.log('ConfirmationStep: отправляем данные для создания книги:', {
          formData,
          normalizedPagesCount: normalizedPages?.length || 0,
          pagesCount: pages?.length || 0
        });
        await onCreate({
          formData,
          normalizedPages,
          pages,
        });
      }
    } catch (err) {
      console.error('Ошибка создания книги:', err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.detail ||
                          err.message || 
                          'Не удалось создать книгу';
      setError(errorMessage);
      setShowErrorModal(true);
    } finally {
      setCreating(false);
    }
  };

  const formatFieldValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return 'Не указано';
    }
    if (Array.isArray(value)) {
      if (value.length === 0) return 'Не указано';
      return value.map(item => {
        if (typeof item === 'object' && item.full_name) {
          return item.full_name;
        }
        return String(item);
      }).join(', ');
    }
    return String(value);
  };


  return (
    <div className="confirmation-step">
      <div className="confirmation-step-header">
        <h3>Подтверждение создания книги</h3>
        <p className="confirmation-step-hint">
          Проверьте все данные перед созданием книги. Вы сможете отредактировать их позже.
        </p>
      </div>

      <div className="confirmation-step-content">
        {/* Основная информация */}
        <div className="confirmation-section">
          <h4 className="confirmation-section-title">Основная информация</h4>
          <div className="confirmation-field">
            <span className="confirmation-field-label">Название:</span>
            <span className="confirmation-field-value">{formatFieldValue(formData?.title)}</span>
          </div>
          {formData?.subtitle && (
            <div className="confirmation-field">
              <span className="confirmation-field-label">Подзаголовок:</span>
              <span className="confirmation-field-value">{formatFieldValue(formData.subtitle)}</span>
            </div>
          )}
          {formData?.authors && formData.authors.length > 0 && (
            <div className="confirmation-field">
              <span className="confirmation-field-label">Авторы:</span>
              <span className="confirmation-field-value">
                {formData.authors.map(a => a.full_name || a).join(', ')}
              </span>
            </div>
          )}
          {formData?.category_id && (
            <div className="confirmation-field">
              <span className="confirmation-field-label">Категория:</span>
              <span className="confirmation-field-value">
                {formData.category_name || `ID: ${formData.category_id}`}
              </span>
            </div>
          )}
        </div>

        {/* Издательство и публикация */}
        {(formData?.publisher_name || formData?.publication_place || formData?.year || formData?.year_approx) && (
          <div className="confirmation-section">
            <h4 className="confirmation-section-title">Издательство и публикация</h4>
            {formData?.publisher_name && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Издательство:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.publisher_name)}</span>
              </div>
            )}
            {formData?.publication_place && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Место издания:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.publication_place)}</span>
              </div>
            )}
            {(formData?.year || formData?.year_approx) && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Год издания:</span>
                <span className="confirmation-field-value">
                  {formData.year || formData.year_approx || 'Не указано'}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Дополнительная информация */}
        {(formData?.pages_info || formData?.circulation || formData?.language_name || 
          formData?.binding_type || formData?.format || formData?.condition || formData?.isbn) && (
          <div className="confirmation-section">
            <h4 className="confirmation-section-title">Дополнительная информация</h4>
            {formData?.pages_info && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Страниц:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.pages_info)}</span>
              </div>
            )}
            {formData?.circulation && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Тираж:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.circulation)}</span>
              </div>
            )}
            {formData?.language_name && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Язык:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.language_name)}</span>
              </div>
            )}
            {formData?.binding_type && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Тип переплета:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.binding_type)}</span>
              </div>
            )}
            {formData?.format && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Формат:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.format)}</span>
              </div>
            )}
            {formData?.condition && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">Состояние:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.condition)}</span>
              </div>
            )}
            {formData?.isbn && (
              <div className="confirmation-field">
                <span className="confirmation-field-label">ISBN:</span>
                <span className="confirmation-field-value">{formatFieldValue(formData.isbn)}</span>
              </div>
            )}
          </div>
        )}

        {/* Описание */}
        {formData?.description && (
          <div className="confirmation-section">
            <h4 className="confirmation-section-title">Описание</h4>
            <div className="confirmation-field-full">
              <p className="confirmation-description">{formData.description}</p>
            </div>
          </div>
        )}

        {/* Страницы */}
        {normalizedPages && normalizedPages.length > 0 && (
          <div className="confirmation-section">
            <h4 className="confirmation-section-title">Загруженные страницы</h4>
            <div className="confirmation-pages-grid">
              {normalizedPages.slice(0, 6).map((page, index) => (
                <div key={page.id || index} className="confirmation-page-thumbnail">
                  <img 
                    src={page.normalized_url || page.url} 
                    alt={`Страница ${index + 1}`}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              ))}
              {normalizedPages.length > 6 && (
                <div className="confirmation-page-more">
                  +{normalizedPages.length - 6} еще
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Навигация */}
      <div className="wizard-navigation">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="wizard-button wizard-button-back"
            disabled={creating}
          >
            ← Назад
          </button>
        )}
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="wizard-button wizard-button-cancel"
            disabled={creating}
          >
            Отмена
          </button>
        )}
        <button
          type="button"
          onClick={handleCreate}
          className="wizard-button wizard-button-primary"
          disabled={creating || !formData?.title || formData.title.trim() === ''}
        >
          {creating ? 'Создание...' : 'Создать книгу'}
        </button>
      </div>

      {/* Модальное окно ошибки */}
      {error && showErrorModal && (
        <ConfirmModal
          isOpen={true}
          title="Ошибка создания книги"
          message={error}
          confirmText="ОК"
          onConfirm={() => setShowErrorModal(false)}
          onCancel={() => setShowErrorModal(false)}
          danger={true}
        />
      )}
    </div>
  );
};

export default ConfirmationStep;

