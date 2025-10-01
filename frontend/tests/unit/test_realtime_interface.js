/**
 * Unit tests for RealtimeInterface component
 * Tests the main interface component functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealtimeInterface } from '../../src/pages/RealtimeInterface';

// Mock dependencies
vi.mock('../../src/services/realtimeWebSocket', () => ({
  useRealtimeWebSocket: () => ({
    isConnected: true,
    sendMessage: vi.fn(),
    lastMessage: null,
    error: null
  })
}));

vi.mock('../../src/store/realtimeStore', () => ({
  useRealtimeStore: () => ({
    videoFile: null,
    isProcessing: false,
    currentTime: 0,
    duration: 0,
    transcriptions: [],
    emotions: [],
    translations: [],
    setVideoFile: vi.fn(),
    setIsProcessing: vi.fn(),
    setCurrentTime: vi.fn(),
    addTranscription: vi.fn(),
    addEmotion: vi.fn(),
    addTranslation: vi.fn()
  })
}));

vi.mock('../../src/hooks/useRealtimeSync', () => ({
  useRealtimeSync: () => ({
    syncVideoWithData: vi.fn(),
    isSynced: true
  })
}));

describe('RealtimeInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the main interface components', () => {
    render(<RealtimeInterface />);
    
    expect(screen.getByTestId('realtime-interface')).toBeInTheDocument();
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
    expect(screen.getByTestId('translation-display')).toBeInTheDocument();
    expect(screen.getByTestId('emotion-gauge')).toBeInTheDocument();
    expect(screen.getByTestId('file-upload')).toBeInTheDocument();
  });

  it('displays file upload when no video is loaded', () => {
    render(<RealtimeInterface />);
    
    expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    expect(screen.getByText('Upload Video File')).toBeInTheDocument();
  });

  it('handles file upload correctly', async () => {
    const mockFile = new File(['test video content'], 'test.mp4', { type: 'video/mp4' });
    const { useRealtimeStore } = await import('../../src/store/realtimeStore');
    const mockSetVideoFile = vi.fn();
    
    useRealtimeStore.mockReturnValue({
      videoFile: null,
      isProcessing: false,
      setVideoFile: mockSetVideoFile
    });

    render(<RealtimeInterface />);
    
    const fileInput = screen.getByTestId('file-input');
    fireEvent.change(fileInput, { target: { files: [mockFile] } });
    
    await waitFor(() => {
      expect(mockSetVideoFile).toHaveBeenCalledWith(mockFile);
    });
  });

  it('displays processing status when video is being processed', () => {
    const { useRealtimeStore } = require('../../src/store/realtimeStore');
    useRealtimeStore.mockReturnValue({
      videoFile: new File(['test'], 'test.mp4'),
      isProcessing: true,
      currentTime: 0,
      duration: 100
    });

    render(<RealtimeInterface />);
    
    expect(screen.getByTestId('processing-status')).toBeInTheDocument();
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('displays video player when video is loaded', () => {
    const { useRealtimeStore } = require('../../src/store/realtimeStore');
    useRealtimeStore.mockReturnValue({
      videoFile: new File(['test'], 'test.mp4'),
      isProcessing: false,
      currentTime: 0,
      duration: 100
    });

    render(<RealtimeInterface />);
    
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
    expect(screen.queryByTestId('file-upload')).not.toBeInTheDocument();
  });

  it('handles keyboard shortcuts', () => {
    render(<RealtimeInterface />);
    
    // Test spacebar for play/pause
    fireEvent.keyDown(document, { key: ' ' });
    // Test arrow keys for seeking
    fireEvent.keyDown(document, { key: 'ArrowLeft' });
    fireEvent.keyDown(document, { key: 'ArrowRight' });
    // Test volume controls
    fireEvent.keyDown(document, { key: 'ArrowUp' });
    fireEvent.keyDown(document, { key: 'ArrowDown' });
  });

  it('displays error messages when WebSocket connection fails', () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    useRealtimeWebSocket.mockReturnValue({
      isConnected: false,
      error: 'Connection failed',
      sendMessage: vi.fn(),
      lastMessage: null
    });

    render(<RealtimeInterface />);
    
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });

  it('updates interface when real-time data is received', async () => {
    const mockTranscription = {
      text: 'Hello world',
      timestamp: 1234567890,
      confidence: 0.95
    };

    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    useRealtimeWebSocket.mockReturnValue({
      isConnected: true,
      lastMessage: { type: 'transcription', data: mockTranscription },
      sendMessage: vi.fn(),
      error: null
    });

    render(<RealtimeInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Hello world')).toBeInTheDocument();
    });
  });

  it('handles component unmounting correctly', () => {
    const { unmount } = render(<RealtimeInterface />);
    
    // Should not throw errors when unmounting
    expect(() => unmount()).not.toThrow();
  });

  it('displays help overlay when help is requested', () => {
    render(<RealtimeInterface />);
    
    // Press 'h' to show help
    fireEvent.keyDown(document, { key: 'h' });
    
    expect(screen.getByTestId('help-overlay')).toBeInTheDocument();
  });

  it('closes help overlay when escape is pressed', () => {
    render(<RealtimeInterface />);
    
    // Show help
    fireEvent.keyDown(document, { key: 'h' });
    expect(screen.getByTestId('help-overlay')).toBeInTheDocument();
    
    // Close help
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByTestId('help-overlay')).not.toBeInTheDocument();
  });

  it('handles settings panel toggle', () => {
    render(<RealtimeInterface />);
    
    // Press 's' to show settings
    fireEvent.keyDown(document, { key: 's' });
    expect(screen.getByTestId('settings-panel')).toBeInTheDocument();
    
    // Press 's' again to hide settings
    fireEvent.keyDown(document, { key: 's' });
    expect(screen.queryByTestId('settings-panel')).not.toBeInTheDocument();
  });

  it('displays video information when info is requested', () => {
    const { useRealtimeStore } = require('../../src/store/realtimeStore');
    useRealtimeStore.mockReturnValue({
      videoFile: new File(['test'], 'test.mp4'),
      isProcessing: false,
      currentTime: 30,
      duration: 120
    });

    render(<RealtimeInterface />);
    
    // Press 'i' to show info
    fireEvent.keyDown(document, { key: 'i' });
    
    expect(screen.getByTestId('video-info')).toBeInTheDocument();
    expect(screen.getByText('30 / 120')).toBeInTheDocument();
  });
});

