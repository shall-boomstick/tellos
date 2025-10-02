import React, { useEffect, useState, useRef } from 'react';
import { Card, Badge, ProgressBar } from 'react-bootstrap';
import '../styles/emotion-visualization.css';

const EmotionMeter = ({
  emotionData,
  currentTime,
  playbackState,
  isConnected
}) => {
  const [currentEmotion, setCurrentEmotion] = useState(null);
  const [emotionHistory, setEmotionHistory] = useState([]);
  const meterRef = useRef(null);
  const animationRef = useRef(null);

  // Emotion type configurations
  const emotionConfig = {
    joy: { color: '#28a745', icon: '😊', label: 'Joy', intensity: 0.7 },
    sadness: { color: '#6c757d', icon: '😢', label: 'Sadness', intensity: 0.3 },
    anger: { color: '#dc3545', icon: '😠', label: 'Anger', intensity: 0.9 },
    fear: { color: '#6f42c1', icon: '😨', label: 'Fear', intensity: 0.8 },
    surprise: { color: '#fd7e14', icon: '😲', label: 'Surprise', intensity: 0.6 },
    neutral: { color: '#17a2b8', icon: '😐', label: 'Neutral', intensity: 0.5 }
  };

  // Get current emotion based on playback time
  useEffect(() => {
    if (!emotionData || !Array.isArray(emotionData) || !currentTime) {
      setCurrentEmotion(null);
      return;
    }

    const currentEmotionSegment = emotionData.find(emotion => 
      emotion.start_time <= currentTime && emotion.end_time >= currentTime
    );

    if (currentEmotionSegment) {
      setCurrentEmotion(currentEmotionSegment);
      
      // Add to history if it's a new emotion
      setEmotionHistory(prev => {
        const lastEmotion = prev[prev.length - 1];
        if (!lastEmotion || lastEmotion.emotion_type !== currentEmotionSegment.emotion_type) {
          return [...prev.slice(-9), currentEmotionSegment]; // Keep last 10 emotions
        }
        return prev;
      });
    }
  }, [emotionData, currentTime]);

  // Animate meter based on emotion intensity
  useEffect(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    const animateMeter = () => {
      if (meterRef.current && currentEmotion) {
        const config = emotionConfig[currentEmotion.emotion_type] || emotionConfig.neutral;
        const intensity = currentEmotion.confidence * config.intensity;
        
        // Update meter height and color
        const meter = meterRef.current;
        meter.style.height = `${intensity * 100}%`;
        meter.style.backgroundColor = config.color;
        
        // Add pulsing effect for high intensity emotions
        if (intensity > 0.7) {
          meter.style.boxShadow = `0 0 20px ${config.color}`;
        } else {
          meter.style.boxShadow = 'none';
        }
      }
      
      animationRef.current = requestAnimationFrame(animateMeter);
    };

    animateMeter();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [currentEmotion]);

  // Calculate emotional intensity score (0-100)
  const getIntensityScore = () => {
    if (!currentEmotion) return 0;
    
    const config = emotionConfig[currentEmotion.emotion_type] || emotionConfig.neutral;
    const baseIntensity = config.intensity;
    const confidenceMultiplier = currentEmotion.confidence;
    
    return Math.round(baseIntensity * confidenceMultiplier * 100);
  };

  // Get emotion color for styling
  const getEmotionColor = () => {
    if (!currentEmotion) return emotionConfig.neutral.color;
    return emotionConfig[currentEmotion.emotion_type]?.color || emotionConfig.neutral.color;
  };

  // Get emotion icon
  const getEmotionIcon = () => {
    if (!currentEmotion) return emotionConfig.neutral.icon;
    return emotionConfig[currentEmotion.emotion_type]?.icon || emotionConfig.neutral.icon;
  };

  // Get emotion label
  const getEmotionLabel = () => {
    if (!currentEmotion) return emotionConfig.neutral.label;
    return emotionConfig[currentEmotion.emotion_type]?.label || emotionConfig.neutral.label;
  };

  // Format confidence as percentage
  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  return (
    <div className="emotion-meter">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">
          <i className="fas fa-heart me-2"></i>
          Emotional Analysis
        </h6>
        <div className="d-flex align-items-center">
          {isConnected ? (
            <Badge bg="success" className="me-2">
              <i className="fas fa-circle"></i> Live
            </Badge>
          ) : (
            <Badge bg="danger" className="me-2">
              <i className="fas fa-circle"></i> Offline
            </Badge>
          )}
          {emotionData && emotionData.length > 0 && (
            <Badge bg="info">
              {emotionData.length} emotions
            </Badge>
          )}
        </div>
      </div>

      {/* Main Emotion Meter */}
      <Card className="mb-3">
        <Card.Body className="text-center">
          {/* Current Emotion Display */}
          <div className="current-emotion mb-3">
            <div 
              className={`emotion-icon mb-2 ${getIntensityScore() > 70 ? 'emotion-pulse' : ''}`}
              style={{ 
                fontSize: '3rem',
                color: getEmotionColor(),
                transition: 'all 0.3s ease'
              }}
            >
              {getEmotionIcon()}
            </div>
            <h5 
              className="emotion-label mb-1"
              style={{ color: getEmotionColor() }}
            >
              {getEmotionLabel()}
            </h5>
            {currentEmotion && (
              <div className="emotion-details">
                <Badge 
                  bg="secondary" 
                  className="me-2"
                >
                  {formatConfidence(currentEmotion.confidence)}
                </Badge>
                <small className="text-muted">
                  Intensity: {getIntensityScore()}%
                </small>
              </div>
            )}
          </div>

          {/* Visual Intensity Meter */}
          <div className="intensity-meter mb-3">
            <div 
              className="meter-container"
              style={{
                height: '120px',
                width: '60px',
                border: '2px solid #dee2e6',
                borderRadius: '30px',
                margin: '0 auto',
                position: 'relative',
                overflow: 'hidden',
                backgroundColor: '#f8f9fa'
              }}
            >
              <div
                ref={meterRef}
                className={`meter-fill ${getIntensityScore() > 70 ? 'emotion-high-intensity' : ''}`}
                style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: '0%',
                  backgroundColor: getEmotionColor(),
                  transition: 'height 0.5s ease, background-color 0.3s ease',
                  borderRadius: '28px 28px 0 0'
                }}
              />
              
              {/* Intensity markers */}
              <div className="meter-markers" style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: 'none'
              }}>
                {[25, 50, 75].map(level => (
                  <div
                    key={level}
                    style={{
                      position: 'absolute',
                      top: `${100 - level}%`,
                      left: 0,
                      right: 0,
                      height: '1px',
                      backgroundColor: '#6c757d',
                      opacity: 0.3
                    }}
                  />
                ))}
              </div>
            </div>
            
            {/* Intensity labels */}
            <div className="meter-labels mt-2">
              <small className="text-muted d-flex justify-content-between">
                <span>Low</span>
                <span>Medium</span>
                <span>High</span>
              </small>
            </div>
          </div>

          {/* Progress Bar for Current Emotion */}
          {currentEmotion && (
            <div className="emotion-progress">
              <small className="text-muted mb-1 d-block">
                Current Emotion Intensity
              </small>
              <ProgressBar
                now={getIntensityScore()}
                variant="custom"
                style={{
                  height: '8px',
                  backgroundColor: '#e9ecef'
                }}
              />
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Emotion History */}
      {emotionHistory.length > 0 && (
        <Card>
          <Card.Header>
            <h6 className="mb-0">Recent Emotions</h6>
          </Card.Header>
          <Card.Body className="p-2">
            <div className="emotion-timeline">
              {emotionHistory.slice(-5).map((emotion, index) => {
                const config = emotionConfig[emotion.emotion_type] || emotionConfig.neutral;
                const isCurrent = currentEmotion && 
                  emotion.start_time === currentEmotion.start_time;
                
                return (
                  <div
                    key={index}
                    className={`emotion-item d-flex align-items-center p-1 mb-1 rounded ${
                      isCurrent ? 'bg-warning' : 'bg-light'
                    }`}
                    style={{
                      border: isCurrent ? '2px solid #ffc107' : '1px solid #dee2e6',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <span 
                      className="me-2"
                      style={{ fontSize: '1.2rem' }}
                    >
                      {config.icon}
                    </span>
                    <div className="flex-grow-1">
                      <small className="fw-bold" style={{ color: config.color }}>
                        {config.label}
                      </small>
                      <div className="d-flex justify-content-between">
                        <small className="text-muted">
                          {formatConfidence(emotion.confidence)}
                        </small>
                        <small className="text-muted">
                          {Math.floor(emotion.start_time / 60)}:
                          {Math.floor(emotion.start_time % 60).toString().padStart(2, '0')}
                        </small>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card.Body>
        </Card>
      )}

      {/* No Data State */}
      {(!emotionData || emotionData.length === 0) && (
        <Card>
          <Card.Body className="text-center text-muted py-4">
            {isConnected ? (
              <>
                <i className="fas fa-heart fa-2x mb-2"></i>
                <p className="mb-0">Analyzing emotions...</p>
                <small>Emotion data will appear here as the conversation progresses</small>
              </>
            ) : (
              <>
                <i className="fas fa-heart fa-2x mb-2"></i>
                <p className="mb-0">Connect to start emotion analysis</p>
              </>
            )}
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default EmotionMeter;