"""
Real-time transcript model for streaming transcription data.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TranscriptStatus(str, Enum):
    """Status of transcription processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WordTiming(BaseModel):
    """Word-level timing information."""
    word: str = Field(..., description="The transcribed word")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this word")


class RealTimeTranscript(BaseModel):
    """Real-time transcript model for streaming transcription."""
    
    # Basic information
    file_id: str = Field(..., description="Unique identifier for the file")
    session_id: str = Field(..., description="Session identifier for real-time processing")
    
    # Transcript content
    text: str = Field(default="", description="The transcribed text")
    english_text: Optional[str] = Field(default=None, description="English translation of the text")
    
    # Timing information
    timestamp: float = Field(..., description="Timestamp when this transcript was generated")
    start_time: float = Field(..., description="Start time of this transcript segment")
    end_time: float = Field(..., description="End time of this transcript segment")
    
    # Word-level information
    words: List[WordTiming] = Field(default_factory=list, description="Word-level timing information")
    
    # Quality metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    language: str = Field(default="auto", description="Detected or specified language")
    
    # Status and metadata
    status: TranscriptStatus = Field(default=TranscriptStatus.PENDING, description="Processing status")
    is_final: bool = Field(default=False, description="Whether this is a final transcript")
    is_partial: bool = Field(default=True, description="Whether this is a partial transcript")
    
    # Additional metadata
    processing_time: Optional[float] = Field(default=None, description="Time taken to process this segment")
    model_version: Optional[str] = Field(default=None, description="Version of the transcription model used")
    created_at: datetime = Field(default_factory=datetime.now, description="When this transcript was created")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class TranscriptUpdate(BaseModel):
    """Model for real-time transcript updates."""
    
    type: str = Field(default="transcript", description="Type of update")
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Update content
    transcript: RealTimeTranscript = Field(..., description="The transcript data")
    
    # Update metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="When this update was sent")
    sequence_number: int = Field(..., description="Sequence number for ordering updates")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TranscriptBatch(BaseModel):
    """Model for batch transcript updates."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Batch content
    transcripts: List[RealTimeTranscript] = Field(..., description="List of transcript segments")
    
    # Batch metadata
    batch_timestamp: datetime = Field(default_factory=datetime.now, description="When this batch was created")
    total_segments: int = Field(..., description="Total number of segments in this batch")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TranscriptSummary(BaseModel):
    """Summary of transcript processing."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Summary statistics
    total_duration: float = Field(..., description="Total duration of the audio/video")
    processed_duration: float = Field(..., description="Duration that has been processed")
    total_segments: int = Field(..., description="Total number of transcript segments")
    
    # Quality metrics
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    language: str = Field(..., description="Detected language")
    
    # Status
    status: TranscriptStatus = Field(..., description="Overall processing status")
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




