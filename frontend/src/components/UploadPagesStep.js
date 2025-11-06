import { useState, useRef } from 'react';
import ConfirmModal from './ConfirmModal';
import './UploadPagesStep.css';

const UploadPagesStep = ({ files, onFilesChange, onNext, onSkip, onBack }) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const MAX_FILES = 50;
  const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];

  const validateFile = (file) => {
    // Проверка типа файла
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Неподдерживаемый формат файла. Разрешены только JPEG, PNG и WebP.';
    }

    // Проверка размера файла
    if (file.size > MAX_FILE_SIZE) {
      return `Файл "${file.name}" слишком большой. Максимальный размер: ${(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)} МБ.`;
    }

    return null;
  };

  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList);
    const existingFilesCount = files.length;

    // Проверка общего количества файлов
    if (existingFilesCount + newFiles.length > MAX_FILES) {
      setValidationError(`Максимальное количество файлов: ${MAX_FILES}. У вас уже ${existingFilesCount} файлов.`);
      return;
    }

    // Валидация каждого файла
    const errors = [];
    const validFiles = [];

    newFiles.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setValidationError(errors.join('\n'));
    } else {
      setValidationError(null);
      // Добавляем новые файлы к существующим
      onFilesChange([...files, ...validFiles]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
      // Сбрасываем input, чтобы можно было выбрать тот же файл снова
      e.target.value = '';
    }
  };

  const handleRemoveFile = (index) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
    setValidationError(null);
  };

  const handleClearAll = () => {
    onFilesChange([]);
    setValidationError(null);
  };

  const handleNext = () => {
    if (files.length === 0) {
      // Если нет файлов, пропускаем этот шаг
      if (onSkip) {
        onSkip();
      }
    } else {
      // Передаем данные и переходим к следующему шагу
      if (onNext) {
        onNext({ pages: files });
      }
    }
  };

  const handleSkip = () => {
    if (onSkip) {
      onSkip();
    }
  };

  const getFilePreview = (file) => {
    return URL.createObjectURL(file);
  };

  return (
    <div className="upload-pages-step">
      <div className="upload-pages-instructions">
        <p>Загрузите изображения страниц книги (обложка, титульный лист, страницы с описанием и т.д.)</p>
        <p className="upload-pages-hint">
          Поддерживаемые форматы: JPEG, PNG, WebP. Максимальный размер файла: {(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)} МБ. 
          Максимальное количество файлов: {MAX_FILES}.
        </p>
      </div>

      <div
        className={`upload-pages-dropzone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="upload-pages-dropzone-content">
          <div className="upload-pages-dropzone-icon">📄</div>
          <p className="upload-pages-dropzone-text">
            Перетащите файлы сюда или нажмите для выбора
          </p>
          <button
            type="button"
            className="upload-pages-select-button"
            onClick={() => fileInputRef.current?.click()}
          >
            Выбрать файлы
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/jpg,image/png,image/webp"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      {validationError && (
        <div className="upload-pages-error">
          <p>{validationError}</p>
          <button
            type="button"
            className="upload-pages-error-close"
            onClick={() => setValidationError(null)}
          >
            ×
          </button>
        </div>
      )}

      {files.length > 0 && (
        <div className="upload-pages-files">
          <div className="upload-pages-files-header">
            <h3>Загруженные файлы ({files.length})</h3>
            <button
              type="button"
              className="upload-pages-clear-all"
              onClick={handleClearAll}
            >
              Очистить все
            </button>
          </div>
          <div className="upload-pages-files-list">
            {files.map((file, index) => (
              <div key={index} className="upload-pages-file-item">
                <div className="upload-pages-file-preview">
                  <img
                    src={getFilePreview(file)}
                    alt={file.name}
                    onLoad={(e) => {
                      // Освобождаем URL после загрузки в браузерный кэш
                      setTimeout(() => URL.revokeObjectURL(e.target.src), 100);
                    }}
                  />
                </div>
                <div className="upload-pages-file-info">
                  <p className="upload-pages-file-name" title={file.name}>
                    {file.name}
                  </p>
                  <p className="upload-pages-file-size">
                    {(file.size / 1024).toFixed(1)} КБ
                  </p>
                </div>
                <button
                  type="button"
                  className="upload-pages-file-remove"
                  onClick={() => handleRemoveFile(index)}
                  aria-label={`Удалить ${file.name}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="upload-pages-actions">
        {onBack && (
          <button
            type="button"
            className="upload-pages-button upload-pages-button-back"
            onClick={onBack}
          >
            Назад
          </button>
        )}
        <button
          type="button"
          className="upload-pages-button upload-pages-button-skip"
          onClick={handleSkip}
        >
          Пропустить
        </button>
        <button
          type="button"
          className="upload-pages-button upload-pages-button-next"
          onClick={handleNext}
          disabled={validationError !== null}
        >
          Далее
        </button>
      </div>
    </div>
  );
};

export default UploadPagesStep;

