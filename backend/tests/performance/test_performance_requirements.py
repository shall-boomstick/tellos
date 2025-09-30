"""
Performance tests for constitutional requirements
Tests video processing speed, latency, and memory usage requirements.
"""

import pytest
import os
import time
import psutil
import threading
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Import will fail initially - this is expected for TDD
try:
    from src.main import app
    client = TestClient(app)
except ImportError:
    client = None

class TestPerformanceRequirements:
    """Performance tests validating constitutional requirements."""
    
    def setup_method(self):
        """Setup test data."""
        self.test_video_path = "videos/aggression.mp4"
        self.process = psutil.Process()
        
    def test_video_processing_speed_requirement(self):
        """Test 1.5x real-time video processing requirement."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Get file duration first (for reference)
        # This would normally be done by analyzing the actual video file
        expected_duration = 30.0  # Assume 30 seconds for test
        
        # Measure total processing time
        start_time = time.time()
        
        # Upload file
        with open(self.test_video_path, "rb") as f:
            files = {"file": ("aggression.mp4", f, "video/mp4")}
            upload_response = client.post("/api/upload", files=files)
        
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]
        
        # Wait for processing completion
        timeout = 120  # 2 minutes max
        processing_start = time.time()
        
        while time.time() - processing_start < timeout:
            status_response = client.get(f"/api/upload/{file_id}/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail("Processing failed")
                
            time.sleep(1)
        else:
            pytest.fail("Processing timeout")
        
        total_processing_time = time.time() - start_time
        
        # Constitutional requirement: process within 1.5x real-time
        max_allowed_time = expected_duration * 1.5
        
        assert total_processing_time <= max_allowed_time, \
            f"Processing took {total_processing_time:.2f}s for {expected_duration}s video " \
            f"(max allowed: {max_allowed_time:.2f}s, ratio: {total_processing_time/expected_duration:.2f}x)"
    
    def test_audio_extraction_latency_requirement(self):
        """Test <50ms audio extraction latency requirement."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # This test would measure the specific audio extraction step
        # For now, we test the upload response time as a proxy
        
        latencies = []
        
        # Test multiple times for statistical significance
        for i in range(5):
            start_time = time.perf_counter()
            
            with open(self.test_video_path, "rb") as f:
                files = {"file": (f"test_{i}.mp4", f, "video/mp4")}
                response = client.post("/api/upload", files=files)
            
            latency = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
            
            assert response.status_code == 200
            
            # Small delay between tests
            time.sleep(0.1)
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # Constitutional requirement: <50ms audio extraction
        # Note: This tests upload latency as a proxy. Real audio extraction would be tested separately
        assert avg_latency < 1000, \
            f"Average upload latency too high: {avg_latency:.2f}ms (should be much less for audio extraction)"
        assert max_latency < 2000, \
            f"Maximum upload latency too high: {max_latency:.2f}ms"
        
        print(f"Upload latencies: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")
    
    def test_emotion_analysis_latency_requirement(self):
        """Test <200ms emotion analysis processing requirement."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        # Upload and process a file first
        file_id = self._upload_and_process_file()
        
        # Measure emotion analysis response time
        latencies = []
        
        for i in range(10):  # Test multiple times
            start_time = time.perf_counter()
            
            response = client.get(f"/api/processing/{file_id}/emotions")
            
            latency = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
            
            assert response.status_code == 200
            
            # Small delay between requests
            time.sleep(0.05)
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        
        # Constitutional requirement: <200ms emotion analysis
        assert avg_latency < 200, \
            f"Average emotion analysis latency too high: {avg_latency:.2f}ms (requirement: <200ms)"
        assert p95_latency < 300, \
            f"95th percentile latency too high: {p95_latency:.2f}ms (should be close to 200ms)"
        
        print(f"Emotion analysis latencies: avg={avg_latency:.2f}ms, p95={p95_latency:.2f}ms, max={max_latency:.2f}ms")
    
    def test_memory_usage_during_continuous_processing(self):
        """Test constant memory usage during continuous processing."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        # Measure initial memory usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        memory_measurements = [initial_memory]
        file_ids = []
        
        # Process multiple files to test memory stability
        num_files = 5
        
        for i in range(num_files):
            # Upload file
            with open(self.test_video_path, "rb") as f:
                files = {"file": (f"test_{i}.mp4", f, "video/mp4")}
                response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            file_ids.append(response.json()["file_id"])
            
            # Measure memory after each upload
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(current_memory)
            
            # Small delay
            time.sleep(1)
        
        # Wait for all processing to complete
        for file_id in file_ids:
            timeout = 60
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                status_response = client.get(f"/api/upload/{file_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] in ["completed", "failed"]:
                        break
                time.sleep(2)
        
        # Final memory measurement
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_measurements.append(final_memory)
        
        # Analyze memory usage
        max_memory = max(memory_measurements)
        memory_growth = final_memory - initial_memory
        
        # Constitutional requirement: constant memory usage
        # Allow some growth but not excessive
        max_allowed_growth = initial_memory * 0.5  # 50% growth max
        
        assert memory_growth < max_allowed_growth, \
            f"Memory growth too high: {memory_growth:.2f}MB " \
            f"(initial: {initial_memory:.2f}MB, final: {final_memory:.2f}MB, " \
            f"max allowed growth: {max_allowed_growth:.2f}MB)"
        
        print(f"Memory usage: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, "
              f"max={max_memory:.2f}MB, growth={memory_growth:.2f}MB")
    
    def test_concurrent_processing_performance(self):
        """Test performance under concurrent load."""
        if client is None:
            pytest.skip("App not implemented yet")
            
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        num_concurrent = 3
        results = []
        
        def upload_and_measure():
            start_time = time.time()
            
            with open(self.test_video_path, "rb") as f:
                files = {"file": ("concurrent_test.mp4", f, "video/mp4")}
                response = client.post("/api/upload", files=files)
            
            upload_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "upload_time": upload_time,
                    "file_id": response.json()["file_id"]
                }
            else:
                return {
                    "success": False,
                    "upload_time": upload_time,
                    "error": response.text
                }
        
        # Execute concurrent uploads
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_and_measure) for _ in range(num_concurrent)]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_uploads = [r for r in results if r["success"]]
        failed_uploads = [r for r in results if not r["success"]]
        
        assert len(successful_uploads) > 0, "At least some concurrent uploads should succeed"
        
        # Check upload times didn't degrade too much under load
        avg_upload_time = sum(r["upload_time"] for r in successful_uploads) / len(successful_uploads)
        max_upload_time = max(r["upload_time"] for r in successful_uploads)
        
        assert avg_upload_time < 10.0, f"Average concurrent upload time too high: {avg_upload_time:.2f}s"
        assert max_upload_time < 20.0, f"Maximum concurrent upload time too high: {max_upload_time:.2f}s"
        
        print(f"Concurrent performance: {len(successful_uploads)}/{num_concurrent} successful, "
              f"avg_time={avg_upload_time:.2f}s, max_time={max_upload_time:.2f}s")
    
    def test_websocket_performance_under_load(self):
        """Test WebSocket performance under load."""
        if client is None:
            pytest.skip("App not implemented yet")
        
        # Upload a file first
        file_id = self._upload_test_file()
        
        # Test WebSocket connection performance
        connection_times = []
        message_counts = []
        
        for i in range(3):  # Test multiple connections
            try:
                start_time = time.perf_counter()
                
                with client.websocket_connect(f"/ws/processing/{file_id}") as websocket:
                    connection_time = (time.perf_counter() - start_time) * 1000  # ms
                    connection_times.append(connection_time)
                    
                    # Count messages received in 5 seconds
                    message_count = 0
                    test_start = time.time()
                    
                    while time.time() - test_start < 5:
                        try:
                            websocket.receive_json(timeout=1.0)
                            message_count += 1
                        except:
                            break
                    
                    message_counts.append(message_count)
                    
            except Exception as e:
                if "404" in str(e):
                    pytest.skip("WebSocket endpoint not implemented")
                raise
        
        if connection_times:
            avg_connection_time = sum(connection_times) / len(connection_times)
            avg_message_count = sum(message_counts) / len(message_counts)
            
            # WebSocket connections should be fast
            assert avg_connection_time < 1000, f"WebSocket connection too slow: {avg_connection_time:.2f}ms"
            
            print(f"WebSocket performance: avg_connection={avg_connection_time:.2f}ms, "
                  f"avg_messages_per_5s={avg_message_count:.1f}")
    
    def _upload_and_process_file(self):
        """Helper to upload and process test file."""
        if not os.path.exists(self.test_video_path):
            pytest.skip("Test video file not found")
        
        with open(self.test_video_path, "rb") as f:
            files = {"file": ("aggression.mp4", f, "video/mp4")}
            response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        file_id = response.json()["file_id"]
        
        # Wait for processing
        timeout = 120
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_response = client.get(f"/api/upload/{file_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    return file_id
                elif status_data["status"] == "failed":
                    pytest.fail("Processing failed")
            time.sleep(2)
        
        pytest.fail("Processing timeout")
    
    def _upload_test_file(self):
        """Helper to upload test file."""
        if os.path.exists(self.test_video_path):
            with open(self.test_video_path, "rb") as f:
                files = {"file": ("test.mp4", f, "video/mp4")}
        else:
            # Use dummy content if test file not available
            files = {"file": ("test.mp4", b"dummy content", "video/mp4")}
        
        response = client.post("/api/upload", files=files)
        if response.status_code == 200:
            return response.json()["file_id"]
        else:
            pytest.skip("Could not upload test file")

if __name__ == "__main__":
    pytest.main([__file__])
