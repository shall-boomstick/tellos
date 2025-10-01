/**
 * Custom hook for managing keyboard shortcuts in the real-time video interface
 * Provides comprehensive keyboard navigation and control functionality
 */

import { useEffect, useCallback, useRef } from 'react';

/**
 * Keyboard shortcut configuration
 */
const DEFAULT_SHORTCUTS = {
  // Video playback controls
  ' ': 'togglePlayPause',           // Spacebar - Play/Pause
  'ArrowLeft': 'seekBackward',      // Left Arrow - Seek backward 10s
  'ArrowRight': 'seekForward',      // Right Arrow - Seek forward 10s
  'ArrowUp': 'volumeUp',            // Up Arrow - Volume up
  'ArrowDown': 'volumeDown',        // Down Arrow - Volume down
  'm': 'toggleMute',                // M - Toggle mute
  'f': 'toggleFullscreen',          // F - Toggle fullscreen
  '0': 'seekToStart',               // 0 - Seek to beginning
  'End': 'seekToEnd',               // End - Seek to end
  
  // Translation controls
  't': 'toggleTranslation',         // T - Toggle translation display
  'l': 'cycleLanguage',             // L - Cycle through languages
  'r': 'repeatTranslation',         // R - Repeat last translation
  
  // Emotion analysis controls
  'e': 'toggleEmotionAnalysis',     // E - Toggle emotion analysis
  'c': 'toggleEmotionChart',        // C - Toggle emotion chart
  
  // Interface controls
  'h': 'toggleHelp',                // H - Toggle help overlay
  's': 'toggleSettings',            // S - Toggle settings panel
  'u': 'uploadFile',                // U - Open file upload dialog
  'Escape': 'closeModals',          // Escape - Close all modals/overlays
  
  // Accessibility
  'Tab': 'focusNext',               // Tab - Focus next element
  'Shift+Tab': 'focusPrevious',     // Shift+Tab - Focus previous element
  'Enter': 'activateElement',       // Enter - Activate focused element
  
  // Debug/Development
  'd': 'toggleDebugMode',           // D - Toggle debug mode
  'i': 'showInfo',                  // I - Show video/processing info
};

/**
 * Modifier key combinations
 */
const MODIFIER_KEYS = {
  'Ctrl': 'ctrlKey',
  'Shift': 'shiftKey',
  'Alt': 'altKey',
  'Meta': 'metaKey' // Cmd on Mac, Windows key on Windows
};

/**
 * Parse keyboard shortcut string
 * @param {string} shortcut - Shortcut string (e.g., "Ctrl+Shift+S")
 * @returns {Object} Parsed shortcut object
 */
const parseShortcut = (shortcut) => {
  const parts = shortcut.split('+').map(part => part.trim());
  const modifiers = {};
  let key = parts[parts.length - 1];
  
  // Extract modifiers
  for (let i = 0; i < parts.length - 1; i++) {
    const modifier = parts[i];
    if (MODIFIER_KEYS[modifier]) {
      modifiers[MODIFIER_KEYS[modifier]] = true;
    }
  }
  
  return { key, modifiers };
};

/**
 * Check if modifier keys match
 * @param {Object} event - Keyboard event
 * @param {Object} modifiers - Required modifiers
 * @returns {boolean} True if modifiers match
 */
const checkModifiers = (event, modifiers) => {
  return Object.entries(modifiers).every(([key, value]) => {
    return event[key] === value;
  });
};

/**
 * Custom hook for keyboard shortcuts
 * @param {Object} shortcuts - Custom shortcuts object
 * @param {Object} handlers - Handler functions for shortcuts
 * @param {Object} options - Configuration options
 * @returns {Object} Hook utilities and state
 */
export const useKeyboardShortcuts = (shortcuts = {}, handlers = {}, options = {}) => {
  const {
    enabled = true,
    preventDefault = true,
    stopPropagation = false,
    target = null, // DOM element to attach listeners to, null = document
    debug = false
  } = options;

  const shortcutsRef = useRef({ ...DEFAULT_SHORTCUTS, ...shortcuts });
  const handlersRef = useRef(handlers);
  const activeShortcutsRef = useRef(new Set());
  const lastKeyPressRef = useRef(null);
  const keySequenceRef = useRef([]);
  const sequenceTimeoutRef = useRef(null);

  // Update refs when props change
  useEffect(() => {
    shortcutsRef.current = { ...DEFAULT_SHORTCUTS, ...shortcuts };
    handlersRef.current = handlers;
  }, [shortcuts, handlers]);

  /**
   * Handle key down events
   */
  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    const key = event.key;
    const code = event.code;
    
    if (debug) {
      console.log('Key pressed:', { key, code, modifiers: {
        ctrl: event.ctrlKey,
        shift: event.shiftKey,
        alt: event.altKey,
        meta: event.metaKey
      }});
    }

    // Handle key sequences (e.g., 'g' then 'g' for seek to start)
    if (keySequenceRef.current.length > 0) {
      keySequenceRef.current.push(key);
      
      // Clear previous timeout
      if (sequenceTimeoutRef.current) {
        clearTimeout(sequenceTimeoutRef.current);
      }
      
      // Set new timeout
      sequenceTimeoutRef.current = setTimeout(() => {
        keySequenceRef.current = [];
      }, 1000); // 1 second timeout for sequences
    } else {
      keySequenceRef.current = [key];
    }

    // Check for exact key matches first
    let matchedShortcut = null;
    let matchedAction = null;

    // Check single key shortcuts
    if (shortcutsRef.current[key]) {
      matchedShortcut = key;
      matchedAction = shortcutsRef.current[key];
    }

    // Check modifier key combinations
    if (!matchedShortcut) {
      for (const [shortcut, action] of Object.entries(shortcutsRef.current)) {
        if (shortcut.includes('+')) {
          const { key: shortcutKey, modifiers } = parseShortcut(shortcut);
          if (shortcutKey === key && checkModifiers(event, modifiers)) {
            matchedShortcut = shortcut;
            matchedAction = action;
            break;
          }
        }
      }
    }

    // Check key sequences
    if (!matchedShortcut) {
      const sequence = keySequenceRef.current.join('');
      if (shortcutsRef.current[sequence]) {
        matchedShortcut = sequence;
        matchedAction = shortcutsRef.current[sequence];
      }
    }

    if (matchedAction && handlersRef.current[matchedAction]) {
      // Prevent default behavior if specified
      if (preventDefault) {
        event.preventDefault();
      }
      
      // Stop propagation if specified
      if (stopPropagation) {
        event.stopPropagation();
      }

      // Track active shortcuts
      activeShortcutsRef.current.add(matchedAction);
      lastKeyPressRef.current = {
        key,
        action: matchedAction,
        timestamp: Date.now()
      };

      // Execute handler
      try {
        handlersRef.current[matchedAction](event, {
          key,
          code,
          modifiers: {
            ctrl: event.ctrlKey,
            shift: event.shiftKey,
            alt: event.altKey,
            meta: event.metaKey
          },
          sequence: keySequenceRef.current
        });
      } catch (error) {
        console.error(`Error executing keyboard shortcut handler for '${matchedAction}':`, error);
      }
    }
  }, [enabled, preventDefault, stopPropagation, debug]);

  /**
   * Handle key up events
   */
  const handleKeyUp = useCallback((event) => {
    if (!enabled) return;

    // Remove from active shortcuts
    const key = event.key;
    for (const [shortcut, action] of Object.entries(shortcutsRef.current)) {
      if (shortcut === key || (shortcut.includes('+') && parseShortcut(shortcut).key === key)) {
        activeShortcutsRef.current.delete(action);
      }
    }
  }, [enabled]);

  /**
   * Register event listeners
   */
  useEffect(() => {
    if (!enabled) return;

    const targetElement = target || document;
    
    targetElement.addEventListener('keydown', handleKeyDown);
    targetElement.addEventListener('keyup', handleKeyUp);

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown);
      targetElement.removeEventListener('keyup', handleKeyUp);
      
      // Clear timeouts
      if (sequenceTimeoutRef.current) {
        clearTimeout(sequenceTimeoutRef.current);
      }
    };
  }, [enabled, target, handleKeyDown, handleKeyUp]);

  /**
   * Get current active shortcuts
   */
  const getActiveShortcuts = useCallback(() => {
    return Array.from(activeShortcutsRef.current);
  }, []);

  /**
   * Get last key press info
   */
  const getLastKeyPress = useCallback(() => {
    return lastKeyPressRef.current;
  }, []);

  /**
   * Check if a specific shortcut is active
   */
  const isShortcutActive = useCallback((action) => {
    return activeShortcutsRef.current.has(action);
  }, []);

  /**
   * Add a new shortcut dynamically
   */
  const addShortcut = useCallback((shortcut, action, handler) => {
    shortcutsRef.current[shortcut] = action;
    if (handler) {
      handlersRef.current[action] = handler;
    }
  }, []);

  /**
   * Remove a shortcut
   */
  const removeShortcut = useCallback((shortcut) => {
    const action = shortcutsRef.current[shortcut];
    if (action) {
      delete shortcutsRef.current[shortcut];
      delete handlersRef.current[action];
    }
  }, []);

  /**
   * Update shortcut handler
   */
  const updateHandler = useCallback((action, handler) => {
    handlersRef.current[action] = handler;
  }, []);

  /**
   * Get all available shortcuts
   */
  const getShortcuts = useCallback(() => {
    return { ...shortcutsRef.current };
  }, []);

  /**
   * Clear all shortcuts
   */
  const clearShortcuts = useCallback(() => {
    shortcutsRef.current = {};
    handlersRef.current = {};
    activeShortcutsRef.current.clear();
  }, []);

  return {
    // State
    activeShortcuts: getActiveShortcuts(),
    lastKeyPress: getLastKeyPress(),
    
    // Methods
    isShortcutActive,
    addShortcut,
    removeShortcut,
    updateHandler,
    getShortcuts,
    clearShortcuts,
    
    // Utilities
    parseShortcut,
    checkModifiers
  };
};

/**
 * Predefined shortcut handlers for common video interface actions
 */
export const createVideoShortcutHandlers = (videoRef, translationRef, emotionRef, settingsRef) => {
  return {
    // Video playback
    togglePlayPause: (event) => {
      if (videoRef?.current) {
        if (videoRef.current.paused) {
          videoRef.current.play();
        } else {
          videoRef.current.pause();
        }
      }
    },
    
    seekBackward: (event) => {
      if (videoRef?.current) {
        videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 10);
      }
    },
    
    seekForward: (event) => {
      if (videoRef?.current) {
        videoRef.current.currentTime = Math.min(
          videoRef.current.duration || 0,
          videoRef.current.currentTime + 10
        );
      }
    },
    
    volumeUp: (event) => {
      if (videoRef?.current) {
        videoRef.current.volume = Math.min(1, videoRef.current.volume + 0.1);
      }
    },
    
    volumeDown: (event) => {
      if (videoRef?.current) {
        videoRef.current.volume = Math.max(0, videoRef.current.volume - 0.1);
      }
    },
    
    toggleMute: (event) => {
      if (videoRef?.current) {
        videoRef.current.muted = !videoRef.current.muted;
      }
    },
    
    toggleFullscreen: (event) => {
      if (videoRef?.current) {
        if (videoRef.current.requestFullscreen) {
          videoRef.current.requestFullscreen();
        }
      }
    },
    
    seekToStart: (event) => {
      if (videoRef?.current) {
        videoRef.current.currentTime = 0;
      }
    },
    
    seekToEnd: (event) => {
      if (videoRef?.current) {
        videoRef.current.currentTime = videoRef.current.duration || 0;
      }
    },
    
    // Translation controls
    toggleTranslation: (event) => {
      if (translationRef?.current) {
        translationRef.current.toggleVisibility();
      }
    },
    
    cycleLanguage: (event) => {
      if (translationRef?.current) {
        translationRef.current.cycleLanguage();
      }
    },
    
    repeatTranslation: (event) => {
      if (translationRef?.current) {
        translationRef.current.repeatLast();
      }
    },
    
    // Emotion analysis
    toggleEmotionAnalysis: (event) => {
      if (emotionRef?.current) {
        emotionRef.current.toggleAnalysis();
      }
    },
    
    toggleEmotionChart: (event) => {
      if (emotionRef?.current) {
        emotionRef.current.toggleChart();
      }
    },
    
    // Interface controls
    toggleHelp: (event) => {
      // Implementation depends on your help system
      console.log('Toggle help overlay');
    },
    
    toggleSettings: (event) => {
      if (settingsRef?.current) {
        settingsRef.current.toggle();
      }
    },
    
    uploadFile: (event) => {
      // Trigger file upload dialog
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'video/*';
      input.click();
    },
    
    closeModals: (event) => {
      // Close all modals and overlays
      document.querySelectorAll('.modal, .overlay').forEach(el => {
        el.style.display = 'none';
      });
    },
    
    // Debug
    toggleDebugMode: (event) => {
      console.log('Toggle debug mode');
    },
    
    showInfo: (event) => {
      if (videoRef?.current) {
        console.log('Video info:', {
          currentTime: videoRef.current.currentTime,
          duration: videoRef.current.duration,
          volume: videoRef.current.volume,
          muted: videoRef.current.muted,
          paused: videoRef.current.paused
        });
      }
    }
  };
};

export default useKeyboardShortcuts;

