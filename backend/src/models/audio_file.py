"""
AudioFile model for SawtFeel application.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid

class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    UPLOADED = "uploaded"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """File type enumeration."""
    AUDIO = "audio"
    VIDEO = "video"


class TranscriptionService(str, Enum):
    """Transcription service enumeration."""
    WHISPER = "whisper"
    GEMINI = "gemini"


class AudioFile(BaseModel):
    """AudioFile model with processing metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: FileType
    format: str
    duration: Optional[float] = None
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    processing_status: ProcessingStatus = ProcessingStatus.UPLOADED
    file_path: str
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    transcription_service: Optional[TranscriptionService] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
