/**
 * Retry service for handling failed requests and operations with exponential backoff
 */

class RetryService {
  constructor(options = {}) {
    this.defaultOptions = {
      maxAttempts: 3,
      baseDelay: 1000, // 1 second
      maxDelay: 10000, // 10 seconds
      backoffFactor: 2,
      jitter: true,
      retryCondition: (error) => {
        // Retry on network errors, 5xx status codes, and specific 4xx codes
        if (!error.response) return true; // Network error
        const status = error.response.status;
        return status >= 500 || status === 408 || status === 429;
      }
    };
    
    this.options = { ...this.defaultOptions, ...options };
  }

  /**
   * Execute a function with retry logic
   * @param {Function} fn - Function to execute
   * @param {Object} options - Retry options
   * @returns {Promise} - Promise that resolves with the result
   */
  async execute(fn, options = {}) {
    const config = { ...this.options, ...options };
    let lastError;
    
    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      try {
        const result = await fn();
        return result;
      } catch (error) {
        lastError = error;
        
        // Check if we should retry
        if (attempt === config.maxAttempts || !config.retryCondition(error)) {
          throw error;
        }
        
        // Calculate delay with exponential backoff
        const delay = this.calculateDelay(attempt, config);
        
        console.warn(`Attempt ${attempt} failed, retrying in ${delay}ms:`, error.message);
        
        // Wait before retrying
        await this.sleep(delay);
      }
    }
    
    throw lastError;
  }

  /**
   * Calculate delay for retry with exponential backoff
   * @param {number} attempt - Current attempt number (1-based)
   * @param {Object} config - Retry configuration
   * @returns {number} - Delay in milliseconds
   */
  calculateDelay(attempt, config) {
    const exponentialDelay = config.baseDelay * Math.pow(config.backoffFactor, attempt - 1);
    const cappedDelay = Math.min(exponentialDelay, config.maxDelay);
    
    if (config.jitter) {
      // Add jitter to prevent thundering herd
      const jitterAmount = cappedDelay * 0.1; // 10% jitter
      const jitter = (Math.random() - 0.5) * 2 * jitterAmount;
      return Math.max(0, cappedDelay + jitter);
    }
    
    return cappedDelay;
  }

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} - Promise that resolves after delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Retry a fetch request
   * @param {string} url - URL to fetch
   * @param {Object} options - Fetch options
   * @param {Object} retryOptions - Retry options
   * @returns {Promise} - Promise that resolves with response
   */
  async fetchWithRetry(url, options = {}, retryOptions = {}) {
    return this.execute(async () => {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        error.response = response;
        throw error;
      }
      
      return response;
    }, retryOptions);
  }

  /**
   * Retry a WebSocket connection
   * @param {string} url - WebSocket URL
   * @param {Object} options - WebSocket options
   * @param {Object} retryOptions - Retry options
   * @returns {Promise} - Promise that resolves with WebSocket
   */
  async connectWebSocketWithRetry(url, options = {}, retryOptions = {}) {
    return this.execute(async () => {
      return new Promise((resolve, reject) => {
        const ws = new WebSocket(url);
        
        ws.onopen = () => resolve(ws);
        ws.onerror = (error) => reject(new Error('WebSocket connection failed'));
        ws.onclose = (event) => {
          if (event.code !== 1000) {
            reject(new Error(`WebSocket closed unexpectedly: ${event.code}`));
          }
        };
      });
    }, retryOptions);
  }

  /**
   * Retry a file upload
   * @param {string} url - Upload URL
   * @param {FormData} formData - Form data to upload
   * @param {Object} options - Upload options
   * @param {Object} retryOptions - Retry options
   * @returns {Promise} - Promise that resolves with response
   */
  async uploadWithRetry(url, formData, options = {}, retryOptions = {}) {
    return this.execute(async () => {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        ...options
      });
      
      if (!response.ok) {
        const error = new Error(`Upload failed: ${response.status} ${response.statusText}`);
        error.response = response;
        throw error;
      }
      
      return response;
    }, retryOptions);
  }

  /**
   * Retry a WebSocket message send
   * @param {WebSocket} ws - WebSocket instance
   * @param {*} message - Message to send
   * @param {Object} retryOptions - Retry options
   * @returns {Promise} - Promise that resolves when message is sent
   */
  async sendWebSocketMessageWithRetry(ws, message, retryOptions = {}) {
    return this.execute(async () => {
      if (ws.readyState !== WebSocket.OPEN) {
        throw new Error('WebSocket is not open');
      }
      
      ws.send(JSON.stringify(message));
      return true;
    }, retryOptions);
  }

  /**
   * Create a retry decorator for functions
   * @param {Object} retryOptions - Retry options
   * @returns {Function} - Decorator function
   */
  createRetryDecorator(retryOptions = {}) {
    return (target, propertyName, descriptor) => {
      const originalMethod = descriptor.value;
      
      descriptor.value = async function(...args) {
        const retryService = new RetryService(retryOptions);
        return retryService.execute(() => originalMethod.apply(this, args));
      };
      
      return descriptor;
    };
  }
}

// Create default instance
const defaultRetryService = new RetryService();

// Export both class and default instance
export { RetryService };
export default defaultRetryService;

// Utility functions
export const retry = (fn, options = {}) => defaultRetryService.execute(fn, options);
export const retryFetch = (url, options = {}, retryOptions = {}) => 
  defaultRetryService.fetchWithRetry(url, options, retryOptions);
export const retryWebSocket = (url, options = {}, retryOptions = {}) => 
  defaultRetryService.connectWebSocketWithRetry(url, options, retryOptions);
export const retryUpload = (url, formData, options = {}, retryOptions = {}) => 
  defaultRetryService.uploadWithRetry(url, formData, options, retryOptions);
