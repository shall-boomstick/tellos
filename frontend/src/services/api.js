/**
 * API service for SawtFeel application
 * Handles all HTTP requests to the backend
 */

import axios from 'axios'

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 404:
          console.error('Resource not found:', error.config.url)
          break
        case 413:
          console.error('File too large:', data.detail?.error)
          break
        case 415:
          console.error('Unsupported file format:', data.detail?.error)
          break
        case 500:
          console.error('Server error:', data.detail?.error)
          break
        default:
          console.error('API error:', data.detail?.error || error.message)
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error:', error.message)
    } else {
      // Something else happened
      console.error('Request error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

/**
 * Upload API functions
 */
export const uploadAPI = {
  /**
   * Upload a file for processing
   * @param {File} file - The file to upload
   * @param {Function} onProgress - Progress callback
   * @returns {Promise} Upload response
   */
  uploadFile: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percentCompleted)
        }
      },
    })
  },

  /**
   * Get upload status
   * @param {string} fileId - File identifier
   * @returns {Promise} Status response
   */
  getUploadStatus: async (fileId) => {
    return api.get(`/upload/${fileId}/status`)
  },
}

/**
 * Processing API functions
 */
export const processingAPI = {
  /**
   * Get transcript data
   * @param {string} fileId - File identifier
   * @returns {Promise} Transcript response
   */
  getTranscript: async (fileId) => {
    return api.get(`/processing/${fileId}/transcript`)
  },

  /**
   * Get emotion analysis data
   * @param {string} fileId - File identifier
   * @returns {Promise} Emotion analysis response
   */
  getEmotions: async (fileId) => {
    return api.get(`/processing/${fileId}/emotions`)
  },

  /**
   * Get audio URL for streaming
   * @param {string} fileId - File identifier
   * @returns {Promise} Audio URL response
   */
  getAudioUrl: async (fileId) => {
    return api.get(`/processing/${fileId}/audio-url`)
  },
}

/**
 * Utility functions
 */
export const utils = {
  /**
   * Check if error is a network error
   * @param {Error} error - The error object
   * @returns {boolean} True if network error
   */
  isNetworkError: (error) => {
    return !error.response && error.request
  },

  /**
   * Check if error is a server error (5xx)
   * @param {Error} error - The error object
   * @returns {boolean} True if server error
   */
  isServerError: (error) => {
    return error.response && error.response.status >= 500
  },

  /**
   * Check if error is a client error (4xx)
   * @param {Error} error - The error object
   * @returns {boolean} True if client error
   */
  isClientError: (error) => {
    return error.response && error.response.status >= 400 && error.response.status < 500
  },

  /**
   * Get user-friendly error message
   * @param {Error} error - The error object
   * @returns {string} User-friendly error message
   */
  getErrorMessage: (error) => {
    if (error.response?.data?.detail?.error) {
      return error.response.data.detail.error
    }
    
    if (error.response?.data?.detail) {
      return typeof error.response.data.detail === 'string' 
        ? error.response.data.detail 
        : 'An error occurred'
    }
    
    if (utils.isNetworkError(error)) {
      return 'Network error. Please check your connection and try again.'
    }
    
    if (utils.isServerError(error)) {
      return 'Server error. Please try again later.'
    }
    
    return error.message || 'An unexpected error occurred'
  },

  /**
   * Get supported file formats from error response
   * @param {Error} error - The error object
   * @returns {Array} Array of supported formats
   */
  getSupportedFormats: (error) => {
    return error.response?.data?.detail?.supported_formats || [
      'MP3', 'WAV', 'MP4', 'AVI', 'MOV', 'MKV', 'WebM', 'FLV'
    ]
  },
}

/**
 * Health check function
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check failed:', error)
    throw error
  }
}

/**
 * Polling utility for status updates
 * @param {string} fileId - File identifier
 * @param {Function} callback - Callback function for status updates
 * @param {number} interval - Polling interval in milliseconds
 * @param {number} maxAttempts - Maximum polling attempts
 * @returns {Function} Stop polling function
 */
export const pollUploadStatus = (fileId, callback, interval = 2000, maxAttempts = 150) => {
  let attempts = 0
  let timeoutId = null
  
  const poll = async () => {
    try {
      attempts++
      const response = await uploadAPI.getUploadStatus(fileId)
      const status = response.data.status
      
      callback(response.data)
      
      // Stop polling if completed, failed, or max attempts reached
      if (status === 'completed' || status === 'failed' || attempts >= maxAttempts) {
        return
      }
      
      // Schedule next poll
      timeoutId = setTimeout(poll, interval)
      
    } catch (error) {
      console.error('Polling error:', error)
      callback({ error: utils.getErrorMessage(error) })
    }
  }
  
  // Start polling
  poll()
  
  // Return stop function
  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }
}

export default api
