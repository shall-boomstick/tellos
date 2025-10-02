import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import { useRealtimeStore, useConnectionState, usePlaybackState, useTranscriptData, useEmotionData } from '../store/realtimeStore';
import RealtimeVideoPlayer from '../components/RealtimeVideoPlayer';
import RealtimeTranslation from '../components/RealtimeTranslation';
import EmotionMeter from '../components/EmotionMeter';
import useVideoTranslationSync from '../hooks/useVideoTranslationSync';
import useEmotionVideoSync from '../hooks/useEmotionVideoSync';
import websocketService from '../services/websocket';

const EnhancedDashboard = ({ fileData }) => {
  const videoRef = useRef(null);
  const store = useRealtimeStore();
  
  // Store selectors
  const { isConnected, sessionId, fileId } = useConnectionState();
  const playbackState = usePlaybackState();
  const { transcriptData, currentTranscript } = useTranscriptData();
  const { emotionData, currentEmotion, currentEmotionIntensity } = useEmotionData();
  
  // Local state
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('connecting');

  // Initialize WebSocket connections
  useEffect(() => {
    const initializeConnections = async () => {
      try {
        setProcessingStatus('connecting');
        
        // Set up store with file data
        store.setSession(fileData.file_id, fileData.file_id);
        
        // Connect to WebSocket services
        await websocketService.connect(`processing-${fileData.file_id}`, {
          url: `ws://localhost:8000/ws/processing/${fileData.file_id}`,
          onMessage: handleProcessingMessage,
          onError: handleError,
          onClose: handleDisconnect
        });

        await websocketService.connect(`playback-${fileData.file_id}`, {
          url: `ws://localhost:8000/ws/playback/${fileData.file_id}`,
          onMessage: handlePlaybackMessage,
          onError: handleError,
          onClose: handleDisconnect
        });

        await websocketService.connect(`emotion-${fileData.file_id}`, {
          url: `ws://localhost:8000/ws/emotion/${fileData.file_id}`,
          onMessage: handleEmotionMessage,
          onError: handleError,
          onClose: handleDisconnect
        });

        store.setConnection(true, 'connected');
        setProcessingStatus('connected');
        setIsInitialized(true);
        
      } catch (err) {
        console.error('Error initializing connections:', err);
        setError('Failed to connect to real-time services');
        setProcessingStatus('error');
      }
    };

    initializeConnections();

    return () => {
      // Cleanup connections
      websocketService.disconnect(`processing-${fileData.file_id}`);
      websocketService.disconnect(`playback-${fileData.file_id}`);
      websocketService.disconnect(`emotion-${fileData.file_id}`);
      store.setConnection(false, 'disconnected');
    };
  }, [fileData.file_id]);

  // WebSocket message handlers
  const handleProcessingMessage = (message) => {
    console.log('Processing message:', message);
    
    switch (message.type) {
      case 'connected':
        setProcessingStatus('processing');
        break;
      case 'progress_update':
        setProcessingStatus(message.status);
        break;
      case 'completed':
        setProcessingStatus('completed');
        break;
      case 'error':
        setError(message.message);
        setProcessingStatus('error');
        break;
    }
  };

  const handlePlaybackMessage = (message) => {
    console.log('Playback message:', message);
    
    switch (message.type) {
      case 'connected':
        console.log('Playback WebSocket connected');
        break;
      case 'time_update':
        store.updatePlaybackState({
          currentTime: message.current_time,
          isPlaying: message.is_playing
        });
        break;
      case 'transcript_update':
        // Handle transcript updates
        if (message.current_word && message.current_word !== '...') {
          // Add transcript segment if needed
          const transcriptSegment = {
            text: message.current_word,
            start_time: message.current_time,
            end_time: message.current_time + 0.5,
            confidence: 0.8,
            timestamp: Date.now() / 1000
          };
          store.addTranscript(transcriptSegment);
        }
        break;
    }
  };

  const handleEmotionMessage = (message) => {
    console.log('Emotion message:', message);
    
    switch (message.type) {
      case 'connected':
        console.log('Emotion WebSocket connected');
        break;
      case 'emotion_update':
        // Add emotion data to store
        if (message.emotion) {
          store.addEmotion(message.emotion);
        }
        break;
      case 'emotion_complete':
        console.log('Emotion analysis completed');
        break;
      case 'error':
        setError(`Emotion analysis error: ${message.message}`);
        break;
    }
  };

  const handleError = (error) => {
    console.error('WebSocket error:', error);
    setError('Connection error occurred');
  };

  const handleDisconnect = () => {
    console.log('WebSocket disconnected');
    store.setConnection(false, 'disconnected');
  };

  // Video playback handlers
  const handlePlaybackChange = (updates) => {
    store.updatePlaybackState(updates);
    
    // Send playback updates via WebSocket
    websocketService.send(`playback-${fileData.file_id}`, {
      type: 'time_update',
      current_time: updates.currentTime || playbackState.currentTime,
      is_playing: updates.isPlaying !== undefined ? updates.isPlaying : playbackState.isPlaying
    });
  };

  const handleSeek = (time) => {
    store.updatePlaybackState({ currentTime: time, isSeeking: true });
    
    // Send seek command via WebSocket
    websocketService.send(`playback-${fileData.file_id}`, {
      type: 'seek',
      time: time
    });
  };

  // Use sync hooks
  const videoSync = useVideoTranslationSync(videoRef, playbackState.currentTime);
  const emotionSync = useEmotionVideoSync(videoRef, playbackState.currentTime);

  // Get processing status message
  const getStatusMessage = () => {
    switch (processingStatus) {
      case 'connecting': return 'Connecting to services...';
      case 'connected': return 'Connected to real-time services';
      case 'processing': return 'Processing audio...';
      case 'completed': return 'Processing complete!';
      case 'error': return 'Connection error';
      default: return 'Initializing...';
    }
  };

  const getStatusColor = () => {
    switch (processingStatus) {
      case 'completed': return 'success';
      case 'error': return 'danger';
      case 'connected': return 'info';
      default: return 'primary';
    }
  };

  if (!isInitialized) {
    return (
      <Container className="py-5">
        <Row className="justify-content-center">
          <Col md={8}>
            <Card>
              <Card.Body className="text-center py-5">
                <Spinner animation="border" className="mb-3" />
                <h4>Initializing Dashboard</h4>
                <p className="text-muted">{getStatusMessage()}</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      {/* Header */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <h4 className="mb-0">
                  <i className="fas fa-video me-2"></i>
                  {fileData.filename}
                </h4>
                <div className="d-flex align-items-center gap-3">
                  <span className={`badge bg-${getStatusColor()}`}>
                    {getStatusMessage()}
                  </span>
                  <span className={`badge ${isConnected ? 'bg-success' : 'bg-danger'}`}>
                    <i className="fas fa-circle me-1"></i>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </Card.Header>
          </Card>
        </Col>
      </Row>

      {/* Error Alert */}
      {error && (
        <Row className="mb-4">
          <Col>
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              <i className="fas fa-exclamation-triangle me-2"></i>
              {error}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Main Content */}
      <Row>
        {/* Video Player */}
        <Col lg={8}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-play me-2"></i>
                Video Player
              </h5>
            </Card.Header>
            <Card.Body>
              <RealtimeVideoPlayer
                fileId={fileData.file_id}
                playbackState={playbackState}
                onPlaybackChange={handlePlaybackChange}
                onSeek={handleSeek}
                isConnected={isConnected}
              />
            </Card.Body>
          </Card>

          {/* Translation */}
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-language me-2"></i>
                Live Translation
              </h5>
            </Card.Header>
            <Card.Body>
              <RealtimeTranslation
                transcriptData={transcriptData}
                currentTranscript={currentTranscript}
                playbackState={playbackState}
                isConnected={isConnected}
                emotionData={emotionData}
              />
            </Card.Body>
          </Card>
        </Col>

        {/* Emotion Analysis Sidebar */}
        <Col lg={4}>
          <Card className="mb-4">
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-heart me-2"></i>
                Emotional Analysis
              </h5>
            </Card.Header>
            <Card.Body>
              <EmotionMeter
                emotionData={emotionData}
                currentTime={playbackState.currentTime}
                playbackState={playbackState}
                isConnected={isConnected}
              />
            </Card.Body>
          </Card>

          {/* Statistics */}
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="fas fa-chart-bar me-2"></i>
                Analysis Statistics
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-value">{transcriptData.length}</div>
                  <div className="stat-label">Transcript Segments</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{emotionData.length}</div>
                  <div className="stat-label">Emotion Points</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {Math.floor(playbackState.duration / 60)}:
                    {Math.floor(playbackState.duration % 60).toString().padStart(2, '0')}
                  </div>
                  <div className="stat-label">Duration</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {currentEmotionIntensity}%
                  </div>
                  <div className="stat-label">Current Intensity</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Custom Styles */}
      <style jsx>{`
        .stats-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        
        .stat-item {
          text-align: center;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 0.5rem;
        }
        
        .stat-value {
          font-size: 1.5rem;
          font-weight: bold;
          color: var(--bs-primary);
        }
        
        .stat-label {
          font-size: 0.875rem;
          color: var(--bs-secondary);
          margin-top: 0.25rem;
        }
      `}</style>
    </Container>
  );
};

export default EnhancedDashboard;
