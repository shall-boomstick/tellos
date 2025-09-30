"""
Transcript model for SawtFeel application.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uuid

class WordSegment(BaseModel):
    """Word-level timing and confidence data."""
    
    word: str = Field(..., description="Arabic word")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")
    confidence: float = Field(..., ge=0, le=1, description="Word-level confidence")
    
    @validator('end_time')
    def end_time_must_be_after_start(cls, v, values):
        """Validate that end_time is after start_time."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v
    
    @property
    def duration(self) -> float:
        """Get the duration of this word segment."""
        return self.end_time - self.start_time

class Transcript(BaseModel):
    """Transcript model with word-level timestamps."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_file_id: str = Field(..., description="Reference to AudioFile")
    text: str = Field(..., min_length=1, description="Full Arabic transcript")
    english_text: Optional[str] = Field(None, description="English translation of the transcript")
    words: List[WordSegment] = Field(default_factory=list, description="Word-level timing data")
    language: str = Field(default="ar", description="Detected language")
    confidence: float = Field(..., ge=0, le=1, description="Overall transcription confidence")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('words')
    def validate_word_timing_order(cls, v):
        """Validate that word start times are in ascending order."""
        if len(v) < 2:
            return v
            
        for i in range(1, len(v)):
            if v[i].start_time < v[i-1].start_time:
                raise ValueError('Word start times must be in ascending order')
        return v
    
    @validator('language')
    def validate_language_code(cls, v):
        """Validate language code."""
        valid_languages = ['ar', 'ar-SA', 'ar-EG', 'ar-AE', 'ar-JO', 'ar-LB']
        if v not in valid_languages:
            raise ValueError(f'Language must be one of {valid_languages}')
        return v
    
    @property
    def word_count(self) -> int:
        """Get the total number of words in the transcript."""
        return len(self.words)
    
    @property
    def duration(self) -> float:
        """Get the total duration of the transcript."""
        if not self.words:
            return 0.0
        return self.words[-1].end_time - self.words[0].start_time if self.words else 0.0
    
    def get_word_at_time(self, time: float) -> Optional[WordSegment]:
        """Get the word being spoken at a specific time."""
        for word in self.words:
            if word.start_time <= time <= word.end_time:
                return word
        return None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "audio_file_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "هذا نص تجريبي باللغة العربية",
                "words": [
                    {
                        "word": "هذا",
                        "start_time": 0.0,
                        "end_time": 0.5,
                        "confidence": 0.95
                    },
                    {
                        "word": "نص",
                        "start_time": 0.5,
                        "end_time": 1.0,
                        "confidence": 0.92
                    }
                ],
                "language": "ar",
                "confidence": 0.93,
                "created_at": "2025-01-27T10:00:00"
            }
        }
