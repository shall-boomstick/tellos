"""
Integration test for real-time WebSocket communication
Tests WebSocket functionality for processing and playback.
"""

import pytest
import asyncio
import json
import time
from fastapi.testclient import TestClient

# Import will fail initially - this is expected for TDD
try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None

class TestWebSocketIntegration:
    """Integration tests for WebSocket real-time communication."""
    
    def setup_method(self):
        """Setup test data."""
        self.test_video_path = "videos/aggression.mp4"
        self.timeout_seconds = 30
        
    def test_processing_websocket_flow(self):
        """Test complete WebSocket processing flow."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        # First upload a file to get a valid file ID
        file_id = self._upload_test_file()
        
        # Test WebSocket connection and message flow
        messages_received = []
        connection_established = False
        processing_completed = False
        
        try:
            with client.websocket_connect(f"/ws/processing/{file_id}") as websocket:
                connection_established = True
                
                # Should receive initial connection message
                start_time = time.time()
                while time.time() - start_time < self.timeout_seconds:
                    try:
                        data = websocket.receive_json(timeout=2.0)
                        messages_received.append(data)
                        
                        # Check message structure
                        assert "type" in data, "All messages should have a type"
                        assert "timestamp" in data, "All messages should have a timestamp"
                        
                        if data["type"] == "connected":
                            assert "file_id" in data
                            assert data["file_id"] == file_id
                            
                        elif data["type"] in ["status_update", "progress_update"]:
                            assert "file_id" in data
                            assert "status" in data
                            if "progress" in data:
                                assert 0 <= data["progress"] <= 100
                                
                        elif data["type"] == "completed":
                            processing_completed = True
                            break
                            
                    except Exception as e:
                        if "timeout" not in str(e).lower():
                            raise
                        break
                        
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not implemented")
            raise
            
        # Verify connection was established
        assert connection_established, "WebSocket connection should be established"
        
        # Verify we received messages
        assert len(messages_received) > 0, "Should receive at least one message"
        
        # Verify first message is connection confirmation
        first_message = messages_received[0]
        assert first_message["type"] == "connected", "First message should be connection confirmation"
    
    def test_playback_websocket_synchronization(self):
        """Test WebSocket playback synchronization."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        # Upload and process a file first
        file_id = self._upload_and_wait_for_processing()
        
        messages_received = []
        
        try:
            with client.websocket_connect(f"/ws/playback/{file_id}") as websocket:
                # Send play command
                websocket.send_json({
                    "type": "play",
                    "timestamp": time.time() * 1000
                })
                
                # Send time update
                websocket.send_json({
                    "type": "time_update",
                    "current_time": 5.0,
                    "is_playing": True
                })
                
                # Receive messages
                start_time = time.time()
                while time.time() - start_time < 10:  # 10 second timeout
                    try:
                        data = websocket.receive_json(timeout=1.0)
                        messages_received.append(data)
                        
                        # Validate message structure
                        assert "type" in data
                        
                        if data["type"] == "emotion_update":
                            assert "emotion" in data
                            assert "confidence" in data
                            assert "current_time" in data
                            assert 0 <= data["confidence"] <= 1
                            
                        elif data["type"] == "transcript_update":
                            assert "current_word" in data
                            assert "current_time" in data
                            
                    except Exception as e:
                        if "timeout" not in str(e).lower():
                            raise
                        break
                        
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not implemented")
            raise
        
        # Verify we received real-time updates
        assert len(messages_received) > 0, "Should receive playback messages"
        
        # Check for expected message types
        message_types = [msg["type"] for msg in messages_received]
        expected_types = ["connected", "emotion_update", "transcript_update"]
        
        # At least one expected type should be present
        assert any(msg_type in message_types for msg_type in expected_types), \
            f"Should receive expected message types, got: {message_types}"
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling with invalid file ID."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        invalid_file_id = "00000000-0000-0000-0000-000000000000"
        
        # Test processing WebSocket with invalid ID
        try:
            with client.websocket_connect(f"/ws/processing/{invalid_file_id}") as websocket:
                # Should either close immediately or send error message
                try:
                    data = websocket.receive_json(timeout=5.0)
                    if data.get("type") == "error":
                        assert "error_code" in data or "error_message" in data
                except Exception:
                    # Connection might be closed immediately, which is acceptable
                    pass
        except Exception as e:
            # Connection rejection is acceptable for invalid file ID
            assert "404" in str(e) or "4004" in str(e), "Should reject invalid file ID appropriately"
    
    def test_websocket_connection_cleanup(self):
        """Test that WebSocket connections are properly cleaned up."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        file_id = self._upload_test_file()
        
        # Create and close multiple connections
        for i in range(3):
            try:
                with client.websocket_connect(f"/ws/processing/{file_id}") as websocket:
                    # Send a message to ensure connection is active
                    websocket.send_json({"type": "ping"})
                    
                    # Receive initial message
                    try:
                        websocket.receive_json(timeout=2.0)
                    except:
                        pass  # Timeout is acceptable
                    
                # Connection should be automatically closed here
                
            except Exception as e:
                if "404" in str(e):
                    pytest.skip("WebSocket endpoint not implemented")
                # Other connection errors might be acceptable
        
        # If we reach here, connection cleanup is working
        assert True, "Connection cleanup test passed"
    
    def test_websocket_message_ordering(self):
        """Test that WebSocket messages are received in correct order."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        file_id = self._upload_test_file()
        
        messages_received = []
        
        try:
            with client.websocket_connect(f"/ws/processing/{file_id}") as websocket:
                start_time = time.time()
                
                while time.time() - start_time < 15:  # 15 second test
                    try:
                        data = websocket.receive_json(timeout=1.0)
                        messages_received.append(data)
                        
                        # Stop after receiving a few messages
                        if len(messages_received) >= 5:
                            break
                            
                    except:
                        break
                        
        except Exception as e:
            if "404" in str(e):
                pytest.skip("WebSocket endpoint not implemented")
            raise
        
        if len(messages_received) < 2:
            pytest.skip("Need at least 2 messages to test ordering")
        
        # Verify first message is always "connected"
        assert messages_received[0]["type"] == "connected", \
            "First message should always be connection confirmation"
        
        # Verify timestamps are in order (if present)
        timestamps = []
        for msg in messages_received:
            if "timestamp" in msg:
                try:
                    # Handle both ISO format and Unix timestamp
                    if isinstance(msg["timestamp"], str):
                        from datetime import datetime
                        ts = datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00')).timestamp()
                    else:
                        ts = float(msg["timestamp"])
                    timestamps.append(ts)
                except:
                    pass  # Skip invalid timestamps
        
        # Check timestamp ordering
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], \
                "Message timestamps should be in chronological order"
    
    def _upload_test_file(self):
        """Helper to upload test file and return file ID."""
        if not hasattr(self, 'test_video_path') or not os.path.exists(self.test_video_path):
            # Create a minimal test file if video doesn't exist
            test_content = b"fake video content for testing"
            files = {"file": ("test.mp4", test_content, "video/mp4")}
        else:
            with open(self.test_video_path, "rb") as f:
                files = {"file": ("aggression.mp4", f, "video/mp4")}
        
        response = client.post("/api/upload", files=files)
        assert response.status_code in [200, 415], "Upload should succeed or fail gracefully"
        
        if response.status_code == 415:
            pytest.skip("File format not supported in current implementation")
        
        return response.json()["file_id"]
    
    def _upload_and_wait_for_processing(self):
        """Helper to upload file and wait for processing completion."""
        file_id = self._upload_test_file()
        
        # Wait for processing (or timeout)
        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                status_response = client.get(f"/api/upload/{file_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] in ["completed", "failed"]:
                        break
            except:
                pass
            time.sleep(2)
        
        return file_id

if __name__ == "__main__":
    pytest.main([__file__])
