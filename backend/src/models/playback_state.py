"""
Playback state model for real-time video synchronization.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class PlaybackStatus(str, Enum):
    """Status of video playback."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    SEEKING = "seeking"
    ERROR = "error"


class SyncStatus(str, Enum):
    """Status of synchronization."""
    SYNCED = "synced"
    SYNCING = "syncing"
    OUT_OF_SYNC = "out_of_sync"
    ERROR = "error"


class PlaybackState(BaseModel):
    """Model for real-time playback state."""
    
    # Basic information
    file_id: str = Field(..., description="Unique identifier for the file")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session identifier")
    
    # Playback information
    current_time: float = Field(..., ge=0.0, description="Current playback time in seconds")
    duration: float = Field(..., ge=0.0, description="Total duration in seconds")
    playback_rate: float = Field(default=1.0, ge=0.1, le=4.0, description="Playback rate multiplier")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Volume level")
    
    # Status information
    status: PlaybackStatus = Field(default=PlaybackStatus.STOPPED, description="Current playback status")
    is_playing: bool = Field(default=False, description="Whether video is currently playing")
    is_paused: bool = Field(default=True, description="Whether video is paused")
    is_seeking: bool = Field(default=False, description="Whether video is seeking")
    
    # Synchronization information
    sync_status: SyncStatus = Field(default=SyncStatus.SYNCED, description="Synchronization status")
    sync_offset: float = Field(default=0.0, description="Synchronization offset in seconds")
    last_sync_time: Optional[datetime] = Field(default=None, description="Last synchronization time")
    
    # Real-time data synchronization
    transcript_sync: bool = Field(default=True, description="Whether transcript is synchronized")
    emotion_sync: bool = Field(default=True, description="Whether emotion analysis is synchronized")
    
    # Buffering information
    buffered_time: float = Field(default=0.0, ge=0.0, description="Amount of video buffered in seconds")
    buffer_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Buffer percentage")
    
    # Quality information
    video_quality: Optional[str] = Field(default=None, description="Current video quality")
    audio_quality: Optional[str] = Field(default=None, description="Current audio quality")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if any")
    error_code: Optional[str] = Field(default=None, description="Error code if any")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="When this state was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When this state was last updated")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class PlaybackUpdate(BaseModel):
    """Model for real-time playback updates."""
    
    type: str = Field(default="playback", description="Type of update")
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Update content
    state: PlaybackState = Field(..., description="The playback state")
    
    # Update metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="When this update was sent")
    sequence_number: int = Field(..., description="Sequence number for ordering updates")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SeekRequest(BaseModel):
    """Model for seek requests."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    target_time: float = Field(..., ge=0.0, description="Target time to seek to")
    seek_type: str = Field(default="absolute", description="Type of seek (absolute, relative)")
    
    class Config:
        """Pydantic configuration."""
        pass


class PlaybackControl(BaseModel):
    """Model for playback control commands."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Control commands
    command: str = Field(..., description="Control command (play, pause, stop, seek)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Command parameters")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.now, description="When this command was sent")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SyncRequest(BaseModel):
    """Model for synchronization requests."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Synchronization parameters
    current_time: float = Field(..., ge=0.0, description="Current playback time")
    target_time: float = Field(..., ge=0.0, description="Target synchronization time")
    tolerance: float = Field(default=0.1, ge=0.0, description="Synchronization tolerance in seconds")
    
    # Data to sync
    sync_transcript: bool = Field(default=True, description="Whether to sync transcript")
    sync_emotion: bool = Field(default=True, description="Whether to sync emotion analysis")
    
    class Config:
        """Pydantic configuration."""
        pass


class PlaybackSummary(BaseModel):
    """Summary of playback session."""
    
    file_id: str = Field(..., description="File identifier")
    session_id: str = Field(..., description="Session identifier")
    
    # Session statistics
    total_duration: float = Field(..., description="Total session duration")
    played_duration: float = Field(..., description="Total time played")
    paused_duration: float = Field(..., description="Total time paused")
    seek_count: int = Field(default=0, description="Number of seeks performed")
    
    # Quality metrics
    average_video_quality: Optional[str] = Field(default=None, description="Average video quality")
    average_audio_quality: Optional[str] = Field(default=None, description="Average audio quality")
    buffer_underruns: int = Field(default=0, description="Number of buffer underruns")
    
    # Synchronization metrics
    sync_accuracy: float = Field(..., ge=0.0, le=1.0, description="Synchronization accuracy")
    sync_errors: int = Field(default=0, description="Number of synchronization errors")
    
    # Timestamps
    started_at: datetime = Field(..., description="When session started")
    ended_at: Optional[datetime] = Field(default=None, description="When session ended")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlaybackSession:
    """Playback session manager for real-time synchronization."""
    
    def __init__(self, file_id: str, session_id: str = None):
        self.file_id = file_id
        self.session_id = session_id or str(uuid.uuid4())
        self.current_time = 0.0
        self.duration = 0.0
        self.is_playing = False
        self.is_paused = False
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_position(self, current_time: float):
        """Update current playback position."""
        self.current_time = current_time
        self.updated_at = datetime.now()
    
    def set_playing_state(self, is_playing: bool):
        """Set playing state."""
        self.is_playing = is_playing
        self.is_paused = not is_playing
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "file_id": self.file_id,
            "session_id": self.session_id,
            "current_time": self.current_time,
            "duration": self.duration,
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class PlaybackManager:
    """Manages playback sessions for real-time synchronization."""
    
    def __init__(self):
        self.sessions: Dict[str, PlaybackSession] = {}
    
    def create_session(self, file_id: str) -> PlaybackSession:
        """Create a new playback session."""
        session = PlaybackSession(file_id)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[PlaybackSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """Remove session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_file_sessions(self, file_id: str) -> List[PlaybackSession]:
        """Get all sessions for a file."""
        return [session for session in self.sessions.values() if session.file_id == file_id]
    
    def update_session_position(self, session_id: str, current_time: float):
        """Update session position."""
        session = self.get_session(session_id)
        if session:
            session.update_position(current_time)
    
    def set_session_playing(self, session_id: str, is_playing: bool):
        """Set session playing state."""
        session = self.get_session(session_id)
        if session:
            session.set_playing_state(is_playing)


# Global playback manager instance
playback_manager = PlaybackManager()