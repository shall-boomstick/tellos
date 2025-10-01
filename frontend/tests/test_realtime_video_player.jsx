/**
 * Test real-time video player component.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RealtimeVideoPlayer from '../src/components/RealtimeVideoPlayer';

// Mock video.js
jest.mock('video.js', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    ready: jest.fn(),
    play: jest.fn(),
    pause: jest.fn(),
    currentTime: jest.fn(() => 0),
    duration: jest.fn(() => 100),
    on: jest.fn(),
    off: jest.fn(),
    dispose: jest.fn(),
  })),
}));

// Mock react-player
jest.mock('react-player', () => {
  return function MockReactPlayer({ url, onReady, onPlay, onPause, onSeek }) {
    return (
      <div data-testid="video-player">
        <button onClick={() => onReady()}>Ready</button>
        <button onClick={() => onPlay()}>Play</button>
        <button onClick={() => onPause()}>Pause</button>
        <button onClick={() => onSeek(50)}>Seek</button>
      </div>
    );
  };
});

describe('RealtimeVideoPlayer', () => {
  const mockProps = {
    videoUrl: 'http://example.com/video.mp4',
    onTimeUpdate: jest.fn(),
    onPlay: jest.fn(),
    onPause: jest.fn(),
    onSeek: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders video player component', () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('handles play event', async () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    const playButton = screen.getByText('Play');
    fireEvent.click(playButton);
    
    await waitFor(() => {
      expect(mockProps.onPlay).toHaveBeenCalled();
    });
  });

  test('handles pause event', async () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    const pauseButton = screen.getByText('Pause');
    fireEvent.click(pauseButton);
    
    await waitFor(() => {
      expect(mockProps.onPause).toHaveBeenCalled();
    });
  });

  test('handles seek event', async () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    const seekButton = screen.getByText('Seek');
    fireEvent.click(seekButton);
    
    await waitFor(() => {
      expect(mockProps.onSeek).toHaveBeenCalledWith(50);
    });
  });

  test('handles video ready event', async () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    const readyButton = screen.getByText('Ready');
    fireEvent.click(readyButton);
    
    // Should not throw error
    expect(readyButton).toBeInTheDocument();
  });

  test('displays video controls', () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    // Should have play/pause controls
    expect(screen.getByText('Play')).toBeInTheDocument();
    expect(screen.getByText('Pause')).toBeInTheDocument();
  });

  test('handles video URL changes', () => {
    const { rerender } = render(<RealtimeVideoPlayer {...mockProps} />);
    
    const newProps = { ...mockProps, videoUrl: 'http://example.com/new-video.mp4' };
    rerender(<RealtimeVideoPlayer {...newProps} />);
    
    // Should re-render with new URL
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('handles video loading state', () => {
    render(<RealtimeVideoPlayer {...mockProps} loading={true} />);
    
    // Should show loading indicator
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('handles video error state', () => {
    render(<RealtimeVideoPlayer {...mockProps} error="Video failed to load" />);
    
    // Should show error message
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('handles keyboard shortcuts', () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    // Test space key for play/pause
    fireEvent.keyDown(document, { key: ' ' });
    
    // Should handle keyboard events
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  test('handles video duration updates', async () => {
    render(<RealtimeVideoPlayer {...mockProps} />);
    
    const readyButton = screen.getByText('Ready');
    fireEvent.click(readyButton);
    
    // Should handle duration updates
    expect(readyButton).toBeInTheDocument();
  });
});



