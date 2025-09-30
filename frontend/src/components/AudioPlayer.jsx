import React, { useState, useRef, useEffect } from 'react'

const AudioPlayer = ({ audioUrl, duration, onTimeUpdate, onPlay, onPause }) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [volume, setVolume] = useState(1)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const audioRef = useRef(null)
  const progressRef = useRef(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleLoadedData = () => {
      setIsLoading(false)
      setError(null)
    }

    const handleError = () => {
      setIsLoading(false)
      setError('Failed to load audio file')
    }

    const handleTimeUpdate = () => {
      const time = audio.currentTime
      setCurrentTime(time)
      onTimeUpdate?.(time)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onPause?.()
    }

    audio.addEventListener('loadeddata', handleLoadedData)
    audio.addEventListener('error', handleError)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('loadeddata', handleLoadedData)
      audio.removeEventListener('error', handleError)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [onTimeUpdate, onPause])

  const togglePlayPause = () => {
    const audio = audioRef.current
    if (!audio || isLoading) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
      onPause?.()
    } else {
      audio.play()
      setIsPlaying(true)
      onPlay?.()
    }
  }

  const handleSeek = (e) => {
    const audio = audioRef.current
    if (!audio || isLoading) return

    const rect = progressRef.current.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const percentage = clickX / rect.width
    const newTime = percentage * duration
    
    audio.currentTime = newTime
    setCurrentTime(newTime)
    onTimeUpdate?.(newTime)
  }

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    if (audioRef.current) {
      audioRef.current.volume = newVolume
    }
  }

  const handleSpeedChange = (e) => {
    const newSpeed = parseFloat(e.target.value)
    setPlaybackSpeed(newSpeed)
    if (audioRef.current) {
      audioRef.current.playbackRate = newSpeed
    }
  }

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0

  if (error) {
    return (
      <div className="audio-player error">
        <p>❌ {error}</p>
      </div>
    )
  }

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
        style={{ display: 'none' }}
      />
      
      <div className="player-controls">
        <button
          className="play-pause-btn"
          onClick={togglePlayPause}
          disabled={isLoading}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isLoading ? '⏳' : isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <div className="time-display">
          <span>{formatTime(currentTime)}</span>
          <span>/</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      <div className="progress-container">
        <div
          ref={progressRef}
          className="progress-bar"
          onClick={handleSeek}
          role="slider"
          aria-label="Audio progress"
        >
          <div
            className="progress-fill"
            style={{ width: `${progressPercentage}%` }}
          />
          <div
            className="progress-handle"
            style={{ left: `${progressPercentage}%` }}
          />
        </div>
      </div>

      <div className="player-settings">
        <div className="volume-control">
          <label htmlFor="volume">🔊</label>
          <input
            id="volume"
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={handleVolumeChange}
            className="volume-slider"
          />
        </div>
        
        <div className="speed-control">
          <label htmlFor="speed">Speed:</label>
          <select
            id="speed"
            value={playbackSpeed}
            onChange={handleSpeedChange}
            className="speed-select"
          >
            <option value={0.5}>0.5x</option>
            <option value={0.75}>0.75x</option>
            <option value={1}>1x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>
        </div>
      </div>

    </div>
  )
}

export default AudioPlayer
