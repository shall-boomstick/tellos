import { useEffect, useCallback, useRef } from 'react';
import { useRealtimeStore } from '../store/realtimeStore';

const useVideoTranslationSync = (videoRef, currentTime) => {
  const store = useRealtimeStore();
  const lastSyncTime = useRef(0);
  const syncTolerance = 0.5; // 500ms tolerance

  // Sync transcript data with video time
  const syncTranscriptWithVideo = useCallback((transcript) => {
    if (!transcript || !currentTime) return;

    const { start_time, end_time } = transcript;
    
    // Check if current video time is within transcript time range
    const isInRange = currentTime >= start_time - syncTolerance && 
                     currentTime <= end_time + syncTolerance;

    if (isInRange) {
      // Update current transcript in store
      store.setCurrentTranscript(transcript);
      
      // Highlight current words if available
      if (transcript.words && transcript.words.length > 0) {
        highlightCurrentWords(transcript.words, currentTime);
      }
    }
  }, [currentTime, store]);

  // Highlight current words in the transcript
  const highlightCurrentWords = useCallback((words, time) => {
    // This would typically update the UI to highlight current words
    // For now, we'll just log the current word
    const currentWord = words.find(word => 
      time >= word.start && time <= word.end
    );
    
    if (currentWord) {
      console.log('Current word:', currentWord.word);
    }
  }, []);

  // Seek to specific transcript time
  const seekToTranscript = useCallback((transcript) => {
    if (!videoRef.current || !transcript) return;

    const seekTime = transcript.start_time;
    videoRef.current.currentTime = seekTime;
    
    // Update store playback state
    store.updatePlaybackState({
      currentTime: seekTime,
      isSeeking: true
    });

    // Clear seeking state after a short delay
    setTimeout(() => {
      store.updatePlaybackState({ isSeeking: false });
    }, 100);
  }, [videoRef, store]);

  // Get transcript for current time
  const getCurrentTranscript = useCallback(() => {
    const { transcriptData } = store;
    
    if (!transcriptData.length || !currentTime) return null;

    // Find transcript that matches current time
    const matchingTranscript = transcriptData.find(transcript => 
      currentTime >= transcript.start_time - syncTolerance && 
      currentTime <= transcript.end_time + syncTolerance
    );

    return matchingTranscript || null;
  }, [store, currentTime]);

  // Get transcript segments for a time range
  const getTranscriptSegments = useCallback((startTime, endTime) => {
    const { transcriptData } = store;
    
    return transcriptData.filter(transcript => 
      transcript.start_time >= startTime && transcript.end_time <= endTime
    );
  }, [store]);

  // Auto-sync when time changes
  useEffect(() => {
    if (currentTime && currentTime !== lastSyncTime.current) {
      lastSyncTime.current = currentTime;
      
      // Get current transcript
      const currentTranscript = getCurrentTranscript();
      
      if (currentTranscript) {
        syncTranscriptWithVideo(currentTranscript);
      }
    }
  }, [currentTime, getCurrentTranscript, syncTranscriptWithVideo]);

  // Sync all transcript data when it changes
  useEffect(() => {
    const { transcriptData } = store;
    
    if (transcriptData.length > 0 && currentTime) {
      const currentTranscript = getCurrentTranscript();
      if (currentTranscript) {
        syncTranscriptWithVideo(currentTranscript);
      }
    }
  }, [store.transcriptData, currentTime, getCurrentTranscript, syncTranscriptWithVideo]);

  // Handle transcript updates from WebSocket
  const handleTranscriptUpdate = useCallback((transcript) => {
    // Add to store
    store.addTranscript(transcript);
    
    // Sync if it matches current time
    syncTranscriptWithVideo(transcript);
  }, [store, syncTranscriptWithVideo]);

  // Get transcript statistics
  const getTranscriptStats = useCallback(() => {
    const { transcriptData } = store;
    
    if (!transcriptData.length) {
      return {
        totalSegments: 0,
        totalDuration: 0,
        averageConfidence: 0,
        language: null
      };
    }

    const totalDuration = Math.max(...transcriptData.map(t => t.end_time));
    const averageConfidence = transcriptData.reduce((sum, t) => sum + (t.confidence || 0), 0) / transcriptData.length;
    const languages = [...new Set(transcriptData.map(t => t.language).filter(Boolean))];

    return {
      totalSegments: transcriptData.length,
      totalDuration,
      averageConfidence,
      language: languages[0] || null,
      languages
    };
  }, [store]);

  // Clear transcript data
  const clearTranscripts = useCallback(() => {
    store.clearTranscripts();
  }, [store]);

  return {
    // Sync functions
    syncTranscriptWithVideo,
    seekToTranscript,
    handleTranscriptUpdate,
    
    // Getter functions
    getCurrentTranscript,
    getTranscriptSegments,
    getTranscriptStats,
    
    // Utility functions
    clearTranscripts,
    
    // State
    currentTranscript: store.currentTranscript,
    transcriptData: store.transcriptData
  };
};

export { useVideoTranslationSync };
