import { useState, useRef, useEffect } from 'react';
import { booksAPI } from '../services/api';
import ConfirmModal from './ConfirmModal';
import './UploadPagesStep.css';

const UploadPagesStep = ({ files, onFilesChange, onNext, onSkip, normalizedPages, onNormalizedPagesChange, onAutoFillData }) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [normalizationError, setNormalizationError] = useState(null);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [hasStartedNormalization, setHasStartedNormalization] = useState(false);
  const [autoFilling, setAutoFilling] = useState(false);
  const [autoFillProgress, setAutoFillProgress] = useState(0);
  const [overallProgress, setOverallProgress] = useState(0); // Общий прогресс (0-100%)
  const [progressText, setProgressText] = useState(''); // Текст для отображения текущего этапа
  const [displayFiles, setDisplayFiles] = useState([]); // Файлы для отображения (могут быть нормализованными)
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

  // Инициализируем displayFiles при изменении files
  useEffect(() => {
    if (files.length > 0 && displayFiles.length === 0) {
      setDisplayFiles(files);
    }
  }, [files]);

  // Автоматически запускаем нормализацию после загрузки файлов
  useEffect(() => {
    // Запускаем нормализацию только если:
    // 1. Есть файлы
    // 2. Нормализация еще не запускалась
    // 3. Нормализация не в процессе
    // 4. Нет уже нормализованных страниц
    if (files.length > 0 && !hasStartedNormalization && !processing && (!normalizedPages || normalizedPages.length === 0)) {
      // Небольшая задержка для визуального отклика
      const timer = setTimeout(() => {
        handleAutoNormalize();
      }, 300);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files.length]); // Запускаем только при изменении количества файлов

  const handleAutoNormalize = async () => {
    if (!files || files.length === 0 || processing) {
      return;
    }

    // Проверяем, что все файлы - это объекты File
    const invalidFiles = files.filter(file => !(file instanceof File) && !(file instanceof Blob));
    if (invalidFiles.length > 0) {
      console.error('Обнаружены файлы неправильного типа:', invalidFiles);
      setNormalizationError('Ошибка: некоторые файлы имеют неправильный тип. Пожалуйста, загрузите файлы заново.');
      setShowErrorModal(true);
      return;
    }

    setHasStartedNormalization(true);
    setProcessing(true);
    setProgress(0);
    setOverallProgress(0);
    setProgressText('Нормализация страниц...');
    setNormalizationError(null);

    try {
      console.log('🚀 Запуск нормализации для', files.length, 'файлов');
      console.log('📁 Типы файлов:', files.map(f => ({ name: f.name, type: f.type, size: f.size })));
      
      // Симулируем прогресс нормализации (0-40% общего прогресса)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          const newProgress = prev + 10;
          if (newProgress >= 90) {
            clearInterval(progressInterval);
            // Обновляем общий прогресс: нормализация занимает 0-40%
            setOverallProgress(40);
            return 90;
          }
          // Обновляем общий прогресс: нормализация занимает 0-40%
          setOverallProgress((newProgress / 90) * 40);
          return newProgress;
        });
      }, 200);

      const result = await booksAPI.normalizePages(files);
      clearInterval(progressInterval);
      setProgress(100);
      setOverallProgress(40); // Нормализация завершена, это 40% общего прогресса

      // Разделяем успешно обработанные и файлы с ошибками
      const successful = result.normalized_images?.filter(img => img.normalized_url && !img.error) || [];
      const failed = result.normalized_images?.filter(img => img.error || !img.normalized_url) || [];

      // Сохраняем все результаты (включая файлы с ошибками)
      if (result.normalized_images && result.normalized_images.length > 0) {
        if (onNormalizedPagesChange) {
          onNormalizedPagesChange(result.normalized_images);
        }
      }

      // Обновляем отображаемые файлы на нормализованные
      if (successful.length > 0) {
        const baseUrl = 'http://localhost:8000';
        const normalizedDisplayFiles = successful.map((normalizedImg, index) => {
          // Создаем объект для отображения нормализованного изображения
          const normalizedUrl = normalizedImg.normalized_url.startsWith('http')
            ? normalizedImg.normalized_url
            : `${baseUrl}${normalizedImg.normalized_url}`;
          
          return {
            id: normalizedImg.id || `normalized-${index}`,
            name: normalizedImg.original_filename || `normalized_${index + 1}.jpg`,
            url: normalizedUrl,
            isNormalized: true,
            normalizedData: normalizedImg, // Сохраняем данные нормализованного изображения
            originalIndex: index // Сохраняем индекс оригинального файла для удаления
          };
        });
        
        // Обновляем отображаемые файлы
        setDisplayFiles(normalizedDisplayFiles);
        
        console.log('✅ Нормализованные файлы обновлены в интерфейсе:', normalizedDisplayFiles.length);
        
        // Небольшая задержка для визуального обновления перед запуском LLM
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Показываем предупреждение, если есть ошибки
      if (failed.length > 0) {
        const errorMessages = failed.map(img => `${img.original_filename}: ${img.error || 'Документ не найден на изображении'}`).join('\n');
        
        if (successful.length === 0) {
          // Если все файлы не удалось обработать, переходим к форме без LLM
          setNormalizationError(`Не удалось обработать ни одного файла. Возможные причины:\n- На изображении не видно четких границ документа\n- Изображение слишком темное или размытое\n- Документ занимает слишком маленькую область\n\nПереходим к форме без автозаполнения.\n\nОшибки:\n${errorMessages}`);
          setShowErrorModal(true);
          // Переходим к форме после закрытия модального окна
        } else {
          // Если часть файлов обработана успешно, обновляем отображаемые файлы на нормализованные
          const baseUrl = 'http://localhost:8000';
          const normalizedDisplayFiles = successful.map((normalizedImg, index) => {
            const normalizedUrl = normalizedImg.normalized_url.startsWith('http')
              ? normalizedImg.normalized_url
              : `${baseUrl}${normalizedImg.normalized_url}`;
            
            return {
              id: normalizedImg.id || `normalized-${index}`,
              name: normalizedImg.original_filename || `normalized_${index + 1}.jpg`,
              url: normalizedUrl,
              isNormalized: true,
              normalizedData: normalizedImg,
              originalIndex: index
            };
          });
          
          // Обновляем отображаемые файлы
          setDisplayFiles(normalizedDisplayFiles);
          
          setNormalizationError(`Успешно обработано: ${successful.length} из ${result.normalized_images.length} файлов.\n\nНе удалось обработать:\n${errorMessages}\n\nПродолжаем с успешно обработанными файлами.`);
          setShowErrorModal(true);
          // После закрытия модального окна запустим LLM
          // Это будет обработано в onConfirm модального окна
        }
      } else {
        // Если все успешно, автоматически запускаем LLM анализ
        if (successful.length > 0) {
          // Небольшая задержка перед запуском LLM
          setTimeout(() => {
            handleAutoFill(successful);
          }, 500);
        } else {
          // Если нет успешных страниц, переходим к форме
          setTimeout(() => {
            if (onNext) {
              onNext({ normalizedPages: successful });
            } else if (onSkip) {
              onSkip();
            }
          }, 500);
        }
      }
    } catch (err) {
      console.error('Ошибка нормализации:', err);
      setNormalizationError(err.response?.data?.error || err.message || 'Не удалось обработать страницы');
      setShowErrorModal(true);
    } finally {
      setProcessing(false);
    }
  };

  const handleAutoFill = async (successfulPages) => {
    if (!successfulPages || successfulPages.length === 0) {
      // Если нет успешных страниц, переходим к форме
      if (onNext) {
        onNext({ normalizedPages: successfulPages || [] });
      } else if (onSkip) {
        onSkip();
      }
      return;
    }

    setAutoFilling(true);
    setAutoFillProgress(0);
    setOverallProgress(40); // Начинаем LLM анализ с 40% (нормализация завершена)
    setProgressText('Анализ страниц LLM...');
    setNormalizationError(null);

    let progressInterval = null;
    let slowProgressInterval = null;

    try {
      // Симуляция прогресса LLM анализа - более равномерная и медленная
      // Ожидаемое время анализа: примерно 15-20 секунд на изображение (LLM может работать долго)
      const estimatedTime = successfulPages.length * 18; // ~18 секунд на изображение
      const totalSteps = 98; // До 98%, последние 2% - после получения результата
      const stepTime = Math.max(150, (estimatedTime * 1000) / totalSteps); // Минимум 150мс на шаг
      
      let currentProgress = 0;
      progressInterval = setInterval(() => {
        currentProgress += 1;
        if (currentProgress >= 98) {
          // Останавливаемся на 98%, последние 2% - после получения результата
          clearInterval(progressInterval);
          setAutoFillProgress(98);
          // Обновляем общий прогресс: LLM анализ занимает 40-100%, 98% от LLM = 40 + (98/100 * 60) = 98.8%
          setOverallProgress(40 + (98 / 100) * 60);
        } else {
          setAutoFillProgress(currentProgress);
          // Обновляем общий прогресс: LLM анализ занимает 40-100%
          setOverallProgress(40 + (currentProgress / 100) * 60);
        }
      }, stepTime);
      
      // Дополнительный таймер для медленного роста от 98% до 99% пока ждем ответ
      slowProgressInterval = setInterval(() => {
        setAutoFillProgress((prev) => {
          if (prev < 99) {
            const newProgress = prev + 0.05;
            // Обновляем общий прогресс: LLM анализ занимает 40-100%
            setOverallProgress(40 + (newProgress / 100) * 60);
            return newProgress;
          }
          return prev;
        });
      }, 500); // Каждые 500мс увеличиваем на 0.05%

      // Формируем полные URL для изображений
      const baseUrl = 'http://localhost:8000';
      const imageUrls = successfulPages.map(img => {
        if (img.normalized_url.startsWith('http')) {
          return img.normalized_url;
        }
        return `${baseUrl}${img.normalized_url}`;
      });

      const result = await booksAPI.autoFill(imageUrls);
      
      // Останавливаем оба интервала
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      if (slowProgressInterval) {
        clearInterval(slowProgressInterval);
      }
      
      // Плавно доводим до 100% после получения результата
      setAutoFillProgress(100);
      setOverallProgress(100); // Общий прогресс завершен

      console.log('AutoFill результат:', result);

      if (result.success && result.data) {
        // Передаем данные автозаполнения и нормализованные страницы
        if (onAutoFillData) {
          onAutoFillData(result.data);
        }
        // Автоматически переходим к форме (шаг 4)
        setTimeout(() => {
          if (onNext) {
            onNext({ 
              normalizedPages: successfulPages,
              autoFillData: result.data 
            });
          } else if (onSkip) {
            onSkip();
          }
        }, 500);
      } else {
        // Если LLM не сработал, переходим к форме без автозаполнения
        let errorMessage = result.error || 'Не удалось получить данные от LLM';
        
        // Специальная обработка ошибки региона
        if (errorMessage.includes('недоступен в вашем регионе') || 
            errorMessage.includes('unsupported_country_region_territory')) {
          console.warn('OpenAI API недоступен в регионе, переходим к форме без автозаполнения');
        } else {
          console.warn('Ошибка автозаполнения:', errorMessage);
        }
        
        // Переходим к форме даже при ошибке LLM
        setTimeout(() => {
          if (onNext) {
            onNext({ normalizedPages: successfulPages });
          } else if (onSkip) {
            onSkip();
          }
        }, 500);
      }
    } catch (err) {
      console.error('Ошибка автозаполнения:', err);
      // Останавливаем прогресс при ошибке
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      if (slowProgressInterval) {
        clearInterval(slowProgressInterval);
      }
      setAutoFillProgress(100);
      setOverallProgress(100); // Общий прогресс завершен (даже при ошибке)
      // Переходим к форме даже при ошибке
      setTimeout(() => {
        if (onNext) {
          onNext({ normalizedPages: successfulPages });
        } else if (onSkip) {
          onSkip();
        }
      }, 500);
    } finally {
      setAutoFilling(false);
    }
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
      // Нормализация запустится автоматически через useEffect
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


  const handleNext = () => {
    // Если нормализация завершена и есть успешные результаты, переходим дальше
    const hasSuccessful = normalizedPages && normalizedPages.some(img => img.normalized_url && !img.error);
    
    if (hasSuccessful) {
      const successfulPages = normalizedPages.filter(img => img.normalized_url && !img.error);
      if (onNext) {
        onNext({ normalizedPages: successfulPages });
      }
    } else if (files.length === 0) {
      // Если нет файлов, пропускаем этот шаг
      if (onSkip) {
        onSkip();
      }
    } else {
      // Если есть файлы, но нормализация не завершена или не удалась, переходим с оригинальными файлами
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
    // Если это нормализованное изображение (объект с url)
    if (file && typeof file === 'object' && file.url) {
      return file.url;
    }
    // Если это обычный File объект
    if (file instanceof File) {
      return URL.createObjectURL(file);
    }
    return null;
  };

  return (
    <div className="upload-pages-step">
      {/* Окно для перетаскивания файлов показывается только если нет загруженных файлов */}
      {files.length === 0 && !processing && !autoFilling && (
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
            <p className="upload-pages-dropzone-hint">
              Загрузите изображения страниц книги (обложка, титульный лист, страницы с описанием и т.д.)
            </p>
            <p className="upload-pages-dropzone-hint-small">
              Поддерживаемые форматы: JPEG, PNG, WebP. Максимальный размер файла: {(MAX_FILE_SIZE / 1024 / 1024).toFixed(0)} МБ. Максимальное количество файлов: {MAX_FILES}.
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
      )}

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

          {(files.length > 0 || displayFiles.length > 0) && (
            <div className="upload-pages-files">
              <div className="upload-pages-files-header">
                <h3>Загруженные файлы ({displayFiles.length > 0 ? displayFiles.length : files.length})</h3>
              </div>
          
          {/* Объединенный прогресс-бар для нормализации и анализа */}
          {(processing || autoFilling) && (
            <div className="upload-pages-normalization-progress">
              <div className="upload-pages-progress-bar">
                <div 
                  className="upload-pages-progress-fill" 
                  style={{ width: `${overallProgress}%` }}
                ></div>
              </div>
              <p className="upload-pages-progress-text">
                {progressText} {Math.round(overallProgress)}%
              </p>
            </div>
          )}

          <div className="upload-pages-files-list">
            {(displayFiles.length > 0 ? displayFiles : files).map((file, index) => {
              const fileKey = file.id || file.name || index;
              const fileName = file.name || (file instanceof File ? file.name : `Файл ${index + 1}`);
              const fileSize = file.size ? `${(file.size / 1024).toFixed(1)} КБ` : (file.isNormalized ? 'Нормализовано' : '');
              const previewUrl = getFilePreview(file);
              
              return (
                <div key={fileKey} className="upload-pages-file-item">
                  <div className="upload-pages-file-preview">
                    {previewUrl && (
                      <img
                        src={previewUrl}
                        alt={fileName}
                        onLoad={(e) => {
                          // Освобождаем URL только для File объектов (не для нормализованных)
                          if (file instanceof File) {
                            setTimeout(() => URL.revokeObjectURL(e.target.src), 100);
                          }
                        }}
                      />
                    )}
                  </div>
                  <div className="upload-pages-file-info">
                    <p className="upload-pages-file-name" title={fileName}>
                      {fileName}
                    </p>
                    {fileSize && (
                      <p className="upload-pages-file-size">
                        {fileSize}
                      </p>
                    )}
                    {file.isNormalized && (
                      <p className="upload-pages-file-status" style={{ color: '#4CAF50', fontSize: '11px', marginTop: '2px' }}>
                        ✓ Нормализовано
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}


      {normalizationError && showErrorModal && (
        <ConfirmModal
          isOpen={true}
          title="Результаты нормализации"
          message={normalizationError}
          confirmText="Продолжить"
          cancelText="Пропустить"
          onConfirm={() => {
            setShowErrorModal(false);
            // Если есть успешные страницы, запускаем LLM
            const successful = normalizedPages?.filter(img => img.normalized_url && !img.error) || [];
            if (successful.length > 0) {
              // Небольшая задержка для визуального обновления
              setTimeout(() => {
                handleAutoFill(successful);
              }, 300);
            } else {
              // Если нет успешных страниц, переходим к форме
              handleNext();
            }
          }}
          onCancel={() => {
            setShowErrorModal(false);
            // Переходим к форме без автозаполнения
            if (onNext) {
              onNext({ normalizedPages: [] });
            } else if (onSkip) {
              onSkip();
            }
          }}
          danger={false}
        />
      )}
    </div>
  );
};

export default UploadPagesStep;

