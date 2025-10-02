import { useState, useCallback, useRef, useEffect } from 'react';

const useRealtimeWebSocket = ({
  onConnect,
  onDisconnect,
  onTranscript,
  onEmotion,
  onStatus,
  onError
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  // Connect to WebSocket
  const connect = useCallback(async (fileId) => {
    return new Promise((resolve, reject) => {
      try {
        // Close existing connection
        if (wsRef.current) {
          wsRef.current.close();
        }

        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }

        setConnectionStatus('connecting');
        
        // Create WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use Vite proxy for WebSocket connections
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime/${fileId}`;
        
        console.log('Creating WebSocket connection to:', wsUrl);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        // Connection opened
        ws.onopen = () => {
          console.log('WebSocket connected successfully');
          setIsConnected(true);
          setConnectionStatus('connected');
          reconnectAttempts.current = 0;
          
          // Generate a session ID and resolve the promise
          const sessionId = `session_${fileId}_${Date.now()}`;
          console.log('WebSocket session ID:', sessionId);
          resolve(sessionId);
          
          if (onConnect) {
            onConnect();
          }
        };

      // Connection closed
      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        if (onDisconnect) {
          onDisconnect(event);
        }

        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          setConnectionStatus('reconnecting');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
            connect(fileId);
          }, reconnectDelay * reconnectAttempts.current);
        }
      };

      // Connection error
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        reject(new Error('WebSocket connection failed'));
        
        if (onError) {
          onError(error);
        }
      };

      // Message received
      ws.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionStatus('error');
      reject(error);
      
      if (onError) {
        onError(error);
      }
    }
    });
  }, [onConnect, onDisconnect, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((data) => {
    try {
      switch (data.type) {
        case 'transcript':
          if (onTranscript) {
            onTranscript(data.data);
          }
          break;
          
        case 'emotion':
          if (onEmotion) {
            onEmotion(data.data);
          }
          break;
          
        case 'emotion_update':
          if (onEmotion) {
            onEmotion(data);
          }
          break;
          
        case 'status':
        case 'playback_state':
        case 'seek_complete':
          if (onStatus) {
            onStatus(data);
          }
          break;
          
        case 'error':
          console.error('WebSocket error message:', data.message);
          if (onError) {
            onError(new Error(data.message));
          }
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }, [onTranscript, onEmotion, onStatus, onError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const heartbeatInterval = setInterval(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          sendMessage({ type: 'ping' });
        }
      }, 30000); // Send ping every 30 seconds

      return () => {
        clearInterval(heartbeatInterval);
      };
    }
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendMessage
  };
};

export { useRealtimeWebSocket };
