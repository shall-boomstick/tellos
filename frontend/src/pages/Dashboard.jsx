import React, { useState, useEffect } from 'react'
import { uploadAPI, processingAPI, pollUploadStatus } from '../services/api'
import websocketService from '../services/websocket'
import AudioPlayer from '../components/AudioPlayer'
import EmotionGauge from '../components/EmotionGauge'
import EmotionMeter from '../components/EmotionMeter'
import Transcript from '../components/Transcript'

const Dashboard = ({ fileData }) => {
  const [status, setStatus] = useState(fileData.status || 'uploaded')
  const [progress, setProgress] = useState(10)
  const [error, setError] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const [emotions, setEmotions] = useState(null)
  const [emotionData, setEmotionData] = useState([])
  const [currentEmotion, setCurrentEmotion] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [pollingActive, setPollingActive] = useState(false)

  // Set up WebSocket connections
  useEffect(() => {
    let stopPolling = null
    
    const setupConnections = async () => {
      try {
        // Try to connect to realtime WebSocket for emotion analysis
        try {
          await websocketService.connect(`realtime-${fileData.file_id}`, {
            url: `ws://localhost:8000/ws/realtime/${fileData.file_id}`,
            onMessage: (message) => {
              console.log('Realtime WebSocket message:', message);
              if (message.type === 'emotion_update' && message.emotion) {
                setEmotionData(prev => [...prev, message.emotion]);
                
                // Update current emotion if it matches current time
                if (message.emotion.start_time <= currentTime && message.emotion.end_time >= currentTime) {
                  setCurrentEmotion(message.emotion);
                }
              } else if (message.type === 'test') {
                console.log('Realtime WebSocket test message received:', message.message);
              }
            },
            onError: (error) => {
              console.error('Realtime WebSocket error:', error);
            },
            onClose: () => {
              console.log('Realtime WebSocket disconnected');
            }
          });
          console.log('Realtime WebSocket connected');
        } catch (wsError) {
          console.log('Realtime WebSocket connection failed, using polling only:', wsError);
        }

        // WebSocket connections disabled - using polling only
        console.log('Using polling-only mode (WebSockets disabled)')

        // Start polling immediately as a fallback
        console.log('Starting polling immediately as fallback')
        setPollingActive(true)
        console.log('pollingActive set to true')
        stopPolling = pollUploadStatus(fileData.file_id, (statusData) => {
              console.log('Polling status update:', statusData)
              if (statusData.error) {
                setError(statusData.error)
                return
              }
              
              console.log('Setting status from polling:', statusData.status)
              setStatus(statusData.status)
              setProgress(statusData.progress || 0)
              
              // Always clear error state when polling provides any status update
              // This ensures polling can override WebSocket errors
              console.log('Clearing error state due to polling update')
              setError(null)
              
              if (statusData.status === 'completed') {
                console.log('Status is completed, loading data...')
                loadProcessedData()
              } else if (statusData.status === 'failed') {
                setError('Processing failed')
              }
            })
        
      } catch (err) {
        console.error('Error setting up connections:', err)
        setError('Failed to connect to real-time updates')
      }
    }

    setupConnections()

    return () => {
      // Stop polling if active
      if (stopPolling) {
        stopPolling()
      }
      
      // Disconnect realtime WebSocket
      websocketService.disconnect(`realtime-${fileData.file_id}`)
      
      // Reset polling state
      setPollingActive(false)
    }
  }, [fileData.file_id, status, wsConnected])

  const loadProcessedData = async () => {
    if (isLoadingData) {
      console.log('Data loading already in progress, skipping...')
      return
    }
    
    setIsLoadingData(true)
    try {
      console.log('Loading processed data for file:', fileData.file_id)
      
      // Load transcript
      const transcriptResponse = await processingAPI.getTranscript(fileData.file_id)
      console.log('Transcript loaded:', transcriptResponse.data)
      setTranscript(transcriptResponse.data)

      // Load emotions
      const emotionsResponse = await processingAPI.getEmotions(fileData.file_id)
      console.log('Emotions loaded:', emotionsResponse.data)
      setEmotions(emotionsResponse.data)

      // Load audio URL
      const audioResponse = await processingAPI.getAudioUrl(fileData.file_id)
      console.log('Audio URL loaded:', audioResponse.data)
      setAudioUrl(audioResponse.data.audio_url)

    } catch (err) {
      console.error('Error loading processed data:', err)
      setError('Failed to load analysis results')
    } finally {
      setIsLoadingData(false)
    }
  }

  // Load data immediately if already completed
  useEffect(() => {
    if (status === 'completed' && !transcript && !emotions) {
      console.log('Status is completed, loading data immediately...')
      loadProcessedData()
    }
  }, [status, transcript, emotions])

  // Check initial status on mount
  useEffect(() => {
    const checkInitialStatus = async () => {
      try {
        console.log('Checking initial status for file:', fileData.file_id)
        const statusResponse = await uploadAPI.getUploadStatus(fileData.file_id)
        console.log('Initial status response:', statusResponse.data)
        
        if (statusResponse.data.status === 'completed') {
          console.log('Initial status check: file is completed, setting status')
          setStatus('completed')
          setProgress(100)
          setError(null) // Clear any previous error state
          loadProcessedData()
        }
      } catch (err) {
        console.error('Error checking initial status:', err)
      }
    }
    
    checkInitialStatus()
  }, [fileData.file_id])

  // Update current emotion based on playback time
  useEffect(() => {
    if (emotionData.length > 0 && currentTime > 0) {
      const matchingEmotion = emotionData.find(emotion => 
        emotion.start_time <= currentTime && emotion.end_time >= currentTime
      );
      
      if (matchingEmotion) {
        setCurrentEmotion(matchingEmotion);
      }
    } else if (currentTime > 0 && emotionData.length === 0) {
      // Generate mock emotion data for testing
      const mockEmotions = [
        { emotion_type: 'neutral', confidence: 0.6, intensity: 'medium', start_time: 0, end_time: 5 },
        { emotion_type: 'joy', confidence: 0.8, intensity: 'high', start_time: 5, end_time: 10 },
        { emotion_type: 'anger', confidence: 0.7, intensity: 'high', start_time: 10, end_time: 15 },
        { emotion_type: 'sadness', confidence: 0.5, intensity: 'low', start_time: 15, end_time: 20 },
        { emotion_type: 'surprise', confidence: 0.9, intensity: 'high', start_time: 20, end_time: 25 }
      ];
      
      const currentMockEmotion = mockEmotions.find(emotion => 
        emotion.start_time <= currentTime && emotion.end_time >= currentTime
      );
      
      if (currentMockEmotion) {
        setCurrentEmotion(currentMockEmotion);
        setEmotionData(mockEmotions);
      }
    }
  }, [currentTime, emotionData])

  const getStatusMessage = () => {
    switch (status) {
      case 'uploaded': return 'File uploaded successfully'
      case 'extracting': return 'Extracting audio from video...'
      case 'transcribing': return 'Transcribing Arabic speech...'
      case 'analyzing': return 'Analyzing emotions...'
      case 'completed': return 'Processing complete!'
      case 'failed': return 'Processing failed'
      default: return 'Processing...'
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'var(--success-color)'
      case 'failed': return 'var(--error-color)'
      default: return 'var(--primary-color)'
    }
  }

  return (
    <div className="dashboard">
      <div className="card">
        <h2>Processing: {fileData.filename}</h2>
        
        <div className="status-section">
          <div className="status-header">
            <span className="status-label">Status:</span>
            <span className="status-value" style={{ color: getStatusColor() }}>
              {getStatusMessage()}
            </span>
          </div>
          
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: `${progress}%`,
                backgroundColor: getStatusColor()
              }}
            ></div>
          </div>
          
          <div className="progress-text">{progress}% complete</div>
        </div>

        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}

        {status === 'completed' && (
          <div className="completed-section">
            <h3>🎉 Analysis Complete!</h3>
            <p>Your Arabic audio has been processed successfully.</p>
            
            {audioUrl && (
              <div className="audio-section">
                <AudioPlayer 
                  audioUrl={audioUrl}
                  duration={emotions?.segments?.[emotions.segments.length - 1]?.end_time || 30}
                  onTimeUpdate={(time) => {
                    setCurrentTime(time)
                    // Send time update via WebSocket for real-time sync
                    websocketService.send(`playback-${fileData.file_id}`, {
                      type: 'time_update',
                      current_time: time,
                      is_playing: isPlaying
                    })
                  }}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                />
              </div>
            )}

            {emotions && (
              <div className="emotion-section">
                <EmotionGauge 
                  currentEmotion={emotions.overall_emotion}
                  confidence={emotions.overall_confidence}
                  emotionHistory={emotions.segments}
                />
              </div>
            )}

            {/* Real-time Emotion Analysis */}
            <div className="realtime-emotion-section">
              <EmotionMeter
                emotionData={emotionData}
                currentTime={currentTime}
                playbackState={{
                  currentTime: currentTime,
                  duration: emotions?.segments?.[emotions.segments.length - 1]?.end_time || 30,
                  isPlaying: isPlaying
                }}
                isConnected={wsConnected}
              />
            </div>

                {transcript && (
                  <div className="transcript-section">
                    <Transcript 
                      transcript={transcript.text}
                      englishText={transcript.english_text}
                      words={transcript.words}
                      currentTime={currentTime}
                      isPlaying={isPlaying}
                      onWordClick={(time) => {
                        setCurrentTime(time)
                        // Send seek command via WebSocket
                        websocketService.send(`playback-${fileData.file_id}`, {
                          type: 'seek',
                          time: time
                        })
                      }}
                    />
                  </div>
                )}
          </div>
        )}

        {status === 'failed' && (
          <div className="failed-section">
            <h3>❌ Processing Failed</h3>
            <p>Something went wrong while processing your file. Please try uploading again.</p>
            <button 
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              Try Again
            </button>
          </div>
        )}
      </div>

    </div>
  )
}

export default Dashboard
