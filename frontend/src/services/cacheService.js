/**
 * Caching service for real-time video interface
 * Provides multiple caching strategies for different types of data
 */

/**
 * Base cache interface
 */
class BaseCache {
  constructor(maxSize = 100, ttl = 300000) { // 5 minutes default TTL
    this.maxSize = maxSize;
    this.ttl = ttl;
    this.cache = new Map();
    this.timers = new Map();
  }

  set(key, value, customTtl = null) {
    // Remove oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.delete(firstKey);
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      ttl: customTtl || this.ttl
    });

    // Set expiration timer
    this.setExpirationTimer(key, customTtl || this.ttl);
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      this.delete(key);
      return null;
    }

    return item.value;
  }

  has(key) {
    return this.get(key) !== null;
  }

  delete(key) {
    this.cache.delete(key);
    this.clearExpirationTimer(key);
  }

  clear() {
    this.cache.clear();
    this.timers.forEach(timer => clearTimeout(timer));
    this.timers.clear();
  }

  setExpirationTimer(key, ttl) {
    this.clearExpirationTimer(key);
    const timer = setTimeout(() => {
      this.delete(key);
    }, ttl);
    this.timers.set(key, timer);
  }

  clearExpirationTimer(key) {
    const timer = this.timers.get(key);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(key);
    }
  }

  size() {
    return this.cache.size;
  }

  keys() {
    return Array.from(this.cache.keys());
  }
}

/**
 * LRU (Least Recently Used) cache implementation
 */
class LRUCache extends BaseCache {
  constructor(maxSize = 100, ttl = 300000) {
    super(maxSize, ttl);
    this.accessOrder = [];
  }

  set(key, value, customTtl = null) {
    // Update access order
    this.updateAccessOrder(key);
    super.set(key, value, customTtl);
  }

  get(key) {
    const value = super.get(key);
    if (value !== null) {
      this.updateAccessOrder(key);
    }
    return value;
  }

  updateAccessOrder(key) {
    // Remove from current position
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
    // Add to end (most recently used)
    this.accessOrder.push(key);
  }

  set(key, value, customTtl = null) {
    // Remove oldest if at capacity
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      const oldestKey = this.accessOrder.shift();
      this.delete(oldestKey);
    }

    super.set(key, value, customTtl);
    this.updateAccessOrder(key);
  }

  delete(key) {
    super.delete(key);
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
  }
}

/**
 * Video frame cache for real-time processing
 */
class VideoFrameCache {
  constructor(maxFrames = 50, frameTTL = 10000) { // 10 seconds for frames
    this.cache = new Map();
    this.maxFrames = maxFrames;
    this.frameTTL = frameTTL;
    this.frameOrder = [];
  }

  setFrame(timestamp, frameData) {
    // Remove oldest frames if at capacity
    if (this.cache.size >= this.maxFrames) {
      const oldestTimestamp = this.frameOrder.shift();
      this.cache.delete(oldestTimestamp);
    }

    this.cache.set(timestamp, {
      data: frameData,
      timestamp: Date.now()
    });
    this.frameOrder.push(timestamp);

    // Set expiration timer
    setTimeout(() => {
      this.cache.delete(timestamp);
      const index = this.frameOrder.indexOf(timestamp);
      if (index > -1) {
        this.frameOrder.splice(index, 1);
      }
    }, this.frameTTL);
  }

  getFrame(timestamp) {
    const frame = this.cache.get(timestamp);
    if (!frame) return null;

    // Check if expired
    if (Date.now() - frame.timestamp > this.frameTTL) {
      this.cache.delete(timestamp);
      const index = this.frameOrder.indexOf(timestamp);
      if (index > -1) {
        this.frameOrder.splice(index, 1);
      }
      return null;
    }

    return frame.data;
  }

  getClosestFrame(timestamp, tolerance = 100) {
    let closestTimestamp = null;
    let minDifference = Infinity;

    for (const cachedTimestamp of this.cache.keys()) {
      const difference = Math.abs(cachedTimestamp - timestamp);
      if (difference < minDifference && difference <= tolerance) {
        minDifference = difference;
        closestTimestamp = cachedTimestamp;
      }
    }

    return closestTimestamp ? this.getFrame(closestTimestamp) : null;
  }

  clear() {
    this.cache.clear();
    this.frameOrder = [];
  }
}

/**
 * Translation cache for real-time translation
 */
class TranslationCache {
  constructor(maxTranslations = 200, ttl = 600000) { // 10 minutes
    this.cache = new Map();
    this.maxTranslations = maxTranslations;
    this.ttl = ttl;
    this.accessCounts = new Map();
  }

  setTranslation(text, language, translation) {
    const key = this.getKey(text, language);
    
    // Remove least accessed if at capacity
    if (this.cache.size >= this.maxTranslations && !this.cache.has(key)) {
      this.removeLeastAccessed();
    }

    this.cache.set(key, {
      translation,
      timestamp: Date.now()
    });
    this.accessCounts.set(key, 0);
  }

  getTranslation(text, language) {
    const key = this.getKey(text, language);
    const item = this.cache.get(key);
    
    if (!item) return null;

    // Check if expired
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      this.accessCounts.delete(key);
      return null;
    }

    // Update access count
    this.accessCounts.set(key, (this.accessCounts.get(key) || 0) + 1);
    return item.translation;
  }

  getKey(text, language) {
    return `${language}:${text}`;
  }

  removeLeastAccessed() {
    let leastAccessedKey = null;
    let minAccessCount = Infinity;

    for (const [key, count] of this.accessCounts.entries()) {
      if (count < minAccessCount) {
        minAccessCount = count;
        leastAccessedKey = key;
      }
    }

    if (leastAccessedKey) {
      this.cache.delete(leastAccessedKey);
      this.accessCounts.delete(leastAccessedKey);
    }
  }

  clear() {
    this.cache.clear();
    this.accessCounts.clear();
  }
}

/**
 * Emotion analysis cache
 */
class EmotionCache {
  constructor(maxEmotions = 100, ttl = 300000) { // 5 minutes
    this.cache = new Map();
    this.maxEmotions = maxEmotions;
    this.ttl = ttl;
  }

  setEmotion(timestamp, emotionData) {
    if (this.cache.size >= this.maxEmotions) {
      // Remove oldest entry
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(timestamp, {
      data: emotionData,
      timestamp: Date.now()
    });
  }

  getEmotion(timestamp) {
    const item = this.cache.get(timestamp);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(timestamp);
      return null;
    }

    return item.data;
  }

  getEmotionsInRange(startTime, endTime) {
    const emotions = [];
    for (const [timestamp, item] of this.cache.entries()) {
      if (timestamp >= startTime && timestamp <= endTime) {
        if (Date.now() - item.timestamp <= this.ttl) {
          emotions.push({
            timestamp,
            data: item.data
          });
        }
      }
    }
    return emotions.sort((a, b) => a.timestamp - b.timestamp);
  }

  clear() {
    this.cache.clear();
  }
}

/**
 * WebSocket message cache for reconnection scenarios
 */
class WebSocketMessageCache {
  constructor(maxMessages = 100) {
    this.cache = [];
    this.maxMessages = maxMessages;
  }

  addMessage(message) {
    if (this.cache.length >= this.maxMessages) {
      this.cache.shift(); // Remove oldest
    }
    this.cache.push({
      message,
      timestamp: Date.now()
    });
  }

  getMessages(sinceTimestamp = 0) {
    return this.cache
      .filter(item => item.timestamp > sinceTimestamp)
      .map(item => item.message);
  }

  clear() {
    this.cache = [];
  }
}

/**
 * Main cache service that coordinates all caching strategies
 */
class CacheService {
  constructor() {
    this.caches = {
      general: new LRUCache(100, 300000), // 5 minutes
      videoFrames: new VideoFrameCache(50, 10000), // 10 seconds
      translations: new TranslationCache(200, 600000), // 10 minutes
      emotions: new EmotionCache(100, 300000), // 5 minutes
      websocket: new WebSocketMessageCache(100)
    };
  }

  // General cache methods
  set(key, value, ttl = null) {
    this.caches.general.set(key, value, ttl);
  }

  get(key) {
    return this.caches.general.get(key);
  }

  has(key) {
    return this.caches.general.has(key);
  }

  delete(key) {
    this.caches.general.delete(key);
  }

  // Video frame cache methods
  setFrame(timestamp, frameData) {
    this.caches.videoFrames.setFrame(timestamp, frameData);
  }

  getFrame(timestamp) {
    return this.caches.videoFrames.getFrame(timestamp);
  }

  getClosestFrame(timestamp, tolerance = 100) {
    return this.caches.videoFrames.getClosestFrame(timestamp, tolerance);
  }

  // Translation cache methods
  setTranslation(text, language, translation) {
    this.caches.translations.setTranslation(text, language, translation);
  }

  getTranslation(text, language) {
    return this.caches.translations.getTranslation(text, language);
  }

  // Emotion cache methods
  setEmotion(timestamp, emotionData) {
    this.caches.emotions.setEmotion(timestamp, emotionData);
  }

  getEmotion(timestamp) {
    return this.caches.emotions.getEmotion(timestamp);
  }

  getEmotionsInRange(startTime, endTime) {
    return this.caches.emotions.getEmotionsInRange(startTime, endTime);
  }

  // WebSocket message cache methods
  addMessage(message) {
    this.caches.websocket.addMessage(message);
  }

  getMessages(sinceTimestamp = 0) {
    return this.caches.websocket.getMessages(sinceTimestamp);
  }

  // Cache management methods
  clearCache(cacheType = null) {
    if (cacheType && this.caches[cacheType]) {
      this.caches[cacheType].clear();
    } else {
      Object.values(this.caches).forEach(cache => cache.clear());
    }
  }

  getCacheStats() {
    return {
      general: {
        size: this.caches.general.size(),
        keys: this.caches.general.keys().length
      },
      videoFrames: {
        size: this.caches.videoFrames.cache.size,
        frames: this.caches.videoFrames.frameOrder.length
      },
      translations: {
        size: this.caches.translations.cache.size,
        keys: this.caches.translations.cache.keys().length
      },
      emotions: {
        size: this.caches.emotions.cache.size,
        keys: this.caches.emotions.cache.keys().length
      },
      websocket: {
        size: this.caches.websocket.cache.length
      }
    };
  }

  // Memory management
  optimizeMemory() {
    // Clear expired entries from all caches
    Object.values(this.caches).forEach(cache => {
      if (cache.clear) {
        cache.clear();
      }
    });
  }
}

// Create singleton instance
export const cacheService = new CacheService();

// Export individual cache classes for specific use cases
export {
  BaseCache,
  LRUCache,
  VideoFrameCache,
  TranslationCache,
  EmotionCache,
  WebSocketMessageCache,
  CacheService
};

