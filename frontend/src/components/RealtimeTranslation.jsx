import React, { useEffect, useRef, useState } from 'react';
import { Card, Badge, Spinner } from 'react-bootstrap';

const RealtimeTranslation = ({
  transcriptData,
  currentTranscript,
  playbackState,
  isConnected
}) => {
  const transcriptRef = useRef(null);
  const [isScrolling, setIsScrolling] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to bottom when new transcript arrives
  useEffect(() => {
    if (transcriptRef.current && autoScroll && !isScrolling) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcriptData, autoScroll, isScrolling]);

  // Handle scroll events
  const handleScroll = () => {
    if (transcriptRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = transcriptRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setAutoScroll(isAtBottom);
    }
  };

  // Format confidence score
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'danger';
  };

  // Format confidence text
  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  // Get current transcript text for highlighting
  const getCurrentText = () => {
    if (!currentTranscript) return '';
    return currentTranscript.text || '';
  };

  // Get transcript segments for current time
  const getCurrentSegments = () => {
    try {
      if (!transcriptData || !Array.isArray(transcriptData) || !transcriptData.length) return [];
      
      const currentTime = playbackState.currentTime || 0;
      return transcriptData.filter(segment => 
        segment && 
        typeof segment === 'object' &&
        typeof segment.start_time === 'number' && 
        typeof segment.end_time === 'number' &&
        segment.start_time <= currentTime && 
        segment.end_time >= currentTime
      );
    } catch (error) {
      console.error('Error in getCurrentSegments:', error);
      return [];
    }
  };

  // Highlight current words
  const highlightCurrentWords = (text, words) => {
    if (!words || !words.length) return text;
    
    let highlightedText = text;
    words.forEach(word => {
      const regex = new RegExp(`\\b${word.word}\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, `<mark class="current-word">${word.word}</mark>`);
    });
    
    return highlightedText;
  };

  // Comprehensive error protection
  try {
    const currentSegments = getCurrentSegments();
    const currentText = getCurrentText();

    // Add error boundary protection
    if (!playbackState) {
      return (
        <Card className="h-100">
          <Card.Header className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="bi bi-translate me-2"></i>
              Real-time Translation
            </h5>
          </Card.Header>
          <Card.Body>
            <div className="text-center text-muted">
              <p>Loading translation interface...</p>
            </div>
          </Card.Body>
        </Card>
      );
    }

    return (
    <div className="realtime-translation">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">Live Translation</h6>
        <div className="d-flex align-items-center">
          <button
            className={`btn btn-sm ${autoScroll ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? 'Disable auto-scroll' : 'Enable auto-scroll'}
          >
            <i className="fas fa-arrow-down"></i>
          </button>
        </div>
      </div>

      {/* Connection Status */}
      <div className="mb-2">
        {isConnected ? (
          <Badge bg="success" className="me-2">
            <i className="fas fa-circle"></i> Live
          </Badge>
        ) : (
          <Badge bg="danger" className="me-2">
            <i className="fas fa-circle"></i> Offline
          </Badge>
        )}
        
        {transcriptData.length > 0 && (
          <Badge bg="info">
            {transcriptData.length} segments
          </Badge>
        )}
      </div>

      {/* Current Transcript Display */}
      {currentText && (
        <div className="current-transcript mb-3">
          <div className="card bg-primary text-white">
            <div className="card-body p-2">
              <small className="fw-bold">Current:</small>
              <div 
                className="mt-1"
                dangerouslySetInnerHTML={{ 
                  __html: highlightCurrentWords(currentText, currentTranscript?.words) 
                }}
              />
              {currentTranscript && (
                <div className="mt-2 d-flex justify-content-between">
                  <small>
                    {currentTranscript.language && (
                      <span className="me-2">
                        <i className="fas fa-globe"></i> {currentTranscript.language}
                      </span>
                    )}
                  </small>
                  <small>
                    <Badge 
                      bg={getConfidenceColor(currentTranscript.confidence)}
                      className="ms-2"
                    >
                      {formatConfidence(currentTranscript.confidence)}
                    </Badge>
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Transcript History */}
      <div 
        ref={transcriptRef}
        className="transcript-history"
        style={{
          minHeight: '100%',
          padding: '15px',
          backgroundColor: '#f8f9fa'
        }}
        onScroll={handleScroll}
      >
        {transcriptData.length === 0 ? (
          <div className="text-center text-muted py-4">
            {isConnected ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Waiting for transcription...
              </>
            ) : (
              'Connect to start receiving live translation'
            )}
          </div>
        ) : (
          transcriptData
            .filter(segment => segment && typeof segment === 'object')
            .map((segment, index) => {
            const isCurrent = currentSegments.includes(segment);
            const isRecent = index >= transcriptData.length - 5;
            
            return (
              <div
                key={index}
                className={`transcript-segment mb-2 p-2 rounded ${
                  isCurrent 
                    ? 'bg-warning text-dark' 
                    : isRecent 
                      ? 'bg-light' 
                      : 'bg-white'
                }`}
                style={{
                  border: isCurrent ? '2px solid #ffc107' : '1px solid #dee2e6',
                  transition: 'all 0.3s ease'
                }}
              >
                {/* Transcript Text */}
                <div className="transcript-text" style={{ 
                  wordWrap: 'break-word', 
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.4',
                  fontSize: '14px'
                }}>
                  <div className="mb-1">
                    <strong>Arabic:</strong> {segment && segment.text ? segment.text : 'No Arabic text'}
                  </div>
                  {segment && segment.english_text && (
                    <div className="text-muted">
                      <strong>English:</strong> {segment.english_text}
                    </div>
                  )}
                </div>
                
                {/* Metadata */}
                <div className="transcript-meta d-flex justify-content-between align-items-center mt-1">
                  <small className="text-muted">
                    {segment && segment.timestamp ? new Date(segment.timestamp * 1000).toLocaleTimeString() : 'No timestamp'}
                    {segment && typeof segment.start_time === 'number' && (
                      <span className="ms-2">
                        {Math.floor(segment.start_time / 60)}:
                        {Math.floor(segment.start_time % 60).toString().padStart(2, '0')}
                      </span>
                    )}
                  </small>
                  
                  <div className="d-flex align-items-center">
                    {segment && segment.language && (
                      <Badge bg="secondary" className="me-1" style={{ fontSize: '0.7em' }}>
                        {segment.language}
                      </Badge>
                    )}
                    {segment && segment.confidence !== undefined && (
                      <Badge 
                        bg={getConfidenceColor(segment.confidence)}
                        style={{ fontSize: '0.7em' }}
                      >
                        {formatConfidence(segment.confidence)}
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Word-level timing (if available) */}
                {segment && segment.words && segment.words.length > 0 && (
                  <div className="word-timing mt-1">
                    <small className="text-muted">
                      {segment.words.filter(word => word && typeof word === 'object').map((word, wordIndex) => (
                        <span
                          key={wordIndex}
                          className={`word-item me-1 ${
                            isCurrent && 
                            playbackState.currentTime >= word.start && 
                            playbackState.currentTime <= word.end
                              ? 'fw-bold text-primary'
                              : ''
                          }`}
                          style={{ cursor: 'pointer' }}
                          onClick={() => {
                            // Seek to word start time
                            if (window.parent && window.parent.seekTo) {
                              window.parent.seekTo(word.start);
                            }
                          }}
                        >
                          {word.word}
                        </span>
                      ))}
                    </small>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Controls */}
      <div className="transcript-controls mt-2 d-flex justify-content-between">
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => {
            if (transcriptRef.current) {
              transcriptRef.current.scrollTop = 0;
            }
          }}
        >
          <i className="fas fa-arrow-up"></i> Top
        </button>
        
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => {
            if (transcriptRef.current) {
              transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
            }
          }}
        >
          <i className="fas fa-arrow-down"></i> Bottom
        </button>
        
        <button
          className="btn btn-sm btn-outline-danger"
          onClick={() => {
            if (window.confirm('Clear all transcript data?')) {
              // This would need to be handled by parent component
              window.location.reload();
            }
          }}
        >
          <i className="fas fa-trash"></i> Clear
        </button>
      </div>
    </div>
  );
  } catch (error) {
    console.error('Error in RealtimeTranslation component:', error);
    return (
      <Card className="h-100">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            <i className="bi bi-translate me-2"></i>
            Real-time Translation
          </h5>
        </Card.Header>
        <Card.Body>
          <div className="text-center text-muted">
            <p>Error loading translation interface. Please refresh the page.</p>
          </div>
        </Card.Body>
      </Card>
    );
  }
};

export default RealtimeTranslation;
