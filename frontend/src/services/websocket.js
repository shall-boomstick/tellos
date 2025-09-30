/**
 * WebSocket service for SawtFeel application
 * Handles real-time communication with the backend
 */

class WebSocketService {
  constructor() {
    this.connections = new Map()
    this.reconnectAttempts = new Map()
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000 // Start with 1 second
    this.maxReconnectDelay = 30000 // Max 30 seconds
  }

  /**
   * Connect to processing WebSocket
   * @param {string} fileId - File identifier
   * @param {Object} callbacks - Event callbacks
   * @returns {WebSocket} WebSocket instance
   */
  connectProcessing(fileId, callbacks = {}) {
    const wsUrl = `${this.getWebSocketUrl()}/ws/processing/${fileId}`
    return this.connect(`processing-${fileId}`, wsUrl, callbacks)
  }

  /**
   * Connect to playback WebSocket
   * @param {string} fileId - File identifier
   * @param {Object} callbacks - Event callbacks
   * @returns {WebSocket} WebSocket instance
   */
  connectPlayback(fileId, callbacks = {}) {
    const wsUrl = `${this.getWebSocketUrl()}/ws/playback/${fileId}`
    return this.connect(`playback-${fileId}`, wsUrl, callbacks)
  }

  /**
   * Generic WebSocket connection
   * @param {string} key - Connection key
   * @param {string} url - WebSocket URL
   * @param {Object} callbacks - Event callbacks
   * @returns {WebSocket} WebSocket instance
   */
  connect(key, url, callbacks = {}) {
    // Close existing connection if any
    this.disconnect(key)

    const ws = new WebSocket(url)
    
    // Store connection info
    this.connections.set(key, {
      ws,
      url,
      callbacks,
      isConnected: false,
      lastActivity: Date.now()
    })

    // Setup event handlers
    ws.onopen = (event) => {
      console.log(`WebSocket connected: ${key}`)
      const connection = this.connections.get(key)
      if (connection) {
        connection.isConnected = true
        connection.lastActivity = Date.now()
        this.reconnectAttempts.set(key, 0) // Reset reconnect attempts
      }
      
      if (callbacks.onOpen) {
        callbacks.onOpen(event)
      }
    }

    ws.onmessage = (event) => {
      const connection = this.connections.get(key)
      if (connection) {
        connection.lastActivity = Date.now()
      }

      try {
        const data = JSON.parse(event.data)
        console.log(`WebSocket message (${key}):`, data)
        
        // Handle different message types
        switch (data.type) {
          case 'connected':
            if (callbacks.onConnected) {
              callbacks.onConnected(data)
            }
            break
          case 'status_update':
          case 'progress_update':
            if (callbacks.onProgress) {
              callbacks.onProgress(data)
            }
            break
          case 'completed':
            if (callbacks.onCompleted) {
              callbacks.onCompleted(data)
            }
            break
          case 'time_update':
            if (callbacks.onTimeUpdate) {
              callbacks.onTimeUpdate(data)
            }
            break
          case 'emotion_update':
            if (callbacks.onEmotionUpdate) {
              callbacks.onEmotionUpdate(data)
            }
            break
          case 'transcript_update':
            if (callbacks.onTranscriptUpdate) {
              callbacks.onTranscriptUpdate(data)
            }
            break
          case 'error':
            if (callbacks.onError) {
              callbacks.onError(data)
            }
            break
          case 'pong':
            // Handle ping/pong for keep-alive
            break
          default:
            if (callbacks.onMessage) {
              callbacks.onMessage(data)
            }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
        if (callbacks.onError) {
          callbacks.onError({ type: 'parse_error', error: error.message })
        }
      }
    }

    ws.onclose = (event) => {
      console.log(`WebSocket closed: ${key}`, event.code, event.reason)
      const connection = this.connections.get(key)
      if (connection) {
        connection.isConnected = false
      }

      if (callbacks.onClose) {
        callbacks.onClose(event)
      }

      // Attempt reconnection if not a normal closure
      if (event.code !== 1000 && event.code !== 1001) {
        this.attemptReconnect(key)
      }
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error (${key}):`, error)
      if (callbacks.onError) {
        callbacks.onError({ type: 'connection_error', error: error.message })
      }
    }

    return ws
  }

  /**
   * Disconnect WebSocket
   * @param {string} key - Connection key
   */
  disconnect(key) {
    const connection = this.connections.get(key)
    if (connection && connection.ws) {
      connection.ws.close(1000, 'Manual disconnect')
      this.connections.delete(key)
      this.reconnectAttempts.delete(key)
    }
  }

  /**
   * Disconnect all WebSockets
   */
  disconnectAll() {
    for (const key of this.connections.keys()) {
      this.disconnect(key)
    }
  }

  /**
   * Send message to WebSocket
   * @param {string} key - Connection key
   * @param {Object} message - Message to send
   * @returns {boolean} Success status
   */
  send(key, message) {
    const connection = this.connections.get(key)
    if (!connection || !connection.isConnected) {
      console.warn(`Cannot send message: WebSocket ${key} not connected`)
      return false
    }

    try {
      connection.ws.send(JSON.stringify(message))
      connection.lastActivity = Date.now()
      return true
    } catch (error) {
      console.error(`Failed to send WebSocket message (${key}):`, error)
      return false
    }
  }

  /**
   * Send ping message
   * @param {string} key - Connection key
   */
  ping(key) {
    return this.send(key, { type: 'ping', timestamp: Date.now() })
  }

  /**
   * Check if WebSocket is connected
   * @param {string} key - Connection key
   * @returns {boolean} Connection status
   */
  isConnected(key) {
    const connection = this.connections.get(key)
    return connection && connection.isConnected && connection.ws.readyState === WebSocket.OPEN
  }

  /**
   * Get WebSocket URL based on current location
   * @returns {string} WebSocket base URL
   */
  getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}`
  }

  /**
   * Attempt to reconnect WebSocket
   * @param {string} key - Connection key
   */
  attemptReconnect(key) {
    const connection = this.connections.get(key)
    if (!connection) return

    const attempts = this.reconnectAttempts.get(key) || 0
    if (attempts >= this.maxReconnectAttempts) {
      console.warn(`Max reconnect attempts reached for ${key}`)
      if (connection.callbacks.onMaxReconnectAttempts) {
        connection.callbacks.onMaxReconnectAttempts()
      }
      return
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, attempts), // Exponential backoff
      this.maxReconnectDelay
    )

    console.log(`Reconnecting ${key} in ${delay}ms (attempt ${attempts + 1})`)
    
    setTimeout(() => {
      if (this.connections.has(key)) { // Check if still needed
        this.reconnectAttempts.set(key, attempts + 1)
        this.connect(key, connection.url, connection.callbacks)
      }
    }, delay)
  }

  /**
   * Start keep-alive for all connections
   */
  startKeepAlive(interval = 30000) {
    setInterval(() => {
      for (const [key, connection] of this.connections) {
        if (connection.isConnected) {
          // Check if connection is stale
          const timeSinceActivity = Date.now() - connection.lastActivity
          if (timeSinceActivity > interval * 2) {
            console.warn(`Connection ${key} appears stale, reconnecting`)
            this.attemptReconnect(key)
          } else {
            this.ping(key)
          }
        }
      }
    }, interval)
  }
}

// Playback control helpers
export const playbackControls = {
  /**
   * Send play command
   * @param {WebSocketService} ws - WebSocket service instance
   * @param {string} fileId - File identifier
   */
  play: (ws, fileId) => {
    return ws.send(`playback-${fileId}`, {
      type: 'play',
      timestamp: Date.now()
    })
  },

  /**
   * Send pause command
   * @param {WebSocketService} ws - WebSocket service instance
   * @param {string} fileId - File identifier
   */
  pause: (ws, fileId) => {
    return ws.send(`playback-${fileId}`, {
      type: 'pause',
      timestamp: Date.now()
    })
  },

  /**
   * Send seek command
   * @param {WebSocketService} ws - WebSocket service instance
   * @param {string} fileId - File identifier
   * @param {number} time - Seek time in seconds
   */
  seek: (ws, fileId, time) => {
    return ws.send(`playback-${fileId}`, {
      type: 'seek',
      time: time,
      timestamp: Date.now()
    })
  },

  /**
   * Send time update
   * @param {WebSocketService} ws - WebSocket service instance
   * @param {string} fileId - File identifier
   * @param {number} currentTime - Current time in seconds
   * @param {boolean} isPlaying - Playing state
   */
  updateTime: (ws, fileId, currentTime, isPlaying) => {
    return ws.send(`playback-${fileId}`, {
      type: 'time_update',
      current_time: currentTime,
      is_playing: isPlaying,
      timestamp: Date.now()
    })
  }
}

// Create singleton instance
const websocketService = new WebSocketService()

// Start keep-alive
websocketService.startKeepAlive()

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  websocketService.disconnectAll()
})

export default websocketService
