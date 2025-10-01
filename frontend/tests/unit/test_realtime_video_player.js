/**
 * Unit tests for RealtimeVideoPlayer component
 * Tests video player functionality and real-time synchronization
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealtimeVideoPlayer } from '../../src/components/RealtimeVideoPlayer';

// Mock dependencies
vi.mock('../../src/hooks/useRealtimeSync', () => ({
  useRealtimeSync: () => ({
    syncVideoWithData: vi.fn(),
    isSynced: true
  })
}));

vi.mock('../../src/services/realtimeWebSocket', () => ({
  useRealtimeWebSocket: () => ({
    isConnected: true,
    sendMessage: vi.fn(),
    lastMessage: null,
    error: null
  })
}));

describe('RealtimeVideoPlayer', () => {
  const mockVideoFile = new File(['test video content'], 'test.mp4', { type: 'video/mp4' });
  const defaultProps = {
    videoFile: mockVideoFile,
    currentTime: 0,
    duration: 100,
    isPlaying: false,
    onTimeUpdate: vi.fn(),
    onPlay: vi.fn(),
    onPause: vi.fn(),
    onSeek: vi.fn(),
    onVolumeChange: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders video player with correct props', () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    const videoElement = screen.getByTestId('video-player');
    expect(videoElement).toBeInTheDocument();
    expect(videoElement).toHaveAttribute('src', expect.stringContaining('blob:'));
  });

  it('displays video controls', () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    expect(screen.getByTestId('play-pause-button')).toBeInTheDocument();
    expect(screen.getByTestId('seek-bar')).toBeInTheDocument();
    expect(screen.getByTestId('volume-control')).toBeInTheDocument();
    expect(screen.getByTestId('time-display')).toBeInTheDocument();
  });

  it('handles play/pause functionality', () => {
    const mockOnPlay = vi.fn();
    const mockOnPause = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onPlay={mockOnPlay}
        onPause={mockOnPause}
      />
    );
    
    const playButton = screen.getByTestId('play-pause-button');
    
    // Test play
    fireEvent.click(playButton);
    expect(mockOnPlay).toHaveBeenCalled();
    
    // Test pause
    fireEvent.click(playButton);
    expect(mockOnPause).toHaveBeenCalled();
  });

  it('updates play button icon based on playing state', () => {
    const { rerender } = render(
      <RealtimeVideoPlayer {...defaultProps} isPlaying={false} />
    );
    
    expect(screen.getByTestId('play-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('pause-icon')).not.toBeInTheDocument();
    
    rerender(<RealtimeVideoPlayer {...defaultProps} isPlaying={true} />);
    
    expect(screen.getByTestId('pause-icon')).toBeInTheDocument();
    expect(screen.queryByTestId('play-icon')).not.toBeInTheDocument();
  });

  it('handles seeking functionality', () => {
    const mockOnSeek = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onSeek={mockOnSeek}
      />
    );
    
    const seekBar = screen.getByTestId('seek-bar');
    
    fireEvent.change(seekBar, { target: { value: '50' } });
    expect(mockOnSeek).toHaveBeenCalledWith(50);
  });

  it('displays current time and duration correctly', () => {
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        currentTime={30}
        duration={120}
      />
    );
    
    expect(screen.getByText('0:30 / 2:00')).toBeInTheDocument();
  });

  it('handles volume control', () => {
    const mockOnVolumeChange = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onVolumeChange={mockOnVolumeChange}
      />
    );
    
    const volumeControl = screen.getByTestId('volume-control');
    
    fireEvent.change(volumeControl, { target: { value: '0.5' } });
    expect(mockOnVolumeChange).toHaveBeenCalledWith(0.5);
  });

  it('handles keyboard shortcuts', () => {
    const mockOnPlay = vi.fn();
    const mockOnPause = vi.fn();
    const mockOnSeek = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onPlay={mockOnPlay}
        onPause={mockOnPause}
        onSeek={mockOnSeek}
      />
    );
    
    // Test spacebar for play/pause
    fireEvent.keyDown(document, { key: ' ' });
    expect(mockOnPlay).toHaveBeenCalled();
    
    // Test arrow keys for seeking
    fireEvent.keyDown(document, { key: 'ArrowLeft' });
    expect(mockOnSeek).toHaveBeenCalledWith(expect.any(Number));
    
    fireEvent.keyDown(document, { key: 'ArrowRight' });
    expect(mockOnSeek).toHaveBeenCalledWith(expect.any(Number));
  });

  it('handles fullscreen functionality', () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    const fullscreenButton = screen.getByTestId('fullscreen-button');
    
    // Mock fullscreen API
    const mockRequestFullscreen = vi.fn();
    Object.defineProperty(document.documentElement, 'requestFullscreen', {
      value: mockRequestFullscreen,
      writable: true
    });
    
    fireEvent.click(fullscreenButton);
    expect(mockRequestFullscreen).toHaveBeenCalled();
  });

  it('handles video loading states', async () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    const videoElement = screen.getByTestId('video-player');
    
    // Test loading state
    fireEvent.loadStart(videoElement);
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    
    // Test loaded state
    fireEvent.canPlay(videoElement);
    expect(screen.queryByTestId('loading-indicator')).not.toBeInTheDocument();
  });

  it('handles video errors', () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    const videoElement = screen.getByTestId('video-player');
    
    fireEvent.error(videoElement, { target: { error: { code: 4 } } });
    expect(screen.getByTestId('error-message')).toBeInTheDocument();
  });

  it('updates time display when currentTime changes', () => {
    const { rerender } = render(
      <RealtimeVideoPlayer {...defaultProps} currentTime={0} />
    );
    
    expect(screen.getByText('0:00 / 1:40')).toBeInTheDocument();
    
    rerender(<RealtimeVideoPlayer {...defaultProps} currentTime={30} />);
    
    expect(screen.getByText('0:30 / 1:40')).toBeInTheDocument();
  });

  it('handles video file changes', () => {
    const { rerender } = render(
      <RealtimeVideoPlayer {...defaultProps} videoFile={null} />
    );
    
    expect(screen.getByTestId('no-video-message')).toBeInTheDocument();
    
    rerender(<RealtimeVideoPlayer {...defaultProps} videoFile={mockVideoFile} />);
    
    expect(screen.queryByTestId('no-video-message')).not.toBeInTheDocument();
    expect(screen.getByTestId('video-player')).toBeInTheDocument();
  });

  it('handles real-time synchronization', () => {
    const { useRealtimeSync } = require('../../src/hooks/useRealtimeSync');
    const mockSyncVideoWithData = vi.fn();
    
    useRealtimeSync.mockReturnValue({
      syncVideoWithData: mockSyncVideoWithData,
      isSynced: true
    });
    
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    expect(mockSyncVideoWithData).toHaveBeenCalled();
  });

  it('displays sync status', () => {
    const { useRealtimeSync } = require('../../src/hooks/useRealtimeSync');
    
    useRealtimeSync.mockReturnValue({
      syncVideoWithData: vi.fn(),
      isSynced: false
    });
    
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    expect(screen.getByTestId('sync-status')).toBeInTheDocument();
    expect(screen.getByText('Syncing...')).toBeInTheDocument();
  });

  it('handles WebSocket connection status', () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    
    useRealtimeWebSocket.mockReturnValue({
      isConnected: false,
      error: 'Connection lost',
      sendMessage: vi.fn(),
      lastMessage: null
    });
    
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    expect(screen.getByTestId('connection-status')).toBeInTheDocument();
    expect(screen.getByText('Connection lost')).toBeInTheDocument();
  });

  it('handles video metadata loading', async () => {
    render(<RealtimeVideoPlayer {...defaultProps} />);
    
    const videoElement = screen.getByTestId('video-player');
    
    // Mock metadata loading
    Object.defineProperty(videoElement, 'duration', {
      value: 120,
      writable: true
    });
    
    fireEvent.loadedMetadata(videoElement);
    
    await waitFor(() => {
      expect(screen.getByText('0:00 / 2:00')).toBeInTheDocument();
    });
  });

  it('handles video seeking with keyboard', () => {
    const mockOnSeek = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onSeek={mockOnSeek}
        currentTime={30}
      />
    );
    
    // Test left arrow (seek backward)
    fireEvent.keyDown(document, { key: 'ArrowLeft' });
    expect(mockOnSeek).toHaveBeenCalledWith(20); // 30 - 10
    
    // Test right arrow (seek forward)
    fireEvent.keyDown(document, { key: 'ArrowRight' });
    expect(mockOnSeek).toHaveBeenCalledWith(40); // 30 + 10
  });

  it('handles volume control with keyboard', () => {
    const mockOnVolumeChange = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onVolumeChange={mockOnVolumeChange}
      />
    );
    
    // Test volume up
    fireEvent.keyDown(document, { key: 'ArrowUp' });
    expect(mockOnVolumeChange).toHaveBeenCalledWith(expect.any(Number));
    
    // Test volume down
    fireEvent.keyDown(document, { key: 'ArrowDown' });
    expect(mockOnVolumeChange).toHaveBeenCalledWith(expect.any(Number));
  });

  it('handles mute toggle', () => {
    const mockOnVolumeChange = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onVolumeChange={mockOnVolumeChange}
      />
    );
    
    const muteButton = screen.getByTestId('mute-button');
    
    fireEvent.click(muteButton);
    expect(mockOnVolumeChange).toHaveBeenCalledWith(0);
    
    fireEvent.click(muteButton);
    expect(mockOnVolumeChange).toHaveBeenCalledWith(1);
  });

  it('handles component cleanup', () => {
    const { unmount } = render(<RealtimeVideoPlayer {...defaultProps} />);
    
    // Should not throw errors when unmounting
    expect(() => unmount()).not.toThrow();
  });

  it('handles video progress updates', () => {
    const mockOnTimeUpdate = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onTimeUpdate={mockOnTimeUpdate}
      />
    );
    
    const videoElement = screen.getByTestId('video-player');
    
    fireEvent.timeUpdate(videoElement, { target: { currentTime: 30 } });
    expect(mockOnTimeUpdate).toHaveBeenCalledWith(30);
  });

  it('handles video ended event', () => {
    const mockOnPause = vi.fn();
    
    render(
      <RealtimeVideoPlayer 
        {...defaultProps} 
        onPause={mockOnPause}
      />
    );
    
    const videoElement = screen.getByTestId('video-player');
    
    fireEvent.ended(videoElement);
    expect(mockOnPause).toHaveBeenCalled();
  });
});

