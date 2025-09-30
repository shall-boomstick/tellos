"""
PlaybackState model for SawtFeel application.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timedelta
import uuid

class PlaybackState(BaseModel):
    """Playback state for UI synchronization."""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    audio_file_id: str = Field(..., description="Reference to AudioFile")
    current_time_seconds: float = Field(default=0.0, ge=0, description="Current playback position in seconds")
    is_playing: bool = Field(default=False, description="Whether audio is currently playing")
    current_word_index: Optional[int] = Field(default=None, ge=0, description="Current word index in transcript")
    current_emotion_segment_index: Optional[int] = Field(default=None, ge=0, description="Current emotion segment index")
    playback_speed: float = Field(default=1.0, gt=0, le=2.0, description="Playback speed multiplier")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last state update timestamp")
    
    @validator('playback_speed')
    def validate_playback_speed(cls, v):
        """Validate playback speed is within reasonable bounds."""
        if v <= 0 or v > 2.0:
            raise ValueError('Playback speed must be between 0 and 2.0')
        return v
    
    def is_session_active(self, timeout_minutes: int = 5) -> bool:
        """Check if session is still active based on last update time."""
        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)
        return self.last_updated > timeout_threshold
    
    def update_position(self, new_time: float) -> None:
        """Update current position and timestamp."""
        if new_time < 0:
            raise ValueError('Current time cannot be negative')
        self.current_time_seconds = new_time
        self.last_updated = datetime.now()
    
    def set_playing_state(self, is_playing: bool) -> None:
        """Update playing state and timestamp."""
        self.is_playing = is_playing
        self.last_updated = datetime.now()
    
    def set_playback_speed(self, speed: float) -> None:
        """Update playback speed and timestamp."""
        if speed <= 0 or speed > 2.0:
            raise ValueError('Playback speed must be between 0 and 2.0')
        self.playback_speed = speed
        self.last_updated = datetime.now()
    
    def get_estimated_current_time(self) -> float:
        """Get estimated current time based on last update and playing state."""
        if not self.is_playing:
            return self.current_time_seconds
        
        # Calculate elapsed time since last update
        elapsed = (datetime.now() - self.last_updated).total_seconds()
        estimated_time = self.current_time_seconds + (elapsed * self.playback_speed)
        
        return max(0, estimated_time)  # Ensure non-negative
    
    def to_websocket_message(self) -> dict:
        """Convert to WebSocket message format."""
        return {
            "type": "time_update",
            "file_id": self.audio_file_id,
            "current_time_seconds": self.current_time_seconds,
            "is_playing": self.is_playing,
            "current_word_index": self.current_word_index,
            "current_emotion_segment_index": self.current_emotion_segment_index,
            "playback_speed": self.playback_speed,
            "timestamp": self.last_updated.isoformat()
        }
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_time_seconds": 15.5,
                "is_playing": True,
                "current_word_index": 10,
                "current_emotion_segment_index": 2,
                "playback_speed": 1.0,
                "last_updated": "2025-01-27T10:00:00"
            }
        }

class PlaybackManager:
    """Manager for multiple playback sessions."""
    
    def __init__(self):
        self.sessions: dict[str, PlaybackState] = {}
    
    def create_session(self, audio_file_id: str) -> PlaybackState:
        """Create a new playback session."""
        session = PlaybackState(audio_file_id=audio_file_id)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[PlaybackState]:
        """Get playback session by ID."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> Optional[PlaybackState]:
        """Update session with new data."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_updated = datetime.now()
        return session
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a playback session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 5) -> int:
        """Remove inactive sessions and return count of removed sessions."""
        inactive_sessions = [
            session_id for session_id, session in self.sessions.items()
            if not session.is_session_active(timeout_minutes)
        ]
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
        
        return len(inactive_sessions)
    
    def get_sessions_for_file(self, audio_file_id: str) -> list[PlaybackState]:
        """Get all active sessions for a specific audio file."""
        return [
            session for session in self.sessions.values()
            if session.audio_file_id == audio_file_id and session.is_session_active()
        ]

# Global playback manager instance
playback_manager = PlaybackManager()
