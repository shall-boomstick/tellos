import React from 'react'

const EmotionGauge = ({ 
  currentEmotion = 'neutral', 
  confidence = 0.0,
  emotionHistory = [],
  size = 'medium' 
}) => {
  const emotions = {
    anger: { color: '#ef4444', icon: '😠', label: 'Anger' },
    sadness: { color: '#3b82f6', icon: '😢', label: 'Sadness' },
    joy: { color: '#eab308', icon: '😊', label: 'Joy' },
    neutral: { color: '#6b7280', icon: '😐', label: 'Neutral' },
    fear: { color: '#8b5cf6', icon: '😨', label: 'Fear' },
    surprise: { color: '#f97316', icon: '😲', label: 'Surprise' }
  }

  const sizeClasses = {
    small: 'gauge-small',
    medium: 'gauge-medium',
    large: 'gauge-large'
  }

  const currentEmotionData = emotions[currentEmotion] || emotions.neutral
  const confidencePercentage = Math.round(confidence * 100)

  // Calculate emotion distribution from history
  const getEmotionDistribution = () => {
    if (!emotionHistory.length) return {}
    
    const distribution = {}
    let totalDuration = 0

    emotionHistory.forEach(segment => {
      const duration = segment.end_time - segment.start_time
      const emotion = segment.combined_emotion
      
      if (!distribution[emotion]) {
        distribution[emotion] = 0
      }
      distribution[emotion] += duration * segment.combined_confidence
      totalDuration += duration
    })

    // Convert to percentages
    Object.keys(distribution).forEach(emotion => {
      distribution[emotion] = (distribution[emotion] / totalDuration) * 100
    })

    return distribution
  }

  const distribution = getEmotionDistribution()

  return (
    <div className={`emotion-gauge ${sizeClasses[size]}`}>
      {/* Main Emotion Display */}
      <div className="main-emotion">
        <div 
          className="emotion-circle"
          style={{ 
            borderColor: currentEmotionData.color,
            backgroundColor: `${currentEmotionData.color}20`
          }}
        >
          <div className="emotion-icon">
            {currentEmotionData.icon}
          </div>
        </div>
        
        <div className="emotion-info">
          <h3 className="emotion-label" style={{ color: currentEmotionData.color }}>
            {currentEmotionData.label}
          </h3>
          <div className="confidence-info">
            <span className="confidence-text">
              {confidencePercentage}% confidence
            </span>
            <div className="confidence-bar">
              <div 
                className="confidence-fill"
                style={{ 
                  width: `${confidencePercentage}%`,
                  backgroundColor: currentEmotionData.color
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Emotion Distribution */}
      {Object.keys(distribution).length > 0 && (
        <div className="emotion-distribution">
          <h4>Overall Distribution</h4>
          <div className="distribution-bars">
            {Object.entries(emotions).map(([emotion, data]) => {
              const percentage = distribution[emotion] || 0
              return (
                <div key={emotion} className="distribution-item">
                  <div className="distribution-header">
                    <span className="distribution-icon">{data.icon}</span>
                    <span className="distribution-label">{data.label}</span>
                    <span className="distribution-percentage">
                      {Math.round(percentage)}%
                    </span>
                  </div>
                  <div className="distribution-bar">
                    <div 
                      className="distribution-fill"
                      style={{ 
                        width: `${percentage}%`,
                        backgroundColor: data.color
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Real-time Indicator */}
      <div className="real-time-indicator">
        <div className="pulse-dot" style={{ backgroundColor: currentEmotionData.color }} />
        <span>Live Analysis</span>
      </div>

    </div>
  )
}

export default EmotionGauge
