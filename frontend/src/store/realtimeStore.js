import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

const useRealtimeStore = create(
  subscribeWithSelector((set, get) => ({
    // Connection state
    isConnected: false,
    connectionStatus: 'disconnected',
    sessionId: null,
    fileId: null,

    // Processing state
    isProcessing: false,
    processingProgress: 0,
    processingSteps: [],

    // Playback state
    playbackState: {
      currentTime: 0,
      duration: 0,
      isPlaying: false,
      isPaused: true,
      isSeeking: false,
      volume: 1.0,
      playbackRate: 1.0
    },

    // Real-time data
    transcriptData: [],
    emotionData: [],
    currentTranscript: null,
    currentEmotion: null,
    currentEmotionIntensity: 0,

    // UI state
    error: null,
    isUploading: false,
    uploadProgress: 0,

    // Actions
    setConnection: (isConnected, connectionStatus = 'connected') => {
      set({ isConnected, connectionStatus });
    },

    setSession: (sessionId, fileId) => {
      set({ sessionId, fileId });
    },

    setProcessing: (isProcessing, progress = 0, steps = []) => {
      set({ 
        isProcessing, 
        processingProgress: progress,
        processingSteps: steps
      });
    },

    updatePlaybackState: (updates) => {
      set(state => ({
        playbackState: { ...state.playbackState, ...updates }
      }));
    },

    addTranscript: (transcript) => {
      set(state => ({
        transcriptData: [...state.transcriptData, transcript].slice(-100) // Keep last 100
      }));
    },

    addEmotion: (emotion) => {
      set(state => ({
        emotionData: [...state.emotionData, emotion].slice(-100) // Keep last 100
      }));
    },

    setCurrentTranscript: (transcript) => {
      set({ currentTranscript: transcript });
    },

    setCurrentEmotion: (emotion) => {
      set({ currentEmotion: emotion });
    },

    updateEmotionIntensity: (intensity) => {
      set({ currentEmotionIntensity: intensity });
    },

    setError: (error) => {
      set({ error });
    },

    clearError: () => {
      set({ error: null });
    },

    setUploading: (isUploading, progress = 0) => {
      set({ isUploading, uploadProgress: progress });
    },

    // Sync functions
    syncTranscript: (transcript) => {
      const state = get();
      const { currentTime } = state.playbackState;
      
      // Check if transcript matches current time
      const isInRange = currentTime >= transcript.start_time - 0.5 && 
                       currentTime <= transcript.end_time + 0.5;
      
      if (isInRange) {
        set({ currentTranscript: transcript });
      }
      
      // Add to history
      get().addTranscript(transcript);
    },

    syncEmotion: (emotion) => {
      const state = get();
      const { currentTime } = state.playbackState;
      
      // Check if emotion matches current time
      const isInRange = currentTime >= emotion.start_time - 0.5 && 
                       currentTime <= emotion.end_time + 0.5;
      
      if (isInRange) {
        set({ currentEmotion: emotion });
      }
      
      // Add to history
      get().addEmotion(emotion);
    },

    // Seek to specific time
    seekTo: (time) => {
      const state = get();
      set({
        playbackState: {
          ...state.playbackState,
          currentTime: time,
          isSeeking: true
        }
      });

      // Find matching transcript and emotion for this time
      const matchingTranscript = state.transcriptData.find(t => 
        time >= t.start_time - 0.5 && time <= t.end_time + 0.5
      );
      
      const matchingEmotion = state.emotionData.find(e => 
        time >= e.start_time - 0.5 && time <= e.end_time + 0.5
      );

      if (matchingTranscript) {
        set({ currentTranscript: matchingTranscript });
      }

      if (matchingEmotion) {
        set({ currentEmotion: matchingEmotion });
      }

      // Clear seeking state after a short delay
      setTimeout(() => {
        set(state => ({
          playbackState: { ...state.playbackState, isSeeking: false }
        }));
      }, 100);
    },

    // Get smoothed emotion from recent history
    getSmoothedEmotion: (windowSize = 5) => {
      const state = get();
      const recentEmotions = state.emotionData.slice(-windowSize);
      
      if (recentEmotions.length === 0) return null;

      const emotionCounts = {};
      let totalConfidence = 0;
      let totalIntensity = 0;

      recentEmotions.forEach(emotion => {
        const emotionType = emotion.emotion_type || emotion.type;
        emotionCounts[emotionType] = (emotionCounts[emotionType] || 0) + 1;
        totalConfidence += emotion.confidence || 0;
        totalIntensity += emotion.intensity || 0;
      });

      const mostCommonEmotion = Object.keys(emotionCounts).reduce((a, b) => 
        emotionCounts[a] > emotionCounts[b] ? a : b
      );

      return {
        emotion_type: mostCommonEmotion,
        confidence: totalConfidence / recentEmotions.length,
        intensity: totalIntensity / recentEmotions.length,
        timestamp: recentEmotions[recentEmotions.length - 1]?.timestamp
      };
    },

    // Get statistics
    getStats: () => {
      const state = get();
      return {
        totalTranscripts: state.transcriptData.length,
        totalEmotions: state.emotionData.length,
        currentTime: state.playbackState.currentTime,
        duration: state.playbackState.duration,
        isConnected: state.isConnected,
        isProcessing: state.isProcessing
      };
    },

    // Reset all data
    reset: () => {
      set({
        isConnected: false,
        connectionStatus: 'disconnected',
        sessionId: null,
        fileId: null,
        isProcessing: false,
        processingProgress: 0,
        processingSteps: [],
        playbackState: {
          currentTime: 0,
          duration: 0,
          isPlaying: false,
          isPaused: true,
          isSeeking: false,
          volume: 1.0,
          playbackRate: 1.0
        },
        transcriptData: [],
        emotionData: [],
        currentTranscript: null,
        currentEmotion: null,
        error: null,
        isUploading: false,
        uploadProgress: 0
      });
    },

    // Clear specific data
    clearTranscripts: () => {
      set({ transcriptData: [], currentTranscript: null });
    },

    clearEmotions: () => {
      set({ emotionData: [], currentEmotion: null });
    },

    clearAllData: () => {
      set({
        transcriptData: [],
        emotionData: [],
        currentTranscript: null,
        currentEmotion: null
      });
    }
  }))
);

// Selectors for common use cases
export const useConnectionState = () => useRealtimeStore(state => ({
  isConnected: state.isConnected,
  connectionStatus: state.connectionStatus,
  sessionId: state.sessionId,
  fileId: state.fileId
}));

export const useProcessingState = () => useRealtimeStore(state => ({
  isProcessing: state.isProcessing,
  processingProgress: state.processingProgress,
  processingSteps: state.processingSteps
}));

export const usePlaybackState = () => useRealtimeStore(state => state.playbackState);

export const useTranscriptData = () => useRealtimeStore(state => ({
  transcriptData: state.transcriptData,
  currentTranscript: state.currentTranscript
}));

export const useEmotionData = () => useRealtimeStore(state => ({
  emotionData: state.emotionData,
  currentEmotion: state.currentEmotion,
  currentEmotionIntensity: state.currentEmotionIntensity
}));

export const useUIState = () => useRealtimeStore(state => ({
  error: state.error,
  isUploading: state.isUploading,
  uploadProgress: state.uploadProgress
}));

export default useRealtimeStore;
