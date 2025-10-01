import { useEffect, useCallback, useRef } from 'react';
import { useRealtimeStore } from '../store/realtimeStore';

const useVideoEmotionSync = (videoRef, currentTime) => {
  const store = useRealtimeStore();
  const lastSyncTime = useRef(0);
  const syncTolerance = 0.5; // 500ms tolerance
  const emotionHistory = useRef([]);

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
      
      // Add to history for smoothing
      emotionHistory.current.push(emotion);
      
      // Keep only recent emotions (last 10)
      if (emotionHistory.current.length > 10) {
        emotionHistory.current = emotionHistory.current.slice(-10);
      }
    }
  }, [currentTime, store]);

  // Get smoothed emotion from recent history
  const getSmoothedEmotion = useCallback((windowSize = 5) => {
    const recentEmotions = emotionHistory.current.slice(-windowSize);
    
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

    // Get most common emotion
    const mostCommonEmotion = Object.keys(emotionCounts).reduce((a, b) => 
      emotionCounts[a] > emotionCounts[b] ? a : b
    );

    return {
      emotion_type: mostCommonEmotion,
      confidence: totalConfidence / recentEmotions.length,
      intensity: totalIntensity / recentEmotions.length,
      timestamp: recentEmotions[recentEmotions.length - 1]?.timestamp,
      smoothed: true
    };
  }, []);

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
  }, [store, currentTime]);

  // Get emotion segments for a time range
  const getEmotionSegments = useCallback((startTime, endTime) => {
    const { emotionData } = store;
    
    return emotionData.filter(emotion => 
      emotion.start_time >= startTime && emotion.end_time <= endTime
    );
  }, [store]);

  // Get emotion distribution
  const getEmotionDistribution = useCallback(() => {
    const { emotionData } = store;
    
    if (!emotionData.length) return {};

    const distribution = {};
    emotionData.forEach(emotion => {
      const emotionType = emotion.emotion_type || emotion.type;
      distribution[emotionType] = (distribution[emotionType] || 0) + 1;
    });

    return distribution;
  }, [store]);

  // Get emotion intensity over time
  const getEmotionIntensityOverTime = useCallback((windowSize = 10) => {
    const { emotionData } = store;
    
    if (!emotionData.length) return [];

    // Group emotions by time windows
    const timeWindows = [];
    const sortedEmotions = emotionData.sort((a, b) => a.start_time - b.start_time);
    
    for (let i = 0; i < sortedEmotions.length; i += windowSize) {
      const window = sortedEmotions.slice(i, i + windowSize);
      const avgIntensity = window.reduce((sum, e) => sum + (e.intensity || 0), 0) / window.length;
      const avgConfidence = window.reduce((sum, e) => sum + (e.confidence || 0), 0) / window.length;
      
      timeWindows.push({
        startTime: window[0].start_time,
        endTime: window[window.length - 1].end_time,
        avgIntensity,
        avgConfidence,
        emotionCount: window.length
      });
    }

    return timeWindows;
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
        totalDuration: 0,
        averageConfidence: 0,
        averageIntensity: 0,
        emotionDistribution: {}
      };
    }

    const totalDuration = Math.max(...emotionData.map(e => e.end_time));
    const averageConfidence = emotionData.reduce((sum, e) => sum + (e.confidence || 0), 0) / emotionData.length;
    const averageIntensity = emotionData.reduce((sum, e) => sum + (e.intensity || 0), 0) / emotionData.length;
    const emotionDistribution = getEmotionDistribution();

    return {
      totalEmotions: emotionData.length,
      totalDuration,
      averageConfidence,
      averageIntensity,
      emotionDistribution
    };
  }, [store, getEmotionDistribution]);

  // Clear emotion data
  const clearEmotions = useCallback(() => {
    store.clearEmotions();
    emotionHistory.current = [];
  }, [store]);

  // Get emotion trends
  const getEmotionTrends = useCallback(() => {
    const { emotionData } = store;
    
    if (!emotionData.length) return null;

    const sortedEmotions = emotionData.sort((a, b) => a.start_time - b.start_time);
    const trends = {
      dominantEmotion: null,
      emotionChanges: 0,
      intensityTrend: 'stable',
      confidenceTrend: 'stable'
    };

    // Find dominant emotion
    const distribution = getEmotionDistribution();
    trends.dominantEmotion = Object.keys(distribution).reduce((a, b) => 
      distribution[a] > distribution[b] ? a : b
    );

    // Count emotion changes
    for (let i = 1; i < sortedEmotions.length; i++) {
      if (sortedEmotions[i].emotion_type !== sortedEmotions[i-1].emotion_type) {
        trends.emotionChanges++;
      }
    }

    // Calculate intensity trend
    const firstHalf = sortedEmotions.slice(0, Math.floor(sortedEmotions.length / 2));
    const secondHalf = sortedEmotions.slice(Math.floor(sortedEmotions.length / 2));
    
    const firstHalfAvg = firstHalf.reduce((sum, e) => sum + (e.intensity || 0), 0) / firstHalf.length;
    const secondHalfAvg = secondHalf.reduce((sum, e) => sum + (e.intensity || 0), 0) / secondHalf.length;
    
    if (secondHalfAvg > firstHalfAvg + 0.1) {
      trends.intensityTrend = 'increasing';
    } else if (secondHalfAvg < firstHalfAvg - 0.1) {
      trends.intensityTrend = 'decreasing';
    }

    return trends;
  }, [store, getEmotionDistribution]);

  return {
    // Sync functions
    syncEmotionWithVideo,
    seekToEmotion,
    handleEmotionUpdate,
    
    // Getter functions
    getCurrentEmotion,
    getEmotionSegments,
    getSmoothedEmotion,
    getEmotionDistribution,
    getEmotionIntensityOverTime,
    getEmotionStats,
    getEmotionTrends,
    
    // Utility functions
    clearEmotions,
    
    // State
    currentEmotion: store.currentEmotion,
    emotionData: store.emotionData
  };
};

export { useVideoEmotionSync };
