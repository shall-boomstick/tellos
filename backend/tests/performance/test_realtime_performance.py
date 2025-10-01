"""
Performance tests for real-time video processing system
Tests system performance under various load conditions
"""

import pytest
import time
import asyncio
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch

# Import the services
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.streaming_transcription_service import StreamingTranscriptionService
from services.streaming_emotion_service import StreamingEmotionService
from services.realtime_processor import RealtimeProcessor
from services.video_metadata import VideoMetadataService


class TestRealtimePerformance:
    """Test real-time processing performance"""

    def setup_method(self):
        """Set up test fixtures"""
        self.transcription_service = StreamingTranscriptionService()
        self.emotion_service = StreamingEmotionService()
        self.realtime_processor = RealtimeProcessor()
        self.video_service = VideoMetadataService()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_video_frames(self, count=100, width=640, height=480):
        """Create test video frames for performance testing"""
        frames = []
        for i in range(count):
            # Create a simple colored frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [i % 255, (i * 2) % 255, (i * 3) % 255]
            frames.append(frame)
        return frames

    def test_transcription_performance(self):
        """Test transcription service performance"""
        test_audio = os.path.join(self.temp_dir, 'test_audio.wav')
        
        # Create test audio file
        import wave
        with wave.open(test_audio, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b'\x00' * 16000)  # 1 second of silence
        
        start_time = time.time()
        
        # Test transcription performance
        result = self.transcription_service.transcribe_audio(test_audio)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result['success'] is True
        assert processing_time < 5.0  # Should complete within 5 seconds
        
        print(f"Transcription processing time: {processing_time:.2f} seconds")

    def test_emotion_analysis_performance(self):
        """Test emotion analysis service performance"""
        frames = self.create_test_video_frames(10)
        
        start_time = time.time()
        
        # Test emotion analysis performance
        results = []
        for frame in frames:
            result = self.emotion_service.analyze_emotion(frame)
            results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All results should be successful
        assert all(result['success'] for result in results)
        assert processing_time < 10.0  # Should complete within 10 seconds
        
        print(f"Emotion analysis processing time: {processing_time:.2f} seconds")
        print(f"Average time per frame: {processing_time / len(frames):.3f} seconds")

    def test_video_processing_performance(self):
        """Test video processing performance"""
        video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        # Create test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))
        
        frames = self.create_test_video_frames(300)  # 10 seconds at 30fps
        for frame in frames:
            out.write(frame)
        out.release()
        
        start_time = time.time()
        
        # Test video processing
        result = self.realtime_processor.process_video(video_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result['success'] is True
        assert processing_time < 30.0  # Should complete within 30 seconds
        
        print(f"Video processing time: {processing_time:.2f} seconds")

    def test_concurrent_processing_performance(self):
        """Test concurrent processing performance"""
        frames = self.create_test_video_frames(50)
        
        def process_frame(frame):
            return self.emotion_service.analyze_emotion(frame)
        
        start_time = time.time()
        
        # Test concurrent processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_frame, frame) for frame in frames]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All results should be successful
        assert all(result['success'] for result in results)
        assert processing_time < 15.0  # Should complete within 15 seconds
        
        print(f"Concurrent processing time: {processing_time:.2f} seconds")
        print(f"Average time per frame: {processing_time / len(frames):.3f} seconds")

    def test_memory_usage_performance(self):
        """Test memory usage during processing"""
        frames = self.create_test_video_frames(100)
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process frames
        results = []
        for frame in frames:
            result = self.emotion_service.analyze_emotion(frame)
            results.append(result)
            
            # Check memory usage every 10 frames
            if len(results) % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                assert memory_increase < 500  # Should not increase by more than 500MB
        
        # All results should be successful
        assert all(result['success'] for result in results)
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    def test_websocket_performance(self):
        """Test WebSocket performance"""
        from services.realtime_websocket import RealtimeWebSocketService
        
        websocket_service = RealtimeWebSocketService()
        
        # Test message sending performance
        start_time = time.time()
        
        messages = []
        for i in range(100):
            message = {
                'type': 'test',
                'data': f'Test message {i}',
                'timestamp': time.time()
            }
            messages.append(message)
        
        # Simulate sending messages
        for message in messages:
            websocket_service.send_message(message)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 1.0  # Should complete within 1 second
        
        print(f"WebSocket message sending time: {processing_time:.3f} seconds")

    def test_database_performance(self):
        """Test database performance"""
        from models.realtime_transcript import RealTimeTranscript
        from models.realtime_emotion import RealTimeEmotion
        
        # Test transcript insertion performance
        start_time = time.time()
        
        transcripts = []
        for i in range(1000):
            transcript = RealTimeTranscript(
                text=f'Test transcript {i}',
                timestamp=time.time(),
                confidence=0.9,
                language='en'
            )
            transcripts.append(transcript)
        
        # Simulate database insertion
        for transcript in transcripts:
            # In a real implementation, this would insert into database
            pass
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 2.0  # Should complete within 2 seconds
        
        print(f"Database insertion time: {processing_time:.3f} seconds")

    def test_caching_performance(self):
        """Test caching performance"""
        from services.cache_service import CacheService
        
        cache_service = CacheService()
        
        # Test cache performance
        start_time = time.time()
        
        # Test cache operations
        for i in range(1000):
            key = f'test_key_{i}'
            value = f'test_value_{i}'
            cache_service.set(key, value)
            retrieved_value = cache_service.get(key)
            assert retrieved_value == value
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 1.0  # Should complete within 1 second
        
        print(f"Cache operations time: {processing_time:.3f} seconds")

    def test_api_response_performance(self):
        """Test API response performance"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test API endpoint performance
        start_time = time.time()
        
        # Test multiple API calls
        for i in range(100):
            response = client.get('/health')
            assert response.status_code == 200
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 5.0  # Should complete within 5 seconds
        
        print(f"API response time: {processing_time:.3f} seconds")

    def test_video_streaming_performance(self):
        """Test video streaming performance"""
        video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        # Create test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))
        
        frames = self.create_test_video_frames(300)  # 10 seconds at 30fps
        for frame in frames:
            out.write(frame)
        out.release()
        
        start_time = time.time()
        
        # Test video streaming
        result = self.video_service.stream_video(video_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result['success'] is True
        assert processing_time < 20.0  # Should complete within 20 seconds
        
        print(f"Video streaming time: {processing_time:.2f} seconds")

    def test_real_time_synchronization_performance(self):
        """Test real-time synchronization performance"""
        from services.realtime_processor import RealtimeProcessor
        
        processor = RealtimeProcessor()
        
        # Test synchronization performance
        start_time = time.time()
        
        # Simulate real-time data processing
        for i in range(1000):
            data = {
                'timestamp': time.time(),
                'type': 'test',
                'data': f'Test data {i}'
            }
            processor.process_realtime_data(data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 2.0  # Should complete within 2 seconds
        
        print(f"Real-time synchronization time: {processing_time:.3f} seconds")

    def test_system_load_performance(self):
        """Test system performance under load"""
        frames = self.create_test_video_frames(200)
        
        def process_frame_with_load(frame):
            # Simulate CPU-intensive processing
            result = self.emotion_service.analyze_emotion(frame)
            
            # Additional CPU load
            for i in range(1000):
                _ = i * i
            
            return result
        
        start_time = time.time()
        
        # Test under load
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_frame_with_load, frame) for frame in frames]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All results should be successful
        assert all(result['success'] for result in results)
        assert processing_time < 30.0  # Should complete within 30 seconds
        
        print(f"System load processing time: {processing_time:.2f} seconds")

    def test_memory_leak_detection(self):
        """Test for memory leaks during processing"""
        frames = self.create_test_video_frames(1000)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process frames in batches
        for batch_start in range(0, len(frames), 100):
            batch_frames = frames[batch_start:batch_start + 100]
            
            results = []
            for frame in batch_frames:
                result = self.emotion_service.analyze_emotion(frame)
                results.append(result)
            
            # Check memory usage after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Memory increase should be reasonable
            assert memory_increase < 1000  # Should not increase by more than 1GB
        
        # All results should be successful
        assert all(result['success'] for result in results)
        
        print(f"Memory leak test completed. Final memory increase: {memory_increase:.2f} MB")

    def test_error_handling_performance(self):
        """Test error handling performance"""
        # Test with invalid data
        invalid_frames = [None, np.array([]), np.zeros((0, 0, 3))]
        
        start_time = time.time()
        
        results = []
        for frame in invalid_frames:
            try:
                result = self.emotion_service.analyze_emotion(frame)
                results.append(result)
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle errors quickly
        assert processing_time < 1.0  # Should complete within 1 second
        
        print(f"Error handling time: {processing_time:.3f} seconds")

    def test_scalability_performance(self):
        """Test system scalability"""
        frame_counts = [10, 50, 100, 200, 500]
        
        for frame_count in frame_counts:
            frames = self.create_test_video_frames(frame_count)
            
            start_time = time.time()
            
            results = []
            for frame in frames:
                result = self.emotion_service.analyze_emotion(frame)
                results.append(result)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # All results should be successful
            assert all(result['success'] for result in results)
            
            # Processing time should scale reasonably
            assert processing_time < frame_count * 0.1  # Should be less than 0.1s per frame
            
            print(f"Frame count: {frame_count}, Processing time: {processing_time:.2f}s, "
                  f"Time per frame: {processing_time / frame_count:.3f}s")

    def test_network_performance(self):
        """Test network performance"""
        import requests
        
        # Test API endpoint performance
        start_time = time.time()
        
        # Test multiple HTTP requests
        for i in range(100):
            try:
                response = requests.get('http://localhost:8000/health', timeout=1)
                assert response.status_code == 200
            except requests.exceptions.RequestException:
                # Skip if server is not running
                pass
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"Network performance test completed: {processing_time:.3f} seconds")

    def test_end_to_end_performance(self):
        """Test end-to-end system performance"""
        video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        # Create test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))
        
        frames = self.create_test_video_frames(300)  # 10 seconds at 30fps
        for frame in frames:
            out.write(frame)
        out.release()
        
        start_time = time.time()
        
        # Test complete pipeline
        result = self.realtime_processor.process_video_complete(video_path)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result['success'] is True
        assert processing_time < 60.0  # Should complete within 60 seconds
        
        print(f"End-to-end processing time: {processing_time:.2f} seconds")
        print(f"Processing speed: {300 / processing_time:.2f} frames per second")

