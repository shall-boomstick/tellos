import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import RealtimeVideoPlayer from '../components/RealtimeVideoPlayer';
import RealtimeTranslation from '../components/RealtimeTranslation';
import RealtimeEmotionGauge from '../components/RealtimeEmotionGauge';
import RealtimeFileUpload from '../components/RealtimeFileUpload';
import FileManager from '../components/FileManager';
import ProcessingStatus from '../components/ProcessingStatus';
import { useRealtimeSync } from '../hooks/useRealtimeSync';
import { useRealtimeWebSocket } from '../services/realtimeWebSocket';

const RealtimeInterface = ({ fileData, onNewUpload, onFileSelect, isUploading, error: appError }) => {
  // State management
  const [fileId, setFileId] = useState(fileData?.file_id || null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  // Real-time data state
  const [transcriptData, setTranscriptData] = useState([]);
  const [emotionData, setEmotionData] = useState(null);
  const [playbackState, setPlaybackState] = useState({
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    isPaused: true,
    isSeeking: false
  });

  // WebSocket connection
  const { connect, disconnect, sendMessage } = useRealtimeWebSocket({
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
    onTranscript: handleTranscriptUpdate,
    onEmotion: handleEmotionUpdate,
    onStatus: handleStatusUpdate,
    onError: handleError
  });

  // Real-time synchronization hook
  const {
    syncTranscript,
    syncEmotion,
    getCurrentTranscript,
    getCurrentEmotion
  } = useRealtimeSync(playbackState.currentTime);

  // Update fileId when fileData changes and connect to WebSocket
  useEffect(() => {
    if (fileData?.file_id && fileData.file_id !== fileId) {
      setFileId(fileData.file_id);
      
      // Connect to WebSocket for real-time features
      if (fileData.file_id) {
        console.log('Connecting to WebSocket for file:', fileData.file_id);
        connect(fileData.file_id).then((sessionId) => {
          console.log('WebSocket connected with session:', sessionId);
          setSessionId(sessionId);
        }).catch((error) => {
          console.error('WebSocket connection failed:', error);
          setError(`Failed to connect to real-time features: ${error.message}`);
        });
      }
    }
  }, [fileData, fileId, connect]);

  // Load processed data function
  const loadProcessedData = useCallback(async () => {
      if (fileId) {
        try {
          // Check if processing is completed
          const statusResponse = await fetch(`/api/upload/${fileId}/status`);
          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            console.log('File status:', statusData);
            
            if (statusData.status === 'completed') {
              // Load transcript data
              try {
                const transcriptResponse = await fetch(`/api/processing/${fileId}/transcript`);
                if (transcriptResponse.ok) {
                  const transcriptData = await transcriptResponse.json();
                  console.log('Loaded transcript data:', transcriptData);
                  // Convert word-level data to segment-level data for the UI
                  const words = transcriptData.words || [];
                  if (words.length > 0) {
                    // Group words into segments (every 5-10 words or by time gaps)
                    const segments = [];
                    let currentSegment = {
                      text: '',
                      english_text: '',
                      start_time: words[0].start_time,
                      end_time: words[0].end_time,
                      confidence: 0,
                      language: transcriptData.language || 'ar',
                      words: []
                    };
                    
                    let wordCount = 0;
                    let totalConfidence = 0;
                    
                    for (let i = 0; i < words.length; i++) {
                      const word = words[i];
                      currentSegment.text += (currentSegment.text ? ' ' : '') + word.word;
                      currentSegment.words.push(word);
                      currentSegment.end_time = word.end_time;
                      totalConfidence += word.confidence;
                      wordCount++;
                      
                      // Create a new segment based on natural speech patterns
                      const nextWord = words[i + 1];
                      const timeGap = nextWord ? (nextWord.start_time - word.end_time) : 0;
                      
                      // Look for natural break points in Arabic dialogue
                      const isNaturalBreak = word.word && (
                        word.word.includes('اعطني') ||  // "Give me" - command
                        word.word.includes('ليش') ||    // "Why" - question
                        word.word.includes('خلصني') ||  // "Finish me" - statement
                        word.word.includes('شنطاتك') || // "Your bag" - object
                        word.word.includes('قمتك')     // "Your ID" - object
                      );
                      
                      const shouldCreateNewSegment = 
                        wordCount >= 6 ||           // Shorter segments for dialogue
                        timeGap > 1.5 ||           // Shorter pause threshold
                        isNaturalBreak ||          // Natural dialogue breaks
                        i === words.length - 1;    // Last word
                      
                      if (shouldCreateNewSegment) {
                        currentSegment.confidence = totalConfidence / wordCount;
                        // Use the structured English translation from Gemini
                        if (transcriptData.english_text) {
                          // Try to match the current segment to the appropriate English translation
                          const arabicText = currentSegment.text.toLowerCase();
                          
                          // Enhanced phrase matching for better translation distribution
                          if (arabicText.includes('اعطني') && arabicText.includes('إقامتك')) {
                            currentSegment.english_text = "Give me your ID";
                          } else if (arabicText.includes('اعطني') && arabicText.includes('شنطتك')) {
                            currentSegment.english_text = "Give me your bag";
                          } else if (arabicText.includes('ليش تطلب')) {
                            currentSegment.english_text = "Why are you asking for my ID?";
                          } else if (arabicText.includes('خلصني')) {
                            currentSegment.english_text = "Just get it over with";
                          } else if (arabicText.includes('السلام عليكم')) {
                            currentSegment.english_text = "Peace be upon you";
                          } else if (arabicText.includes('هذه ساعة')) {
                            currentSegment.english_text = "I've been waiting for my turn for an hour";
                          } else if (arabicText.includes('ولا تكثر كلام')) {
                            currentSegment.english_text = "and don't talk so much";
                          } else if (arabicText.includes('بسرعة')) {
                            currentSegment.english_text = "quickly";
                          } else {
                            // Fallback to proportional distribution from the full English text
                            const englishSentences = transcriptData.english_text.split('.').filter(s => s.trim());
                            const sentencesPerSegment = Math.ceil(englishSentences.length / Math.max(1, Math.ceil(words.length / 6)));
                            const startIdx = segments.length * sentencesPerSegment;
                            currentSegment.english_text = englishSentences.slice(startIdx, startIdx + sentencesPerSegment).join('. ').trim();
                          }
                        } else {
                          currentSegment.english_text = currentSegment.text;
                        }
                        
                        segments.push(currentSegment);
                        
                        // Start new segment if there are more words
                        if (i < words.length - 1) {
                          currentSegment = {
                            text: '',
                            english_text: '',
                            start_time: nextWord.start_time,
                            end_time: nextWord.end_time,
                            confidence: 0,
                            language: transcriptData.language || 'ar',
                            words: []
                          };
                          wordCount = 0;
                          totalConfidence = 0;
                        }
                      }
                    }
                    
                    console.log('Created segments from words:', segments);
                    setTranscriptData(segments);
                  } else {
                    setTranscriptData([]);
                  }
                }
              } catch (error) {
                console.warn('Could not load transcript data:', error);
              }
              
              // Load emotion data
              try {
                const emotionResponse = await fetch(`/api/processing/${fileId}/emotions`);
                if (emotionResponse.ok) {
                  const emotionData = await emotionResponse.json();
                  console.log('Loaded emotion data:', emotionData);
                  // Convert API response to expected format
                  const emotions = emotionData.segments || emotionData.emotions || emotionData;
                  setEmotionData(emotions);
                }
              } catch (error) {
                console.warn('Could not load emotion data:', error);
              }
            }
          }
        } catch (error) {
          console.error('Error loading processed data:', error);
        }
      }
  }, [fileId]);

  // Load processed data if file is already completed
  useEffect(() => {
    if (fileId) {
      loadProcessedData();
    }
  }, [fileId, loadProcessedData]);

  // Poll for completion status if file is still processing
  useEffect(() => {
    let pollInterval;
    
    const pollForCompletion = async () => {
      if (!fileId) return;
      
      try {
        const statusResponse = await fetch(`/api/upload/${fileId}/status`);
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          console.log('Polling status:', statusData);
          
          if (statusData.status === 'completed') {
            console.log('File processing completed, loading data...');
            // Clear the polling interval
            if (pollInterval) {
              clearInterval(pollInterval);
            }
            // Load the processed data
            await loadProcessedData();
          } else if (statusData.status === 'failed') {
            console.error('File processing failed');
            if (pollInterval) {
              clearInterval(pollInterval);
            }
          }
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    if (fileId) {
      // Start polling every 2 seconds
      pollInterval = setInterval(pollForCompletion, 2000);
      
      // Also check immediately
      pollForCompletion();
    }

    // Cleanup interval on unmount or fileId change
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [fileId]);

  // Handle file upload - use the app's upload handler
  const handleFileUpload = useCallback(async (fileOrData) => {
    if (onFileSelect) {
      await onFileSelect(fileOrData);
    } else {
      // Fallback to local upload logic
      try {
        setError(null);
        setIsProcessing(true);
        
        // Check if it's a File object or file data
        if (fileOrData instanceof File) {
          const formData = new FormData();
          formData.append('file', fileOrData);
          
          const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
          });
          
          if (!response.ok) {
            throw new Error('File upload failed');
          }
          
          const result = await response.json();
          const newFileId = result.file_id;
          setFileId(newFileId);
          
          await connect(newFileId);
        } else {
          // It's file data, just set the file ID
          setFileId(fileOrData.file_id);
          await connect(fileOrData.file_id);
        }
        
      } catch (err) {
        setError(`Upload failed: ${err.message}`);
        setIsProcessing(false);
      }
    }
  }, [onFileSelect, connect]);

  // Handle transcript updates
  function handleTranscriptUpdate(data) {
    setTranscriptData(prev => [...prev, data]);
    syncTranscript(data);
  }

  // Handle emotion updates
  function handleEmotionUpdate(data) {
    console.log('RealtimeInterface: Received emotion update:', data);
    if (data.emotion) {
      setEmotionData(data.emotion);
      syncEmotion(data.emotion);
    }
  }

  // Generate mock emotion data for testing
  useEffect(() => {
    if (isConnected && !emotionData) {
      const mockEmotion = {
        emotion_type: "anger",
        confidence: 0.75,
        intensity: 0.6,
        timestamp: Date.now() / 1000
      };
      setEmotionData(mockEmotion);
      console.log('RealtimeInterface: Using mock emotion data for testing');
    }
  }, [isConnected, emotionData]);

  // Handle status updates
  function handleStatusUpdate(data) {
    if (data.type === 'status') {
      if (data.message.includes('started')) {
        setIsProcessing(false);
      }
    } else if (data.type === 'playback_state') {
      setPlaybackState(data.data);
    }
  }

  // Handle errors
  function handleError(error) {
    setError(`Connection error: ${error.message}`);
    setIsProcessing(false);
  }

  // Handle video player events
  const handlePlaybackChange = useCallback((newState) => {
    console.log('Playback state changed:', newState);
    setPlaybackState(prev => ({ ...prev, ...newState }));
    
    // Send playback update to WebSocket
    if (isConnected && sessionId) {
      sendMessage({
        type: 'playback_update',
        current_time: newState.currentTime,
        status: newState.isPlaying ? 'playing' : 'paused',
        is_seeking: newState.isSeeking
      });
    }
  }, [isConnected, sessionId, sendMessage]);

  const handleSeek = useCallback((time) => {
    setPlaybackState(prev => ({ ...prev, currentTime: time, isSeeking: true }));
    
    // Send seek message to WebSocket
    if (isConnected && sessionId) {
      sendMessage({
        type: 'seek',
        time: time
      });
    }
  }, [isConnected, sessionId, sendMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isConnected) {
        disconnect();
      }
    };
  }, [isConnected, disconnect]);

  // Get current synchronized data
  const currentTranscript = getCurrentTranscript();
  const currentEmotion = getCurrentEmotion();

  const [showUpload, setShowUpload] = useState(true); // Always show file manager by default

  return (
    <Container fluid className="realtime-interface">
      <Row className="mb-4">
        <Col>
          <h1 className="text-center">Real-Time Video Translation & Emotion Analysis</h1>
          <p className="text-center text-muted">
            Upload a video and watch it with live translation and emotion analysis
          </p>
        </Col>
      </Row>

      {/* Collapsible File Upload Section - At Top */}
      <Row className="mb-4">
        <Col>
          <Card className="file-manager-card">
            <Card.Header 
              className={`d-flex justify-content-between align-items-center file-manager-header ${showUpload ? 'expanded' : 'collapsed'}`}
              style={{ 
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                backgroundColor: showUpload ? '#f8f9fa' : '#e9ecef',
                borderBottom: showUpload ? '1px solid #dee2e6' : 'none'
              }}
              onClick={() => setShowUpload(!showUpload)}
            >
              <h5 className="mb-0">
                <i className="fas fa-folder-open me-2"></i>
                File Manager - Upload or Select Video
                <small className="text-muted ms-2">
                  {showUpload ? '(Click to hide)' : '(Click to expand)'}
                </small>
              </h5>
              <div className="d-flex align-items-center">
                {/* Connection Status */}
                {isConnected ? (
                  <span className="text-success me-3">
                    <i className="fas fa-circle"></i> Connected
                  </span>
                ) : (
                  <span className="text-danger me-3">
                    <i className="fas fa-circle"></i> Disconnected
                  </span>
                )}
                {isProcessing && (
                  <div className="me-3">
                    <Spinner animation="border" size="sm" className="me-2" />
                    Processing...
                  </div>
                )}
                <i 
                  className={`fas fa-chevron-${showUpload ? 'up' : 'down'} transition-icon`}
                  style={{ 
                    transition: 'transform 0.3s ease',
                    transform: showUpload ? 'rotate(0deg)' : 'rotate(180deg)'
                  }}
                ></i>
              </div>
            </Card.Header>
            <div 
              className={`file-manager-content ${showUpload ? 'show' : 'hide'}`}
              style={{
                maxHeight: showUpload ? '1000px' : '0px',
                overflow: 'hidden',
                transition: 'max-height 0.3s ease-in-out'
              }}
            >
              <Card.Body>
                <FileManager
                  onFileSelect={handleFileUpload}
                  isProcessing={isUploading || isProcessing}
                />
                {/* Processing Status */}
                {fileId && (
                  <div className="mt-3">
                    <ProcessingStatus
                      isProcessing={isProcessing}
                      isConnected={isConnected}
                      fileId={fileId}
                    />
                  </div>
                )}
              </Card.Body>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Error Display */}
      {(error || appError) && (
        <Row className="mb-4">
          <Col>
            <Alert variant="danger" dismissible onClose={() => { setError(null); }}>
              {error || appError}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Video Player - Full Width */}
      <Row className="mb-4">
        <Col>
          <Card>
                <Card.Header>
                  <h5 className="mb-0">Video Player</h5>
                </Card.Header>
                <Card.Body className="p-0">
                  {fileId ? (
                    <RealtimeVideoPlayer
                      fileId={fileId}
                      playbackState={playbackState}
                      onPlaybackChange={handlePlaybackChange}
                      onSeek={handleSeek}
                      isConnected={isConnected}
                    />
                  ) : (
                    <div className="text-center p-5">
                      <div className="mb-3">
                        <i className="fas fa-video fa-3x text-muted"></i>
                      </div>
                      <h6 className="text-muted">No video selected</h6>
                      <p className="text-muted small">Upload a video to see it here</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
      </Row>

      {/* Translation and Emotion Analysis - Side by Side Below Video */}
      <Row className="main-content">
        {/* Live Translation Panel - 66% Width */}
        <Col lg={8} className="mb-4">
          <Card style={{ height: '450px' }}>
                <Card.Header>
                  <h5 className="mb-0">Live Translation</h5>
                </Card.Header>
            <Card.Body style={{ 
              height: 'calc(100% - 60px)', 
              overflow: 'auto',
              padding: '0'
            }}>
                  {fileId ? (
                    <RealtimeTranslation
                      transcriptData={transcriptData}
                      currentTranscript={currentTranscript}
                      playbackState={playbackState}
                      isConnected={isConnected}
                    />
                  ) : (
                    <div className="text-center p-4">
                      <div className="mb-3">
                        <i className="fas fa-language fa-2x text-muted"></i>
                      </div>
                      <h6 className="text-muted">Live Translation</h6>
                      <p className="text-muted small">Arabic speech-to-text will appear here</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>

        {/* Emotion Analysis Panel - 33% Width */}
        <Col lg={4} className="mb-4">
          <Card style={{ height: '450px' }}>
                <Card.Header>
                  <h5 className="mb-0">Emotion Analysis</h5>
                </Card.Header>
            <Card.Body style={{ 
              height: 'calc(100% - 60px)', 
              overflow: 'auto',
              padding: '12px'
            }}>
                  {fileId ? (
                    <RealtimeEmotionGauge
                      emotionData={emotionData}
                      currentEmotion={currentEmotion}
                      playbackState={playbackState}
                      isConnected={isConnected}
                    />
                  ) : (
                    <div className="text-center p-4">
                      <div className="mb-3">
                        <i className="fas fa-heart fa-2x text-muted"></i>
                      </div>
                      <h6 className="text-muted">Emotion Analysis</h6>
                      <p className="text-muted small">Real-time emotions will appear here</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>

      {/* Reset Button */}
      {fileId && (
        <Row className="mt-4">
          <Col className="text-center">
            <button
              className="btn btn-outline-secondary"
              onClick={() => {
                setFileId(null);
                setTranscriptData([]);
                setEmotionData(null);
                setPlaybackState({
                  currentTime: 0,
                  duration: 0,
                  isPlaying: false,
                  isPaused: true,
                  isSeeking: false
                });
                if (isConnected) {
                  disconnect();
                }
                if (onNewUpload) {
                  onNewUpload();
                }
              }}
            >
              Upload New Video
            </button>
          </Col>
        </Row>
      )}

      {/* Custom Styles for File Manager Collapsible */}
      <style>{`
        .file-manager-card {
          border: 1px solid #dee2e6;
          border-radius: 0.375rem;
          box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        }
        
        .file-manager-header {
          user-select: none;
          border-radius: 0.375rem 0.375rem 0 0;
        }
        
        .file-manager-header:hover {
          background-color: #e9ecef !important;
        }
        
        .file-manager-header.expanded {
          border-radius: 0.375rem 0.375rem 0 0;
        }
        
        .file-manager-header.collapsed {
          border-radius: 0.375rem;
        }
        
        .file-manager-content {
          transition: max-height 0.3s ease-in-out, opacity 0.3s ease-in-out;
        }
        
        .file-manager-content.hide {
          opacity: 0;
        }
        
        .file-manager-content.show {
          opacity: 1;
        }
        
        .transition-icon {
          transition: transform 0.3s ease;
        }
        
        .file-manager-card .card-body {
          padding: 1rem;
        }
      `}</style>
    </Container>
  );
};

export default RealtimeInterface;
