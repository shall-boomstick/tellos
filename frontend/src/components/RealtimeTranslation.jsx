import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, Badge, Spinner } from 'react-bootstrap';

const RealtimeTranslation = ({
  transcriptData,
  currentTranscript,
  playbackState,
  isConnected,
  emotionData = []
}) => {
  const transcriptRef = useRef(null);
  const [isScrolling, setIsScrolling] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  // Scroll to current segment
  const scrollToCurrentSegment = useCallback(() => {
    if (!transcriptRef.current || !currentTranscript) {
      console.log('RealtimeTranslation: Cannot scroll - missing ref or currentTranscript');
      return;
    }
    
    console.log('RealtimeTranslation: Attempting to scroll to current segment:', currentTranscript);
    
    const segments = transcriptRef.current.querySelectorAll('.transcript-segment');
    console.log('RealtimeTranslation: Found segments:', segments.length);
    
    const currentSegment = Array.from(segments).find(segment => {
      const segmentData = segment.getAttribute('data-segment-index');
      const segmentIndex = parseInt(segmentData);
      const isCurrent = segmentData && transcriptData[segmentIndex] === currentTranscript;
      console.log('RealtimeTranslation: Checking segment', segmentIndex, 'isCurrent:', isCurrent);
      return isCurrent;
    });
    
    if (currentSegment) {
      console.log('RealtimeTranslation: Found current segment, scrolling...');
      // Find the scrollable parent container
      const scrollableParent = transcriptRef.current.closest('[style*="overflow"]') || 
                              transcriptRef.current.closest('.card-body') ||
                              document.querySelector('.main-content');
      
      if (scrollableParent) {
        const parentRect = scrollableParent.getBoundingClientRect();
        const segmentRect = currentSegment.getBoundingClientRect();
        const scrollTop = scrollableParent.scrollTop;
        
        // Calculate position to keep segment at top of parent container
        const targetScrollTop = scrollTop + (segmentRect.top - parentRect.top);
        
        scrollableParent.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'
        });
      } else {
        // Fallback to scrolling the segment into view
        currentSegment.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } else {
      console.log('RealtimeTranslation: Current segment not found in DOM');
    }
  }, [currentTranscript, transcriptData]);

  // Auto-scroll to keep current segment at top
  useEffect(() => {
    console.log('RealtimeTranslation: Auto-scroll effect triggered', {
      hasRef: !!transcriptRef.current,
      autoScroll,
      isScrolling,
      hasCurrentTranscript: !!currentTranscript,
      currentTranscript
    });
    
    if (transcriptRef.current && autoScroll && !isScrolling && currentTranscript) {
      console.log('RealtimeTranslation: Auto-scroll triggered');
      scrollToCurrentSegment();
    }
  }, [currentTranscript, autoScroll, isScrolling, scrollToCurrentSegment]);

  // Also trigger auto-scroll when transcript data changes
  useEffect(() => {
    if (transcriptRef.current && autoScroll && !isScrolling && transcriptData.length > 0) {
      console.log('RealtimeTranslation: Auto-scroll triggered by transcript data change');
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        if (currentTranscript) {
          scrollToCurrentSegment();
        } else {
          // Fallback: scroll to bottom if no current transcript
          console.log('RealtimeTranslation: No current transcript, scrolling to bottom');
          const scrollableParent = transcriptRef.current?.closest('[style*="overflow"]') || 
                                  transcriptRef.current?.closest('.card-body');
          if (scrollableParent) {
            scrollableParent.scrollTop = scrollableParent.scrollHeight;
          }
        }
      }, 100);
    }
  }, [transcriptData, autoScroll, isScrolling, scrollToCurrentSegment, currentTranscript]);

  // Handle scroll events
  const handleScroll = () => {
    if (transcriptRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = transcriptRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setAutoScroll(isAtBottom);
    }
  };

  // Manual scroll to current segment
  const handleScrollToCurrent = () => {
    console.log('RealtimeTranslation: Manual scroll to current triggered', {
      hasRef: !!transcriptRef.current,
      hasCurrentTranscript: !!currentTranscript,
      currentTranscript
    });
    setIsScrolling(true);
    scrollToCurrentSegment();
    setTimeout(() => {
      setIsScrolling(false);
      console.log('RealtimeTranslation: Manual scroll completed');
    }, 1000);
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

  // Get emotion for a specific time segment
  const getEmotionForSegment = (segment) => {
    if (!emotionData || !Array.isArray(emotionData) || !segment) return null;
    
    const segmentStart = segment.start_time || 0;
    const segmentEnd = segment.end_time || segmentStart + 1;
    
    // Find emotion that overlaps with this segment
    return emotionData.find(emotion => 
      emotion.start_time <= segmentEnd && emotion.end_time >= segmentStart
    );
  };

  // Get emotion color for styling
  const getEmotionColor = (emotion) => {
    if (!emotion) return '#6c757d'; // Default gray
    
    const emotionColors = {
      joy: '#28a745',      // Green
      sadness: '#6c757d',  // Gray
      anger: '#dc3545',    // Red
      fear: '#6f42c1',     // Purple
      surprise: '#fd7e14', // Orange
      neutral: '#17a2b8'   // Blue
    };
    
    return emotionColors[emotion.emotion_type] || emotionColors.neutral;
  };

  // Get emotion icon
  const getEmotionIcon = (emotion) => {
    if (!emotion) return '😐';
    
    const emotionIcons = {
      joy: '😊',
      sadness: '😢',
      anger: '😠',
      fear: '😨',
      surprise: '😲',
      neutral: '😐'
    };
    
    return emotionIcons[emotion.emotion_type] || emotionIcons.neutral;
  };

  // Get emotion intensity level
  const getEmotionIntensity = (emotion) => {
    if (!emotion) return 'medium';
    return emotion.intensity || 'medium';
  };

  // Calculate emotional intensity score (0-100)
  const getEmotionIntensityScore = (emotion) => {
    if (!emotion) return 0;
    
    const intensityMultipliers = {
      low: 0.3,
      medium: 0.6,
      high: 0.9
    };
    
    const baseIntensity = intensityMultipliers[emotion.intensity] || 0.6;
    const confidenceMultiplier = emotion.confidence || 0.5;
    
    return Math.round(baseIntensity * confidenceMultiplier * 100);
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
        <h6 className="mb-0">
          <i className="fas fa-language me-2"></i>
          Live Translation
          {currentTranscript && (
            <small className="text-muted ms-2">
              <i className="fas fa-crosshairs me-1"></i>
              Following current segment
            </small>
          )}
        </h6>
        <div className="d-flex align-items-center">
          <button
            className={`btn btn-sm ${autoScroll ? 'btn-success' : 'btn-outline-secondary'} me-2`}
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? 'Disable auto-follow' : 'Enable auto-follow'}
          >
            <i className={`fas ${autoScroll ? 'fa-eye' : 'fa-eye-slash'}`}></i>
            {autoScroll ? 'Auto-follow ON' : 'Auto-follow OFF'}
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
            const emotion = getEmotionForSegment(segment);
            const emotionColor = getEmotionColor(emotion);
            const emotionIcon = getEmotionIcon(emotion);
            const emotionIntensity = getEmotionIntensityScore(emotion);
            
            return (
              <div
                key={index}
                data-segment-index={index}
                className={`transcript-segment mb-2 p-2 rounded ${
                  isCurrent 
                    ? 'current-segment' 
                    : ''
                }`}
                style={{
                  backgroundColor: emotion ? `${emotionColor}15` : '#f8f9fa',
                  borderTop: isCurrent ? '2px solid #ffc107' : `2px solid ${emotionColor}`,
                  borderRight: isCurrent ? '2px solid #ffc107' : `2px solid ${emotionColor}`,
                  borderBottom: isCurrent ? '2px solid #ffc107' : `2px solid ${emotionColor}`,
                  borderLeft: `6px solid ${emotionColor}`,
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  boxShadow: isCurrent ? '0 4px 8px rgba(0,0,0,0.1)' : '0 2px 4px rgba(0,0,0,0.05)'
                }}
              >
                {/* Emotion Indicator */}
                {emotion && (
                  <div 
                    className="emotion-indicator"
                    style={{
                      position: 'absolute',
                      top: '5px',
                      right: '5px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      color: emotionColor,
                      padding: '3px 8px',
                      borderRadius: '15px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      zIndex: 1,
                      border: `1px solid ${emotionColor}40`,
                      backdropFilter: 'blur(4px)'
                    }}
                  >
                    <span style={{ fontSize: '0.9rem' }}>{emotionIcon}</span>
                    <span style={{ textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {emotion.emotion_type}
                    </span>
                    <span style={{ 
                      backgroundColor: emotionColor + '20', 
                      padding: '1px 4px', 
                      borderRadius: '8px',
                      fontSize: '0.7rem'
                    }}>
                      {emotionIntensity}%
                    </span>
                  </div>
                )}

                {/* Transcript Text */}
                <div className="transcript-text" style={{ 
                  wordWrap: 'break-word', 
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.4',
                  fontSize: '14px',
                  paddingRight: emotion ? '80px' : '0' // Make room for emotion indicator
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
                
                {/* Emotion Intensity Bar */}
                {emotion && (
                  <div className="emotion-intensity-bar mt-2 mb-1">
                    <div 
                      className="intensity-bar"
                      style={{
                        height: '3px',
                        backgroundColor: emotionColor + '30',
                        borderRadius: '2px',
                        overflow: 'hidden',
                        position: 'relative'
                      }}
                    >
                      <div
                        className="intensity-fill"
                        style={{
                          height: '100%',
                          width: `${emotionIntensity}%`,
                          backgroundColor: emotionColor,
                          transition: 'width 0.5s ease',
                          borderRadius: '2px',
                          boxShadow: `0 0 4px ${emotionColor}60`
                        }}
                      />
                    </div>
                  </div>
                )}

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
            console.log('RealtimeTranslation: Top button clicked');
            const scrollableParent = transcriptRef.current?.closest('[style*="overflow"]') || 
                                    transcriptRef.current?.closest('.card-body');
            if (scrollableParent) {
              console.log('RealtimeTranslation: Scrolling to top');
              scrollableParent.scrollTop = 0;
            } else {
              console.log('RealtimeTranslation: No scrollable parent found');
            }
          }}
        >
          <i className="fas fa-arrow-up"></i> Top
        </button>
        
        <button
          className="btn btn-sm btn-outline-primary"
          onClick={handleScrollToCurrent}
          disabled={!currentTranscript}
        >
          <i className="fas fa-crosshairs"></i> Current
        </button>
        
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => {
            console.log('RealtimeTranslation: Bottom button clicked');
            const scrollableParent = transcriptRef.current?.closest('[style*="overflow"]') || 
                                    transcriptRef.current?.closest('.card-body');
            if (scrollableParent) {
              console.log('RealtimeTranslation: Scrolling to bottom');
              scrollableParent.scrollTop = scrollableParent.scrollHeight;
            } else {
              console.log('RealtimeTranslation: No scrollable parent found');
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
      
      {/* Custom Styles */}
      <style>{`
        .current-segment {
          transform: scale(1.02);
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0% { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
          50% { box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
          100% { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        }
        
        .transcript-segment:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }
      `}</style>
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
