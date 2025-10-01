import React, { useCallback, useState, useEffect } from 'react';
import { Card, Button, ButtonGroup, Form, Row, Col } from 'react-bootstrap';
import { useRealtimeStore } from '../store/realtimeStore';

const PlaybackController = ({ videoRef, onPlaybackChange }) => {
  const store = useRealtimeStore();
  const { playbackState, isConnected } = store;
  
  const [isSeeking, setIsSeeking] = useState(false);
  const [seekTime, setSeekTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [volume, setVolume] = useState(1.0);

  // Update local state when store changes
  useEffect(() => {
    setSeekTime(playbackState.currentTime);
    setPlaybackRate(playbackState.playbackRate);
    setVolume(playbackState.volume);
  }, [playbackState]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    if (!videoRef.current) return;

    if (playbackState.isPlaying) {
      videoRef.current.pause();
      store.updatePlaybackState({ isPlaying: false, isPaused: true });
    } else {
      videoRef.current.play();
      store.updatePlaybackState({ isPlaying: true, isPaused: false });
    }
  }, [videoRef, playbackState.isPlaying, store]);

  // Handle stop
  const handleStop = useCallback(() => {
    if (!videoRef.current) return;

    videoRef.current.pause();
    videoRef.current.currentTime = 0;
    store.updatePlaybackState({
      isPlaying: false,
      isPaused: true,
      currentTime: 0,
      isSeeking: false
    });
  }, [videoRef, store]);

  // Handle seek
  const handleSeek = useCallback((time) => {
    if (!videoRef.current) return;

    const seekTime = Math.max(0, Math.min(time, playbackState.duration));
    videoRef.current.currentTime = seekTime;
    
    store.updatePlaybackState({
      currentTime: seekTime,
      isSeeking: true
    });

    // Clear seeking state after a short delay
    setTimeout(() => {
      store.updatePlaybackState({ isSeeking: false });
    }, 100);
  }, [videoRef, playbackState.duration, store]);

  // Handle seek input change
  const handleSeekInputChange = useCallback((e) => {
    const time = parseFloat(e.target.value);
    setSeekTime(time);
  }, []);

  // Handle seek input submit
  const handleSeekSubmit = useCallback((e) => {
    e.preventDefault();
    handleSeek(seekTime);
  }, [seekTime, handleSeek]);

  // Handle playback rate change
  const handlePlaybackRateChange = useCallback((rate) => {
    if (!videoRef.current) return;

    videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
    store.updatePlaybackState({ playbackRate: rate });
  }, [videoRef, store]);

  // Handle volume change
  const handleVolumeChange = useCallback((vol) => {
    if (!videoRef.current) return;

    videoRef.current.volume = vol;
    setVolume(vol);
    store.updatePlaybackState({ volume: vol });
  }, [videoRef, store]);

  // Handle step forward/backward
  const handleStep = useCallback((direction) => {
    if (!videoRef.current) return;

    const stepSize = 10; // 10 seconds
    const currentTime = videoRef.current.currentTime;
    const newTime = direction === 'forward' 
      ? Math.min(currentTime + stepSize, playbackState.duration)
      : Math.max(currentTime - stepSize, 0);
    
    handleSeek(newTime);
  }, [videoRef, playbackState.duration, handleSeek]);

  // Format time for display
  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Calculate progress percentage
  const progressPercentage = playbackState.duration > 0 
    ? (playbackState.currentTime / playbackState.duration) * 100 
    : 0;

  return (
    <Card className="playback-controller">
      <Card.Body>
        <h6 className="mb-3">Playback Controls</h6>
        
        {/* Main Controls */}
        <div className="main-controls mb-3">
          <ButtonGroup className="me-2">
            <Button
              variant="outline-primary"
              onClick={() => handleStep('backward')}
              disabled={!isConnected || playbackState.currentTime <= 0}
              title="Step backward 10s"
            >
              <i className="fas fa-step-backward"></i>
            </Button>
            
            <Button
              variant={playbackState.isPlaying ? "danger" : "success"}
              onClick={handlePlayPause}
              disabled={!isConnected}
              title={playbackState.isPlaying ? "Pause" : "Play"}
            >
              <i className={`fas fa-${playbackState.isPlaying ? 'pause' : 'play'}`}></i>
            </Button>
            
            <Button
              variant="outline-primary"
              onClick={() => handleStep('forward')}
              disabled={!isConnected || playbackState.currentTime >= playbackState.duration}
              title="Step forward 10s"
            >
              <i className="fas fa-step-forward"></i>
            </Button>
            
            <Button
              variant="outline-secondary"
              onClick={handleStop}
              disabled={!isConnected}
              title="Stop"
            >
              <i className="fas fa-stop"></i>
            </Button>
          </ButtonGroup>
        </div>

        {/* Progress Bar */}
        <div className="progress-section mb-3">
          <div className="d-flex justify-content-between mb-1">
            <small>{formatTime(playbackState.currentTime)}</small>
            <small>{formatTime(playbackState.duration)}</small>
          </div>
          <div className="progress" style={{ height: '8px' }}>
            <div
              className="progress-bar"
              role="progressbar"
              style={{ width: `${progressPercentage}%` }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const percentage = clickX / rect.width;
                const newTime = percentage * playbackState.duration;
                handleSeek(newTime);
              }}
            ></div>
          </div>
        </div>

        {/* Seek Input */}
        <Form onSubmit={handleSeekSubmit} className="mb-3">
          <Row className="align-items-center">
            <Col xs={8}>
              <Form.Control
                type="number"
                min="0"
                max={playbackState.duration}
                step="0.1"
                value={seekTime.toFixed(1)}
                onChange={handleSeekInputChange}
                placeholder="Seek to time (seconds)"
                disabled={!isConnected}
              />
            </Col>
            <Col xs={4}>
              <Button
                type="submit"
                variant="outline-primary"
                size="sm"
                disabled={!isConnected}
                className="w-100"
              >
                Seek
              </Button>
            </Col>
          </Row>
        </Form>

        {/* Playback Rate */}
        <div className="playback-rate mb-3">
          <Form.Label className="small">Playback Rate</Form.Label>
          <ButtonGroup size="sm" className="w-100">
            {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map(rate => (
              <Button
                key={rate}
                variant={playbackRate === rate ? "primary" : "outline-primary"}
                onClick={() => handlePlaybackRateChange(rate)}
                disabled={!isConnected}
              >
                {rate}x
              </Button>
            ))}
          </ButtonGroup>
        </div>

        {/* Volume Control */}
        <div className="volume-control mb-3">
          <Form.Label className="small">Volume</Form.Label>
          <div className="d-flex align-items-center">
            <i className="fas fa-volume-down me-2"></i>
            <Form.Range
              min="0"
              max="1"
              step="0.1"
              value={volume}
              onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
              disabled={!isConnected}
              className="flex-grow-1"
            />
            <i className="fas fa-volume-up ms-2"></i>
            <small className="ms-2">{Math.round(volume * 100)}%</small>
          </div>
        </div>

        {/* Status Display */}
        <div className="status-display">
          <div className="d-flex justify-content-between align-items-center">
            <div className="status-info">
              <small className="text-muted">
                {playbackState.isPlaying ? 'Playing' : 'Paused'}
                {playbackState.isSeeking && ' | Seeking...'}
              </small>
            </div>
            <div className="connection-status">
              <span className={`badge ${isConnected ? 'bg-success' : 'bg-danger'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Keyboard Shortcuts Info */}
        <div className="keyboard-shortcuts mt-3">
          <small className="text-muted">
            <strong>Shortcuts:</strong> Space (play/pause), ← → (seek), ↑ ↓ (volume)
          </small>
        </div>
      </Card.Body>
    </Card>
  );
};

export default PlaybackController;
