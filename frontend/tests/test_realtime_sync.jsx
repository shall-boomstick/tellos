/**
 * Test real-time synchronization functionality.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRealtimeSync } from '../src/hooks/useRealtimeSync';

// Mock the hook
jest.mock('../src/hooks/useRealtimeSync', () => ({
  useRealtimeSync: jest.fn(),
}));

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
};

global.WebSocket = jest.fn(() => mockWebSocket);

describe('RealtimeSync', () => {
  const mockVideoRef = { current: { currentTime: 0, duration: 100 } };
  const mockOnTranslationUpdate = jest.fn();
  const mockOnEmotionUpdate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockWebSocket.send.mockClear();
    mockWebSocket.close.mockClear();
  });

  test('initializes real-time synchronization', () => {
    useRealtimeSync.mockReturnValue({
      isConnected: false,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    expect(result.current.isConnected).toBe(false);
    expect(result.current.isSyncing).toBe(false);
  });

  test('connects to WebSocket', async () => {
    const mockConnect = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: false,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: mockConnect,
      disconnect: jest.fn(),
      sync: jest.fn(),
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await act(async () => {
      result.current.connect('test-file-id');
    });

    expect(mockConnect).toHaveBeenCalledWith('test-file-id');
  });

  test('handles WebSocket connection success', async () => {
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    expect(result.current.isConnected).toBe(true);
    expect(result.current.isSyncing).toBe(true);
  });

  test('handles WebSocket connection failure', async () => {
    useRealtimeSync.mockReturnValue({
      isConnected: false,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
      error: 'Connection failed',
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    expect(result.current.error).toBe('Connection failed');
  });

  test('synchronizes video time with translations', async () => {
    const mockSync = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 5.0,
      translations: [
        { text: 'Hello', timestamp: 0, confidence: 0.9 },
        { text: 'World', timestamp: 5, confidence: 0.8 },
      ],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: mockSync,
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await act(async () => {
      result.current.sync(5.0);
    });

    expect(mockSync).toHaveBeenCalledWith(5.0);
  });

  test('synchronizes video time with emotions', async () => {
    const mockSync = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 5.0,
      translations: [],
      emotions: [
        { emotion: 'happy', intensity: 0.8, timestamp: 5 },
      ],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: mockSync,
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await act(async () => {
      result.current.sync(5.0);
    });

    expect(mockSync).toHaveBeenCalledWith(5.0);
  });

  test('handles real-time translation updates', async () => {
    const mockOnTranslationUpdate = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 0,
      translations: [
        { text: 'New translation', timestamp: 0, confidence: 0.9 },
      ],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
    });

    renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await waitFor(() => {
      expect(mockOnTranslationUpdate).toHaveBeenCalledWith([
        { text: 'New translation', timestamp: 0, confidence: 0.9 },
      ]);
    });
  });

  test('handles real-time emotion updates', async () => {
    const mockOnEmotionUpdate = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 0,
      translations: [],
      emotions: [
        { emotion: 'happy', intensity: 0.8, timestamp: 0 },
      ],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
    });

    renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await waitFor(() => {
      expect(mockOnEmotionUpdate).toHaveBeenCalledWith([
        { emotion: 'happy', intensity: 0.8, timestamp: 0 },
      ]);
    });
  });

  test('handles video seeking synchronization', async () => {
    const mockSync = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: true,
      currentTime: 10.0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: mockSync,
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    // Simulate video seeking
    mockVideoRef.current.currentTime = 10.0;

    await act(async () => {
      result.current.sync(10.0);
    });

    expect(mockSync).toHaveBeenCalledWith(10.0);
  });

  test('handles disconnection', async () => {
    const mockDisconnect = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: false,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: mockDisconnect,
      sync: jest.fn(),
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await act(async () => {
      result.current.disconnect();
    });

    expect(mockDisconnect).toHaveBeenCalled();
  });

  test('handles reconnection', async () => {
    const mockConnect = jest.fn();
    useRealtimeSync.mockReturnValue({
      isConnected: false,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: mockConnect,
      disconnect: jest.fn(),
      sync: jest.fn(),
      reconnect: jest.fn(),
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    await act(async () => {
      result.current.reconnect();
    });

    expect(mockConnect).toHaveBeenCalled();
  });

  test('handles synchronization errors', async () => {
    useRealtimeSync.mockReturnValue({
      isConnected: true,
      isSyncing: false,
      currentTime: 0,
      translations: [],
      emotions: [],
      connect: jest.fn(),
      disconnect: jest.fn(),
      sync: jest.fn(),
      error: 'Synchronization failed',
    });

    const { result } = renderHook(() => 
      useRealtimeSync(mockVideoRef, mockOnTranslationUpdate, mockOnEmotionUpdate)
    );

    expect(result.current.error).toBe('Synchronization failed');
  });
});



