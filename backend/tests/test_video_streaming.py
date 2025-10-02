"""
Test video streaming functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import os

# Mock the main app import
with patch.dict('sys.modules', {'src.main': patch('src.main')}):
    from src.main import app

client = TestClient(app)

class TestVideoStreaming:
    """Test video streaming endpoints."""
    
    def test_video_streaming_endpoint_exists(self):
        """Test that video streaming endpoint exists."""
        response = client.get("/api/video/stream/test-file-id")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_video_streaming_handles_range_requests(self):
        """Test that video streaming handles HTTP range requests."""
        headers = {"Range": "bytes=0-1023"}
        response = client.get("/api/video/stream/test-file-id", headers=headers)
        # Should handle range requests
        assert response.status_code in [200, 206]
    
    def test_video_streaming_returns_correct_content_type(self):
        """Test that video streaming returns correct content type."""
        response = client.get("/api/video/stream/test-file-id")
        assert "video/" in response.headers.get("content-type", "")
    
    def test_video_streaming_handles_invalid_file_id(self):
        """Test video streaming handles invalid file ID."""
        response = client.get("/api/video/stream/invalid-file-id")
        assert response.status_code == 404
    
    def test_video_streaming_supports_cors(self):
        """Test that video streaming supports CORS."""
        response = client.options("/api/video/stream/test-file-id")
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_video_streaming_returns_file_size(self):
        """Test that video streaming returns file size in headers."""
        response = client.get("/api/video/stream/test-file-id")
        assert "Content-Length" in response.headers
    
    def test_video_streaming_handles_partial_content(self):
        """Test that video streaming handles partial content requests."""
        headers = {"Range": "bytes=100-200"}
        response = client.get("/api/video/stream/test-file-id", headers=headers)
        assert response.status_code in [200, 206]
    
    def test_video_streaming_metadata_endpoint(self):
        """Test video metadata endpoint."""
        response = client.get("/api/video/metadata/test-file-id")
        # Should return metadata or 404 if file doesn't exist
        assert response.status_code in [200, 404]
    
    def test_video_streaming_thumbnail_endpoint(self):
        """Test video thumbnail endpoint."""
        response = client.get("/api/video/thumbnail/test-file-id")
        # Should return thumbnail or 404 if file doesn't exist
        assert response.status_code in [200, 404]




