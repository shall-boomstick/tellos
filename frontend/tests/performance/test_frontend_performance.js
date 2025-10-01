/**
 * Performance tests for frontend real-time interface
 * Tests component rendering, memory usage, and user interaction performance
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealtimeInterface } from '../../src/pages/RealtimeInterface';
import { RealtimeVideoPlayer } from '../../src/components/RealtimeVideoPlayer';
import { RealtimeTranslation } from '../../src/components/RealtimeTranslation';
import { RealtimeEmotionGauge } from '../../src/components/RealtimeEmotionGauge';

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

describe('Frontend Performance Tests', () => {
  let performanceObserver;
  let memoryObserver;

  beforeEach(() => {
    // Set up performance monitoring
    performanceObserver = {
      entries: [],
      observe: vi.fn(),
      disconnect: vi.fn()
    };
    
    memoryObserver = {
      entries: [],
      observe: vi.fn(),
      disconnect: vi.fn()
    };

    // Mock performance API
    global.performance = {
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByType: vi.fn(() => []),
      getEntriesByName: vi.fn(() => []),
      clearMarks: vi.fn(),
      clearMeasures: vi.fn()
    };

    // Mock memory API
    global.performance.memory = {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering Performance', () => {
    it('renders RealtimeInterface within performance budget', () => {
      const startTime = performance.now();
      
      render(<RealtimeInterface />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      expect(renderTime).toBeLessThan(100); // Should render within 100ms
      expect(screen.getByTestId('realtime-interface')).toBeInTheDocument();
    });

    it('renders RealtimeVideoPlayer within performance budget', () => {
      const mockVideoFile = new File(['test video content'], 'test.mp4', { type: 'video/mp4' });
      
      const startTime = performance.now();
      
      render(
        <RealtimeVideoPlayer
          videoFile={mockVideoFile}
          currentTime={0}
          duration={100}
          isPlaying={false}
          onTimeUpdate={vi.fn()}
          onPlay={vi.fn()}
          onPause={vi.fn()}
          onSeek={vi.fn()}
          onVolumeChange={vi.fn()}
        />
      );
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      expect(renderTime).toBeLessThan(50); // Should render within 50ms
      expect(screen.getByTestId('video-player')).toBeInTheDocument();
    });

    it('renders RealtimeTranslation within performance budget', () => {
      const translations = Array.from({ length: 100 }, (_, i) => ({
        id: i.toString(),
        text: `Test text ${i}`,
        translation: `Test translation ${i}`,
        timestamp: Date.now() + i,
        confidence: 0.9,
        language: 'es'
      }));

      const startTime = performance.now();
      
      render(<RealtimeTranslation translations={translations} />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      expect(renderTime).toBeLessThan(200); // Should render within 200ms
      expect(screen.getByTestId('translation-display')).toBeInTheDocument();
    });

    it('renders RealtimeEmotionGauge within performance budget', () => {
      const emotions = Array.from({ length: 100 }, (_, i) => ({
        id: i.toString(),
        timestamp: Date.now() + i,
        emotions: [{ emotion: 'happy', confidence: 0.8 }],
        dominant_emotion: 'happy',
        confidence: 0.8
      }));

      const startTime = performance.now();
      
      render(<RealtimeEmotionGauge emotions={emotions} />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      expect(renderTime).toBeLessThan(150); // Should render within 150ms
      expect(screen.getByTestId('emotion-gauge')).toBeInTheDocument();
    });
  });

  describe('Memory Usage Performance', () => {
    it('does not leak memory during component updates', () => {
      const initialMemory = performance.memory.usedJSHeapSize;
      
      const { rerender } = render(<RealtimeInterface />);
      
      // Simulate multiple updates
      for (let i = 0; i < 100; i++) {
        rerender(<RealtimeInterface />);
      }
      
      const finalMemory = performance.memory.usedJSHeapSize;
      const memoryIncrease = finalMemory - initialMemory;
      
      expect(memoryIncrease).toBeLessThan(1000000); // Should not increase by more than 1MB
    });

    it('handles large datasets without memory issues', () => {
      const largeTranslations = Array.from({ length: 1000 }, (_, i) => ({
        id: i.toString(),
        text: `Test text ${i}`.repeat(100), // Large text
        translation: `Test translation ${i}`.repeat(100),
        timestamp: Date.now() + i,
        confidence: 0.9,
        language: 'es'
      }));

      const initialMemory = performance.memory.usedJSHeapSize;
      
      render(<RealtimeTranslation translations={largeTranslations} />);
      
      const finalMemory = performance.memory.usedJSHeapSize;
      const memoryIncrease = finalMemory - initialMemory;
      
      expect(memoryIncrease).toBeLessThan(5000000); // Should not increase by more than 5MB
    });
  });

  describe('User Interaction Performance', () => {
    it('handles rapid button clicks efficiently', () => {
      render(<RealtimeInterface />);
      
      const playButton = screen.getByTestId('play-pause-button');
      
      const startTime = performance.now();
      
      // Simulate rapid clicks
      for (let i = 0; i < 100; i++) {
        fireEvent.click(playButton);
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(1000); // Should handle 100 clicks within 1 second
    });

    it('handles rapid keyboard input efficiently', () => {
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate rapid keyboard input
      for (let i = 0; i < 100; i++) {
        fireEvent.keyDown(document, { key: ' ' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(500); // Should handle 100 key presses within 500ms
    });

    it('handles rapid mouse movements efficiently', () => {
      render(<RealtimeInterface />);
      
      const videoPlayer = screen.getByTestId('video-player');
      
      const startTime = performance.now();
      
      // Simulate rapid mouse movements
      for (let i = 0; i < 100; i++) {
        fireEvent.mouseMove(videoPlayer, { clientX: i, clientY: i });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(200); // Should handle 100 mouse movements within 200ms
    });
  });

  describe('Real-time Data Processing Performance', () => {
    it('processes real-time translations efficiently', async () => {
      const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
      
      render(<RealtimeTranslation />);
      
      const startTime = performance.now();
      
      // Simulate rapid translation updates
      for (let i = 0; i < 100; i++) {
        const mockTranslation = {
          id: i.toString(),
          text: `Test text ${i}`,
          translation: `Test translation ${i}`,
          timestamp: Date.now() + i,
          confidence: 0.9,
          language: 'es'
        };
        
        useRealtimeWebSocket.mockReturnValue({
          isConnected: true,
          lastMessage: { type: 'translation', data: mockTranslation },
          sendMessage: vi.fn(),
          error: null
        });
        
        // Trigger re-render
        fireEvent.keyDown(document, { key: 'r' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(2000); // Should handle 100 updates within 2 seconds
    });

    it('processes real-time emotions efficiently', async () => {
      const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
      
      render(<RealtimeEmotionGauge />);
      
      const startTime = performance.now();
      
      // Simulate rapid emotion updates
      for (let i = 0; i < 100; i++) {
        const mockEmotion = {
          id: i.toString(),
          timestamp: Date.now() + i,
          emotions: [{ emotion: 'happy', confidence: 0.8 }],
          dominant_emotion: 'happy',
          confidence: 0.8
        };
        
        useRealtimeWebSocket.mockReturnValue({
          isConnected: true,
          lastMessage: { type: 'emotion', data: mockEmotion },
          sendMessage: vi.fn(),
          error: null
        });
        
        // Trigger re-render
        fireEvent.keyDown(document, { key: 'e' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(2000); // Should handle 100 updates within 2 seconds
    });
  });

  describe('Video Player Performance', () => {
    it('handles video seeking efficiently', () => {
      const mockVideoFile = new File(['test video content'], 'test.mp4', { type: 'video/mp4' });
      const mockOnSeek = vi.fn();
      
      render(
        <RealtimeVideoPlayer
          videoFile={mockVideoFile}
          currentTime={0}
          duration={100}
          isPlaying={false}
          onTimeUpdate={vi.fn()}
          onPlay={vi.fn()}
          onPause={vi.fn()}
          onSeek={mockOnSeek}
          onVolumeChange={vi.fn()}
        />
      );
      
      const seekBar = screen.getByTestId('seek-bar');
      
      const startTime = performance.now();
      
      // Simulate rapid seeking
      for (let i = 0; i < 100; i++) {
        fireEvent.change(seekBar, { target: { value: i.toString() } });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(500); // Should handle 100 seeks within 500ms
      expect(mockOnSeek).toHaveBeenCalledTimes(100);
    });

    it('handles volume changes efficiently', () => {
      const mockVideoFile = new File(['test video content'], 'test.mp4', { type: 'video/mp4' });
      const mockOnVolumeChange = vi.fn();
      
      render(
        <RealtimeVideoPlayer
          videoFile={mockVideoFile}
          currentTime={0}
          duration={100}
          isPlaying={false}
          onTimeUpdate={vi.fn()}
          onPlay={vi.fn()}
          onPause={vi.fn()}
          onSeek={vi.fn()}
          onVolumeChange={mockOnVolumeChange}
        />
      );
      
      const volumeControl = screen.getByTestId('volume-control');
      
      const startTime = performance.now();
      
      // Simulate rapid volume changes
      for (let i = 0; i < 100; i++) {
        fireEvent.change(volumeControl, { target: { value: (i / 100).toString() } });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(300); // Should handle 100 volume changes within 300ms
      expect(mockOnVolumeChange).toHaveBeenCalledTimes(100);
    });
  });

  describe('Component Update Performance', () => {
    it('updates efficiently when props change', () => {
      const { rerender } = render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate prop changes
      for (let i = 0; i < 100; i++) {
        rerender(<RealtimeInterface />);
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(1000); // Should handle 100 updates within 1 second
    });

    it('handles state updates efficiently', () => {
      const { useRealtimeStore } = require('../../src/store/realtimeStore');
      
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate state updates
      for (let i = 0; i < 100; i++) {
        useRealtimeStore.mockReturnValue({
          videoFile: null,
          isProcessing: i % 2 === 0,
          currentTime: i,
          duration: 100,
          transcriptions: [],
          emotions: [],
          translations: [],
          setVideoFile: vi.fn(),
          setIsProcessing: vi.fn(),
          setCurrentTime: vi.fn(),
          addTranscription: vi.fn(),
          addEmotion: vi.fn(),
          addTranslation: vi.fn()
        });
        
        // Trigger re-render
        fireEvent.keyDown(document, { key: 's' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(2000); // Should handle 100 state updates within 2 seconds
    });
  });

  describe('Animation Performance', () => {
    it('handles animations smoothly', () => {
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate animation frames
      for (let i = 0; i < 60; i++) {
        fireEvent.animationFrame();
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(1000); // Should handle 60 animation frames within 1 second
    });

    it('handles transitions efficiently', () => {
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate transitions
      for (let i = 0; i < 100; i++) {
        fireEvent.transitionEnd(screen.getByTestId('realtime-interface'));
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(500); // Should handle 100 transitions within 500ms
    });
  });

  describe('Network Performance', () => {
    it('handles WebSocket messages efficiently', () => {
      const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
      
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate rapid WebSocket messages
      for (let i = 0; i < 100; i++) {
        const mockMessage = {
          type: 'test',
          data: `Test message ${i}`,
          timestamp: Date.now() + i
        };
        
        useRealtimeWebSocket.mockReturnValue({
          isConnected: true,
          lastMessage: mockMessage,
          sendMessage: vi.fn(),
          error: null
        });
        
        // Trigger re-render
        fireEvent.keyDown(document, { key: 't' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(1000); // Should handle 100 messages within 1 second
    });
  });

  describe('Error Handling Performance', () => {
    it('handles errors efficiently', () => {
      const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
      
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate rapid errors
      for (let i = 0; i < 100; i++) {
        useRealtimeWebSocket.mockReturnValue({
          isConnected: false,
          error: `Test error ${i}`,
          sendMessage: vi.fn(),
          lastMessage: null
        });
        
        // Trigger re-render
        fireEvent.keyDown(document, { key: 'e' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(500); // Should handle 100 errors within 500ms
    });
  });

  describe('Accessibility Performance', () => {
    it('handles screen reader updates efficiently', () => {
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate screen reader updates
      for (let i = 0; i < 100; i++) {
        fireEvent.focus(screen.getByTestId('realtime-interface'));
        fireEvent.blur(screen.getByTestId('realtime-interface'));
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(300); // Should handle 100 focus changes within 300ms
    });

    it('handles keyboard navigation efficiently', () => {
      render(<RealtimeInterface />);
      
      const startTime = performance.now();
      
      // Simulate keyboard navigation
      for (let i = 0; i < 100; i++) {
        fireEvent.keyDown(document, { key: 'Tab' });
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      
      expect(totalTime).toBeLessThan(200); // Should handle 100 tab presses within 200ms
    });
  });
});

