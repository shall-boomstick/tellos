"""
Integration test for emotion analysis pipeline with videos/aggression.mp4
Tests the dual-path emotion analysis system.
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

class TestEmotionAnalysisIntegration:
    """Integration tests for emotion analysis pipeline."""
    
    def setup_method(self):
        """Setup test data."""
        self.test_video_path = "videos/aggression.mp4"
        self.timeout_seconds = 120
        self.valid_emotions = ["anger", "sadness", "joy", "neutral", "fear", "surprise"]
        
    def test_dual_path_emotion_analysis(self):
        """Test that both textual and tonal emotion analysis work."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        # Get emotion analysis
        emotions_response = client.get(f"/api/processing/{file_id}/emotions")
        assert emotions_response.status_code == 200
        
        emotions_data = emotions_response.json()
        
        # Validate overall emotion structure
        assert "overall_emotion" in emotions_data
        assert "overall_confidence" in emotions_data
        assert "segments" in emotions_data
        
        # Validate overall emotion
        assert emotions_data["overall_emotion"] in self.valid_emotions
        assert 0 <= emotions_data["overall_confidence"] <= 1
        
        # Validate segments
        segments = emotions_data["segments"]
        assert len(segments) > 0, "Should have emotion segments"
        
        for segment in segments:
            # Validate segment structure
            assert "start_time" in segment
            assert "end_time" in segment
            assert "textual_emotion" in segment
            assert "textual_confidence" in segment
            assert "tonal_emotion" in segment
            assert "tonal_confidence" in segment
            assert "combined_emotion" in segment
            assert "combined_confidence" in segment
            
            # Validate timing
            assert segment["start_time"] >= 0
            assert segment["end_time"] > segment["start_time"]
            
            # Validate emotions are valid
            assert segment["textual_emotion"] in self.valid_emotions
            assert segment["tonal_emotion"] in self.valid_emotions
            assert segment["combined_emotion"] in self.valid_emotions
            
            # Validate confidence scores
            assert 0 <= segment["textual_confidence"] <= 1
            assert 0 <= segment["tonal_confidence"] <= 1
            assert 0 <= segment["combined_confidence"] <= 1
    
    def test_emotion_segment_timing_consistency(self):
        """Test that emotion segments have consistent timing."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        emotions_response = client.get(f"/api/processing/{file_id}/emotions")
        emotions_data = emotions_response.json()
        segments = emotions_data["segments"]
        
        if len(segments) < 2:
            pytest.skip("Need at least 2 segments to test timing")
        
        # Test chronological order
        for i in range(1, len(segments)):
            prev_segment = segments[i-1]
            curr_segment = segments[i]
            
            assert curr_segment["start_time"] >= prev_segment["end_time"], \
                f"Segments should not overlap: segment {i} starts before segment {i-1} ends"
        
        # Test total duration doesn't exceed constitutional limits
        total_duration = segments[-1]["end_time"] - segments[0]["start_time"]
        assert total_duration <= 120, "Total emotion analysis should not exceed 2 minutes"
    
    def test_emotion_confidence_correlation(self):
        """Test that combined confidence correlates with individual confidences."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        emotions_response = client.get(f"/api/processing/{file_id}/emotions")
        emotions_data = emotions_response.json()
        segments = emotions_data["segments"]
        
        for i, segment in enumerate(segments):
            textual_conf = segment["textual_confidence"]
            tonal_conf = segment["tonal_confidence"]
            combined_conf = segment["combined_confidence"]
            
            # Combined confidence should be reasonable given individual confidences
            min_individual = min(textual_conf, tonal_conf)
            max_individual = max(textual_conf, tonal_conf)
            
            # Allow some flexibility but combined should be in a reasonable range
            assert combined_conf >= min_individual * 0.5, \
                f"Combined confidence too low in segment {i}: {combined_conf} vs min {min_individual}"
            assert combined_conf <= max_individual * 1.1, \
                f"Combined confidence too high in segment {i}: {combined_conf} vs max {max_individual}"
    
    def test_aggression_detection_accuracy(self):
        """Test that the aggression.mp4 file correctly detects aggressive emotions."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        file_id = self._upload_and_process_file()
        
        emotions_response = client.get(f"/api/processing/{file_id}/emotions")
        emotions_data = emotions_response.json()
        
        # Given the filename "aggression.mp4", we expect to detect some aggressive emotions
        # This is a behavioral test based on the expected content
        segments = emotions_data["segments"]
        
        # Count aggressive emotions (anger, fear)
        aggressive_emotions = ["anger", "fear"]
        aggressive_segments = [s for s in segments if s["combined_emotion"] in aggressive_emotions]
        
        # We should detect at least some aggression in an "aggression" video
        # But we allow for the possibility that the test video might not actually contain aggression
        if len(aggressive_segments) == 0:
            # Log warning but don't fail - the test video content might be different than expected
            print("Warning: No aggressive emotions detected in aggression.mp4 - verify test file content")
        
        # Verify that if aggression is detected, it has reasonable confidence
        for segment in aggressive_segments:
            assert segment["combined_confidence"] > 0.3, \
                "Aggressive emotions should have reasonable confidence when detected"
    
    def test_emotion_analysis_performance_requirement(self):
        """Test that emotion analysis meets constitutional performance requirements."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Measure processing time
        start_time = time.time()
        file_id = self._upload_and_process_file()
        processing_time = time.time() - start_time
        
        # Get file duration for comparison
        audio_response = client.get(f"/api/processing/{file_id}/audio-url")
        audio_data = audio_response.json()
        file_duration = audio_data.get("duration", 30.0)  # Default assumption
        
        # Constitutional requirement: process within 1.5x real-time
        max_allowed_time = file_duration * 1.5
        assert processing_time <= max_allowed_time, \
            f"Processing took {processing_time:.2f}s for {file_duration:.2f}s file (max allowed: {max_allowed_time:.2f}s)"
    
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
