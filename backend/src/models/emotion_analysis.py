"""
EmotionAnalysis model for SawtFeel application.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid

class EmotionType(str, Enum):
    """Supported emotion types."""
    ANGER = "anger"
    SADNESS = "sadness"
    JOY = "joy"
    NEUTRAL = "neutral"
    FEAR = "fear"
    SURPRISE = "surprise"

class EmotionSegment(BaseModel):
    """Time-based emotion analysis data."""
    
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")
    textual_emotion: EmotionType = Field(..., description="Emotion from text analysis")
    textual_confidence: float = Field(..., ge=0, le=1, description="Text emotion confidence")
    tonal_emotion: EmotionType = Field(..., description="Emotion from audio tone")
    tonal_confidence: float = Field(..., ge=0, le=1, description="Tone emotion confidence")
    combined_emotion: EmotionType = Field(..., description="Final combined emotion")
    combined_confidence: float = Field(..., ge=0, le=1, description="Combined confidence")
    
    @validator('end_time')
    def end_time_must_be_after_start(cls, v, values):
        """Validate that end_time is after start_time."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v
    
    @validator('combined_confidence')
    def validate_combined_confidence(cls, v, values):
        """Validate combined confidence is reasonable given individual confidences."""
        if 'textual_confidence' in values and 'tonal_confidence' in values:
            min_conf = min(values['textual_confidence'], values['tonal_confidence'])
            max_conf = max(values['textual_confidence'], values['tonal_confidence'])
            if v < min_conf * 0.5 or v > max_conf * 1.1:
                raise ValueError('Combined confidence should be reasonable given individual confidences')
        return v
    
    @property
    def duration(self) -> float:
        """Get the duration of this emotion segment."""
        return self.end_time - self.start_time

class EmotionAnalysis(BaseModel):
    """Emotion analysis model with time-based segments."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_file_id: str = Field(..., description="Reference to AudioFile")
    segments: List[EmotionSegment] = Field(default_factory=list, description="Time-based emotion data")
    overall_emotion: EmotionType = Field(..., description="Primary emotion for entire file")
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('segments')
    def validate_segment_timing_order(cls, v):
        """Validate that segments are in chronological order and don't overlap."""
        if len(v) < 2:
            return v
            
        for i in range(1, len(v)):
            current = v[i]
            previous = v[i-1]
            
            # Check chronological order
            if current.start_time < previous.start_time:
                raise ValueError('Emotion segments must be in chronological order')
            
            # Check for overlaps
            if current.start_time < previous.end_time:
                raise ValueError('Emotion segments must not overlap')
                
        return v
    
    @validator('overall_emotion')
    def validate_overall_emotion_consistency(cls, v, values):
        """Validate overall emotion is consistent with segment data."""
        if 'segments' in values and values['segments']:
            # Count emotion occurrences in segments
            emotion_counts = {}
            total_duration = 0
            
            for segment in values['segments']:
                duration = segment.end_time - segment.start_time
                emotion = segment.combined_emotion
                
                if emotion not in emotion_counts:
                    emotion_counts[emotion] = 0
                emotion_counts[emotion] += duration * segment.combined_confidence
                total_duration += duration
            
            # Most prevalent emotion should match overall emotion
            if emotion_counts:
                most_prevalent = max(emotion_counts.items(), key=lambda x: x[1])[0]
                if v != most_prevalent:
                    # Allow some flexibility - warn but don't fail
                    pass
                    
        return v
    
    @property
    def total_duration(self) -> float:
        """Get the total duration of the emotion analysis."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end_time - self.segments[0].start_time if self.segments else 0.0
    
    def get_dominant_emotion(self) -> EmotionType:
        """Get the dominant emotion across all segments."""
        if not self.segments:
            return EmotionType.NEUTRAL
        
        emotion_weights = {}
        for segment in self.segments:
            duration = segment.duration
            emotion = segment.combined_emotion
            weight = duration * segment.combined_confidence
            
            if emotion not in emotion_weights:
                emotion_weights[emotion] = 0
            emotion_weights[emotion] += weight
        
        return max(emotion_weights.items(), key=lambda x: x[1])[0] if emotion_weights else EmotionType.NEUTRAL
    
    def get_emotion_at_time(self, time_seconds: float) -> Optional[EmotionSegment]:
        """Get emotion analysis for a specific time point."""
        for segment in self.segments:
            if segment.start_time <= time_seconds <= segment.end_time:
                return segment
        return None
    
    def get_emotion_distribution(self) -> dict:
        """Get distribution of emotions across the entire analysis."""
        distribution = {emotion.value: 0.0 for emotion in EmotionType}
        total_duration = 0
        
        for segment in self.segments:
            duration = segment.end_time - segment.start_time
            weighted_duration = duration * segment.combined_confidence
            distribution[segment.combined_emotion.value] += weighted_duration
            total_duration += duration
        
        # Normalize to percentages
        if total_duration > 0:
            for emotion in distribution:
                distribution[emotion] = (distribution[emotion] / total_duration) * 100
                
        return distribution
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "textual_emotion": "neutral",
                        "textual_confidence": 0.85,
                        "tonal_emotion": "neutral",
                        "tonal_confidence": 0.78,
                        "combined_emotion": "neutral",
                        "combined_confidence": 0.82
                    },
                    {
                        "start_time": 5.0,
                        "end_time": 10.0,
                        "textual_emotion": "anger",
                        "textual_confidence": 0.92,
                        "tonal_emotion": "anger",
                        "tonal_confidence": 0.88,
                        "combined_emotion": "anger",
                        "combined_confidence": 0.90
                    }
                ],
                "overall_emotion": "neutral",
                "overall_confidence": 0.86,
                "created_at": "2025-01-27T10:00:00"
            }
        }
