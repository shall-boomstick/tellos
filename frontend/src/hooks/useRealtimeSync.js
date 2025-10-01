import { useState, useEffect, useCallback, useRef } from 'react';

const useRealtimeSync = (currentTime) => {
  const [transcriptData, setTranscriptData] = useState([]);
  const [emotionData, setEmotionData] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState(null);
  const [currentEmotion, setCurrentEmotion] = useState(null);
  
  const syncTolerance = 0.5; // 500ms tolerance for synchronization
  const historyLimit = 100; // Keep last 100 items

  // Sync transcript data with current time
  const syncTranscript = useCallback((newTranscript) => {
    if (!newTranscript) return;

    setTranscriptData(prev => {
      const updated = [...prev, newTranscript].slice(-historyLimit);
      return updated;
    });

    // Update current transcript if it matches current time
    if (isTimeInRange(currentTime, newTranscript.start_time, newTranscript.end_time)) {
      setCurrentTranscript(newTranscript);
    }
  }, [currentTime]);

  // Sync emotion data with current time
  const syncEmotion = useCallback((newEmotion) => {
    if (!newEmotion) return;

    setEmotionData(prev => {
      const updated = [...prev, newEmotion].slice(-historyLimit);
      return updated;
    });

    // Update current emotion if it matches current time
    if (isTimeInRange(currentTime, newEmotion.start_time, newEmotion.end_time)) {
      setCurrentEmotion(newEmotion);
    }
  }, [currentTime]);

  // Check if current time is within a time range
  const isTimeInRange = useCallback((current, start, end) => {
    return current >= start - syncTolerance && current <= end + syncTolerance;
  }, [syncTolerance]);

  // Get current transcript based on time
  const getCurrentTranscript = useCallback(() => {
    if (!transcriptData.length) return null;

    // Find transcript that matches current time
    const matchingTranscript = transcriptData.find(transcript => 
      isTimeInRange(currentTime, transcript.start_time, transcript.end_time)
    );

    if (matchingTranscript) {
      return matchingTranscript;
    }

    // If no exact match, find the closest one
    const sortedTranscripts = transcriptData.sort((a, b) => 
      Math.abs(a.start_time - currentTime) - Math.abs(b.start_time - currentTime)
    );

    return sortedTranscripts[0] || null;
  }, [transcriptData, currentTime, isTimeInRange]);

  // Get current emotion based on time
  const getCurrentEmotion = useCallback(() => {
    if (!emotionData.length) return null;

    // Find emotion that matches current time
    const matchingEmotion = emotionData.find(emotion => 
      isTimeInRange(currentTime, emotion.start_time, emotion.end_time)
    );

    if (matchingEmotion) {
      return matchingEmotion;
    }

    // If no exact match, find the closest one
    const sortedEmotions = emotionData.sort((a, b) => 
      Math.abs(a.start_time - currentTime) - Math.abs(b.start_time - currentTime)
    );

    return sortedEmotions[0] || null;
  }, [emotionData, currentTime, isTimeInRange]);

  // Update current transcript and emotion when time changes
  useEffect(() => {
    const newCurrentTranscript = getCurrentTranscript();
    const newCurrentEmotion = getCurrentEmotion();

    if (newCurrentTranscript !== currentTranscript) {
      setCurrentTranscript(newCurrentTranscript);
    }

    if (newCurrentEmotion !== currentEmotion) {
      setCurrentEmotion(newCurrentEmotion);
    }
  }, [currentTime, getCurrentTranscript, getCurrentEmotion, currentTranscript, currentEmotion]);

  // Get transcript history for a time range
  const getTranscriptHistory = useCallback((startTime, endTime) => {
    return transcriptData.filter(transcript => 
      transcript.start_time >= startTime && transcript.end_time <= endTime
    );
  }, [transcriptData]);

  // Get emotion history for a time range
  const getEmotionHistory = useCallback((startTime, endTime) => {
    return emotionData.filter(emotion => 
      emotion.start_time >= startTime && emotion.end_time <= endTime
    );
  }, [emotionData]);

  // Get smoothed emotion from recent history
  const getSmoothedEmotion = useCallback((windowSize = 5) => {
    if (!emotionData.length) return null;

    const recentEmotions = emotionData.slice(-windowSize);
    
    // Calculate average emotion
    const emotionCounts = {};
    let totalConfidence = 0;
    let totalIntensity = 0;

    recentEmotions.forEach(emotion => {
      const emotionType = emotion.emotion_type || emotion.type;
      emotionCounts[emotionType] = (emotionCounts[emotionType] || 0) + 1;
      totalConfidence += emotion.confidence || 0;
      totalIntensity += emotion.intensity || 0;
    });

    // Get most common emotion
    const mostCommonEmotion = Object.keys(emotionCounts).reduce((a, b) => 
      emotionCounts[a] > emotionCounts[b] ? a : b
    );

    return {
      emotion_type: mostCommonEmotion,
      confidence: totalConfidence / recentEmotions.length,
      intensity: totalIntensity / recentEmotions.length,
      timestamp: recentEmotions[recentEmotions.length - 1]?.timestamp
    };
  }, [emotionData]);

  // Clear all data
  const clearData = useCallback(() => {
    setTranscriptData([]);
    setEmotionData([]);
    setCurrentTranscript(null);
    setCurrentEmotion(null);
  }, []);

  // Get synchronization statistics
  const getSyncStats = useCallback(() => {
    const totalTranscripts = transcriptData.length;
    const totalEmotions = emotionData.length;
    
    const syncedTranscripts = transcriptData.filter(transcript => 
      isTimeInRange(currentTime, transcript.start_time, transcript.end_time)
    ).length;
    
    const syncedEmotions = emotionData.filter(emotion => 
      isTimeInRange(currentTime, emotion.start_time, emotion.end_time)
    ).length;

    return {
      totalTranscripts,
      totalEmotions,
      syncedTranscripts,
      syncedEmotions,
      syncRate: totalTranscripts > 0 ? (syncedTranscripts / totalTranscripts) * 100 : 0
    };
  }, [transcriptData, emotionData, currentTime, isTimeInRange]);

  return {
    // Data
    transcriptData,
    emotionData,
    currentTranscript,
    currentEmotion,
    
    // Sync functions
    syncTranscript,
    syncEmotion,
    
    // Getter functions
    getCurrentTranscript,
    getCurrentEmotion,
    getTranscriptHistory,
    getEmotionHistory,
    getSmoothedEmotion,
    
    // Utility functions
    clearData,
    getSyncStats,
    
    // State
    isTimeInRange
  };
};

export { useRealtimeSync };
