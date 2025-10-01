import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Card } from 'react-bootstrap';

const RealtimeVideoPlayer = ({
  fileId,
  playbackState,
  onPlaybackChange,
  onSeek,
  isConnected
}) => {
  const videoRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Video source URL with browser compatibility check
  // Now proxied through vite.config.js to backend:8000
  const videoSrc = fileId ? `/video/stream/${fileId}` : null;
  
  // Check browser video codec support
  const checkBrowserSupport = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    const mp4Support = video.canPlayType('video/mp4; codecs="avc1.42E01E"');
    const webmSupport = video.canPlayType('video/webm; codecs="vp8"');
    
    console.log('Browser video support:');
    console.log('MP4 H.264:', mp4Support);
    console.log('WebM VP8:', webmSupport);
    
    return {
      mp4: mp4Support !== '',
      webm: webmSupport !== ''
    };
  }, []);

  // Handle video load
  useEffect(() => {
    if (videoRef.current && videoSrc) {
      const video = videoRef.current;
      
      // Clear any previous errors and reset retry count
      setError(null);
      setIsLoading(true);
      setRetryCount(0);
      
      const handleLoadStart = () => {
        console.log('Video load started:', videoSrc);
        setIsLoading(true);
        setError(null);
      };
      
      const handleLoadedMetadata = () => {
        console.log('Video metadata loaded:', {
          duration: video.duration,
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState
        });
      };
      
      const handleLoadedData = () => {
        console.log('Video data loaded successfully');
        setIsLoading(false);
        // Update duration when video loads
        onPlaybackChange({
          duration: video.duration,
          currentTime: video.currentTime
        });
      };
      
      const handleCanPlay = () => {
        console.log('Video can start playing');
        setIsLoading(false);
        setError(null); // Clear any previous errors
      };
      
      const handleProgress = () => {
        console.log('Video loading progress');
      };
      
      const handleWaiting = () => {
        console.log('Video is waiting for data');
        setIsLoading(true);
      };
      
      const handlePlaying = () => {
        console.log('Video started playing');
        setIsLoading(false);
        setError(null);
      };
      
      const handleError = (e) => {
        const video = e.target;
        const errorCode = video.error?.code;
        const errorMessage = video.error?.message || 'Unknown error';
        
        let errorMsg = `Failed to load video: ${errorMessage}`;
        let troubleshootingMsg = '';
        
        if (errorCode) {
          switch (errorCode) {
            case 1:
              errorMsg += ' (MEDIA_ERR_ABORTED)';
              troubleshootingMsg = 'Video loading was aborted. Please try refreshing the page.';
              break;
            case 2:
              errorMsg += ' (MEDIA_ERR_NETWORK)';
              troubleshootingMsg = 'Network error while loading video. Check your connection and try again.';
              break;
            case 3:
              errorMsg += ' (MEDIA_ERR_DECODE)';
              troubleshootingMsg = 'Video format error. The video file may be corrupted or in an unsupported format.';
              break;
            case 4:
              errorMsg += ' (MEDIA_ERR_SRC_NOT_SUPPORTED)';
              troubleshootingMsg = 'Video format not supported by your browser. Try the test page at http://100.93.116.1:8081/test_video_playback.html';
              
              // Try to retry with a fresh video element
              if (retryCount < 2) {
                console.log(`Retrying video load (attempt ${retryCount + 1})`);
                setTimeout(() => {
                  setRetryCount(prev => prev + 1);
                  setError(null);
                  setIsLoading(true);
                  
                  // Force re-render of video element
                  if (videoRef.current) {
                    const video = videoRef.current;
                    video.removeAttribute('src');
                    video.load();
                    setTimeout(() => {
                      video.src = videoSrc;
                      video.load();
                    }, 200);
                  }
                }, 1000);
                return; // Don't set error state yet
              }
              break;
          }
        }
        
        setError(`${errorMsg}${troubleshootingMsg ? ` - ${troubleshootingMsg}` : ''}`);
        setIsLoading(false);
        
        // Enhanced logging for debugging
        console.error('=== Video Load Error Debug Info ===');
        console.error('Error event:', e);
        console.error('Video error code:', errorCode);
        console.error('Video error message:', errorMessage);
        console.error('Video src:', videoSrc);
        console.error('Video network state:', video.networkState);
        console.error('Video ready state:', video.readyState);
        console.error('Video current src:', video.currentSrc);
        console.error('Video can play type mp4:', video.canPlayType('video/mp4'));
        console.error('Video can play type webm:', video.canPlayType('video/webm'));
        console.error('User agent:', navigator.userAgent);
        console.error('=====================================');
        
        // Try to fetch the video URL directly to check if it's accessible
        if (videoSrc) {
          fetch(videoSrc, { method: 'HEAD' })
            .then(response => {
              console.log('Video URL HEAD request status:', response.status);
              console.log('Video URL content-type:', response.headers.get('content-type'));
              console.log('Video URL content-length:', response.headers.get('content-length'));
              
              // If the URL is accessible but video won't play, suggest direct access
              if (response.ok) {
                console.log('Video URL is accessible. Try direct access:', videoSrc);
                console.log('Or test page:', 'http://100.93.116.1:8081/test_video_playback.html');
              }
            })
            .catch(fetchError => {
              console.error('Video URL fetch error:', fetchError);
            });
        }
      };
      
      const handleTimeUpdate = () => {
        onPlaybackChange({
          currentTime: video.currentTime,
          isPlaying: !video.paused,
          isPaused: video.paused
        });
      };
      
      const handlePlay = () => {
        onPlaybackChange({ isPlaying: true, isPaused: false });
      };
      
      const handlePause = () => {
        onPlaybackChange({ isPlaying: false, isPaused: true });
      };
      
      const handleSeeking = () => {
        onPlaybackChange({ isSeeking: true });
      };
      
      const handleSeeked = () => {
        onPlaybackChange({ isSeeking: false });
        onSeek(video.currentTime);
      };

      // Add event listeners
      video.addEventListener('loadstart', handleLoadStart);
      video.addEventListener('loadedmetadata', handleLoadedMetadata);
      video.addEventListener('loadeddata', handleLoadedData);
      video.addEventListener('canplay', handleCanPlay);
      video.addEventListener('progress', handleProgress);
      video.addEventListener('waiting', handleWaiting);
      video.addEventListener('playing', handlePlaying);
      video.addEventListener('error', handleError);
      video.addEventListener('timeupdate', handleTimeUpdate);
      video.addEventListener('play', handlePlay);
      video.addEventListener('pause', handlePause);
      video.addEventListener('seeking', handleSeeking);
      video.addEventListener('seeked', handleSeeked);

      // Check browser support before loading
      const support = checkBrowserSupport();
      console.log('Browser codec support:', support);
      
      // Reset video element state
      video.removeAttribute('src');
      video.load(); // Clear any previous source
      
      // Set video source with a small delay to ensure clean state
      setTimeout(() => {
        console.log('Setting video source:', videoSrc);
        video.src = videoSrc;
        video.load();
      }, 100);

      // Cleanup
      return () => {
        video.removeEventListener('loadstart', handleLoadStart);
        video.removeEventListener('loadedmetadata', handleLoadedMetadata);
        video.removeEventListener('loadeddata', handleLoadedData);
        video.removeEventListener('canplay', handleCanPlay);
        video.removeEventListener('progress', handleProgress);
        video.removeEventListener('waiting', handleWaiting);
        video.removeEventListener('playing', handlePlaying);
        video.removeEventListener('error', handleError);
        video.removeEventListener('timeupdate', handleTimeUpdate);
        video.removeEventListener('play', handlePlay);
        video.removeEventListener('pause', handlePause);
        video.removeEventListener('seeking', handleSeeking);
        video.removeEventListener('seeked', handleSeeked);
      };
    }
  }, [videoSrc, onPlaybackChange, onSeek]);

  // Sync video with playback state
  useEffect(() => {
    if (videoRef.current && playbackState) {
      const video = videoRef.current;
      
      // Sync current time if there's a significant difference
      const timeDiff = Math.abs(video.currentTime - playbackState.currentTime);
      if (timeDiff > 0.5) { // 500ms tolerance
        video.currentTime = playbackState.currentTime;
      }
    }
  }, [playbackState.currentTime]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
      } else {
        videoRef.current.pause();
      }
    }
  }, []);

  // Handle seek
  const handleSeekTo = useCallback((time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  }, []);

  // Handle volume change
  const handleVolumeChange = useCallback((volume) => {
    if (videoRef.current) {
      videoRef.current.volume = volume;
    }
  }, []);

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
    <div className="realtime-video-player">
      {/* Video Element */}
      <div className="video-container position-relative">
        <video
          ref={videoRef}
          key={`${fileId}-${retryCount}`}
          className="w-100"
          style={{ maxHeight: '400px' }}
          controls
          preload="auto"
          playsInline
        >
          Your browser does not support the video tag.
        </video>
        
        {/* Loading Overlay */}
        {isLoading && (
          <div className="position-absolute top-50 start-50 translate-middle">
            <div className="spinner-border text-light" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        )}
        
        {/* Error Overlay */}
        {error && (
          <div className="position-absolute top-50 start-50 translate-middle">
            <div className="alert alert-danger text-center">
              {error}
            </div>
          </div>
        )}
      </div>

      {/* Custom Controls */}
      <div className="video-controls p-3 bg-dark text-white">
        <div className="d-flex align-items-center mb-2">
          {/* Play/Pause Button */}
          <button
            className="btn btn-outline-light btn-sm me-2"
            onClick={handlePlayPause}
            disabled={!isConnected}
          >
            <i className={`fas fa-${playbackState.isPlaying ? 'pause' : 'play'}`}></i>
          </button>
          
          {/* Time Display */}
          <span className="me-3">
            {formatTime(playbackState.currentTime)} / {formatTime(playbackState.duration)}
          </span>
          
          {/* Connection Status */}
          <div className="ms-auto">
            <span className={`badge ${isConnected ? 'bg-success' : 'bg-danger'}`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="progress mb-2" style={{ height: '6px' }}>
          <div
            className="progress-bar"
            role="progressbar"
            style={{ width: `${progressPercentage}%` }}
            aria-valuenow={progressPercentage}
            aria-valuemin="0"
            aria-valuemax="100"
          ></div>
        </div>
        
        {/* Volume Control */}
        <div className="d-flex align-items-center">
          <i className="fas fa-volume-up me-2"></i>
          <input
            type="range"
            className="form-range flex-grow-1 me-3"
            min="0"
            max="1"
            step="0.1"
            defaultValue="1"
            onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
          />
          <i className="fas fa-volume-mute"></i>
        </div>
      </div>

      {/* Video Info */}
      <div className="video-info p-2 bg-light">
        <small className="text-muted">
          File ID: {fileId} | 
          Duration: {formatTime(playbackState.duration)} | 
          Status: {playbackState.isPlaying ? 'Playing' : 'Paused'}
          {playbackState.isSeeking && ' | Seeking...'}
        </small>
      </div>
    </div>
  );
};

export default RealtimeVideoPlayer;
