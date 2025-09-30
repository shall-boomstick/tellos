"""
Unit tests for all backend models in SawtFeel application.
Tests model validation, serialization, and business logic.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.models.audio_file import AudioFile, ProcessingStatus, FileType
from src.models.transcript import Transcript, WordSegment
from src.models.emotion_analysis import EmotionAnalysis, EmotionSegment, EmotionType
from src.models.playback_state import PlaybackState


class TestAudioFile:
    """Test cases for AudioFile model."""
    
    def test_audio_file_creation_valid(self):
        """Test creating a valid AudioFile."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        assert audio_file.id == "test-123"
        assert audio_file.filename == "test.mp4"
        assert audio_file.file_type == FileType.VIDEO
        assert audio_file.format == "mp4"
        assert audio_file.file_size == 1024000
        assert audio_file.processing_status == ProcessingStatus.UPLOADED
        assert audio_file.upload_timestamp is not None
        assert audio_file.expires_at > datetime.now()
    
    def test_audio_file_validation_empty_id(self):
        """Test AudioFile validation with empty ID."""
        with pytest.raises(ValidationError):
            AudioFile(
                id="",
                filename="test.mp4",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=1024000,
                file_path="/tmp/test.mp4"
            )
    
    def test_audio_file_validation_negative_size(self):
        """Test AudioFile validation with negative file size."""
        with pytest.raises(ValidationError):
            AudioFile(
                id="test-123",
                filename="test.mp4",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=-100,
                file_path="/tmp/test.mp4"
            )
    
    def test_audio_file_validation_invalid_filename(self):
        """Test AudioFile validation with invalid filename."""
        with pytest.raises(ValidationError):
            AudioFile(
                id="test-123",
                filename="",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=1024000,
                file_path="/tmp/test.mp4"
            )
    
    def test_audio_file_serialization(self):
        """Test AudioFile serialization to dict."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        data = audio_file.dict()
        
        assert data["id"] == "test-123"
        assert data["filename"] == "test.mp4"
        assert data["file_type"] == "video"
        assert data["processing_status"] == "uploaded"
        assert "upload_timestamp" in data
    
    def test_audio_file_status_transitions(self):
        """Test valid processing status transitions."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        # Valid transitions
        audio_file.processing_status = ProcessingStatus.EXTRACTING_AUDIO
        assert audio_file.processing_status == ProcessingStatus.EXTRACTING_AUDIO
        
        audio_file.processing_status = ProcessingStatus.TRANSCRIBING
        assert audio_file.processing_status == ProcessingStatus.TRANSCRIBING
        
        audio_file.processing_status = ProcessingStatus.ANALYZING
        assert audio_file.processing_status == ProcessingStatus.ANALYZING
        
        audio_file.processing_status = ProcessingStatus.COMPLETED
        assert audio_file.processing_status == ProcessingStatus.COMPLETED


class TestWordSegment:
    """Test cases for WordSegment model."""
    
    def test_word_segment_creation_valid(self):
        """Test creating a valid WordSegment."""
        word = WordSegment(
            word="مرحبا",
            start_time=1.5,
            end_time=2.0,
            confidence=0.95
        )
        
        assert word.word == "مرحبا"
        assert word.start_time == 1.5
        assert word.end_time == 2.0
        assert word.confidence == 0.95
    
    def test_word_segment_validation_timing(self):
        """Test WordSegment validation with invalid timing."""
        with pytest.raises(ValidationError):
            WordSegment(
                word="مرحبا",
                start_time=2.0,
                end_time=1.5,  # End before start
                confidence=0.95
            )
    
    def test_word_segment_validation_confidence(self):
        """Test WordSegment validation with invalid confidence."""
        with pytest.raises(ValidationError):
            WordSegment(
                word="مرحبا",
                start_time=1.5,
                end_time=2.0,
                confidence=1.5  # > 1.0
            )
        
        with pytest.raises(ValidationError):
            WordSegment(
                word="مرحبا",
                start_time=1.5,
                end_time=2.0,
                confidence=-0.1  # < 0.0
            )
    
    def test_word_segment_duration_property(self):
        """Test WordSegment duration calculation."""
        word = WordSegment(
            word="مرحبا",
            start_time=1.5,
            end_time=2.5,
            confidence=0.95
        )
        
        assert word.duration == 1.0


class TestTranscript:
    """Test cases for Transcript model."""
    
    def test_transcript_creation_valid(self):
        """Test creating a valid Transcript."""
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="بك", start_time=0.5, end_time=1.0, confidence=0.92)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك",
            words=words,
            language="ar",
            confidence=0.93
        )
        
        assert transcript.audio_file_id == "test-123"
        assert transcript.text == "مرحبا بك"
        assert len(transcript.words) == 2
        assert transcript.language == "ar"
        assert transcript.confidence == 0.93
    
    def test_transcript_validation_empty_text(self):
        """Test Transcript validation with empty text."""
        with pytest.raises(ValidationError):
            Transcript(
                audio_file_id="test-123",
                text="",
                words=[],
                language="ar",
                confidence=0.93
            )
    
    def test_transcript_validation_confidence(self):
        """Test Transcript validation with invalid confidence."""
        with pytest.raises(ValidationError):
            Transcript(
                audio_file_id="test-123",
                text="مرحبا",
                words=[],
                language="ar",
                confidence=1.5
            )
    
    def test_transcript_word_count_property(self):
        """Test Transcript word count calculation."""
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="بك", start_time=0.5, end_time=1.0, confidence=0.92)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك",
            words=words,
            language="ar",
            confidence=0.93
        )
        
        assert transcript.word_count == 2
    
    def test_transcript_duration_property(self):
        """Test Transcript total duration calculation."""
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="بك", start_time=0.5, end_time=2.0, confidence=0.92)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك",
            words=words,
            language="ar",
            confidence=0.93
        )
        
        assert transcript.duration == 2.0
    
    def test_transcript_get_word_at_time(self):
        """Test getting word at specific time."""
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="بك", start_time=0.5, end_time=1.0, confidence=0.92)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك",
            words=words,
            language="ar",
            confidence=0.93
        )
        
        # Test exact time matches
        word_at_0_25 = transcript.get_word_at_time(0.25)
        assert word_at_0_25.word == "مرحبا"
        
        word_at_0_75 = transcript.get_word_at_time(0.75)
        assert word_at_0_75.word == "بك"
        
        # Test time outside range
        word_at_2_0 = transcript.get_word_at_time(2.0)
        assert word_at_2_0 is None


class TestEmotionSegment:
    """Test cases for EmotionSegment model."""
    
    def test_emotion_segment_creation_valid(self):
        """Test creating a valid EmotionSegment."""
        segment = EmotionSegment(
            start_time=0.0,
            end_time=2.0,
            textual_emotion=EmotionType.JOY,
            textual_confidence=0.85,
            tonal_emotion=EmotionType.NEUTRAL,
            tonal_confidence=0.78,
            combined_emotion=EmotionType.JOY,
            combined_confidence=0.82
        )
        
        assert segment.start_time == 0.0
        assert segment.end_time == 2.0
        assert segment.textual_emotion == EmotionType.JOY
        assert segment.combined_emotion == EmotionType.JOY
        assert segment.duration == 2.0
    
    def test_emotion_segment_validation_timing(self):
        """Test EmotionSegment validation with invalid timing."""
        with pytest.raises(ValidationError):
            EmotionSegment(
                start_time=2.0,
                end_time=1.0,  # End before start
                textual_emotion=EmotionType.JOY,
                textual_confidence=0.85,
                tonal_emotion=EmotionType.NEUTRAL,
                tonal_confidence=0.78,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.82
            )
    
    def test_emotion_segment_validation_confidence(self):
        """Test EmotionSegment validation with invalid confidence values."""
        with pytest.raises(ValidationError):
            EmotionSegment(
                start_time=0.0,
                end_time=2.0,
                textual_emotion=EmotionType.JOY,
                textual_confidence=1.5,  # > 1.0
                tonal_emotion=EmotionType.NEUTRAL,
                tonal_confidence=0.78,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.82
            )


class TestEmotionAnalysis:
    """Test cases for EmotionAnalysis model."""
    
    def test_emotion_analysis_creation_valid(self):
        """Test creating a valid EmotionAnalysis."""
        segments = [
            EmotionSegment(
                start_time=0.0,
                end_time=2.0,
                textual_emotion=EmotionType.JOY,
                textual_confidence=0.85,
                tonal_emotion=EmotionType.NEUTRAL,
                tonal_confidence=0.78,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.82
            ),
            EmotionSegment(
                start_time=2.0,
                end_time=4.0,
                textual_emotion=EmotionType.SADNESS,
                textual_confidence=0.75,
                tonal_emotion=EmotionType.SADNESS,
                tonal_confidence=0.80,
                combined_emotion=EmotionType.SADNESS,
                combined_confidence=0.78
            )
        ]
        
        analysis = EmotionAnalysis(
            audio_file_id="test-123",
            segments=segments,
            overall_emotion=EmotionType.NEUTRAL,
            overall_confidence=0.80
        )
        
        assert analysis.audio_file_id == "test-123"
        assert len(analysis.segments) == 2
        assert analysis.overall_emotion == EmotionType.NEUTRAL
        assert analysis.total_duration == 4.0
    
    def test_emotion_analysis_get_emotion_at_time(self):
        """Test getting emotion at specific time."""
        segments = [
            EmotionSegment(
                start_time=0.0,
                end_time=2.0,
                textual_emotion=EmotionType.JOY,
                textual_confidence=0.85,
                tonal_emotion=EmotionType.NEUTRAL,
                tonal_confidence=0.78,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.82
            ),
            EmotionSegment(
                start_time=2.0,
                end_time=4.0,
                textual_emotion=EmotionType.SADNESS,
                textual_confidence=0.75,
                tonal_emotion=EmotionType.SADNESS,
                tonal_confidence=0.80,
                combined_emotion=EmotionType.SADNESS,
                combined_confidence=0.78
            )
        ]
        
        analysis = EmotionAnalysis(
            audio_file_id="test-123",
            segments=segments,
            overall_emotion=EmotionType.NEUTRAL,
            overall_confidence=0.80
        )
        
        # Test time in first segment
        emotion_at_1 = analysis.get_emotion_at_time(1.0)
        assert emotion_at_1.combined_emotion == EmotionType.JOY
        
        # Test time in second segment
        emotion_at_3 = analysis.get_emotion_at_time(3.0)
        assert emotion_at_3.combined_emotion == EmotionType.SADNESS
        
        # Test time outside range
        emotion_at_5 = analysis.get_emotion_at_time(5.0)
        assert emotion_at_5 is None
    
    def test_emotion_analysis_dominant_emotion(self):
        """Test calculating dominant emotion across segments."""
        segments = [
            EmotionSegment(
                start_time=0.0,
                end_time=1.0,
                textual_emotion=EmotionType.JOY,
                textual_confidence=0.85,
                tonal_emotion=EmotionType.JOY,
                tonal_confidence=0.78,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.82
            ),
            EmotionSegment(
                start_time=1.0,
                end_time=2.0,
                textual_emotion=EmotionType.JOY,
                textual_confidence=0.75,
                tonal_emotion=EmotionType.JOY,
                tonal_confidence=0.80,
                combined_emotion=EmotionType.JOY,
                combined_confidence=0.78
            ),
            EmotionSegment(
                start_time=2.0,
                end_time=3.0,
                textual_emotion=EmotionType.SADNESS,
                textual_confidence=0.70,
                tonal_emotion=EmotionType.SADNESS,
                tonal_confidence=0.75,
                combined_emotion=EmotionType.SADNESS,
                combined_confidence=0.73
            )
        ]
        
        analysis = EmotionAnalysis(
            audio_file_id="test-123",
            segments=segments,
            overall_emotion=EmotionType.JOY,
            overall_confidence=0.80
        )
        
        dominant = analysis.get_dominant_emotion()
        assert dominant == EmotionType.JOY  # 2 out of 3 segments


class TestPlaybackState:
    """Test cases for PlaybackState model."""
    
    def test_playback_state_creation_valid(self):
        """Test creating a valid PlaybackState."""
        state = PlaybackState(
            audio_file_id="test-123",
            current_time_seconds=15.5,
            is_playing=True,
            current_word_index=10,
            current_emotion_segment_index=2
        )
        
        assert state.audio_file_id == "test-123"
        assert state.current_time_seconds == 15.5
        assert state.is_playing is True
        assert state.current_word_index == 10
        assert state.current_emotion_segment_index == 2
    
    def test_playback_state_validation_negative_time(self):
        """Test PlaybackState validation with negative time."""
        with pytest.raises(ValidationError):
            PlaybackState(
                audio_file_id="test-123",
                current_time_seconds=-1.0,
                is_playing=False
            )
    
    def test_playback_state_validation_negative_indices(self):
        """Test PlaybackState validation with negative indices."""
        with pytest.raises(ValidationError):
            PlaybackState(
                audio_file_id="test-123",
                current_time_seconds=15.5,
                is_playing=True,
                current_word_index=-1
            )
        
        with pytest.raises(ValidationError):
            PlaybackState(
                audio_file_id="test-123",
                current_time_seconds=15.5,
                is_playing=True,
                current_emotion_segment_index=-1
            )
    
    def test_playback_state_serialization(self):
        """Test PlaybackState serialization."""
        state = PlaybackState(
            audio_file_id="test-123",
            current_time_seconds=15.5,
            is_playing=True,
            current_word_index=10,
            current_emotion_segment_index=2
        )
        
        data = state.dict()
        
        assert data["audio_file_id"] == "test-123"
        assert data["current_time_seconds"] == 15.5
        assert data["is_playing"] is True
        assert data["current_word_index"] == 10
        assert data["current_emotion_segment_index"] == 2


class TestEmotionType:
    """Test cases for EmotionType enum."""
    
    def test_emotion_type_values(self):
        """Test EmotionType enum values."""
        assert EmotionType.JOY.value == "joy"
        assert EmotionType.SADNESS.value == "sadness"
        assert EmotionType.ANGER.value == "anger"
        assert EmotionType.FEAR.value == "fear"
        assert EmotionType.SURPRISE.value == "surprise"
        assert EmotionType.NEUTRAL.value == "neutral"
    
    def test_emotion_type_from_string(self):
        """Test creating EmotionType from string."""
        assert EmotionType("joy") == EmotionType.JOY
        assert EmotionType("sadness") == EmotionType.SADNESS
        assert EmotionType("neutral") == EmotionType.NEUTRAL
    
    def test_emotion_type_serialization(self):
        """Test EmotionType serialization in models."""
        segment = EmotionSegment(
            start_time=0.0,
            end_time=2.0,
            textual_emotion=EmotionType.JOY,
            textual_confidence=0.85,
            tonal_emotion=EmotionType.NEUTRAL,
            tonal_confidence=0.78,
            combined_emotion=EmotionType.JOY,
            combined_confidence=0.82
        )
        
        data = segment.dict()
        assert data["textual_emotion"] == "joy"
        assert data["tonal_emotion"] == "neutral"
        assert data["combined_emotion"] == "joy"


class TestFileType:
    """Test cases for FileType enum."""
    
    def test_file_type_values(self):
        """Test FileType enum values."""
        assert FileType.AUDIO.value == "audio"
        assert FileType.VIDEO.value == "video"
    
    def test_file_type_from_string(self):
        """Test creating FileType from string."""
        assert FileType("audio") == FileType.AUDIO
        assert FileType("video") == FileType.VIDEO


class TestProcessingStatus:
    """Test cases for ProcessingStatus enum."""
    
    def test_processing_status_values(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.UPLOADED.value == "uploaded"
        assert ProcessingStatus.EXTRACTING_AUDIO.value == "extracting_audio"
        assert ProcessingStatus.TRANSCRIBING.value == "transcribing"
        assert ProcessingStatus.ANALYZING.value == "analyzing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
    
    def test_processing_status_workflow(self):
        """Test typical processing status workflow."""
        statuses = [
            ProcessingStatus.UPLOADED,
            ProcessingStatus.EXTRACTING_AUDIO,
            ProcessingStatus.TRANSCRIBING,
            ProcessingStatus.ANALYZING,
            ProcessingStatus.COMPLETED
        ]
        
        # Verify all statuses are different
        assert len(set(statuses)) == len(statuses)
        
        # Verify they can be compared
        assert ProcessingStatus.UPLOADED != ProcessingStatus.COMPLETED
        assert ProcessingStatus.FAILED != ProcessingStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
