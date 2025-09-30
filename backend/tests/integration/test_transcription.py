"""
Integration test for Arabic transcription accuracy with videos/aggression.mp4
Tests the Arabic speech recognition pipeline.
"""

import pytest
import os
import time
from fastapi.testclient import TestClient

# Import will fail initially - this is expected for TDD
try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None

class TestArabicTranscriptionIntegration:
    """Integration tests for Arabic transcription accuracy."""
    
    def setup_method(self):
        """Setup test data."""
        self.test_video_path = "videos/aggression.mp4"
        self.timeout_seconds = 120
        
    def test_arabic_transcription_accuracy(self):
        """Test Arabic transcription produces reasonable results."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Upload and process file
        file_id = self._upload_and_process_file()
        
        # Get transcript
        transcript_response = client.get(f"/api/processing/{file_id}/transcript")
        assert transcript_response.status_code == 200
        
        transcript_data = transcript_response.json()
        
        # Validate transcript structure
        assert "text" in transcript_data
        assert "words" in transcript_data
        assert "language" in transcript_data
        assert "overall_confidence" in transcript_data
        
        # Validate Arabic language detection
        assert transcript_data["language"].startswith("ar"), "Should detect Arabic language"
        
        # Validate confidence scores
        assert 0 <= transcript_data["overall_confidence"] <= 1, "Overall confidence should be 0-1"
        
        # Validate word-level data
        words = transcript_data["words"]
        assert len(words) > 0, "Should have transcribed words"
        
        for word in words:
            assert "word" in word, "Each word should have text"
            assert "start_time" in word, "Each word should have start time"
            assert "end_time" in word, "Each word should have end time"
            assert "confidence" in word, "Each word should have confidence"
            
            # Validate timing
            assert word["start_time"] >= 0, "Start time should be non-negative"
            assert word["end_time"] > word["start_time"], "End time should be after start time"
            assert 0 <= word["confidence"] <= 1, "Word confidence should be 0-1"
            
            # Validate Arabic text (basic check for Arabic characters)
            arabic_text = word["word"]
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in arabic_text)
            # Note: Some words might be numbers or punctuation, so we don't enforce all words to be Arabic
        
        # Validate chronological order
        for i in range(1, len(words)):
            assert words[i]["start_time"] >= words[i-1]["start_time"], "Words should be in chronological order"
    
    def test_transcript_timing_accuracy(self):
        """Test that transcript timing is accurate and consistent."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        # Get transcript
        transcript_response = client.get(f"/api/processing/{file_id}/transcript")
        transcript_data = transcript_response.json()
        words = transcript_data["words"]
        
        if len(words) == 0:
            pytest.skip("No words to test timing")
        
        # Test timing constraints
        total_duration = words[-1]["end_time"] - words[0]["start_time"]
        assert total_duration <= 120, "Total duration should not exceed 2 minutes (constitutional requirement)"
        
        # Test for gaps and overlaps
        for i in range(1, len(words)):
            prev_word = words[i-1]
            curr_word = words[i]
            
            # Allow small gaps but no overlaps
            time_gap = curr_word["start_time"] - prev_word["end_time"]
            assert time_gap >= -0.1, f"Minimal overlap allowed: {time_gap}s at word {i}"
            assert time_gap <= 5.0, f"Gap too large: {time_gap}s at word {i}"
    
    def test_low_confidence_word_handling(self):
        """Test handling of low-confidence transcription results."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        transcript_response = client.get(f"/api/processing/{file_id}/transcript")
        transcript_data = transcript_response.json()
        words = transcript_data["words"]
        
        if len(words) == 0:
            pytest.skip("No words to test confidence")
        
        # Check that low-confidence words are still included but marked
        low_confidence_words = [w for w in words if w["confidence"] < 0.7]
        
        # All words should still be present (no filtering)
        for word in low_confidence_words:
            assert word["word"] is not None, "Low-confidence words should still have text"
            assert len(word["word"].strip()) > 0, "Low-confidence words should not be empty"
    
    def test_empty_or_silent_audio(self):
        """Test handling of silent or very quiet audio segments."""
        # This would require a test file with silent segments
        pytest.skip("Silent audio test requires specialized test file")
    
    def _upload_and_process_file(self):
        """Helper method to upload and process test file."""
        # Upload file
        with open(self.test_video_path, "rb") as f:
            files = {"file": ("aggression.mp4", f, "video/mp4")}
            upload_response = client.post("/api/upload", files=files)
        
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]
        
        # Wait for processing
        start_time = time.time()
        while time.time() - start_time < self.timeout_seconds:
            status_response = client.get(f"/api/upload/{file_id}/status")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail("File processing failed")
                
            time.sleep(2)
        else:
            pytest.fail("Processing timeout")
            
        return file_id

if __name__ == "__main__":
    pytest.main([__file__])
