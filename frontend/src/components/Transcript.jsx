import React, { useState, useEffect, useRef } from 'react'

const Transcript = ({ 
  transcript = '',
  englishText = '',
  words = [],
  currentTime = 0,
  isPlaying = false,
  onWordClick,
  showConfidence = true,
  autoScroll = true
}) => {
  const [currentWordIndex, setCurrentWordIndex] = useState(-1)
  const [searchTerm, setSearchTerm] = useState('')
  const [highlightedWords, setHighlightedWords] = useState([])
  const containerRef = useRef(null)
  const currentWordRef = useRef(null)

  // Find current word based on time
  useEffect(() => {
    if (!words.length) return

    let foundIndex = -1
    for (let i = 0; i < words.length; i++) {
      const word = words[i]
      if (currentTime >= word.start_time && currentTime <= word.end_time) {
        foundIndex = i
        break
      } else if (currentTime < word.start_time) {
        // If we're before this word, the current word is the previous one
        foundIndex = Math.max(0, i - 1)
        break
      }
    }

    // If we're past all words, highlight the last one
    if (foundIndex === -1 && words.length > 0) {
      const lastWord = words[words.length - 1]
      if (currentTime > lastWord.end_time) {
        foundIndex = words.length - 1
      }
    }

    setCurrentWordIndex(foundIndex)
  }, [currentTime, words])

  // Auto-scroll to current word
  useEffect(() => {
    if (autoScroll && currentWordRef.current && isPlaying) {
      currentWordRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    }
  }, [currentWordIndex, autoScroll, isPlaying])

  // Handle search
  useEffect(() => {
    if (!searchTerm.trim()) {
      setHighlightedWords([])
      return
    }

    const indices = []
    const searchLower = searchTerm.toLowerCase()
    
    words.forEach((word, index) => {
      if (word.word.toLowerCase().includes(searchLower)) {
        indices.push(index)
      }
    })

    setHighlightedWords(indices)
  }, [searchTerm, words])

  const handleWordClick = (word, index) => {
    if (onWordClick) {
      onWordClick(word.start_time, word, index)
    }
  }

  const getWordClassName = (index) => {
    const classes = ['transcript-word']
    
    if (index === currentWordIndex) {
      classes.push('current-word')
    }
    
    if (highlightedWords.includes(index)) {
      classes.push('highlighted-word')
    }
    
    const word = words[index]
    if (showConfidence && word.confidence < 0.7) {
      classes.push('low-confidence')
    }
    
    return classes.join(' ')
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#22c55e' // Green
    if (confidence >= 0.6) return '#eab308' // Yellow
    return '#ef4444' // Red
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const calculateReadingProgress = () => {
    if (!words.length) return 0
    return Math.round((currentWordIndex / words.length) * 100)
  }

  const getAverageConfidence = () => {
    if (!words.length) return 0
    const total = words.reduce((sum, word) => sum + word.confidence, 0)
    return (total / words.length * 100).toFixed(1)
  }

  return (
    <div className="transcript-container">
      {/* Header with controls */}
      <div className="transcript-header">
        <h3>English Transcript</h3>
        <div className="transcript-stats">
          <span className="stat">
            Progress: {calculateReadingProgress()}%
          </span>
          {showConfidence && (
            <span className="stat">
              Avg. Confidence: {getAverageConfidence()}%
            </span>
          )}
        </div>
      </div>

      {/* Search bar */}
      <div className="search-container">
        <input
          type="text"
          placeholder="Search in transcript..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        {highlightedWords.length > 0 && (
          <span className="search-results">
            {highlightedWords.length} matches
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="reading-progress">
        <div 
          className="progress-fill"
          style={{ width: `${calculateReadingProgress()}%` }}
        />
      </div>

      {/* Transcript content */}
      <div 
        ref={containerRef}
        className="transcript-content"
        dir="ltr" // Left-to-right for English text
      >
        {words.length > 0 ? (
          <div className="transcript-words">
            {words.map((word, index) => (
              <span
                key={index}
                ref={index === currentWordIndex ? currentWordRef : null}
                className={getWordClassName(index)}
                onClick={() => handleWordClick(word, index)}
                title={showConfidence ? 
                  `${word.word} (${Math.round(word.confidence * 100)}% confidence, ${formatTime(word.start_time)}-${formatTime(word.end_time)})` : 
                  `${word.word} (${formatTime(word.start_time)}-${formatTime(word.end_time)})`
                }
                style={{
                  '--confidence-color': getConfidenceColor(word.confidence)
                }}
              >
                {word.word}
                {showConfidence && (
                  <span className="confidence-indicator" />
                )}
              </span>
            ))}
          </div>
        ) : englishText || transcript ? (
          <div className="transcript-text" dir="ltr">
            {englishText || transcript}
          </div>
        ) : (
          <div className="transcript-placeholder">
            <p>Transcript will appear here once processing is complete...</p>
          </div>
        )}
      </div>

      {/* Footer with controls */}
      <div className="transcript-footer">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={showConfidence}
            onChange={(e) => setShowConfidence?.(e.target.checked)}
          />
          Show confidence indicators
        </label>
        
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll?.(e.target.checked)}
          />
          Auto-scroll to current word
        </label>
      </div>

    </div>
  )
}

export default Transcript
