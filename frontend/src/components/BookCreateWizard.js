import { useState } from 'react';
import UploadPagesStep from './UploadPagesStep';
import NormalizationStep from './NormalizationStep';
import AutoFillStep from './AutoFillStep';
import BookFormStep from './BookFormStep';
import ConfirmModal from './ConfirmModal';
import './BookCreateWizard.css';

const BookCreateWizard = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardData, setWizardData] = useState({
    pages: [], // Массив File объектов для загруженных страниц
    normalizedPages: [], // Массив нормализованных страниц (после шага 2)
    autoFillData: null, // Данные от LLM (после шага 3)
    formData: {}, // Данные формы (после шага 4)
  });
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleCancelClick();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancelClick();
    }
  };

  const handleCancelClick = () => {
    // Проверяем, есть ли незавершенные изменения
    const hasChanges = wizardData.pages.length > 0 || 
                       wizardData.normalizedPages.length > 0 ||
                       wizardData.autoFillData !== null ||
                       Object.keys(wizardData.formData).length > 0;
    
    if (hasChanges) {
      setShowCancelConfirm(true);
    } else {
      handleClose();
    }
  };

  const handleConfirmCancel = () => {
    setShowCancelConfirm(false);
    handleClose();
  };

  const handleCancelConfirmCancel = () => {
    setShowCancelConfirm(false);
  };

  const handleClose = () => {
    // Сбрасываем состояние
    setCurrentStep(1);
    setWizardData({
      pages: [],
      normalizedPages: [],
      autoFillData: null,
      formData: {},
    });
    if (onClose) {
      onClose();
    }
  };

  const handleNext = (stepData) => {
    // Обновляем данные мастера
    if (stepData) {
      setWizardData(prev => {
        const updatedData = { ...prev, ...stepData };
        
        // Определяем следующий шаг на основе обновленных данных
        let nextStep = currentStep + 1;

        // Если на шаге 1 и нет файлов, пропускаем шаги 2 и 3, переходим к шагу 4
        if (currentStep === 1 && (!updatedData.pages || updatedData.pages.length === 0)) {
          nextStep = 4;
        }
        // Если на шаге 1 и есть файлы, переходим к шагу 2
        else if (currentStep === 1) {
          nextStep = 2;
        }
        // Если на шаге 2 и пропустили нормализацию, переходим к шагу 4
        else if (currentStep === 2 && (!updatedData.normalizedPages || updatedData.normalizedPages.length === 0)) {
          nextStep = 4;
        }
        // Если на шаге 2 и есть нормализованные страницы, переходим к шагу 3
        else if (currentStep === 2) {
          nextStep = 3;
        }
        // Если на шаге 3 и пропустили автозаполнение, переходим к шагу 4
        else if (currentStep === 3 && !updatedData.autoFillData) {
          nextStep = 4;
        }

        // Переходим на следующий шаг после обновления состояния
        setTimeout(() => setCurrentStep(nextStep), 0);

        return updatedData;
      });
    } else {
      // Если нет данных для обновления, просто переходим на следующий шаг
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = () => {
    // Определяем следующий шаг при пропуске
    let nextStep = currentStep + 1;

    // Логика пропуска:
    if (currentStep === 1) { // Пропуск загрузки страниц
      nextStep = 4; // Переходим сразу к заполнению данных
    } else if (currentStep === 2) { // Пропуск нормализации
      // Если нет нормализованных страниц, пропускаем шаг 3 (автозаполнение)
      if (!wizardData.normalizedPages || wizardData.normalizedPages.length === 0) {
        nextStep = 4; // Переходим сразу к заполнению данных
      } else {
        nextStep = 3; // Переходим к автозаполнению
      }
      setWizardData(prev => ({ ...prev, normalizedPages: [] })); // Очищаем нормализованные страницы
    } else if (currentStep === 3) { // Пропуск автозаполнения
      nextStep = 4; // Переходим к заполнению данных
      setWizardData(prev => ({ ...prev, autoFillData: null })); // Очищаем автозаполненные данные
    }

    setCurrentStep(nextStep);
  };

  const handleBack = () => {
    let prevStep = currentStep - 1;

    // Логика возврата:
    if (currentStep === 4) {
      // Определяем, откуда мы пришли на шаг 4
      if (!wizardData.pages || wizardData.pages.length === 0) {
        prevStep = 1; // Если пришли на шаг 4 без страниц, возвращаемся к шагу 1
      } else if (!wizardData.normalizedPages || wizardData.normalizedPages.length === 0) {
        prevStep = 2; // Если пришли на шаг 4 без нормализованных страниц, возвращаемся к шагу 2
      } else if (!wizardData.autoFillData) {
        prevStep = 3; // Если пришли на шаг 4 без автозаполнения, возвращаемся к шагу 3
      } else {
        prevStep = 3; // Если есть автозаполнение, возвращаемся к шагу 3
      }
    } else if (currentStep === 3) {
      // С шага 3 возвращаемся к шагу 2 (нормализация)
      prevStep = 2;
    } else if (currentStep === 2) {
      // С шага 2 возвращаемся к шагу 1 (загрузка страниц)
      prevStep = 1;
    }

    setCurrentStep(prevStep);
  };

  const handleStepDataUpdate = (stepData) => {
    setWizardData(prev => ({ ...prev, ...stepData }));
  };

  const getStepTitle = () => {
    switch (currentStep) {
      case 1:
        return 'Шаг 1: Загрузка страниц';
      case 2:
        return 'Шаг 2: Нормализация страниц';
      case 3:
        return 'Шаг 3: Автозаполнение данных';
      case 4:
        return 'Шаг 4: Заполнение данных';
      case 5:
        return 'Шаг 5: Подтверждение';
      default:
        return 'Создание книги';
    }
  };

  return (
    <div 
      className="book-create-wizard-overlay" 
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="book-create-wizard" onClick={(e) => e.stopPropagation()}>
        <div className="book-create-wizard-header">
          <h2>{getStepTitle()}</h2>
          <button 
            className="book-create-wizard-close" 
            onClick={handleCancelClick}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>

        <div className="book-create-wizard-progress">
          <div className="wizard-steps">
            {[1, 2, 3, 4, 5].map((step) => (
              <div 
                key={step}
                className={`wizard-step ${step === currentStep ? 'active' : ''} ${step < currentStep ? 'completed' : ''}`}
              >
                <div className="wizard-step-number">{step}</div>
                <div className="wizard-step-label">
                  {step === 1 && 'Загрузка'}
                  {step === 2 && 'Нормализация'}
                  {step === 3 && 'Автозаполнение'}
                  {step === 4 && 'Данные'}
                  {step === 5 && 'Подтверждение'}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="book-create-wizard-body">
          {currentStep === 1 && (
            <UploadPagesStep
              files={wizardData.pages}
              onFilesChange={(files) => handleStepDataUpdate({ pages: files })}
              onNext={handleNext}
              onSkip={handleSkip}
              onBack={currentStep > 1 ? handleBack : null}
            />
          )}
          {currentStep === 2 && (
            <NormalizationStep
              files={wizardData.pages}
              normalizedPages={wizardData.normalizedPages}
              onNormalizedPagesChange={(normalizedPages) => handleStepDataUpdate({ normalizedPages })}
              onNext={handleNext}
              onSkip={handleSkip}
              onBack={currentStep > 1 ? handleBack : null}
            />
          )}
                 {currentStep === 3 && (
                   <AutoFillStep
                     normalizedPages={wizardData.normalizedPages}
                     onAutoFillData={(autoFillData) => handleStepDataUpdate({ autoFillData })}
                     onNext={handleNext}
                     onSkip={handleSkip}
                     onBack={currentStep > 1 ? handleBack : null}
                   />
                 )}
          {currentStep === 4 && (
            <BookFormStep
              autoFillData={wizardData.autoFillData}
              onFormDataChange={(formData) => handleStepDataUpdate({ formData })}
              onNext={handleNext}
              onBack={currentStep > 1 ? handleBack : null}
            />
          )}
          {currentStep === 5 && (
            <div className="wizard-step-placeholder">
              <p>Шаг 5: Подтверждение (будет реализован в следующем этапе)</p>
            </div>
          )}
        </div>

        {/* Модальное окно подтверждения отмены */}
        {showCancelConfirm && (
          <ConfirmModal
            isOpen={true}
            title="Отменить создание книги?"
            message="У вас есть незавершенные изменения. Вы уверены, что хотите закрыть мастер создания книги? Все несохраненные данные будут потеряны."
            confirmText="Да, отменить"
            cancelText="Продолжить"
            danger={true}
            onConfirm={handleConfirmCancel}
            onCancel={handleCancelConfirmCancel}
          />
        )}
      </div>
    </div>
  );
};

export default BookCreateWizard;

