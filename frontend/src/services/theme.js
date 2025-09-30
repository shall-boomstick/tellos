/**
 * Theme service for SawtFeel application
 * Handles dark/light theme switching and persistence
 */

const THEME_STORAGE_KEY = 'sawtfeel-theme'
const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
}

class ThemeService {
  constructor() {
    this.currentTheme = this.getStoredTheme() || this.getSystemTheme()
    this.listeners = new Set()
    this.init()
  }

  /**
   * Initialize theme service
   */
  init() {
    // Apply initial theme
    this.applyTheme(this.currentTheme)
    
    // Listen for system theme changes
    this.setupSystemThemeListener()
    
    // Listen for storage changes (for multi-tab sync)
    this.setupStorageListener()
  }

  /**
   * Get current theme
   * @returns {string} Current theme
   */
  getTheme() {
    return this.currentTheme
  }

  /**
   * Set theme
   * @param {string} theme - Theme to set
   */
  setTheme(theme) {
    if (!Object.values(THEMES).includes(theme)) {
      console.warn(`Invalid theme: ${theme}`)
      return
    }

    if (theme === this.currentTheme) {
      return // No change needed
    }

    this.currentTheme = theme
    this.applyTheme(theme)
    this.storeTheme(theme)
    this.notifyListeners(theme)
  }

  /**
   * Toggle between light and dark themes
   * @returns {string} New theme
   */
  toggleTheme() {
    const newTheme = this.currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT
    this.setTheme(newTheme)
    return newTheme
  }

  /**
   * Check if current theme is dark
   * @returns {boolean} True if dark theme
   */
  isDark() {
    return this.currentTheme === THEMES.DARK
  }

  /**
   * Check if current theme is light
   * @returns {boolean} True if light theme
   */
  isLight() {
    return this.currentTheme === THEMES.LIGHT
  }

  /**
   * Apply theme to DOM
   * @param {string} theme - Theme to apply
   */
  applyTheme(theme) {
    // Remove existing theme classes
    document.body.classList.remove(THEMES.LIGHT, THEMES.DARK)
    
    // Add new theme class
    document.body.classList.add(theme)
    
    // Update CSS custom properties
    this.updateCSSProperties(theme)
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(theme)
  }

  /**
   * Update CSS custom properties based on theme
   * @param {string} theme - Current theme
   */
  updateCSSProperties(theme) {
    const root = document.documentElement
    
    if (theme === THEMES.DARK) {
      // Import dark theme styles
      this.loadThemeStylesheet('dark')
      root.style.setProperty('--theme-transition', 'all 0.3s ease')
    } else {
      // Remove dark theme styles
      this.removeThemeStylesheet('dark')
      root.style.setProperty('--theme-transition', 'all 0.3s ease')
    }
  }

  /**
   * Load theme-specific stylesheet
   * @param {string} theme - Theme name
   */
  loadThemeStylesheet(theme) {
    const existingLink = document.getElementById(`theme-${theme}`)
    if (existingLink) {
      return // Already loaded
    }

    const link = document.createElement('link')
    link.id = `theme-${theme}`
    link.rel = 'stylesheet'
    link.href = `/src/styles/${theme}.css`
    document.head.appendChild(link)
  }

  /**
   * Remove theme-specific stylesheet
   * @param {string} theme - Theme name
   */
  removeThemeStylesheet(theme) {
    const link = document.getElementById(`theme-${theme}`)
    if (link) {
      link.remove()
    }
  }

  /**
   * Update meta theme-color for mobile browsers
   * @param {string} theme - Current theme
   */
  updateMetaThemeColor(theme) {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]')
    
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta')
      metaThemeColor.name = 'theme-color'
      document.head.appendChild(metaThemeColor)
    }
    
    // Set appropriate color based on theme
    const color = theme === THEMES.DARK ? '#1e293b' : '#ffffff'
    metaThemeColor.content = color
  }

  /**
   * Get stored theme from localStorage
   * @returns {string|null} Stored theme or null
   */
  getStoredTheme() {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY)
    } catch (error) {
      console.warn('Failed to get stored theme:', error)
      return null
    }
  }

  /**
   * Store theme in localStorage
   * @param {string} theme - Theme to store
   */
  storeTheme(theme) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch (error) {
      console.warn('Failed to store theme:', error)
    }
  }

  /**
   * Get system theme preference
   * @returns {string} System theme
   */
  getSystemTheme() {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches 
        ? THEMES.DARK 
        : THEMES.LIGHT
    }
    return THEMES.LIGHT // Default fallback
  }

  /**
   * Setup listener for system theme changes
   */
  setupSystemThemeListener() {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleSystemThemeChange = (e) => {
      // Only auto-switch if user hasn't manually set a theme
      if (!this.getStoredTheme()) {
        const systemTheme = e.matches ? THEMES.DARK : THEMES.LIGHT
        this.setTheme(systemTheme)
      }
    }

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleSystemThemeChange)
    } else {
      // Legacy browsers
      mediaQuery.addListener(handleSystemThemeChange)
    }
  }

  /**
   * Setup listener for localStorage changes (multi-tab sync)
   */
  setupStorageListener() {
    if (typeof window === 'undefined') {
      return
    }

    window.addEventListener('storage', (e) => {
      if (e.key === THEME_STORAGE_KEY && e.newValue) {
        const newTheme = e.newValue
        if (newTheme !== this.currentTheme) {
          this.currentTheme = newTheme
          this.applyTheme(newTheme)
          this.notifyListeners(newTheme)
        }
      }
    })
  }

  /**
   * Add theme change listener
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    this.listeners.add(callback)
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback)
    }
  }

  /**
   * Notify all listeners of theme change
   * @param {string} theme - New theme
   */
  notifyListeners(theme) {
    this.listeners.forEach(callback => {
      try {
        callback(theme)
      } catch (error) {
        console.error('Theme listener error:', error)
      }
    })
  }

  /**
   * Get theme colors for programmatic use
   * @param {string} theme - Theme name (optional, uses current if not provided)
   * @returns {Object} Theme colors
   */
  getThemeColors(theme = this.currentTheme) {
    const colors = {
      [THEMES.LIGHT]: {
        primary: '#2563eb',
        secondary: '#64748b',
        background: '#ffffff',
        surface: '#f8fafc',
        text: '#1e293b',
        textSecondary: '#64748b',
        border: '#e2e8f0',
        error: '#dc2626',
        success: '#16a34a',
        warning: '#d97706'
      },
      [THEMES.DARK]: {
        primary: '#3b82f6',
        secondary: '#94a3b8',
        background: '#0f172a',
        surface: '#1e293b',
        text: '#f1f5f9',
        textSecondary: '#94a3b8',
        border: '#334155',
        error: '#ef4444',
        success: '#22c55e',
        warning: '#f59e0b'
      }
    }

    return colors[theme] || colors[THEMES.LIGHT]
  }

  /**
   * Get CSS custom property value
   * @param {string} property - CSS property name (without --)
   * @returns {string} Property value
   */
  getCSSProperty(property) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(`--${property}`)
      .trim()
  }
}

// Create singleton instance
const themeService = new ThemeService()

// Export constants and service
export { THEMES, themeService as default }

// Export convenience functions
export const getTheme = () => themeService.getTheme()
export const setTheme = (theme) => themeService.setTheme(theme)
export const toggleTheme = () => themeService.toggleTheme()
export const isDark = () => themeService.isDark()
export const isLight = () => themeService.isLight()
export const subscribeToTheme = (callback) => themeService.subscribe(callback)
export const getThemeColors = (theme) => themeService.getThemeColors(theme)
