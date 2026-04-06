import { useEffect } from 'react';
import './ConfirmModal.css';

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmText = "Удалить",
  cancelText = "Отмена",
  isLoading,
  error,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onCancel();
    };
    if (isOpen) document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onCancel]);

  useEffect(() => {
    if (isOpen) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => (document.body.style.overflow = "");
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="cm-overlay" onClick={onCancel}>
      <div className="cm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="cm-modal__icon">⚠️</div>
        <h2 className="cm-modal__title">{title}</h2>
        <p className="cm-modal__message">{message}</p>
        
        {error && <div className="cm-modal__error">{error}</div>}

        <div className="cm-modal__actions">
          <button 
            className="cm-modal__btn cm-modal__btn--cancel" 
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelText}
          </button>
          <button
            className="cm-modal__btn cm-modal__btn--danger"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Удаление..." : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}