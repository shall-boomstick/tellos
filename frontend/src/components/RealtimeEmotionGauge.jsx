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

      {/* Current Emotion Display - Compact */}
      {displayEmotion ? (
        <div className="current-emotion mb-3">
          <div className="d-flex align-items-center p-2" style={{ 
            backgroundColor: getEmotionColor(displayEmotion.emotion_type) + '15',
            borderRadius: '8px',
            border: `1px solid ${getEmotionColor(displayEmotion.emotion_type)}40`
          }}>
            <div className="emotion-icon me-3">
              <i 
                className={`fas ${getEmotionIcon(displayEmotion.emotion_type)} fa-2x`}
                style={{ color: getEmotionColor(displayEmotion.emotion_type) }}
              ></i>
            </div>
            
            <div className="flex-grow-1">
              <div className="d-flex align-items-center mb-1">
                <h6 className="mb-0 me-2" style={{ color: getEmotionColor(displayEmotion.emotion_type) }}>
                  {displayEmotion.emotion_type?.toUpperCase() || 'UNKNOWN'}
                </h6>
                <Badge bg={getIntensityColor(displayEmotion.intensity)} size="sm">
                  {getIntensityLevel(displayEmotion.intensity)}
                </Badge>
              </div>
              
              <div className="d-flex justify-content-between align-items-center">
                <small className="text-muted">
                  {formatConfidence(displayEmotion.confidence)} confidence
                </small>
                <small className="text-muted">
                  {displayEmotion.timestamp && 
                    new Date(displayEmotion.timestamp * 1000).toLocaleTimeString()
                  }
                </small>
              </div>
            </div>
          </div>
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

      {/* Compact Intensity & Confidence */}
      {displayEmotion && (
        <div className="compact-meters mb-3">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="fw-bold">Intensity</small>
            <small className="text-muted">{Math.round(displayEmotion.intensity * 100)}%</small>
          </div>
          <ProgressBar
            now={displayEmotion.intensity * 100}
            variant={getIntensityColor(displayEmotion.intensity)}
            style={{ height: '12px', marginBottom: '8px' }}
          />
          
          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="fw-bold">Confidence</small>
            <small className="text-muted">{formatConfidence(displayEmotion.confidence)}</small>
          </div>
          <ProgressBar
            now={displayEmotion.confidence * 100}
            variant={displayEmotion.confidence >= 0.8 ? 'success' : displayEmotion.confidence >= 0.6 ? 'warning' : 'danger'}
            style={{ height: '12px' }}
          />
        </div>
      )}


      {/* Compact Statistics */}
      {emotionHistory.length > 0 && (
        <div className="emotion-stats mb-3">
          <div className="d-flex justify-content-between align-items-center p-2" style={{ 
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            border: '1px solid #e9ecef'
          }}>
            <div className="text-center">
              <div className="fw-bold text-primary fs-6">{emotionHistory.length}</div>
              <small className="text-muted">Emotions</small>
            </div>
            <div className="text-center">
              <div className="fw-bold text-success fs-6">
                {emotionHistory.length > 0 ? 
                  Math.round(emotionHistory.reduce((sum, e) => sum + (e.confidence || 0), 0) / emotionHistory.length * 100) 
                  : 0}%
              </div>
              <small className="text-muted">Avg Confidence</small>
            </div>
          </div>
        </div>
      )}

      {/* Compact Controls */}
      <div className="emotion-controls d-flex gap-2">
        <button
          className="btn btn-sm btn-outline-secondary flex-fill"
          onClick={() => setEmotionHistory([])}
          disabled={emotionHistory.length === 0}
          title="Clear History"
        >
          <i className="fas fa-trash"></i>
        </button>
        
        <button
          className="btn btn-sm btn-outline-info flex-fill"
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
          title="Export Data"
        >
          <i className="fas fa-download"></i>
        </button>
      </div>
    </div>
  );
};

export default RealtimeEmotionGauge;
