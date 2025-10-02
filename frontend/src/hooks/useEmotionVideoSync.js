import { useEffect, useCallback, useRef } from 'react';
import { useRealtimeStore } from '../store/realtimeStore';

const useEmotionVideoSync = (videoRef, currentTime) => {
  const store = useRealtimeStore();
  const lastSyncTime = useRef(0);
  const syncTolerance = 0.5; // 500ms tolerance

  // Sync emotion data with video time
  const syncEmotionWithVideo = useCallback((emotion) => {
    if (!emotion || !currentTime) return;

    const { start_time, end_time } = emotion;
    
    // Check if current video time is within emotion time range
    const isInRange = currentTime >= start_time - syncTolerance && 
                     currentTime <= end_time + syncTolerance;

    if (isInRange) {
      // Update current emotion in store
      store.setCurrentEmotion(emotion);
      
      // Update emotion intensity for visualization
      updateEmotionIntensity(emotion);
    }
  }, [currentTime, store]);

  // Update emotion intensity visualization
  const updateEmotionIntensity = useCallback((emotion) => {
    if (!emotion) return;

    // Calculate intensity score
    const intensityMultipliers = {
      low: 0.3,
      medium: 0.6,
      high: 0.9
    };
    
    const baseIntensity = intensityMultipliers[emotion.intensity] || 0.6;
    const confidenceMultiplier = emotion.confidence || 0.5;
    const intensityScore = Math.round(baseIntensity * confidenceMultiplier * 100);

    // Update store with current emotion intensity
    store.updateEmotionIntensity(intensityScore);
  }, [store]);

  // Get emotion for current time
  const getCurrentEmotion = useCallback(() => {
    const { emotionData } = store;
    
    if (!emotionData.length || !currentTime) return null;

    // Find emotion that matches current time
    const matchingEmotion = emotionData.find(emotion => 
      currentTime >= emotion.start_time - syncTolerance && 
      currentTime <= emotion.end_time + syncTolerance
    );

    return matchingEmotion || null;
  }, [currentTime, store]);

  // Get emotion segments for a time range
  const getEmotionSegments = useCallback((startTime, endTime) => {
    const { emotionData } = store;
    
    return emotionData.filter(emotion => 
      emotion.start_time >= startTime && emotion.end_time <= endTime
    );
  }, [store]);

  // Auto-sync when time changes
  useEffect(() => {
    if (currentTime && currentTime !== lastSyncTime.current) {
      lastSyncTime.current = currentTime;
      
      // Get current emotion
      const currentEmotion = getCurrentEmotion();
      
      if (currentEmotion) {
        syncEmotionWithVideo(currentEmotion);
      }
    }
  }, [currentTime, getCurrentEmotion, syncEmotionWithVideo]);

  // Sync all emotion data when it changes
  useEffect(() => {
    const { emotionData } = store;
    
    if (emotionData.length > 0 && currentTime) {
      const currentEmotion = getCurrentEmotion();
      if (currentEmotion) {
        syncEmotionWithVideo(currentEmotion);
      }
    }
  }, [store.emotionData, currentTime, getCurrentEmotion, syncEmotionWithVideo]);

  // Handle emotion updates from WebSocket
  const handleEmotionUpdate = useCallback((emotion) => {
    // Add to store
    store.addEmotion(emotion);
    
    // Sync if it matches current time
    syncEmotionWithVideo(emotion);
  }, [store, syncEmotionWithVideo]);

  // Get emotion statistics
  const getEmotionStats = useCallback(() => {
    const { emotionData } = store;
    
    if (!emotionData.length) {
      return {
        totalEmotions: 0,
        emotionDistribution: {},
        averageIntensity: 0,
        dominantEmotion: 'neutral'
      };
    }

    // Calculate emotion distribution
    const emotionCounts = {};
    let totalIntensity = 0;
    
    emotionData.forEach(emotion => {
      const emotionType = emotion.emotion_type;
      emotionCounts[emotionType] = (emotionCounts[emotionType] || 0) + 1;
      
      const intensityMultipliers = { low: 0.3, medium: 0.6, high: 0.9 };
      const baseIntensity = intensityMultipliers[emotion.intensity] || 0.6;
      totalIntensity += baseIntensity * (emotion.confidence || 0.5);
    });

    const dominantEmotion = Object.keys(emotionCounts).reduce((a, b) => 
      emotionCounts[a] > emotionCounts[b] ? a : b
    );

    return {
      totalEmotions: emotionData.length,
      emotionDistribution: emotionCounts,
      averageIntensity: totalIntensity / emotionData.length,
      dominantEmotion
    };
  }, [store]);

  // Get emotion timeline for visualization
  const getEmotionTimeline = useCallback((duration) => {
    const { emotionData } = store;
    
    if (!emotionData.length || !duration) return [];

    // Create timeline data points
    const timelinePoints = [];
    const stepSize = duration / 100; // 100 points for smooth visualization

    for (let i = 0; i <= 100; i++) {
      const time = i * stepSize;
      
      // Find emotion at this time
      const emotion = emotionData.find(e => 
        time >= e.start_time && time <= e.end_time
      );

      if (emotion) {
        const intensityMultipliers = { low: 0.3, medium: 0.6, high: 0.9 };
        const baseIntensity = intensityMultipliers[emotion.intensity] || 0.6;
        const intensityScore = baseIntensity * (emotion.confidence || 0.5);

        timelinePoints.push({
          time,
          emotion: emotion.emotion_type,
          intensity: intensityScore,
          confidence: emotion.confidence
        });
      } else {
        timelinePoints.push({
          time,
          emotion: 'neutral',
          intensity: 0,
          confidence: 0
        });
      }
    }

    return timelinePoints;
  }, [store]);

  // Seek to specific emotion time
  const seekToEmotion = useCallback((emotion) => {
    if (!videoRef.current || !emotion) return;

    const seekTime = emotion.start_time;
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

  return {
    syncEmotionWithVideo,
    getCurrentEmotion,
    getEmotionSegments,
    handleEmotionUpdate,
    getEmotionStats,
    getEmotionTimeline,
    seekToEmotion
  };
};

export default useEmotionVideoSync;
