/**
 * Performance optimization utilities for real-time video interface
 * Provides utilities for debouncing, throttling, memoization, and performance monitoring
 */

/**
 * Debounce function to limit the rate of function execution
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in milliseconds
 * @param {boolean} immediate - Execute on leading edge
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) func(...args);
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func(...args);
  };
};

/**
 * Throttle function to limit function execution frequency
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Memoization utility for expensive computations
 * @param {Function} fn - Function to memoize
 * @param {Function} getKey - Function to generate cache key
 * @returns {Function} Memoized function
 */
export const memoize = (fn, getKey = (...args) => JSON.stringify(args)) => {
  const cache = new Map();
  return (...args) => {
    const key = getKey(...args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
};

/**
 * Performance monitor for measuring function execution time
 */
export class PerformanceMonitor {
  constructor() {
    this.marks = new Map();
    this.measures = new Map();
  }

  /**
   * Start timing a performance mark
   * @param {string} name - Name of the performance mark
   */
  markStart(name) {
    this.marks.set(name, performance.now());
  }

  /**
   * End timing and measure duration
   * @param {string} name - Name of the performance mark
   * @returns {number} Duration in milliseconds
   */
  markEnd(name) {
    const startTime = this.marks.get(name);
    if (!startTime) {
      console.warn(`Performance mark '${name}' was not started`);
      return 0;
    }
    
    const duration = performance.now() - startTime;
    this.measures.set(name, duration);
    this.marks.delete(name);
    return duration;
  }

  /**
   * Get performance measure
   * @param {string} name - Name of the measure
   * @returns {number} Duration in milliseconds
   */
  getMeasure(name) {
    return this.measures.get(name) || 0;
  }

  /**
   * Clear all performance data
   */
  clear() {
    this.marks.clear();
    this.measures.clear();
  }

  /**
   * Get all performance measures
   * @returns {Object} Object containing all measures
   */
  getAllMeasures() {
    return Object.fromEntries(this.measures);
  }
}

/**
 * Request Animation Frame throttle for smooth animations
 * @param {Function} callback - Function to execute
 * @returns {Function} Throttled function using RAF
 */
export const rafThrottle = (callback) => {
  let rafId = null;
  return (...args) => {
    if (rafId === null) {
      rafId = requestAnimationFrame(() => {
        callback(...args);
        rafId = null;
      });
    }
  };
};

/**
 * Intersection Observer utility for lazy loading
 * @param {Element} element - Element to observe
 * @param {Function} callback - Callback when element enters viewport
 * @param {Object} options - Intersection Observer options
 * @returns {IntersectionObserver} Observer instance
 */
export const createIntersectionObserver = (element, callback, options = {}) => {
  const defaultOptions = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        callback(entry);
      }
    });
  }, defaultOptions);

  observer.observe(element);
  return observer;
};

/**
 * Virtual scrolling utility for large lists
 * @param {Array} items - Array of items to virtualize
 * @param {number} itemHeight - Height of each item
 * @param {number} containerHeight - Height of visible container
 * @param {number} scrollTop - Current scroll position
 * @returns {Object} Virtual scrolling data
 */
export const getVirtualScrollData = (items, itemHeight, containerHeight, scrollTop) => {
  const totalHeight = items.length * itemHeight;
  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleCount + 1, items.length);
  
  return {
    totalHeight,
    visibleCount,
    startIndex,
    endIndex,
    visibleItems: items.slice(startIndex, endIndex),
    offsetY: startIndex * itemHeight
  };
};

/**
 * Memory usage monitor
 */
export class MemoryMonitor {
  constructor() {
    this.initialMemory = this.getMemoryUsage();
  }

  /**
   * Get current memory usage
   * @returns {Object} Memory usage information
   */
  getMemoryUsage() {
    if (performance.memory) {
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit
      };
    }
    return null;
  }

  /**
   * Get memory usage since initialization
   * @returns {Object} Memory usage delta
   */
  getMemoryDelta() {
    const current = this.getMemoryUsage();
    if (!current || !this.initialMemory) return null;
    
    return {
      used: current.used - this.initialMemory.used,
      total: current.total - this.initialMemory.total,
      percentage: (current.used / current.limit) * 100
    };
  }

  /**
   * Check if memory usage is high
   * @param {number} threshold - Threshold percentage (default: 80)
   * @returns {boolean} True if memory usage is high
   */
  isMemoryHigh(threshold = 80) {
    const current = this.getMemoryUsage();
    if (!current) return false;
    return (current.used / current.limit) * 100 > threshold;
  }
}

/**
 * Batch DOM updates to prevent layout thrashing
 * @param {Function} updateFunction - Function containing DOM updates
 */
export const batchDOMUpdates = (updateFunction) => {
  // Use requestAnimationFrame to batch updates
  requestAnimationFrame(() => {
    // Use DocumentFragment for efficient DOM manipulation
    const fragment = document.createDocumentFragment();
    updateFunction(fragment);
  });
};

/**
 * Preload critical resources
 * @param {Array} resources - Array of resource URLs
 * @returns {Promise} Promise that resolves when all resources are loaded
 */
export const preloadResources = (resources) => {
  const promises = resources.map(resource => {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource.url;
      link.as = resource.type || 'script';
      
      link.onload = () => resolve(resource);
      link.onerror = () => reject(new Error(`Failed to preload ${resource.url}`));
      
      document.head.appendChild(link);
    });
  });
  
  return Promise.all(promises);
};

/**
 * Performance optimization for video processing
 */
export class VideoPerformanceOptimizer {
  constructor() {
    this.frameQueue = [];
    this.isProcessing = false;
    this.maxQueueSize = 10;
  }

  /**
   * Queue video frame for processing
   * @param {ImageData} frameData - Video frame data
   * @param {Function} processor - Frame processing function
   */
  queueFrame(frameData, processor) {
    if (this.frameQueue.length >= this.maxQueueSize) {
      // Remove oldest frame if queue is full
      this.frameQueue.shift();
    }
    
    this.frameQueue.push({ frameData, processor });
    this.processQueue();
  }

  /**
   * Process queued frames
   */
  async processQueue() {
    if (this.isProcessing || this.frameQueue.length === 0) {
      return;
    }
    
    this.isProcessing = true;
    
    while (this.frameQueue.length > 0) {
      const { frameData, processor } = this.frameQueue.shift();
      try {
        await processor(frameData);
      } catch (error) {
        console.error('Frame processing error:', error);
      }
    }
    
    this.isProcessing = false;
  }

  /**
   * Clear the frame queue
   */
  clearQueue() {
    this.frameQueue = [];
  }
}

// Create global instances
export const performanceMonitor = new PerformanceMonitor();
export const memoryMonitor = new MemoryMonitor();
export const videoOptimizer = new VideoPerformanceOptimizer();

