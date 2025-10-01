import React, { useEffect, useState } from 'react';
import { Card, Badge, ProgressBar, Spinner } from 'react-bootstrap';

const RealtimeEmotionGauge = ({
  emotionData,
  currentEmotion,
  playbackState,
  isConnected
}) => {
  const [emotionHistory, setEmotionHistory] = useState([]);
  const [smoothedEmotion, setSmoothedEmotion] = useState(null);

  // Update emotion history
  useEffect(() => {
    if (emotionData) {
      setEmotionHistory(prev => [...prev, emotionData].slice(-20)); // Keep last 20 emotions
    }
  }, [emotionData]);

  // Calculate smoothed emotion from recent history
  useEffect(() => {
    if (emotionHistory.length > 0) {
      const recentEmotions = emotionHistory.slice(-5); // Last 5 emotions
      const emotionCounts = {};
      
      recentEmotions.forEach(emotion => {
        const emotionType = emotion.emotion_type || emotion.type;
        emotionCounts[emotionType] = (emotionCounts[emotionType] || 0) + 1;
      });
      
      // Get most common emotion
      const mostCommonEmotion = Object.keys(emotionCounts).reduce((a, b) => 
        emotionCounts[a] > emotionCounts[b] ? a : b
      );
      
      // Get average confidence and intensity
      const avgConfidence = recentEmotions.reduce((sum, e) => sum + (e.confidence || 0), 0) / recentEmotions.length;
      const avgIntensity = recentEmotions.reduce((sum, e) => sum + (e.intensity || 0), 0) / recentEmotions.length;
      
      setSmoothedEmotion({
        emotion_type: mostCommonEmotion,
        confidence: avgConfidence,
        intensity: avgIntensity,
        timestamp: recentEmotions[recentEmotions.length - 1].timestamp
      });
    }
  }, [emotionHistory]);

  // Get emotion color
  const getEmotionColor = (emotionType) => {
    const colors = {
      joy: '#28a745',
      sadness: '#6c757d',
      anger: '#dc3545',
      fear: '#6f42c1',
      surprise: '#fd7e14',
      neutral: '#17a2b8'
    };
    return colors[emotionType] || colors.neutral;
  };

  // Get emotion icon
  const getEmotionIcon = (emotionType) => {
    const icons = {
      joy: 'fa-smile',
      sadness: 'fa-frown',
      anger: 'fa-angry',
      fear: 'fa-surprise',
      surprise: 'fa-surprise',
      neutral: 'fa-meh'
    };
    return icons[emotionType] || icons.neutral;
  };

  // Get intensity level
  const getIntensityLevel = (intensity) => {
    if (intensity >= 0.7) return 'High';
    if (intensity >= 0.4) return 'Medium';
    return 'Low';
  };

  // Get intensity color
  const getIntensityColor = (intensity) => {
    if (intensity >= 0.7) return 'danger';
    if (intensity >= 0.4) return 'warning';
    return 'success';
  };

  // Format confidence
  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  // Get current emotion for display
  const displayEmotion = currentEmotion || smoothedEmotion || emotionData;

  return (
    <div className="realtime-emotion-gauge">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">Emotion Analysis</h6>
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
        </div>
      </div>

      {/* Current Emotion Display */}
      {displayEmotion ? (
        <div className="current-emotion mb-4">
          <Card className="text-center" style={{ backgroundColor: getEmotionColor(displayEmotion.emotion_type) + '20' }}>
            <Card.Body className="p-3">
              <div className="emotion-icon mb-2">
                <i 
                  className={`fas ${getEmotionIcon(displayEmotion.emotion_type)} fa-3x`}
                  style={{ color: getEmotionColor(displayEmotion.emotion_type) }}
                ></i>
              </div>
              
              <h5 className="emotion-type mb-2" style={{ color: getEmotionColor(displayEmotion.emotion_type) }}>
                {displayEmotion.emotion_type?.toUpperCase() || 'UNKNOWN'}
              </h5>
              
              <div className="emotion-meta">
                <div className="mb-2">
                  <Badge bg={getIntensityColor(displayEmotion.intensity)} className="me-2">
                    {getIntensityLevel(displayEmotion.intensity)} Intensity
                  </Badge>
                  <Badge bg="info">
                    {formatConfidence(displayEmotion.confidence)} Confidence
                  </Badge>
                </div>
                
                <small className="text-muted">
                  {displayEmotion.timestamp && 
                    new Date(displayEmotion.timestamp * 1000).toLocaleTimeString()
                  }
                </small>
              </div>
            </Card.Body>
          </Card>
        </div>
      ) : (
        <div className="text-center text-muted py-4">
          {isConnected ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              Analyzing emotions...
            </>
          ) : (
            'Connect to start emotion analysis'
          )}
        </div>
      )}

      {/* Intensity Gauge */}
      {displayEmotion && (
        <div className="intensity-gauge mb-4">
          <h6 className="mb-2">Intensity Level</h6>
          <ProgressBar
            now={displayEmotion.intensity * 100}
            variant={getIntensityColor(displayEmotion.intensity)}
            label={`${Math.round(displayEmotion.intensity * 100)}%`}
            style={{ height: '25px' }}
          />
          <div className="d-flex justify-content-between mt-1">
            <small className="text-muted">Low</small>
            <small className="text-muted">High</small>
          </div>
        </div>
      )}

      {/* Confidence Meter */}
      {displayEmotion && (
        <div className="confidence-meter mb-4">
          <h6 className="mb-2">Confidence</h6>
          <ProgressBar
            now={displayEmotion.confidence * 100}
            variant={displayEmotion.confidence >= 0.8 ? 'success' : displayEmotion.confidence >= 0.6 ? 'warning' : 'danger'}
            label={formatConfidence(displayEmotion.confidence)}
            style={{ height: '20px' }}
          />
        </div>
      )}

      {/* Emotion History */}
      {emotionHistory.length > 0 && (
        <div className="emotion-history">
          <h6 className="mb-2">Recent Emotions</h6>
          <div className="emotion-timeline">
            {emotionHistory.slice(-10).reverse().map((emotion, index) => (
              <div 
                key={index}
                className="emotion-item d-flex align-items-center mb-2 p-2 rounded"
                style={{ 
                  backgroundColor: getEmotionColor(emotion.emotion_type) + '10',
                  borderLeft: `4px solid ${getEmotionColor(emotion.emotion_type)}`
                }}
              >
                <i 
                  className={`fas ${getEmotionIcon(emotion.emotion_type)} me-2`}
                  style={{ color: getEmotionColor(emotion.emotion_type) }}
                ></i>
                <div className="flex-grow-1">
                  <div className="fw-bold" style={{ color: getEmotionColor(emotion.emotion_type) }}>
                    {emotion.emotion_type?.toUpperCase()}
                  </div>
                  <small className="text-muted">
                    {emotion.timestamp && 
                      new Date(emotion.timestamp * 1000).toLocaleTimeString()
                    }
                  </small>
                </div>
                <div className="text-end">
                  <Badge 
                    bg={getIntensityColor(emotion.intensity)}
                    style={{ fontSize: '0.7em' }}
                  >
                    {getIntensityLevel(emotion.intensity)}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistics */}
      {emotionHistory.length > 0 && (
        <div className="emotion-stats mt-3">
          <h6 className="mb-2">Statistics</h6>
          <div className="row text-center">
            <div className="col-6">
              <div className="stat-item">
                <div className="fw-bold text-primary">{emotionHistory.length}</div>
                <small className="text-muted">Total Emotions</small>
              </div>
            </div>
            <div className="col-6">
              <div className="stat-item">
                <div className="fw-bold text-success">
                  {emotionHistory.length > 0 ? 
                    Math.round(emotionHistory.reduce((sum, e) => sum + (e.confidence || 0), 0) / emotionHistory.length * 100) 
                    : 0}%
                </div>
                <small className="text-muted">Avg Confidence</small>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="emotion-controls mt-3 d-flex justify-content-between">
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setEmotionHistory([])}
          disabled={emotionHistory.length === 0}
        >
          <i className="fas fa-trash"></i> Clear History
        </button>
        
        <button
          className="btn btn-sm btn-outline-info"
          onClick={() => {
            // Export emotion data
            const dataStr = JSON.stringify(emotionHistory, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `emotion-analysis-${Date.now()}.json`;
            link.click();
            URL.revokeObjectURL(url);
          }}
          disabled={emotionHistory.length === 0}
        >
          <i className="fas fa-download"></i> Export
        </button>
      </div>
    </div>
  );
};

export default RealtimeEmotionGauge;
