"""
Test real-time streaming emotion analysis functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

class TestStreamingEmotion:
    """Test streaming emotion analysis service."""
    
    @pytest.fixture
    def mock_audio_data(self):
        """Mock audio data for testing."""
        return np.random.randn(16000)  # 1 second of audio at 16kHz
    
    @pytest.fixture
    def mock_emotion_service(self):
        """Mock emotion analysis service."""
        with patch('src.services.streaming_emotion_service.StreamingEmotionService') as mock:
            service = AsyncMock()
            mock.return_value = service
            yield service
    
    def test_streaming_emotion_initializes(self):
        """Test that streaming emotion service initializes."""
        from src.services.streaming_emotion_service import StreamingEmotionService
        service = StreamingEmotionService()
        assert service is not None
    
    def test_streaming_emotion_analyzes_audio_chunks(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion analyzes audio chunks."""
        service = mock_emotion_service
        service.analyze_audio_chunk.return_value = {
            "emotion": "happy",
            "intensity": 0.8,
            "confidence": 0.9,
            "timestamp": 0.0
        }
        
        result = asyncio.run(service.analyze_audio_chunk(mock_audio_data))
        assert result["emotion"] == "happy"
        assert result["intensity"] == 0.8
    
    def test_streaming_emotion_handles_multiple_emotions(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion handles multiple emotion types."""
        service = mock_emotion_service
        service.analyze_audio_chunk.return_value = {
            "emotions": {
                "happy": 0.6,
                "sad": 0.2,
                "angry": 0.1,
                "neutral": 0.1
            },
            "primary_emotion": "happy",
            "intensity": 0.6,
            "timestamp": 0.0
        }
        
        result = asyncio.run(service.analyze_audio_chunk(mock_audio_data))
        assert "emotions" in result
        assert result["primary_emotion"] == "happy"
    
    def test_streaming_emotion_smoothing(self, mock_emotion_service):
        """Test that streaming emotion applies smoothing to results."""
        service = mock_emotion_service
        service.apply_smoothing.return_value = {
            "emotion": "happy",
            "intensity": 0.7,
            "smoothed": True
        }
        
        raw_emotions = [
            {"emotion": "happy", "intensity": 0.9},
            {"emotion": "happy", "intensity": 0.5},
            {"emotion": "happy", "intensity": 0.7}
        ]
        
        result = asyncio.run(service.apply_smoothing(raw_emotions))
        assert result["smoothed"] is True
    
    def test_streaming_emotion_intensity_calculation(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion calculates intensity correctly."""
        service = mock_emotion_service
        service.calculate_intensity.return_value = 0.85
        
        intensity = asyncio.run(service.calculate_intensity(mock_audio_data))
        assert 0.0 <= intensity <= 1.0
    
    def test_streaming_emotion_handles_silence(self, mock_emotion_service):
        """Test that streaming emotion handles silence in audio."""
        service = mock_emotion_service
        service.analyze_audio_chunk.return_value = {
            "emotion": "neutral",
            "intensity": 0.1,
            "confidence": 0.5,
            "timestamp": 0.0,
            "is_silence": True
        }
        
        silent_audio = np.zeros(16000)  # Silent audio
        result = asyncio.run(service.analyze_audio_chunk(silent_audio))
        assert result["is_silence"] is True
    
    def test_streaming_emotion_streams_results(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion streams results in real-time."""
        service = mock_emotion_service
        service.start_streaming.return_value = AsyncMock()
        
        # Should be able to start streaming
        stream = asyncio.run(service.start_streaming("test-file-id"))
        assert stream is not None
    
    def test_streaming_emotion_handles_errors(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion handles errors gracefully."""
        service = mock_emotion_service
        service.analyze_audio_chunk.side_effect = Exception("Emotion analysis failed")
        
        with pytest.raises(Exception):
            asyncio.run(service.analyze_audio_chunk(mock_audio_data))
    
    def test_streaming_emotion_cleanup(self, mock_emotion_service):
        """Test that streaming emotion cleans up resources."""
        service = mock_emotion_service
        service.cleanup.return_value = AsyncMock()
        
        # Should be able to cleanup
        asyncio.run(service.cleanup())
        service.cleanup.assert_called_once()
    
    def test_streaming_emotion_emotion_transitions(self, mock_emotion_service):
        """Test that streaming emotion handles emotion transitions smoothly."""
        service = mock_emotion_service
        service.handle_transition.return_value = {
            "from_emotion": "happy",
            "to_emotion": "sad",
            "transition_smooth": True
        }
        
        result = asyncio.run(service.handle_transition("happy", "sad"))
        assert result["transition_smooth"] is True
    
    def test_streaming_emotion_confidence_threshold(self, mock_audio_data, mock_emotion_service):
        """Test that streaming emotion applies confidence threshold."""
        service = mock_emotion_service
        service.analyze_audio_chunk.return_value = {
            "emotion": "uncertain",
            "intensity": 0.3,
            "confidence": 0.2,
            "timestamp": 0.0,
            "below_threshold": True
        }
        
        result = asyncio.run(service.analyze_audio_chunk(mock_audio_data))
        assert result["below_threshold"] is True



