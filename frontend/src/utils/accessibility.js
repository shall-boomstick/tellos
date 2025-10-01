/**
 * Accessibility utilities for real-time video interface
 * Provides comprehensive accessibility features and utilities
 */

/**
 * ARIA (Accessible Rich Internet Applications) utilities
 */
export const ARIA = {
  /**
   * Set ARIA label for an element
   * @param {HTMLElement} element - Target element
   * @param {string} label - ARIA label text
   */
  setLabel: (element, label) => {
    if (element) {
      element.setAttribute('aria-label', label);
    }
  },

  /**
   * Set ARIA described by reference
   * @param {HTMLElement} element - Target element
   * @param {string} describedBy - ID of describing element
   */
  setDescribedBy: (element, describedBy) => {
    if (element) {
      element.setAttribute('aria-describedby', describedBy);
    }
  },

  /**
   * Set ARIA expanded state
   * @param {HTMLElement} element - Target element
   * @param {boolean} expanded - Expanded state
   */
  setExpanded: (element, expanded) => {
    if (element) {
      element.setAttribute('aria-expanded', expanded.toString());
    }
  },

  /**
   * Set ARIA hidden state
   * @param {HTMLElement} element - Target element
   * @param {boolean} hidden - Hidden state
   */
  setHidden: (element, hidden) => {
    if (element) {
      element.setAttribute('aria-hidden', hidden.toString());
    }
  },

  /**
   * Set ARIA live region for announcements
   * @param {HTMLElement} element - Target element
   * @param {string} politeness - Politeness level ('polite', 'assertive', 'off')
   */
  setLiveRegion: (element, politeness = 'polite') => {
    if (element) {
      element.setAttribute('aria-live', politeness);
    }
  },

  /**
   * Set ARIA current state
   * @param {HTMLElement} element - Target element
   * @param {string|boolean} current - Current state
   */
  setCurrent: (element, current) => {
    if (element) {
      element.setAttribute('aria-current', current.toString());
    }
  },

  /**
   * Set ARIA controls reference
   * @param {HTMLElement} element - Target element
   * @param {string} controls - ID of controlled element
   */
  setControls: (element, controls) => {
    if (element) {
      element.setAttribute('aria-controls', controls);
    }
  },

  /**
   * Set ARIA owns reference
   * @param {HTMLElement} element - Target element
   * @param {string} owns - ID of owned element
   */
  setOwns: (element, owns) => {
    if (element) {
      element.setAttribute('aria-owns', owns);
    }
  }
};

/**
 * Focus management utilities
 */
export const FocusManager = {
  /**
   * Trap focus within a container
   * @param {HTMLElement} container - Container element
   * @param {HTMLElement} firstFocusable - First focusable element
   * @param {HTMLElement} lastFocusable - Last focusable element
   */
  trapFocus: (container, firstFocusable, lastFocusable) => {
    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  },

  /**
   * Get all focusable elements within a container
   * @param {HTMLElement} container - Container element
   * @returns {Array<HTMLElement>} Array of focusable elements
   */
  getFocusableElements: (container) => {
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      'area[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(container.querySelectorAll(focusableSelectors))
      .filter(el => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
      });
  },

  /**
   * Focus first focusable element in container
   * @param {HTMLElement} container - Container element
   */
  focusFirst: (container) => {
    const focusableElements = FocusManager.getFocusableElements(container);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  },

  /**
   * Focus last focusable element in container
   * @param {HTMLElement} container - Container element
   */
  focusLast: (container) => {
    const focusableElements = FocusManager.getFocusableElements(container);
    if (focusableElements.length > 0) {
      focusableElements[focusableElements.length - 1].focus();
    }
  },

  /**
   * Store and restore focus
   */
  focusStack: [],
  
  /**
   * Store current focus
   */
  storeFocus: () => {
    FocusManager.focusStack.push(document.activeElement);
  },

  /**
   * Restore previous focus
   */
  restoreFocus: () => {
    const previousFocus = FocusManager.focusStack.pop();
    if (previousFocus && typeof previousFocus.focus === 'function') {
      previousFocus.focus();
    }
  }
};

/**
 * Screen reader utilities
 */
export const ScreenReader = {
  /**
   * Announce text to screen readers
   * @param {string} text - Text to announce
   * @param {string} politeness - Politeness level
   */
  announce: (text, politeness = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', politeness);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = text;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  },

  /**
   * Create live region for dynamic content
   * @param {string} id - Unique ID for the region
   * @param {string} politeness - Politeness level
   * @returns {HTMLElement} Live region element
   */
  createLiveRegion: (id, politeness = 'polite') => {
    const liveRegion = document.createElement('div');
    liveRegion.id = id;
    liveRegion.setAttribute('aria-live', politeness);
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    document.body.appendChild(liveRegion);
    return liveRegion;
  },

  /**
   * Update live region content
   * @param {string} id - Live region ID
   * @param {string} content - New content
   */
  updateLiveRegion: (id, content) => {
    const liveRegion = document.getElementById(id);
    if (liveRegion) {
      liveRegion.textContent = content;
    }
  }
};

/**
 * Color contrast utilities
 */
export const ColorContrast = {
  /**
   * Calculate relative luminance of a color
   * @param {number} r - Red component (0-255)
   * @param {number} g - Green component (0-255)
   * @param {number} b - Blue component (0-255)
   * @returns {number} Relative luminance
   */
  getLuminance: (r, g, b) => {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  },

  /**
   * Calculate contrast ratio between two colors
   * @param {string} color1 - First color (hex, rgb, or hsl)
   * @param {string} color2 - Second color (hex, rgb, or hsl)
   * @returns {number} Contrast ratio
   */
  getContrastRatio: (color1, color2) => {
    const rgb1 = ColorContrast.hexToRgb(color1);
    const rgb2 = ColorContrast.hexToRgb(color2);
    
    if (!rgb1 || !rgb2) return 0;
    
    const lum1 = ColorContrast.getLuminance(rgb1.r, rgb1.g, rgb1.b);
    const lum2 = ColorContrast.getLuminance(rgb2.r, rgb2.g, rgb2.b);
    
    const brightest = Math.max(lum1, lum2);
    const darkest = Math.min(lum1, lum2);
    
    return (brightest + 0.05) / (darkest + 0.05);
  },

  /**
   * Convert hex color to RGB
   * @param {string} hex - Hex color string
   * @returns {Object|null} RGB object or null if invalid
   */
  hexToRgb: (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  },

  /**
   * Check if contrast meets WCAG standards
   * @param {string} foreground - Foreground color
   * @param {string} background - Background color
   * @param {string} level - WCAG level ('AA' or 'AAA')
   * @param {string} size - Text size ('normal' or 'large')
   * @returns {Object} Contrast check result
   */
  checkContrast: (foreground, background, level = 'AA', size = 'normal') => {
    const ratio = ColorContrast.getContrastRatio(foreground, background);
    
    const requirements = {
      'AA': { normal: 4.5, large: 3 },
      'AAA': { normal: 7, large: 4.5 }
    };
    
    const required = requirements[level][size];
    const passes = ratio >= required;
    
    return {
      ratio: Math.round(ratio * 100) / 100,
      required,
      passes,
      level: passes ? level : 'Fail'
    };
  }
};

/**
 * Keyboard navigation utilities
 */
export const KeyboardNavigation = {
  /**
   * Handle arrow key navigation in a grid
   * @param {KeyboardEvent} event - Keyboard event
   * @param {HTMLElement} container - Container element
   * @param {number} columns - Number of columns
   */
  handleGridNavigation: (event, container, columns) => {
    const currentElement = document.activeElement;
    const focusableElements = FocusManager.getFocusableElements(container);
    const currentIndex = focusableElements.indexOf(currentElement);
    
    if (currentIndex === -1) return;
    
    let newIndex = currentIndex;
    
    switch (event.key) {
      case 'ArrowUp':
        newIndex = Math.max(0, currentIndex - columns);
        break;
      case 'ArrowDown':
        newIndex = Math.min(focusableElements.length - 1, currentIndex + columns);
        break;
      case 'ArrowLeft':
        newIndex = Math.max(0, currentIndex - 1);
        break;
      case 'ArrowRight':
        newIndex = Math.min(focusableElements.length - 1, currentIndex + 1);
        break;
      case 'Home':
        newIndex = 0;
        break;
      case 'End':
        newIndex = focusableElements.length - 1;
        break;
      default:
        return;
    }
    
    if (newIndex !== currentIndex) {
      event.preventDefault();
      focusableElements[newIndex].focus();
    }
  },

  /**
   * Handle roving tabindex for radio groups
   * @param {HTMLElement} container - Container element
   * @param {string} groupName - Group name
   */
  setupRovingTabindex: (container, groupName) => {
    const radioButtons = container.querySelectorAll(`input[type="radio"][name="${groupName}"]`);
    let currentIndex = 0;
    
    // Set initial tabindex
    radioButtons.forEach((radio, index) => {
      radio.setAttribute('tabindex', index === 0 ? '0' : '-1');
    });
    
    // Handle focus events
    radioButtons.forEach((radio, index) => {
      radio.addEventListener('focus', () => {
        // Update tabindex
        radioButtons.forEach((r, i) => {
          r.setAttribute('tabindex', i === index ? '0' : '-1');
        });
        currentIndex = index;
      });
      
      // Handle arrow key navigation
      radio.addEventListener('keydown', (e) => {
        let newIndex = currentIndex;
        
        switch (e.key) {
          case 'ArrowUp':
          case 'ArrowLeft':
            newIndex = Math.max(0, currentIndex - 1);
            break;
          case 'ArrowDown':
          case 'ArrowRight':
            newIndex = Math.min(radioButtons.length - 1, currentIndex + 1);
            break;
          default:
            return;
        }
        
        if (newIndex !== currentIndex) {
          e.preventDefault();
          radioButtons[newIndex].focus();
          radioButtons[newIndex].checked = true;
        }
      });
    });
  }
};

/**
 * Video accessibility utilities
 */
export const VideoAccessibility = {
  /**
   * Add captions to video element
   * @param {HTMLVideoElement} video - Video element
   * @param {Array} captions - Array of caption objects
   */
  addCaptions: (video, captions) => {
    const track = document.createElement('track');
    track.kind = 'captions';
    track.label = 'English Captions';
    track.srclang = 'en';
    track.default = true;
    
    // Create VTT content
    const vttContent = VideoAccessibility.createVTTContent(captions);
    const blob = new Blob([vttContent], { type: 'text/vtt' });
    track.src = URL.createObjectURL(blob);
    
    video.appendChild(track);
    video.textTracks[0].mode = 'showing';
  },

  /**
   * Create VTT content from captions
   * @param {Array} captions - Array of caption objects
   * @returns {string} VTT content
   */
  createVTTContent: (captions) => {
    let vtt = 'WEBVTT\n\n';
    
    captions.forEach(caption => {
      const start = VideoAccessibility.formatTime(caption.start);
      const end = VideoAccessibility.formatTime(caption.end);
      vtt += `${start} --> ${end}\n${caption.text}\n\n`;
    });
    
    return vtt;
  },

  /**
   * Format time for VTT
   * @param {number} seconds - Time in seconds
   * @returns {string} Formatted time string
   */
  formatTime: (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  },

  /**
   * Announce video state changes
   * @param {HTMLVideoElement} video - Video element
   */
  announceVideoState: (video) => {
    const state = video.paused ? 'paused' : 'playing';
    const time = Math.floor(video.currentTime);
    const duration = Math.floor(video.duration);
    
    ScreenReader.announce(`Video ${state} at ${time} seconds of ${duration} seconds`);
  },

  /**
   * Create accessible video controls
   * @param {HTMLVideoElement} video - Video element
   * @returns {HTMLElement} Controls container
   */
  createAccessibleControls: (video) => {
    const controls = document.createElement('div');
    controls.className = 'video-controls';
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Video controls');
    
    // Play/Pause button
    const playButton = document.createElement('button');
    playButton.setAttribute('aria-label', 'Play video');
    playButton.innerHTML = '▶';
    
    playButton.addEventListener('click', () => {
      if (video.paused) {
        video.play();
        playButton.innerHTML = '⏸';
        playButton.setAttribute('aria-label', 'Pause video');
      } else {
        video.pause();
        playButton.innerHTML = '▶';
        playButton.setAttribute('aria-label', 'Play video');
      }
    });
    
    // Volume control
    const volumeSlider = document.createElement('input');
    volumeSlider.type = 'range';
    volumeSlider.min = '0';
    volumeSlider.max = '1';
    volumeSlider.step = '0.1';
    volumeSlider.setAttribute('aria-label', 'Volume control');
    volumeSlider.value = video.volume;
    
    volumeSlider.addEventListener('input', (e) => {
      video.volume = parseFloat(e.target.value);
    });
    
    // Time display
    const timeDisplay = document.createElement('span');
    timeDisplay.setAttribute('aria-live', 'polite');
    timeDisplay.className = 'time-display';
    
    const updateTimeDisplay = () => {
      const current = Math.floor(video.currentTime);
      const duration = Math.floor(video.duration);
      timeDisplay.textContent = `${current} / ${duration}`;
    };
    
    video.addEventListener('timeupdate', updateTimeDisplay);
    
    controls.appendChild(playButton);
    controls.appendChild(volumeSlider);
    controls.appendChild(timeDisplay);
    
    return controls;
  }
};

/**
 * High contrast mode detection
 */
export const HighContrast = {
  /**
   * Check if high contrast mode is enabled
   * @returns {boolean} True if high contrast mode is enabled
   */
  isEnabled: () => {
    // Check for Windows High Contrast mode
    if (window.matchMedia) {
      return window.matchMedia('(-ms-high-contrast: active)').matches ||
             window.matchMedia('(-ms-high-contrast: black-on-white)').matches ||
             window.matchMedia('(-ms-high-contrast: white-on-black)').matches;
    }
    return false;
  },

  /**
   * Apply high contrast styles
   * @param {HTMLElement} element - Target element
   */
  applyHighContrastStyles: (element) => {
    if (HighContrast.isEnabled()) {
      element.classList.add('high-contrast');
    }
  }
};

/**
 * Reduced motion detection
 */
export const ReducedMotion = {
  /**
   * Check if reduced motion is preferred
   * @returns {boolean} True if reduced motion is preferred
   */
  isPreferred: () => {
    if (window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  },

  /**
   * Apply reduced motion styles
   * @param {HTMLElement} element - Target element
   */
  applyReducedMotionStyles: (element) => {
    if (ReducedMotion.isPreferred()) {
      element.classList.add('reduced-motion');
    }
  }
};

/**
 * Screen reader only text utility
 */
export const ScreenReaderOnly = {
  /**
   * Create screen reader only text element
   * @param {string} text - Text content
   * @returns {HTMLElement} Screen reader only element
   */
  create: (text) => {
    const element = document.createElement('span');
    element.className = 'sr-only';
    element.textContent = text;
    return element;
  },

  /**
   * Add screen reader only text to element
   * @param {HTMLElement} element - Target element
   * @param {string} text - Text content
   */
  add: (element, text) => {
    const srText = ScreenReaderOnly.create(text);
    element.appendChild(srText);
  }
};

// CSS for screen reader only class
const srOnlyCSS = `
.sr-only {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
`;

// Inject CSS if not already present
if (!document.querySelector('#sr-only-styles')) {
  const style = document.createElement('style');
  style.id = 'sr-only-styles';
  style.textContent = srOnlyCSS;
  document.head.appendChild(style);
}

