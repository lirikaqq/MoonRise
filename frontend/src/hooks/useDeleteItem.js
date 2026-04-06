import { useState, useCallback } from 'react';

export const useDeleteItem = (onSuccess) => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    item: null,
    isLoading: false,
    error: null,
  });

  const openDeleteModal = useCallback((item) => {
    setModalState({ isOpen: true, item, isLoading: false, error: null });
  }, []);

  const closeDeleteModal = useCallback(() => {
    if (modalState.isLoading) return;
    setModalState({ isOpen: false, item: null, isLoading: false, error: null });
  }, [modalState.isLoading]);

  const confirmDelete = useCallback(async (deleteFn) => {
    if (!modalState.item) return;

    setModalState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      await deleteFn(modalState.item.id);
      setModalState({ isOpen: false, item: null, isLoading: false, error: null });
      if (onSuccess) {
        onSuccess(modalState.item.id);
      }
    } catch (err) {
      console.error("Delete error:", err);
      const errorMessage = err.response?.data?.detail || "Произошла ошибка при удалении.";
      setModalState(prev => ({ ...prev, isLoading: false, error: errorMessage }));
    }
  }, [modalState.item, onSuccess]);

  return {
    modalState,
    openDeleteModal,
    closeDeleteModal,
    confirmDelete,
  };
};