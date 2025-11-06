import { useState } from 'react';
import { booksAPI } from '../services/api';
import ConfirmModal from './ConfirmModal';
import './AutoFillStep.css';

const AutoFillStep = ({ normalizedPages, onAutoFillData, onNext, onSkip, onBack }) => {
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [autoFillResult, setAutoFillResult] = useState(null);

  const handleAutoFill = async () => {
    if (!normalizedPages || normalizedPages.length === 0) {
      setError('Нет нормализованных изображений для анализа');
      setShowErrorModal(true);
      return;
    }

    // Фильтруем только успешно обработанные изображения
    const successfulPages = normalizedPages.filter(
      img => img.normalized_url && !img.error
    );

    if (successfulPages.length === 0) {
      setError('Нет успешно обработанных изображений для анализа');
      setShowErrorModal(true);
      return;
    }

    setProcessing(true);
    setProgress(0);
    setError(null);
    setAutoFillResult(null);

    try {
      // Симуляция прогресса (реальный прогресс будет зависеть от ответа API)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      // Формируем полные URL для изображений
      const baseUrl = 'http://localhost:8000';
      const imageUrls = successfulPages.map(img => {
        if (img.normalized_url.startsWith('http')) {
          return img.normalized_url;
        }
        return `${baseUrl}${img.normalized_url}`;
      });

      const result = await booksAPI.autoFill(imageUrls);
      clearInterval(progressInterval);
      setProgress(100);

      console.log('AutoFill результат:', result);

      if (result.success && result.data) {
        setAutoFillResult(result);
        if (onAutoFillData) {
          onAutoFillData(result.data);
        }
        // Автоматически переходим на следующий шаг после успешного получения данных
        if (onNext) {
          setTimeout(() => {
            onNext({ autoFillData: result.data });
          }, 500); // Небольшая задержка для визуального отклика
        }
      } else {
        let errorMessage = result.error || 'Не удалось получить данные от LLM';
        
        // Специальная обработка ошибки региона
        if (errorMessage.includes('недоступен в вашем регионе') || 
            errorMessage.includes('unsupported_country_region_territory')) {
          errorMessage = 'OpenAI API недоступен в вашем регионе. Для использования автозаполнения необходимо:\n\n' +
            '1. Использовать VPN с сервером в поддерживаемой стране (США, Канада, ЕС)\n' +
            '2. Или обратиться в поддержку OpenAI для получения доступа\n\n' +
            'Вы можете пропустить этот шаг и заполнить данные вручную.';
        }
        
        console.error('Ошибка автозаполнения:', errorMessage, result);
        setError(errorMessage);
        setShowErrorModal(true);
      }
    } catch (err) {
      console.error('Ошибка автозаполнения:', err);
      setError(err.response?.data?.error || err.message || 'Не удалось выполнить автозаполнение');
      setShowErrorModal(true);
    } finally {
      setProcessing(false);
    }
  };

  const handleNext = () => {
    if (autoFillResult && autoFillResult.data) {
      if (onNext) {
        onNext({ autoFillData: autoFillResult.data });
      }
    } else {
      // Если нет данных, просто переходим дальше
      if (onSkip) {
        onSkip();
      }
    }
  };

  const handleSkip = () => {
    if (onSkip) {
      onSkip();
    }
  };

  const hasNormalizedPages = normalizedPages && normalizedPages.length > 0;
  const successfulPages = hasNormalizedPages
    ? normalizedPages.filter(img => img.normalized_url && !img.error)
    : [];

  return (
    <div className="auto-fill-step">
      <div className="auto-fill-instructions">
        <p>Автозаполнение данных книги через OpenAI GPT-4o</p>
        {hasNormalizedPages && successfulPages.length > 0 && (
          <p className="auto-fill-hint">
            Будет проанализировано {successfulPages.length} изображение(й)
          </p>
        )}
        {hasNormalizedPages && successfulPages.length === 0 && (
          <p className="auto-fill-hint" style={{ color: '#f44336' }}>
            Нет успешно обработанных изображений для анализа. Вернитесь на шаг 2 и выполните нормализацию.
          </p>
        )}
        {!hasNormalizedPages && (
          <p className="auto-fill-hint" style={{ color: '#f44336' }}>
            Нет нормализованных изображений. Вернитесь на шаг 1 и загрузите страницы.
          </p>
        )}
      </div>

      {processing && (
        <div className="auto-fill-progress">
          <div className="auto-fill-progress-bar">
            <div
              className="auto-fill-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="auto-fill-progress-text">
            Анализ изображений... {progress}%
          </p>
        </div>
      )}

      {!processing && !autoFillResult && successfulPages.length > 0 && (
        <div className="auto-fill-start">
          <button
            type="button"
            className="auto-fill-button auto-fill-button-start"
            onClick={handleAutoFill}
          >
            Заполнить автоматически
          </button>
        </div>
      )}

      {autoFillResult && autoFillResult.success && (
        <div className="auto-fill-success-message">
          <div className="auto-fill-success-icon">✓</div>
          <p>Данные успешно извлечены. Переход к заполнению формы...</p>
        </div>
      )}

      {/* Навигация показывается только если автозаполнение еще не выполнено или выполнено с ошибкой */}
      {!processing && (!autoFillResult || !autoFillResult.success) && (
        <div className="wizard-navigation">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="wizard-button wizard-button-back"
            >
              ← Назад
            </button>
          )}
          <button
            type="button"
            onClick={handleSkip}
            className="wizard-button wizard-button-skip"
          >
            Пропустить автозаполнение
          </button>
        </div>
      )}

      {error && showErrorModal && (
        <ConfirmModal
          isOpen={true}
          title="Ошибка автозаполнения"
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

export default AutoFillStep;

