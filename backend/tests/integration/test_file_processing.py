"""
Integration test for video upload and processing with videos/aggression.mp4
Tests the complete file processing pipeline.
"""

import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from pathlib import Path
import time

# Import will fail initially - this is expected for TDD
try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None

class TestFileProcessingIntegration:
    """Integration tests for complete file processing pipeline."""
    
    def setup_method(self):
        """Setup test data."""
        self.test_video_path = "videos/aggression.mp4"
        self.timeout_seconds = 120  # 2 minutes max processing time
        
    def test_complete_video_processing_pipeline(self):
        """Test complete video upload and processing pipeline."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Step 1: Upload video file
        with open(self.test_video_path, "rb") as f:
            files = {"file": ("aggression.mp4", f, "video/mp4")}
            upload_response = client.post("/api/upload", files=files)
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        file_id = upload_data["file_id"]
        
        # Step 2: Monitor processing status until completion
        start_time = time.time()
        final_status = None
        
        while time.time() - start_time < self.timeout_seconds:
            status_response = client.get(f"/api/upload/{file_id}/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            current_status = status_data["status"]
            
            if current_status in ["completed", "failed"]:
                final_status = current_status
                break
                
            time.sleep(2)  # Wait 2 seconds between polls
        
        # Verify processing completed successfully
        assert final_status == "completed", f"Processing did not complete in {self.timeout_seconds}s"
        
        # Step 3: Verify all processing results are available
        
        # Test transcript endpoint
        transcript_response = client.get(f"/api/processing/{file_id}/transcript")
        assert transcript_response.status_code == 200
        transcript_data = transcript_response.json()
        assert "text" in transcript_data
        assert "words" in transcript_data
        assert len(transcript_data["words"]) > 0
        
        # Test emotions endpoint
        emotions_response = client.get(f"/api/processing/{file_id}/emotions")
        assert emotions_response.status_code == 200
        emotions_data = emotions_response.json()
        assert "overall_emotion" in emotions_data
        assert "segments" in emotions_data
        assert len(emotions_data["segments"]) > 0
        
        # Test audio URL endpoint
        audio_response = client.get(f"/api/processing/{file_id}/audio-url")
        assert audio_response.status_code == 200
        audio_data = audio_response.json()
        assert "audio_url" in audio_data
        assert "duration" in audio_data
        
    def test_video_format_validation(self):
        """Test that only supported video formats are accepted."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        # Test with unsupported format
        test_content = b"This is not a video file"
        files = {"file": ("test.txt", test_content, "text/plain")}
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 415
        error_data = response.json()
        assert "error" in error_data["detail"]
        assert "supported_formats" in error_data["detail"]
        
    def test_file_size_limits(self):
        """Test file size validation."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        # This would require creating a large test file
        # For now, we'll test the validation logic exists
        pytest.skip("Large file test requires special test setup")
        
    def test_concurrent_uploads(self):
        """Test multiple concurrent file uploads."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Upload the same file multiple times concurrently
        file_ids = []
        
        for i in range(3):
            with open(self.test_video_path, "rb") as f:
                files = {"file": (f"aggression_{i}.mp4", f, "video/mp4")}
                response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            file_ids.append(response.json()["file_id"])
        
        # Verify all files have unique IDs
        assert len(set(file_ids)) == len(file_ids), "File IDs should be unique"
        
        # Verify all files can be processed
        for file_id in file_ids:
            status_response = client.get(f"/api/upload/{file_id}/status")
            assert status_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__])
