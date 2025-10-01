/**
 * Test real-time emotion gauge component.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RealtimeEmotionGauge from '../src/components/RealtimeEmotionGauge';

describe('RealtimeEmotionGauge', () => {
  const mockProps = {
    emotion: 'happy',
    intensity: 0.8,
    confidence: 0.9,
    timestamp: 1234567890,
    onEmotionChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders emotion gauge component', () => {
    render(<RealtimeEmotionGauge {...mockProps} />);
    expect(screen.getByTestId('emotion-gauge')).toBeInTheDocument();
  });

  test('displays current emotion', () => {
    render(<RealtimeEmotionGauge {...mockProps} />);
    
    expect(screen.getByText('Happy')).toBeInTheDocument();
  });

  test('displays emotion intensity on scale', () => {
    render(<RealtimeEmotionGauge {...mockProps} />);
    
    const intensityBar = screen.getByTestId('intensity-bar');
    expect(intensityBar).toHaveStyle('width: 80%');
  });

  test('displays confidence level', () => {
    render(<RealtimeEmotionGauge {...mockProps} />);
    
    expect(screen.getByText('90%')).toBeInTheDocument();
  });

  test('handles different emotion types', () => {
    const emotions = ['happy', 'sad', 'angry', 'neutral', 'excited'];
    
    emotions.forEach(emotion => {
      const { unmount } = render(
        <RealtimeEmotionGauge {...mockProps} emotion={emotion} />
      );
      
      expect(screen.getByText(emotion.charAt(0).toUpperCase() + emotion.slice(1))).toBeInTheDocument();
      unmount();
    });
  });

  test('handles intensity changes', async () => {
    const { rerender } = render(<RealtimeEmotionGauge {...mockProps} />);
    
    const newProps = { ...mockProps, intensity: 0.5 };
    rerender(<RealtimeEmotionGauge {...newProps} />);
    
    await waitFor(() => {
      const intensityBar = screen.getByTestId('intensity-bar');
      expect(intensityBar).toHaveStyle('width: 50%');
    });
  });

  test('handles emotion transitions', async () => {
    const { rerender } = render(<RealtimeEmotionGauge {...mockProps} />);
    
    const newProps = { ...mockProps, emotion: 'sad', intensity: 0.6 };
    rerender(<RealtimeEmotionGauge {...newProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Sad')).toBeInTheDocument();
      const intensityBar = screen.getByTestId('intensity-bar');
      expect(intensityBar).toHaveStyle('width: 60%');
    });
  });

  test('handles low confidence emotions', () => {
    const lowConfidenceProps = { ...mockProps, confidence: 0.3 };
    render(<RealtimeEmotionGauge {...lowConfidenceProps} />);
    
    // Should show low confidence indicator
    expect(screen.getByTestId('low-confidence')).toBeInTheDocument();
  });

  test('handles emotion history', () => {
    const historyProps = {
      ...mockProps,
      emotionHistory: [
        { emotion: 'happy', intensity: 0.8, timestamp: 1234567890 },
        { emotion: 'sad', intensity: 0.6, timestamp: 1234567891 },
        { emotion: 'neutral', intensity: 0.4, timestamp: 1234567892 },
      ],
    };
    
    render(<RealtimeEmotionGauge {...historyProps} />);
    
    // Should display emotion history
    expect(screen.getByTestId('emotion-history')).toBeInTheDocument();
  });

  test('handles real-time updates', async () => {
    const { rerender } = render(<RealtimeEmotionGauge {...mockProps} />);
    
    const newProps = { ...mockProps, emotion: 'excited', intensity: 0.9 };
    rerender(<RealtimeEmotionGauge {...newProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Excited')).toBeInTheDocument();
    });
  });

  test('handles emotion smoothing', () => {
    const smoothingProps = {
      ...mockProps,
      smoothed: true,
      rawEmotion: 'happy',
      rawIntensity: 0.9,
    };
    
    render(<RealtimeEmotionGauge {...smoothingProps} />);
    
    // Should show smoothed emotion
    expect(screen.getByText('Happy')).toBeInTheDocument();
    expect(screen.getByTestId('smoothed-indicator')).toBeInTheDocument();
  });

  test('handles emotion categories', () => {
    const categoryProps = {
      ...mockProps,
      emotionCategory: 'positive',
      emotions: {
        happy: 0.6,
        excited: 0.3,
        sad: 0.1,
      },
    };
    
    render(<RealtimeEmotionGauge {...categoryProps} />);
    
    // Should show emotion breakdown
    expect(screen.getByTestId('emotion-breakdown')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    render(<RealtimeEmotionGauge {...mockProps} loading={true} />);
    
    expect(screen.getByText('Analyzing emotions...')).toBeInTheDocument();
  });

  test('handles error state', () => {
    render(<RealtimeEmotionGauge {...mockProps} error="Emotion analysis failed" />);
    
    expect(screen.getByText('Emotion analysis error')).toBeInTheDocument();
  });

  test('handles custom emotion colors', () => {
    const customColors = {
      happy: '#FFD700',
      sad: '#4169E1',
      angry: '#FF4500',
    };
    
    render(<RealtimeEmotionGauge {...mockProps} customColors={customColors} />);
    
    const emotionDisplay = screen.getByTestId('emotion-display');
    expect(emotionDisplay).toHaveStyle('color: #FFD700');
  });

  test('handles emotion intensity animation', () => {
    render(<RealtimeEmotionGauge {...mockProps} animated={true} />);
    
    const intensityBar = screen.getByTestId('intensity-bar');
    expect(intensityBar).toHaveClass('animated');
  });
});



