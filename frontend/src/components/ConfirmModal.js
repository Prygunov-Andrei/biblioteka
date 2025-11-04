import './ConfirmModal.css';

const ConfirmModal = ({ isOpen, title, message, confirmText = 'Подтвердить', cancelText = 'Отмена', onConfirm, onCancel, danger = false }) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div 
      className="confirm-modal-overlay" 
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-modal-header">
          <h2>{title}</h2>
          <button className="confirm-modal-close" onClick={onCancel}>×</button>
        </div>
        
        <div className="confirm-modal-body">
          <p>{message}</p>
        </div>
        
        <div className="confirm-modal-footer">
          {cancelText && (
            <button 
              className="confirm-modal-button confirm-modal-button-cancel" 
              onClick={onCancel}
            >
              {cancelText}
            </button>
          )}
          <button 
            className={`confirm-modal-button confirm-modal-button-confirm ${danger ? 'confirm-modal-button-danger' : ''}`}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;

