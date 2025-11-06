import { useState } from 'react';
import { booksAPI } from '../services/api';
import ConfirmModal from './ConfirmModal';
import './NormalizationStep.css';

const NormalizationStep = ({ files, normalizedPages, onNormalizedPagesChange, onNext, onSkip }) => {
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);

  // Убрал автоматический запуск - пользователь сам нажимает кнопку "Начать нормализацию"

  const handleNormalize = async () => {
    if (!files || files.length === 0) {
      setError('Нет файлов для нормализации');
      setShowErrorModal(true);
      return;
    }

    setProcessing(true);
    setProgress(0);
    setError(null);

    try {
      // Симулируем прогресс (так как обработка на сервере синхронная)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await booksAPI.normalizePages(files);
      clearInterval(progressInterval);
      setProgress(100);

      // Разделяем успешно обработанные и файлы с ошибками
      const successful = result.normalized_images?.filter(img => img.normalized_url && !img.error) || [];
      const failed = result.normalized_images?.filter(img => img.error || !img.normalized_url) || [];

      // Сохраняем все результаты (включая файлы с ошибками)
      if (result.normalized_images && result.normalized_images.length > 0) {
        onNormalizedPagesChange(result.normalized_images);
      }

      // Показываем предупреждение, если есть ошибки
      if (failed.length > 0) {
        const errorMessages = failed.map(img => `${img.original_filename}: ${img.error || 'Документ не найден на изображении'}`).join('\n');
        
        if (successful.length === 0) {
          // Если все файлы не удалось обработать
          setError(`Не удалось обработать ни одного файла. Возможные причины:\n- На изображении не видно четких границ документа\n- Изображение слишком темное или размытое\n- Документ занимает слишком маленькую область\n\nВы можете пропустить нормализацию и использовать оригинальные изображения.\n\nОшибки:\n${errorMessages}`);
        } else {
          // Если часть файлов обработана успешно
          setError(`Успешно обработано: ${successful.length} из ${result.normalized_images.length} файлов.\n\nНе удалось обработать:\n${errorMessages}\n\nВы можете продолжить с успешно обработанными файлами или пропустить нормализацию.`);
        }
        setShowErrorModal(true);
      }
    } catch (err) {
      console.error('Ошибка нормализации:', err);
      setError(err.response?.data?.error || err.message || 'Не удалось обработать страницы');
      setShowErrorModal(true);
    } finally {
      setProcessing(false);
    }
  };

  const handleNext = () => {
    // Проверяем, есть ли хотя бы один успешно обработанный файл
    const hasSuccessful = normalizedPages && normalizedPages.some(img => img.normalized_url && !img.error);
    
    if (hasSuccessful) {
      // Передаем только успешно обработанные файлы
      const successfulPages = normalizedPages.filter(img => img.normalized_url && !img.error);
      if (onNext) {
        onNext({ normalizedPages: successfulPages });
      }
    } else {
      // Если нет успешно обработанных файлов, пропускаем этот шаг
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

  const getFilePreview = (file) => {
    if (file instanceof File) {
      return URL.createObjectURL(file);
    }
    return null;
  };

  const getNormalizedPreview = (normalizedImage) => {
    if (normalizedImage && normalizedImage.normalized_url) {
      // Добавляем базовый URL если нужно
      const baseUrl = 'http://localhost:8000';
      return normalizedImage.normalized_url.startsWith('http') 
        ? normalizedImage.normalized_url 
        : `${baseUrl}${normalizedImage.normalized_url}`;
    }
    return null;
  };

  // Отладочная информация
  const hasFiles = files && files.length > 0;
  const hasNormalized = normalizedPages && normalizedPages.length > 0;
  const showStartButton = !processing && !hasNormalized && hasFiles;

  return (
    <div className="normalization-step">
      <div className="normalization-instructions">
        <p>Нормализация страниц - автоматическое исправление перспективы и выравнивание изображений</p>
        {hasFiles && (
          <p className="normalization-hint">
            Обрабатывается {files.length} файл(ов)
          </p>
        )}
        {!hasFiles && (
          <p className="normalization-hint" style={{ color: '#f44336' }}>
            Нет файлов для нормализации. Вернитесь на шаг 1 и загрузите страницы.
          </p>
        )}
      </div>

      {processing && (
        <div className="normalization-progress">
          <div className="normalization-progress-bar">
            <div 
              className="normalization-progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="normalization-progress-text">
            Обработка... {progress}%
          </p>
        </div>
      )}

      {showStartButton && (
        <div className="normalization-start">
          <button
            type="button"
            className="normalization-button normalization-button-start"
            onClick={handleNormalize}
          >
            Начать нормализацию
          </button>
        </div>
      )}

      {hasNormalized && (
        <div className="normalization-results">
          <div className="normalization-results-header">
            <h3>Результаты нормализации</h3>
            <div className="normalization-results-stats">
              {(() => {
                const successful = normalizedPages.filter(img => img.normalized_url && !img.error).length;
                const failed = normalizedPages.filter(img => img.error || !img.normalized_url).length;
                return (
                  <>
                    {successful > 0 && <span className="normalization-stat-success">✓ Успешно: {successful}</span>}
                    {failed > 0 && <span className="normalization-stat-error">✗ Ошибок: {failed}</span>}
                  </>
                );
              })()}
            </div>
          </div>
          <div className="normalization-comparison">
            {files.map((file, index) => {
              const normalized = normalizedPages[index];
              const originalPreview = getFilePreview(file);
              const normalizedPreview = normalized ? getNormalizedPreview(normalized) : null;

              return (
                <div key={index} className="normalization-comparison-item">
                  <div className="normalization-comparison-before">
                    <p className="normalization-comparison-label">До</p>
                    {originalPreview && (
                      <img
                        src={originalPreview}
                        alt={`Оригинал ${file.name}`}
                        className="normalization-comparison-image"
                        onLoad={(e) => {
                          setTimeout(() => URL.revokeObjectURL(e.target.src), 100);
                        }}
                      />
                    )}
                    <p className="normalization-comparison-filename">{file.name}</p>
                  </div>
                  <div className="normalization-comparison-arrow">→</div>
                  <div className="normalization-comparison-after">
                    <p className="normalization-comparison-label">После</p>
                    {normalizedPreview ? (
                      <>
                        <img
                          src={normalizedPreview}
                          alt={`Нормализовано ${normalized.original_filename}`}
                          className="normalization-comparison-image"
                        />
                        {normalized.error ? (
                          <p className="normalization-comparison-error">Ошибка: {normalized.error}</p>
                        ) : (
                          <p className="normalization-comparison-info">
                            {normalized.width} × {normalized.height} px
                          </p>
                        )}
                      </>
                    ) : (
                      <div className="normalization-comparison-placeholder">
                        <p>Ошибка обработки</p>
                      </div>
                    )}
                    <p className="normalization-comparison-filename">
                      {normalized ? normalized.original_filename : file.name}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!processing && hasNormalized && (
        <div className="normalization-actions">
          <button
            type="button"
            className="normalization-button normalization-button-skip"
            onClick={handleSkip}
          >
            Пропустить нормализацию
          </button>
          <button
            type="button"
            className="normalization-button normalization-button-next"
            onClick={handleNext}
          >
            Далее
          </button>
        </div>
      )}

      {showErrorModal && (
        <ConfirmModal
          isOpen={true}
          title="Ошибка нормализации"
          message={error || 'Неизвестная ошибка'}
          confirmText="ОК"
          cancelText={null}
          onConfirm={() => setShowErrorModal(false)}
          onCancel={() => setShowErrorModal(false)}
        />
      )}
    </div>
  );
};

export default NormalizationStep;

