"""
Real-time emotion analysis model for streaming emotion data.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class EmotionType(str, Enum):
    """Types of emotions that can be detected."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


class EmotionIntensity(str, Enum):
    """Intensity levels for emotions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmotionStatus(str, Enum):
    """Status of emotion analysis processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RealTimeEmotion(BaseModel):
    """Real-time emotion analysis model for streaming emotion data."""
    
    # Basic information
    file_id: str = Field(..., description="Unique identifier for the file")
    session_id: str = Field(..., description="Session identifier for real-time processing")
    
    # Emotion information
    emotion_type: EmotionType = Field(..., description="Type of emotion detected")
    intensity: EmotionIntensity = Field(..., description="Intensity level of the emotion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this emotion")
    
    # Timing information
    timestamp: float = Field(..., description="Timestamp when this emotion was detected")
    start_time: float = Field(..., description="Start time of this emotion segment")
    end_time: float = Field(..., description="End time of this emotion segment")
    
    # Status and metadata
    status: EmotionStatus = Field(default=EmotionStatus.COMPLETED, description="Processing status")
    is_final: bool = Field(default=False, description="Whether this is a final emotion analysis")
    is_partial: bool = Field(default=True, description="Whether this is a partial emotion analysis")
    
    # Additional metadata
    processing_time: Optional[float] = Field(default=None, description="Time taken to process this segment")
    model_version: Optional[str] = Field(default=None, description="Version of the emotion model used")
    created_at: datetime = Field(default_factory=datetime.now, description="When this emotion was created")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class EmotionUpdate(BaseModel):
    """Model for real-time emotion updates."""
    
    type: str = Field(default="emotion", description="Type of update")
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Update content
    emotion: RealTimeEmotion = Field(..., description="The emotion data")
    
    # Update metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="When this update was sent")
    sequence_number: int = Field(..., description="Sequence number for ordering updates")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmotionBatch(BaseModel):
    """Model for batch emotion updates."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Batch content
    emotions: List[RealTimeEmotion] = Field(..., description="List of emotions in this batch")
    
    # Batch metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="When this batch was created")
    batch_size: int = Field(..., description="Number of emotions in this batch")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmotionSummary(BaseModel):
    """Summary of emotion analysis processing."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Summary statistics
    total_duration: float = Field(..., description="Total duration of the audio/video")
    processed_duration: float = Field(..., description="Duration that has been processed")
    total_segments: int = Field(..., description="Total number of emotion segments")
    
    # Emotion distribution
    emotion_distribution: Dict[EmotionType, int] = Field(..., description="Distribution of emotion types")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    dominant_emotion: EmotionType = Field(..., description="Most frequently detected emotion")
    
    # Intensity distribution
    intensity_distribution: Dict[EmotionIntensity, int] = Field(..., description="Distribution of intensity levels")
    average_intensity: EmotionIntensity = Field(..., description="Average intensity level")
    
    # Status
    status: EmotionStatus = Field(..., description="Overall processing status")
    is_complete: bool = Field(..., description="Whether processing is complete")
    
    # Timestamps
    started_at: datetime = Field(..., description="When processing started")
    completed_at: Optional[datetime] = Field(default=None, description="When processing completed")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True