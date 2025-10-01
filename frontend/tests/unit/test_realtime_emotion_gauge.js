/**
 * Unit tests for RealtimeEmotionGauge component
 * Tests emotion display and real-time updates
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
    emotions: [],
    addEmotion: vi.fn()
  })
}));

describe('RealtimeEmotionGauge', () => {
  const defaultProps = {
    emotions: [],
    onEmotionClick: vi.fn(),
    onChartToggle: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders emotion gauge component', () => {
    render(<RealtimeEmotionGauge {...defaultProps} />);
    
    expect(screen.getByTestId('emotion-gauge')).toBeInTheDocument();
  });

  it('displays no emotions message when empty', () => {
    render(<RealtimeEmotionGauge {...defaultProps} />);
    
    expect(screen.getByText('No emotions detected')).toBeInTheDocument();
  });

  it('displays emotions when available', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 },
          { emotion: 'joy', confidence: 0.7 },
          { emotion: 'neutral', confidence: 0.2 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Happy')).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('displays emotion confidence scores', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 },
          { emotion: 'joy', confidence: 0.7 },
          { emotion: 'neutral', confidence: 0.2 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('80%')).toBeInTheDocument();
    expect(screen.getByText('70%')).toBeInTheDocument();
    expect(screen.getByText('20%')).toBeInTheDocument();
  });

  it('handles emotion click events', () => {
    const mockOnEmotionClick = vi.fn();
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(
      <RealtimeEmotionGauge 
        {...defaultProps} 
        emotions={emotions}
        onEmotionClick={mockOnEmotionClick}
      />
    );
    
    const emotionItem = screen.getByTestId('emotion-item-1');
    
    fireEvent.click(emotionItem);
    expect(mockOnEmotionClick).toHaveBeenCalledWith(emotions[0]);
  });

  it('displays emotion timestamps', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('00:00:00')).toBeInTheDocument();
  });

  it('handles real-time emotion updates', async () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    const mockEmotion = {
      id: '1',
      timestamp: 1234567890,
      emotions: [
        { emotion: 'happy', confidence: 0.8 }
      ],
      dominant_emotion: 'happy',
      confidence: 0.8
    };

    useRealtimeWebSocket.mockReturnValue({
      isConnected: true,
      lastMessage: { type: 'emotion', data: mockEmotion },
      sendMessage: vi.fn(),
      error: null
    });

    render(<RealtimeEmotionGauge {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Happy')).toBeInTheDocument();
    });
  });

  it('handles emotion analysis errors', () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    
    useRealtimeWebSocket.mockReturnValue({
      isConnected: false,
      error: 'Emotion analysis service unavailable',
      sendMessage: vi.fn(),
      lastMessage: null
    });

    render(<RealtimeEmotionGauge {...defaultProps} />);
    
    expect(screen.getByText('Emotion analysis service unavailable')).toBeInTheDocument();
  });

  it('displays emotion chart when enabled', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} showChart={true} />);
    
    expect(screen.getByTestId('emotion-chart')).toBeInTheDocument();
  });

  it('handles chart toggle', () => {
    const mockOnChartToggle = vi.fn();
    
    render(
      <RealtimeEmotionGauge 
        {...defaultProps} 
        onChartToggle={mockOnChartToggle}
      />
    );
    
    const chartToggle = screen.getByTestId('chart-toggle');
    
    fireEvent.click(chartToggle);
    expect(mockOnChartToggle).toHaveBeenCalled();
  });

  it('displays emotion statistics', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      },
      {
        id: '2',
        timestamp: 1234567891,
        emotions: [
          { emotion: 'sad', confidence: 0.7 }
        ],
        dominant_emotion: 'sad',
        confidence: 0.7
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('2 emotions detected')).toBeInTheDocument();
    expect(screen.getByText('75% avg confidence')).toBeInTheDocument();
  });

  it('handles emotion filtering', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      },
      {
        id: '2',
        timestamp: 1234567891,
        emotions: [
          { emotion: 'sad', confidence: 0.7 }
        ],
        dominant_emotion: 'sad',
        confidence: 0.7
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const filterSelect = screen.getByTestId('emotion-filter');
    
    fireEvent.change(filterSelect, { target: { value: 'happy' } });
    
    expect(screen.getByText('Happy')).toBeInTheDocument();
    expect(screen.queryByText('Sad')).not.toBeInTheDocument();
  });

  it('handles emotion sorting', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      },
      {
        id: '2',
        timestamp: 1234567891,
        emotions: [
          { emotion: 'sad', confidence: 0.7 }
        ],
        dominant_emotion: 'sad',
        confidence: 0.7
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const sortSelect = screen.getByTestId('emotion-sort');
    
    fireEvent.change(sortSelect, { target: { value: 'confidence' } });
    
    // Check if emotions are sorted by confidence
    const emotionItems = screen.getAllByTestId(/emotion-item-/);
    expect(emotionItems[0]).toHaveAttribute('data-testid', 'emotion-item-1');
  });

  it('handles emotion export', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const exportButton = screen.getByTestId('export-emotions');
    
    fireEvent.click(exportButton);
    
    expect(screen.getByText('Exporting emotions...')).toBeInTheDocument();
  });

  it('handles emotion clear', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const clearButton = screen.getByTestId('clear-emotions');
    
    fireEvent.click(clearButton);
    
    expect(screen.getByText('No emotions detected')).toBeInTheDocument();
  });

  it('displays emotion trends', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      },
      {
        id: '2',
        timestamp: 1234567891,
        emotions: [
          { emotion: 'happy', confidence: 0.9 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.9
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Trending: Happy')).toBeInTheDocument();
  });

  it('handles emotion analysis toggle', () => {
    render(<RealtimeEmotionGauge {...defaultProps} />);
    
    const toggleButton = screen.getByTestId('analysis-toggle');
    
    fireEvent.click(toggleButton);
    
    expect(screen.getByText('Analysis paused')).toBeInTheDocument();
  });

  it('displays emotion confidence indicators', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const confidenceBar = screen.getByTestId('confidence-bar-1');
    expect(confidenceBar).toHaveStyle('width: 80%');
  });

  it('handles emotion color coding', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const emotionItem = screen.getByTestId('emotion-item-1');
    expect(emotionItem).toHaveClass('emotion-happy');
  });

  it('handles emotion animation', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    const emotionItem = screen.getByTestId('emotion-item-1');
    expect(emotionItem).toHaveClass('emotion-animated');
  });

  it('handles component unmounting', () => {
    const { unmount } = render(<RealtimeEmotionGauge {...defaultProps} />);
    
    expect(() => unmount()).not.toThrow();
  });

  it('handles emotion with multiple emotions', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 },
          { emotion: 'joy', confidence: 0.7 },
          { emotion: 'excitement', confidence: 0.6 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Happy')).toBeInTheDocument();
    expect(screen.getByText('Joy')).toBeInTheDocument();
    expect(screen.getByText('Excitement')).toBeInTheDocument();
  });

  it('handles emotion with low confidence', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.3 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.3
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Low confidence')).toBeInTheDocument();
  });

  it('handles emotion with high confidence', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.95 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.95
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('High confidence')).toBeInTheDocument();
  });

  it('handles emotion with no face detected', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [],
        dominant_emotion: null,
        confidence: 0,
        face_detected: false
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('No face detected')).toBeInTheDocument();
  });

  it('handles emotion with face detected', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8,
        face_detected: true
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Face detected')).toBeInTheDocument();
  });

  it('handles emotion with bounding box', () => {
    const emotions = [
      {
        id: '1',
        timestamp: 1234567890,
        emotions: [
          { emotion: 'happy', confidence: 0.8 }
        ],
        dominant_emotion: 'happy',
        confidence: 0.8,
        bounding_box: [100, 100, 200, 200]
      }
    ];

    render(<RealtimeEmotionGauge {...defaultProps} emotions={emotions} />);
    
    expect(screen.getByText('Face position: (100, 100)')).toBeInTheDocument();
  });
});

