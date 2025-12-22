import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for registering keyboard shortcuts.
 *
 * @param {Object} shortcuts - Map of shortcut keys to handlers
 *   Format: { 'ctrl+k': handler, 'ctrl+n': handler, ... }
 * @param {Object} options - Options for the hook
 *   - enabled: Whether shortcuts are active (default: true)
 *   - preventDefault: Whether to prevent default action (default: true)
 */
export function useKeyboardShortcuts(shortcuts, options = {}) {
  const { enabled = true, preventDefault = true } = options;

  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    // Build the shortcut key string
    const parts = [];
    if (event.ctrlKey || event.metaKey) parts.push('ctrl');
    if (event.altKey) parts.push('alt');
    if (event.shiftKey) parts.push('shift');
    parts.push(event.key.toLowerCase());

    const shortcutKey = parts.join('+');

    // Check if we have a handler for this shortcut
    const handler = shortcuts[shortcutKey];
    if (handler) {
      if (preventDefault) {
        event.preventDefault();
      }
      handler(event);
    }
  }, [shortcuts, enabled, preventDefault]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Custom hook for debouncing a value.
 *
 * @param {any} value - The value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {any} The debounced value
 */
export function useDebouncedValue(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
