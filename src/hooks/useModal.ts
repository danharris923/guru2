/**
 * Custom hook for modal state management.
 * Handles opening, closing, and keyboard interactions for modals.
 */

import { useState, useEffect, useCallback } from 'react';

interface UseModalOptions {
  closeOnEscape?: boolean;
  closeOnBackdropClick?: boolean;
  preventBodyScroll?: boolean;
}

export function useModal(options: UseModalOptions = {}) {
  const {
    closeOnEscape = true,
    closeOnBackdropClick = true,
    preventBodyScroll = true,
  } = options;

  const [isOpen, setIsOpen] = useState(false);

  // Open modal
  const openModal = useCallback(() => {
    setIsOpen(true);
  }, []);

  // Close modal
  const closeModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  // Toggle modal
  const toggleModal = useCallback(() => {
    setIsOpen(prev => !prev);
  }, []);

  // Handle keyboard events
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeModal();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeOnEscape, closeModal]);

  // Handle body scroll prevention
  useEffect(() => {
    if (!preventBodyScroll) return;

    if (isOpen) {
      // Save original body style
      const originalStyle = window.getComputedStyle(document.body).overflow;
      
      // Prevent scrolling
      document.body.style.overflow = 'hidden';
      
      // Cleanup
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen, preventBodyScroll]);

  // Backdrop click handler factory
  const createBackdropClickHandler = useCallback((callback?: () => void) => {
    return (event: React.MouseEvent<HTMLDivElement>) => {
      if (event.target === event.currentTarget) {
        if (closeOnBackdropClick) {
          closeModal();
        }
        callback?.();
      }
    };
  }, [closeOnBackdropClick, closeModal]);

  return {
    isOpen,
    openModal,
    closeModal,
    toggleModal,
    createBackdropClickHandler,
  };
}

/**
 * Hook for managing multiple modals with stack support
 */
export function useModalStack() {
  const [modalStack, setModalStack] = useState<string[]>([]);

  const openModal = useCallback((modalId: string) => {
    setModalStack(prev => {
      if (prev.includes(modalId)) {
        // If modal is already in stack, move it to top
        return [...prev.filter(id => id !== modalId), modalId];
      }
      return [...prev, modalId];
    });
  }, []);

  const closeModal = useCallback((modalId?: string) => {
    setModalStack(prev => {
      if (modalId) {
        // Close specific modal
        return prev.filter(id => id !== modalId);
      } else {
        // Close topmost modal
        return prev.slice(0, -1);
      }
    });
  }, []);

  const closeAllModals = useCallback(() => {
    setModalStack([]);
  }, []);

  const isModalOpen = useCallback((modalId: string) => {
    return modalStack.includes(modalId);
  }, [modalStack]);

  const getTopModal = useCallback(() => {
    return modalStack[modalStack.length - 1] || null;
  }, [modalStack]);

  const getModalZIndex = useCallback((modalId: string) => {
    const index = modalStack.indexOf(modalId);
    return index >= 0 ? 1000 + index : -1;
  }, [modalStack]);

  // Handle escape key for modal stack
  useEffect(() => {
    if (modalStack.length === 0) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeModal(); // Close topmost modal
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [modalStack.length, closeModal]);

  // Body scroll prevention for modal stack
  useEffect(() => {
    if (modalStack.length > 0) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';
      
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [modalStack.length]);

  return {
    modalStack,
    openModal,
    closeModal,
    closeAllModals,
    isModalOpen,
    getTopModal,
    getModalZIndex,
    hasOpenModals: modalStack.length > 0,
  };
}