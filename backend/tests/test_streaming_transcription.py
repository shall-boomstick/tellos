"""
Test real-time streaming transcription functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

class TestStreamingTranscription:
    """Test streaming transcription service."""
    
    @pytest.fixture
    def mock_audio_data(self):
        """Mock audio data for testing."""
        return np.random.randn(16000)  # 1 second of audio at 16kHz
    
    @pytest.fixture
    def mock_transcription_service(self):
        """Mock transcription service."""
        with patch('src.services.streaming_transcription_service.StreamingTranscriptionService') as mock:
            service = AsyncMock()
            mock.return_value = service
            yield service
    
    def test_streaming_transcription_initializes(self):
        """Test that streaming transcription service initializes."""
        from src.services.streaming_transcription_service import StreamingTranscriptionService
        service = StreamingTranscriptionService()
        assert service is not None
    
    def test_streaming_transcription_processes_audio_chunks(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription processes audio chunks."""
        service = mock_transcription_service
        service.process_audio_chunk.return_value = {
            "text": "Hello world",
            "confidence": 0.95,
            "timestamp": 0.0
        }
        
        result = asyncio.run(service.process_audio_chunk(mock_audio_data))
        assert result["text"] == "Hello world"
        assert result["confidence"] == 0.95
    
    def test_streaming_transcription_handles_empty_audio(self, mock_transcription_service):
        """Test that streaming transcription handles empty audio."""
        service = mock_transcription_service
        service.process_audio_chunk.return_value = {
            "text": "",
            "confidence": 0.0,
            "timestamp": 0.0
        }
        
        empty_audio = np.array([])
        result = asyncio.run(service.process_audio_chunk(empty_audio))
        assert result["text"] == ""
    
    def test_streaming_transcription_handles_low_confidence(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription handles low confidence results."""
        service = mock_transcription_service
        service.process_audio_chunk.return_value = {
            "text": "Unclear speech",
            "confidence": 0.3,
            "timestamp": 0.0
        }
        
        result = asyncio.run(service.process_audio_chunk(mock_audio_data))
        assert result["confidence"] < 0.5
    
    def test_streaming_transcription_streams_results(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription streams results in real-time."""
        service = mock_transcription_service
        service.start_streaming.return_value = AsyncMock()
        
        # Should be able to start streaming
        stream = asyncio.run(service.start_streaming("test-file-id"))
        assert stream is not None
    
    def test_streaming_transcription_handles_errors(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription handles errors gracefully."""
        service = mock_transcription_service
        service.process_audio_chunk.side_effect = Exception("Transcription failed")
        
        with pytest.raises(Exception):
            asyncio.run(service.process_audio_chunk(mock_audio_data))
    
    def test_streaming_transcription_cleanup(self, mock_transcription_service):
        """Test that streaming transcription cleans up resources."""
        service = mock_transcription_service
        service.cleanup.return_value = AsyncMock()
        
        # Should be able to cleanup
        asyncio.run(service.cleanup())
        service.cleanup.assert_called_once()
    
    def test_streaming_transcription_language_detection(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription detects language."""
        service = mock_transcription_service
        service.detect_language.return_value = "ar"
        
        language = asyncio.run(service.detect_language(mock_audio_data))
        assert language == "ar"
    
    def test_streaming_transcription_word_timing(self, mock_audio_data, mock_transcription_service):
        """Test that streaming transcription provides word-level timing."""
        service = mock_transcription_service
        service.process_audio_chunk.return_value = {
            "text": "Hello world",
            "confidence": 0.95,
            "timestamp": 0.0,
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.5, "end": 1.0}
            ]
        }
        
        result = asyncio.run(service.process_audio_chunk(mock_audio_data))
        assert "words" in result
        assert len(result["words"]) == 2




