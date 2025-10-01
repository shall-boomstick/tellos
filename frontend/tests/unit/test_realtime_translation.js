/**
 * Unit tests for RealtimeTranslation component
 * Tests translation display and real-time updates
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealtimeTranslation } from '../../src/components/RealtimeTranslation';

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
    translations: [],
    currentLanguage: 'en',
    setCurrentLanguage: vi.fn(),
    addTranslation: vi.fn()
  })
}));

describe('RealtimeTranslation', () => {
  const defaultProps = {
    translations: [],
    currentLanguage: 'en',
    onLanguageChange: vi.fn(),
    onTranslationClick: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders translation component', () => {
    render(<RealtimeTranslation {...defaultProps} />);
    
    expect(screen.getByTestId('translation-display')).toBeInTheDocument();
  });

  it('displays no translations message when empty', () => {
    render(<RealtimeTranslation {...defaultProps} />);
    
    expect(screen.getByText('No translations available')).toBeInTheDocument();
  });

  it('displays translations when available', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      },
      {
        id: '2',
        text: 'How are you?',
        translation: '¿Cómo estás?',
        timestamp: 1234567891,
        confidence: 0.88,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    expect(screen.getByText('¿Cómo estás?')).toBeInTheDocument();
  });

  it('displays translation confidence scores', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('handles language selection', () => {
    const mockOnLanguageChange = vi.fn();
    
    render(
      <RealtimeTranslation 
        {...defaultProps} 
        onLanguageChange={mockOnLanguageChange}
      />
    );
    
    const languageSelect = screen.getByTestId('language-select');
    
    fireEvent.change(languageSelect, { target: { value: 'es' } });
    expect(mockOnLanguageChange).toHaveBeenCalledWith('es');
  });

  it('displays available languages', () => {
    render(<RealtimeTranslation {...defaultProps} />);
    
    const languageSelect = screen.getByTestId('language-select');
    
    expect(languageSelect).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('Spanish')).toBeInTheDocument();
    expect(screen.getByText('French')).toBeInTheDocument();
  });

  it('handles translation click events', () => {
    const mockOnTranslationClick = vi.fn();
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(
      <RealtimeTranslation 
        {...defaultProps} 
        translations={translations}
        onTranslationClick={mockOnTranslationClick}
      />
    );
    
    const translationItem = screen.getByTestId('translation-item-1');
    
    fireEvent.click(translationItem);
    expect(mockOnTranslationClick).toHaveBeenCalledWith(translations[0]);
  });

  it('displays translation timestamps', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('00:00:00')).toBeInTheDocument();
  });

  it('handles real-time translation updates', async () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    const mockTranslation = {
      id: '1',
      text: 'Hello world',
      translation: 'Hola mundo',
      timestamp: 1234567890,
      confidence: 0.95,
      language: 'es'
    };

    useRealtimeWebSocket.mockReturnValue({
      isConnected: true,
      lastMessage: { type: 'translation', data: mockTranslation },
      sendMessage: vi.fn(),
      error: null
    });

    render(<RealtimeTranslation {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    });
  });

  it('handles translation errors', () => {
    const { useRealtimeWebSocket } = require('../../src/services/realtimeWebSocket');
    
    useRealtimeWebSocket.mockReturnValue({
      isConnected: false,
      error: 'Translation service unavailable',
      sendMessage: vi.fn(),
      lastMessage: null
    });

    render(<RealtimeTranslation {...defaultProps} />);
    
    expect(screen.getByText('Translation service unavailable')).toBeInTheDocument();
  });

  it('displays translation source text', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('Hello world')).toBeInTheDocument();
  });

  it('handles translation filtering', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      },
      {
        id: '2',
        text: 'Good morning',
        translation: 'Buenos días',
        timestamp: 1234567891,
        confidence: 0.88,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const filterInput = screen.getByTestId('translation-filter');
    
    fireEvent.change(filterInput, { target: { value: 'Hello' } });
    
    expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    expect(screen.queryByText('Buenos días')).not.toBeInTheDocument();
  });

  it('handles translation sorting', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      },
      {
        id: '2',
        text: 'Good morning',
        translation: 'Buenos días',
        timestamp: 1234567891,
        confidence: 0.88,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const sortSelect = screen.getByTestId('translation-sort');
    
    fireEvent.change(sortSelect, { target: { value: 'confidence' } });
    
    // Check if translations are sorted by confidence
    const translationItems = screen.getAllByTestId(/translation-item-/);
    expect(translationItems[0]).toHaveAttribute('data-testid', 'translation-item-1');
  });

  it('handles translation export', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const exportButton = screen.getByTestId('export-translations');
    
    fireEvent.click(exportButton);
    
    // Check if export functionality is triggered
    expect(screen.getByText('Exporting translations...')).toBeInTheDocument();
  });

  it('handles translation clear', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const clearButton = screen.getByTestId('clear-translations');
    
    fireEvent.click(clearButton);
    
    expect(screen.getByText('No translations available')).toBeInTheDocument();
  });

  it('displays translation statistics', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      },
      {
        id: '2',
        text: 'Good morning',
        translation: 'Buenos días',
        timestamp: 1234567891,
        confidence: 0.88,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('2 translations')).toBeInTheDocument();
    expect(screen.getByText('91.5% avg confidence')).toBeInTheDocument();
  });

  it('handles translation playback', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const playButton = screen.getByTestId('play-translation');
    
    fireEvent.click(playButton);
    
    expect(screen.getByText('Playing translation...')).toBeInTheDocument();
  });

  it('handles translation pause', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const playButton = screen.getByTestId('play-translation');
    
    // Start playing
    fireEvent.click(playButton);
    
    // Pause
    fireEvent.click(playButton);
    
    expect(screen.getByText('Translation paused')).toBeInTheDocument();
  });

  it('handles translation repeat', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    const repeatButton = screen.getByTestId('repeat-translation');
    
    fireEvent.click(repeatButton);
    
    expect(screen.getByText('Repeating translation...')).toBeInTheDocument();
  });

  it('handles translation speed control', () => {
    render(<RealtimeTranslation {...defaultProps} />);
    
    const speedControl = screen.getByTestId('translation-speed');
    
    fireEvent.change(speedControl, { target: { value: '1.5' } });
    
    expect(screen.getByText('Speed: 1.5x')).toBeInTheDocument();
  });

  it('handles translation volume control', () => {
    render(<RealtimeTranslation {...defaultProps} />);
    
    const volumeControl = screen.getByTestId('translation-volume');
    
    fireEvent.change(volumeControl, { target: { value: '0.7' } });
    
    expect(screen.getByText('Volume: 70%')).toBeInTheDocument();
  });

  it('handles component unmounting', () => {
    const { unmount } = render(<RealtimeTranslation {...defaultProps} />);
    
    expect(() => unmount()).not.toThrow();
  });

  it('handles translation with special characters', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello, world! How are you?',
        translation: '¡Hola, mundo! ¿Cómo estás?',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('¡Hola, mundo! ¿Cómo estás?')).toBeInTheDocument();
  });

  it('handles translation with long text', () => {
    const longText = 'This is a very long text that tests the translation component\'s ability to handle large amounts of content.';
    const longTranslation = 'Este es un texto muy largo que prueba la capacidad del componente de traducción para manejar grandes cantidades de contenido.';
    
    const translations = [
      {
        id: '1',
        text: longText,
        translation: longTranslation,
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText(longTranslation)).toBeInTheDocument();
  });

  it('handles translation with multiple languages', () => {
    const translations = [
      {
        id: '1',
        text: 'Hello world',
        translation: 'Hola mundo',
        timestamp: 1234567890,
        confidence: 0.95,
        language: 'es'
      },
      {
        id: '2',
        text: 'Hello world',
        translation: 'Bonjour le monde',
        timestamp: 1234567891,
        confidence: 0.88,
        language: 'fr'
      }
    ];

    render(<RealtimeTranslation {...defaultProps} translations={translations} />);
    
    expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    expect(screen.getByText('Bonjour le monde')).toBeInTheDocument();
  });
});

