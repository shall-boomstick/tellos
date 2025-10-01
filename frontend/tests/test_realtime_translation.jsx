/**
 * Test real-time translation display component.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RealtimeTranslation from '../src/components/RealtimeTranslation';

describe('RealtimeTranslation', () => {
  const mockProps = {
    translations: [
      { text: 'Hello world', timestamp: 0, confidence: 0.95 },
      { text: 'How are you?', timestamp: 2, confidence: 0.88 },
    ],
    currentTime: 1.5,
    onWordClick: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders translation component', () => {
    render(<RealtimeTranslation {...mockProps} />);
    expect(screen.getByTestId('translation-display')).toBeInTheDocument();
  });

  test('displays translation text', () => {
    render(<RealtimeTranslation {...mockProps} />);
    
    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByText('How are you?')).toBeInTheDocument();
  });

  test('highlights current translation based on timestamp', () => {
    render(<RealtimeTranslation {...mockProps} />);
    
    // Should highlight the translation that matches current time
    const currentTranslation = screen.getByText('Hello world');
    expect(currentTranslation).toHaveClass('current');
  });

  test('handles word click events', async () => {
    render(<RealtimeTranslation {...mockProps} />);
    
    const word = screen.getByText('Hello');
    fireEvent.click(word);
    
    await waitFor(() => {
      expect(mockProps.onWordClick).toHaveBeenCalledWith('Hello', 0);
    });
  });

  test('displays confidence indicators', () => {
    render(<RealtimeTranslation {...mockProps} />);
    
    // Should show confidence indicators
    const confidenceElements = screen.getAllByTestId('confidence-indicator');
    expect(confidenceElements).toHaveLength(2);
  });

  test('handles empty translations', () => {
    const emptyProps = { ...mockProps, translations: [] };
    render(<RealtimeTranslation {...emptyProps} />);
    
    expect(screen.getByText('No translations available')).toBeInTheDocument();
  });

  test('handles scrolling for long translations', () => {
    const longTranslations = Array.from({ length: 20 }, (_, i) => ({
      text: `Translation ${i}`,
      timestamp: i,
      confidence: 0.9,
    }));
    
    render(<RealtimeTranslation {...mockProps} translations={longTranslations} />);
    
    // Should have scrollable container
    const scrollContainer = screen.getByTestId('translation-scroll');
    expect(scrollContainer).toHaveClass('scrollable');
  });

  test('handles real-time updates', async () => {
    const { rerender } = render(<RealtimeTranslation {...mockProps} />);
    
    const newTranslations = [
      ...mockProps.translations,
      { text: 'New translation', timestamp: 5, confidence: 0.92 },
    ];
    
    rerender(<RealtimeTranslation {...mockProps} translations={newTranslations} />);
    
    await waitFor(() => {
      expect(screen.getByText('New translation')).toBeInTheDocument();
    });
  });

  test('handles translation errors', () => {
    render(<RealtimeTranslation {...mockProps} error="Translation failed" />);
    
    expect(screen.getByText('Translation error: Translation failed')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    render(<RealtimeTranslation {...mockProps} loading={true} />);
    
    expect(screen.getByText('Loading translations...')).toBeInTheDocument();
  });

  test('handles word-level timing', () => {
    const wordTimingProps = {
      ...mockProps,
      translations: [
        {
          text: 'Hello world',
          timestamp: 0,
          confidence: 0.95,
          words: [
            { word: 'Hello', start: 0, end: 0.5 },
            { word: 'world', start: 0.5, end: 1.0 },
          ],
        },
      ],
    };
    
    render(<RealtimeTranslation {...wordTimingProps} />);
    
    // Should display words with timing
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('world')).toBeInTheDocument();
  });

  test('handles language detection', () => {
    render(<RealtimeTranslation {...mockProps} detectedLanguage="ar" />);
    
    expect(screen.getByText('Detected language: Arabic')).toBeInTheDocument();
  });

  test('handles translation quality indicators', () => {
    render(<RealtimeTranslation {...mockProps} />);
    
    // Should show quality indicators for each translation
    const qualityIndicators = screen.getAllByTestId('quality-indicator');
    expect(qualityIndicators).toHaveLength(2);
  });
});



