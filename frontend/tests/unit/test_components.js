/**
 * Unit tests for all frontend components in SawtFeel application.
 * Tests component rendering, props handling, user interactions, and state management.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { jest } from '@jest/globals';

// Import components to test
import FileUpload from '../../src/components/FileUpload';
import AudioPlayer from '../../src/components/AudioPlayer';
import EmotionGauge from '../../src/components/EmotionGauge';
import Transcript from '../../src/components/Transcript';
import ThemeToggle from '../../src/components/ThemeToggle';

// Mock services
jest.mock('../../src/services/api', () => ({
  uploadAPI: {
    uploadFile: jest.fn()
  }
}));

jest.mock('../../src/services/websocket', () => ({
  connectProcessing: jest.fn(),
  connectPlayback: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn()
}));

describe('FileUpload Component', () => {
  const mockOnFileSelect = jest.fn();
  const defaultProps = {
    onFileSelect: mockOnFileSelect,
    isUploading: false,
    error: null
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders file upload area correctly', () => {
    render(<FileUpload {...defaultProps} />);
    
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
    expect(screen.getByText(/choose file/i)).toBeInTheDocument();
    expect(screen.getByText(/mp4, avi, mov, wav, mp3/i)).toBeInTheDocument();
  });

  test('handles file selection via input', async () => {
    const user = userEvent.setup();
    render(<FileUpload {...defaultProps} />);
    
    const fileInput = screen.getByRole('button', { name: /choose file/i });
    const testFile = new File(['test content'], 'test.mp4', { type: 'video/mp4' });
    
    await user.click(fileInput);
    
    // Simulate file selection
    const hiddenInput = document.querySelector('input[type="file"]');
    await user.upload(hiddenInput, testFile);
    
    expect(mockOnFileSelect).toHaveBeenCalledWith(testFile);
  });

  test('handles drag and drop file upload', async () => {
    render(<FileUpload {...defaultProps} />);
    
    const dropZone = screen.getByRole('button', { name: /drag and drop/i });
    const testFile = new File(['test content'], 'test.mp4', { type: 'video/mp4' });
    
    // Simulate drag enter
    fireEvent.dragEnter(dropZone, {
      dataTransfer: { items: [{ kind: 'file', type: 'video/mp4' }] }
    });
    
    expect(dropZone).toHaveClass('drag-over');
    
    // Simulate drop
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [testFile] }
    });
    
    expect(mockOnFileSelect).toHaveBeenCalledWith(testFile);
  });

  test('validates file type and size', async () => {
    const user = userEvent.setup();
    render(<FileUpload {...defaultProps} />);
    
    const hiddenInput = document.querySelector('input[type="file"]');
    
    // Test invalid file type
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    await user.upload(hiddenInput, invalidFile);
    
    expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument();
    expect(mockOnFileSelect).not.toHaveBeenCalled();
    
    // Test file too large (mock 200MB file)
    const largeFile = new File(['x'.repeat(200 * 1024 * 1024)], 'large.mp4', { type: 'video/mp4' });
    Object.defineProperty(largeFile, 'size', { value: 200 * 1024 * 1024 });
    
    await user.upload(hiddenInput, largeFile);
    
    expect(screen.getByText(/file too large/i)).toBeInTheDocument();
  });

  test('shows uploading state correctly', () => {
    render(<FileUpload {...defaultProps} isUploading={true} />);
    
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays error message', () => {
    const errorMessage = 'Upload failed. Please try again.';
    render(<FileUpload {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  test('clears error on new file selection', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<FileUpload {...defaultProps} error="Previous error" />);
    
    expect(screen.getByText('Previous error')).toBeInTheDocument();
    
    // Select new file
    const hiddenInput = document.querySelector('input[type="file"]');
    const testFile = new File(['test'], 'test.mp4', { type: 'video/mp4' });
    
    await user.upload(hiddenInput, testFile);
    
    // Re-render without error
    rerender(<FileUpload {...defaultProps} error={null} />);
    
    expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
  });
});

describe('AudioPlayer Component', () => {
  const mockOnTimeUpdate = jest.fn();
  const mockOnPlay = jest.fn();
  const mockOnPause = jest.fn();
  
  const defaultProps = {
    audioUrl: 'http://localhost:8000/api/files/test-123/audio',
    duration: 30.5,
    onTimeUpdate: mockOnTimeUpdate,
    onPlay: mockOnPlay,
    onPause: mockOnPause
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock HTMLAudioElement
    window.HTMLAudioElement.prototype.play = jest.fn(() => Promise.resolve());
    window.HTMLAudioElement.prototype.pause = jest.fn();
    window.HTMLAudioElement.prototype.load = jest.fn();
  });

  test('renders audio player controls correctly', () => {
    render(<AudioPlayer {...defaultProps} />);
    
    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: /progress/i })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: /volume/i })).toBeInTheDocument();
    expect(screen.getByText('0:00')).toBeInTheDocument(); // Current time
    expect(screen.getByText('0:30')).toBeInTheDocument(); // Duration
  });

  test('handles play/pause button clicks', async () => {
    const user = userEvent.setup();
    render(<AudioPlayer {...defaultProps} />);
    
    const playButton = screen.getByRole('button', { name: /play/i });
    
    // Click play
    await user.click(playButton);
    
    expect(mockOnPlay).toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
    
    // Click pause
    const pauseButton = screen.getByRole('button', { name: /pause/i });
    await user.click(pauseButton);
    
    expect(mockOnPause).toHaveBeenCalled();
  });

  test('handles progress bar scrubbing', async () => {
    const user = userEvent.setup();
    render(<AudioPlayer {...defaultProps} />);
    
    const progressSlider = screen.getByRole('slider', { name: /progress/i });
    
    // Simulate scrubbing to 50% (15.25 seconds)
    fireEvent.change(progressSlider, { target: { value: 15.25 } });
    
    expect(mockOnTimeUpdate).toHaveBeenCalledWith(15.25);
  });

  test('handles volume control', async () => {
    const user = userEvent.setup();
    render(<AudioPlayer {...defaultProps} />);
    
    const volumeSlider = screen.getByRole('slider', { name: /volume/i });
    
    // Change volume to 70%
    fireEvent.change(volumeSlider, { target: { value: 0.7 } });
    
    // Audio element volume should be updated
    const audioElement = document.querySelector('audio');
    expect(audioElement.volume).toBe(0.7);
  });

  test('formats time display correctly', () => {
    render(<AudioPlayer {...defaultProps} currentTime={125.5} />);
    
    expect(screen.getByText('2:05')).toBeInTheDocument(); // Current time
    expect(screen.getByText('0:30')).toBeInTheDocument(); // Duration
  });

  test('handles audio loading errors', () => {
    render(<AudioPlayer {...defaultProps} audioUrl="invalid-url" />);
    
    const audioElement = document.querySelector('audio');
    fireEvent.error(audioElement);
    
    expect(screen.getByText(/error loading audio/i)).toBeInTheDocument();
  });

  test('updates progress during playback', () => {
    render(<AudioPlayer {...defaultProps} />);
    
    const audioElement = document.querySelector('audio');
    
    // Simulate time update
    Object.defineProperty(audioElement, 'currentTime', { value: 10.5, writable: true });
    fireEvent.timeUpdate(audioElement);
    
    expect(mockOnTimeUpdate).toHaveBeenCalledWith(10.5);
  });
});

describe('EmotionGauge Component', () => {
  const defaultProps = {
    currentEmotion: 'joy',
    confidence: 0.85,
    emotionHistory: [
      { start_time: 0, end_time: 2, combined_emotion: 'joy', combined_confidence: 0.8 },
      { start_time: 2, end_time: 4, combined_emotion: 'neutral', combined_confidence: 0.7 },
      { start_time: 4, end_time: 6, combined_emotion: 'sadness', combined_confidence: 0.75 }
    ]
  };

  test('renders emotion gauge correctly', () => {
    render(<EmotionGauge {...defaultProps} />);
    
    expect(screen.getByText('Joy')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays emotion history timeline', () => {
    render(<EmotionGauge {...defaultProps} />);
    
    const timeline = screen.getByTestId('emotion-timeline');
    expect(timeline).toBeInTheDocument();
    
    // Check for emotion segments in timeline
    expect(screen.getByTitle('Joy (0s-2s)')).toBeInTheDocument();
    expect(screen.getByTitle('Neutral (2s-4s)')).toBeInTheDocument();
    expect(screen.getByTitle('Sadness (4s-6s)')).toBeInTheDocument();
  });

  test('handles different emotion types', () => {
    const emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'neutral'];
    
    emotions.forEach(emotion => {
      const { rerender } = render(
        <EmotionGauge {...defaultProps} currentEmotion={emotion} />
      );
      
      expect(screen.getByText(emotion.charAt(0).toUpperCase() + emotion.slice(1))).toBeInTheDocument();
      
      // Check emotion-specific styling
      const gauge = screen.getByRole('progressbar');
      expect(gauge).toHaveClass(`emotion-${emotion}`);
      
      rerender(<div />); // Clear for next iteration
    });
  });

  test('handles low confidence scores', () => {
    render(<EmotionGauge {...defaultProps} confidence={0.3} />);
    
    expect(screen.getByText('30%')).toBeInTheDocument();
    expect(screen.getByText(/low confidence/i)).toBeInTheDocument();
  });

  test('handles empty emotion history', () => {
    render(<EmotionGauge {...defaultProps} emotionHistory={[]} />);
    
    expect(screen.getByText('Joy')).toBeInTheDocument();
    expect(screen.queryByTestId('emotion-timeline')).not.toBeInTheDocument();
  });

  test('updates in real-time', () => {
    const { rerender } = render(<EmotionGauge {...defaultProps} />);
    
    expect(screen.getByText('Joy')).toBeInTheDocument();
    
    // Update emotion
    rerender(<EmotionGauge {...defaultProps} currentEmotion="anger" confidence={0.92} />);
    
    expect(screen.getByText('Anger')).toBeInTheDocument();
    expect(screen.getByText('92%')).toBeInTheDocument();
  });
});

describe('Transcript Component', () => {
  const mockOnWordClick = jest.fn();
  
  const defaultProps = {
    transcript: 'مرحبا بك في تطبيق تحليل المشاعر',
    words: [
      { word: 'مرحبا', start_time: 0.0, end_time: 0.5, confidence: 0.95 },
      { word: 'بك', start_time: 0.5, end_time: 1.0, confidence: 0.92 },
      { word: 'في', start_time: 1.0, end_time: 1.3, confidence: 0.88 },
      { word: 'تطبيق', start_time: 1.3, end_time: 2.0, confidence: 0.90 },
      { word: 'تحليل', start_time: 2.0, end_time: 2.8, confidence: 0.87 },
      { word: 'المشاعر', start_time: 2.8, end_time: 3.5, confidence: 0.93 }
    ],
    currentTime: 1.5,
    isPlaying: true,
    onWordClick: mockOnWordClick
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders transcript text correctly', () => {
    render(<Transcript {...defaultProps} />);
    
    expect(screen.getByText('مرحبا بك في تطبيق تحليل المشاعر')).toBeInTheDocument();
    
    // Check individual words are rendered
    expect(screen.getByText('مرحبا')).toBeInTheDocument();
    expect(screen.getByText('بك')).toBeInTheDocument();
    expect(screen.getByText('في')).toBeInTheDocument();
  });

  test('highlights current word during playback', () => {
    render(<Transcript {...defaultProps} currentTime={1.5} />);
    
    // Word "في" should be highlighted (1.0-1.3s, current time 1.5s should highlight next word)
    const currentWord = screen.getByText('تطبيق');
    expect(currentWord).toHaveClass('current-word');
  });

  test('handles word clicks for seeking', async () => {
    const user = userEvent.setup();
    render(<Transcript {...defaultProps} />);
    
    const word = screen.getByText('تحليل');
    await user.click(word);
    
    expect(mockOnWordClick).toHaveBeenCalledWith(2.0); // Start time of "تحليل"
  });

  test('shows confidence scores on hover', async () => {
    const user = userEvent.setup();
    render(<Transcript {...defaultProps} />);
    
    const word = screen.getByText('مرحبا');
    await user.hover(word);
    
    await waitFor(() => {
      expect(screen.getByText(/95%/)).toBeInTheDocument();
    });
  });

  test('handles empty transcript', () => {
    render(<Transcript {...defaultProps} transcript="" words={[]} />);
    
    expect(screen.getByText(/no transcript available/i)).toBeInTheDocument();
  });

  test('handles paused state correctly', () => {
    render(<Transcript {...defaultProps} isPlaying={false} />);
    
    // Should not highlight any word when paused
    const words = screen.getAllByRole('button');
    words.forEach(word => {
      expect(word).not.toHaveClass('current-word');
    });
  });

  test('shows low confidence words differently', () => {
    const lowConfidenceProps = {
      ...defaultProps,
      words: [
        { word: 'unclear', start_time: 0.0, end_time: 0.5, confidence: 0.3 },
        { word: 'clear', start_time: 0.5, end_time: 1.0, confidence: 0.95 }
      ]
    };
    
    render(<Transcript {...lowConfidenceProps} />);
    
    const lowConfidenceWord = screen.getByText('unclear');
    const highConfidenceWord = screen.getByText('clear');
    
    expect(lowConfidenceWord).toHaveClass('low-confidence');
    expect(highConfidenceWord).not.toHaveClass('low-confidence');
  });

  test('supports RTL text direction for Arabic', () => {
    render(<Transcript {...defaultProps} />);
    
    const transcriptContainer = screen.getByRole('region');
    expect(transcriptContainer).toHaveAttribute('dir', 'rtl');
  });
});

describe('ThemeToggle Component', () => {
  const mockOnToggle = jest.fn();
  
  const defaultProps = {
    theme: 'light',
    onToggle: mockOnToggle
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders theme toggle button correctly', () => {
    render(<ThemeToggle {...defaultProps} />);
    
    expect(screen.getByRole('button', { name: /toggle theme/i })).toBeInTheDocument();
    expect(screen.getByText(/light/i)).toBeInTheDocument();
  });

  test('shows correct icon for light theme', () => {
    render(<ThemeToggle {...defaultProps} theme="light" />);
    
    expect(screen.getByText('🌙')).toBeInTheDocument(); // Moon icon for switching to dark
  });

  test('shows correct icon for dark theme', () => {
    render(<ThemeToggle {...defaultProps} theme="dark" />);
    
    expect(screen.getByText('☀️')).toBeInTheDocument(); // Sun icon for switching to light
  });

  test('handles theme toggle click', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle {...defaultProps} />);
    
    const toggleButton = screen.getByRole('button', { name: /toggle theme/i });
    await user.click(toggleButton);
    
    expect(mockOnToggle).toHaveBeenCalled();
  });

  test('has proper accessibility attributes', () => {
    render(<ThemeToggle {...defaultProps} />);
    
    const button = screen.getByRole('button', { name: /toggle theme/i });
    expect(button).toHaveAttribute('aria-label');
    expect(button).toHaveAttribute('title');
  });

  test('shows keyboard shortcut hint', () => {
    render(<ThemeToggle {...defaultProps} />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', expect.stringContaining('Ctrl+Shift+T'));
  });

  test('handles keyboard shortcut', () => {
    render(<ThemeToggle {...defaultProps} />);
    
    // Simulate Ctrl+Shift+T
    fireEvent.keyDown(document, {
      key: 'T',
      ctrlKey: true,
      shiftKey: true
    });
    
    expect(mockOnToggle).toHaveBeenCalled();
  });

  test('applies correct CSS classes', () => {
    const { rerender } = render(<ThemeToggle {...defaultProps} theme="light" />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('theme-toggle', 'light');
    
    rerender(<ThemeToggle {...defaultProps} theme="dark" />);
    expect(button).toHaveClass('theme-toggle', 'dark');
  });
});

// Integration tests for component interactions
describe('Component Integration', () => {
  test('FileUpload and Dashboard integration', async () => {
    const mockOnFileUploaded = jest.fn();
    const user = userEvent.setup();
    
    render(<FileUpload onFileSelect={mockOnFileUploaded} isUploading={false} error={null} />);
    
    const testFile = new File(['test content'], 'test.mp4', { type: 'video/mp4' });
    const hiddenInput = document.querySelector('input[type="file"]');
    
    await user.upload(hiddenInput, testFile);
    
    expect(mockOnFileUploaded).toHaveBeenCalledWith(testFile);
  });

  test('AudioPlayer and Transcript synchronization', () => {
    const mockOnTimeUpdate = jest.fn();
    const mockOnWordClick = jest.fn();
    
    const currentTime = 1.5;
    
    render(
      <div>
        <AudioPlayer
          audioUrl="test.mp3"
          duration={30}
          currentTime={currentTime}
          onTimeUpdate={mockOnTimeUpdate}
        />
        <Transcript
          transcript="مرحبا بك"
          words={[
            { word: 'مرحبا', start_time: 0.0, end_time: 1.0, confidence: 0.95 },
            { word: 'بك', start_time: 1.0, end_time: 2.0, confidence: 0.92 }
          ]}
          currentTime={currentTime}
          onWordClick={mockOnWordClick}
        />
      </div>
    );
    
    // Check that transcript highlights correct word
    expect(screen.getByText('بك')).toHaveClass('current-word');
  });

  test('EmotionGauge real-time updates', () => {
    const { rerender } = render(
      <EmotionGauge
        currentEmotion="neutral"
        confidence={0.5}
        emotionHistory={[]}
      />
    );
    
    expect(screen.getByText('Neutral')).toBeInTheDocument();
    
    // Simulate real-time emotion update
    rerender(
      <EmotionGauge
        currentEmotion="joy"
        confidence={0.85}
        emotionHistory={[
          { start_time: 0, end_time: 2, combined_emotion: 'joy', combined_confidence: 0.85 }
        ]}
      />
    );
    
    expect(screen.getByText('Joy')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });
});

// Performance tests
describe('Component Performance', () => {
  test('AudioPlayer handles frequent time updates efficiently', () => {
    const mockOnTimeUpdate = jest.fn();
    
    render(
      <AudioPlayer
        audioUrl="test.mp3"
        duration={30}
        onTimeUpdate={mockOnTimeUpdate}
      />
    );
    
    const audioElement = document.querySelector('audio');
    
    // Simulate rapid time updates (like during playback)
    for (let i = 0; i < 100; i++) {
      Object.defineProperty(audioElement, 'currentTime', { value: i / 10, writable: true });
      fireEvent.timeUpdate(audioElement);
    }
    
    // Should handle all updates without performance issues
    expect(mockOnTimeUpdate).toHaveBeenCalledTimes(100);
  });

  test('Transcript handles large word arrays efficiently', () => {
    const largeWordArray = Array.from({ length: 1000 }, (_, i) => ({
      word: `word${i}`,
      start_time: i * 0.5,
      end_time: (i + 1) * 0.5,
      confidence: 0.8 + Math.random() * 0.2
    }));
    
    const startTime = performance.now();
    
    render(
      <Transcript
        transcript={largeWordArray.map(w => w.word).join(' ')}
        words={largeWordArray}
        currentTime={250}
        onWordClick={jest.fn()}
      />
    );
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within reasonable time (< 100ms)
    expect(renderTime).toBeLessThan(100);
    
    // Should still highlight correct word
    expect(screen.getByText('word500')).toHaveClass('current-word');
  });
});

// Error boundary tests
describe('Error Handling', () => {
  test('components handle missing props gracefully', () => {
    // Test with minimal props
    expect(() => {
      render(<FileUpload onFileSelect={jest.fn()} />);
    }).not.toThrow();
    
    expect(() => {
      render(<AudioPlayer audioUrl="test.mp3" />);
    }).not.toThrow();
    
    expect(() => {
      render(<EmotionGauge currentEmotion="neutral" />);
    }).not.toThrow();
  });

  test('components handle invalid prop values gracefully', () => {
    expect(() => {
      render(<AudioPlayer audioUrl="" duration={-1} />);
    }).not.toThrow();
    
    expect(() => {
      render(<EmotionGauge currentEmotion="invalid" confidence={-1} />);
    }).not.toThrow();
    
    expect(() => {
      render(<Transcript transcript="" words={null} />);
    }).not.toThrow();
  });
});
