"""
Unit tests for video validation functionality
Tests video format validation, metadata extraction, and processing capabilities
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import cv2
import numpy as np

# Import the video validation service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.video_metadata import VideoMetadataService
from models.video_metadata import VideoMetadata


class TestVideoValidation:
    """Test video validation functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.video_service = VideoMetadataService()
        self.test_video_path = None
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        if self.test_video_path and os.path.exists(self.test_video_path):
            os.unlink(self.test_video_path)
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_video(self, duration=5, fps=30, width=640, height=480):
        """Create a test video file for testing"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        # Create frames
        for i in range(int(duration * fps)):
            # Create a simple colored frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [i % 255, (i * 2) % 255, (i * 3) % 255]
            out.write(frame)
        
        out.release()
        return video_path

    def test_validate_video_format_valid_mp4(self):
        """Test validation of valid MP4 video"""
        video_path = self.create_test_video()
        
        result = self.video_service.validate_video_format(video_path)
        
        assert result['valid'] is True
        assert result['format'] == 'mp4'
        assert 'duration' in result
        assert 'fps' in result
        assert 'resolution' in result

    def test_validate_video_format_invalid_file(self):
        """Test validation of invalid file"""
        invalid_path = os.path.join(self.temp_dir, 'nonexistent.mp4')
        
        result = self.video_service.validate_video_format(invalid_path)
        
        assert result['valid'] is False
        assert 'error' in result

    def test_validate_video_format_unsupported_format(self):
        """Test validation of unsupported video format"""
        # Create a text file with .mp4 extension
        invalid_video = os.path.join(self.temp_dir, 'invalid.mp4')
        with open(invalid_video, 'w') as f:
            f.write("This is not a video file")
        
        result = self.video_service.validate_video_format(invalid_video)
        
        assert result['valid'] is False
        assert 'error' in result

    def test_extract_video_metadata(self):
        """Test video metadata extraction"""
        video_path = self.create_test_video(duration=10, fps=25, width=1280, height=720)
        
        metadata = self.video_service.extract_metadata(video_path)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.duration > 0
        assert metadata.fps == 25
        assert metadata.width == 1280
        assert metadata.height == 720
        assert metadata.format == 'mp4'
        assert metadata.file_size > 0

    def test_extract_video_metadata_invalid_file(self):
        """Test metadata extraction from invalid file"""
        invalid_path = os.path.join(self.temp_dir, 'invalid.mp4')
        with open(invalid_path, 'w') as f:
            f.write("Not a video")
        
        with pytest.raises(Exception):
            self.video_service.extract_metadata(invalid_path)

    def test_validate_video_resolution(self):
        """Test video resolution validation"""
        # Test valid resolution
        video_path = self.create_test_video(width=1920, height=1080)
        result = self.video_service.validate_resolution(video_path, 1920, 1080)
        assert result['valid'] is True
        
        # Test invalid resolution
        result = self.video_service.validate_resolution(video_path, 1280, 720)
        assert result['valid'] is False

    def test_validate_video_duration(self):
        """Test video duration validation"""
        video_path = self.create_test_video(duration=30)
        
        # Test valid duration
        result = self.video_service.validate_duration(video_path, max_duration=60)
        assert result['valid'] is True
        
        # Test invalid duration
        result = self.video_service.validate_duration(video_path, max_duration=10)
        assert result['valid'] is False

    def test_validate_video_fps(self):
        """Test video FPS validation"""
        video_path = self.create_test_video(fps=30)
        
        # Test valid FPS
        result = self.video_service.validate_fps(video_path, min_fps=25, max_fps=60)
        assert result['valid'] is True
        
        # Test invalid FPS
        result = self.video_service.validate_fps(video_path, min_fps=60, max_fps=120)
        assert result['valid'] is False

    def test_get_video_thumbnails(self):
        """Test video thumbnail generation"""
        video_path = self.create_test_video(duration=10)
        
        thumbnails = self.video_service.get_thumbnails(video_path, count=3)
        
        assert len(thumbnails) == 3
        for thumbnail in thumbnails:
            assert 'timestamp' in thumbnail
            assert 'data' in thumbnail
            assert isinstance(thumbnail['data'], bytes)

    def test_validate_video_codec(self):
        """Test video codec validation"""
        video_path = self.create_test_video()
        
        # Test supported codec
        result = self.video_service.validate_codec(video_path, ['mp4v', 'h264'])
        assert result['valid'] is True
        
        # Test unsupported codec
        result = self.video_service.validate_codec(video_path, ['h265', 'vp9'])
        assert result['valid'] is False

    def test_calculate_video_file_size(self):
        """Test video file size calculation"""
        video_path = self.create_test_video()
        
        file_size = self.video_service.calculate_file_size(video_path)
        
        assert file_size > 0
        assert isinstance(file_size, int)

    def test_validate_video_quality(self):
        """Test video quality validation"""
        video_path = self.create_test_video(width=1920, height=1080, fps=30)
        
        # Test high quality video
        result = self.video_service.validate_quality(video_path)
        assert result['valid'] is True
        assert result['quality'] == 'high'
        
        # Test low quality video
        low_quality_path = self.create_test_video(width=320, height=240, fps=15)
        result = self.video_service.validate_quality(low_quality_path)
        assert result['valid'] is True
        assert result['quality'] == 'low'

    def test_detect_video_corruption(self):
        """Test video corruption detection"""
        video_path = self.create_test_video()
        
        # Test valid video
        result = self.video_service.detect_corruption(video_path)
        assert result['corrupted'] is False
        
        # Test corrupted video (simulate by truncating file)
        corrupted_path = os.path.join(self.temp_dir, 'corrupted.mp4')
        with open(video_path, 'rb') as src, open(corrupted_path, 'wb') as dst:
            # Copy only first half of the file
            data = src.read()
            dst.write(data[:len(data)//2])
        
        result = self.video_service.detect_corruption(corrupted_path)
        assert result['corrupted'] is True

    def test_validate_video_audio_track(self):
        """Test video audio track validation"""
        video_path = self.create_test_video()
        
        # Test video with audio (simulated)
        with patch.object(self.video_service, 'has_audio_track', return_value=True):
            result = self.video_service.validate_audio_track(video_path)
            assert result['has_audio'] is True
        
        # Test video without audio
        with patch.object(self.video_service, 'has_audio_track', return_value=False):
            result = self.video_service.validate_audio_track(video_path)
            assert result['has_audio'] is False

    def test_get_video_stream_info(self):
        """Test video stream information extraction"""
        video_path = self.create_test_video()
        
        stream_info = self.video_service.get_stream_info(video_path)
        
        assert 'video_streams' in stream_info
        assert 'audio_streams' in stream_info
        assert len(stream_info['video_streams']) > 0

    def test_validate_video_processing_requirements(self):
        """Test video processing requirements validation"""
        video_path = self.create_test_video()
        
        requirements = {
            'max_duration': 60,
            'min_resolution': (640, 480),
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'supported_formats': ['mp4', 'avi'],
            'supported_codecs': ['mp4v', 'h264']
        }
        
        result = self.video_service.validate_processing_requirements(video_path, requirements)
        
        assert result['valid'] is True
        assert 'violations' in result
        assert len(result['violations']) == 0

    def test_validate_video_processing_requirements_violations(self):
        """Test video processing requirements with violations"""
        video_path = self.create_test_video(duration=120, width=320, height=240)
        
        requirements = {
            'max_duration': 60,
            'min_resolution': (640, 480),
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'supported_formats': ['mp4'],
            'supported_codecs': ['h264']
        }
        
        result = self.video_service.validate_processing_requirements(video_path, requirements)
        
        assert result['valid'] is False
        assert 'violations' in result
        assert len(result['violations']) > 0

    def test_extract_video_frames_at_timestamps(self):
        """Test frame extraction at specific timestamps"""
        video_path = self.create_test_video(duration=10)
        
        timestamps = [1.0, 5.0, 9.0]
        frames = self.video_service.extract_frames_at_timestamps(video_path, timestamps)
        
        assert len(frames) == len(timestamps)
        for i, frame in enumerate(frames):
            assert 'timestamp' in frame
            assert 'data' in frame
            assert frame['timestamp'] == timestamps[i]
            assert isinstance(frame['data'], bytes)

    def test_validate_video_for_realtime_processing(self):
        """Test video validation specifically for real-time processing"""
        video_path = self.create_test_video(duration=30, fps=30, width=1280, height=720)
        
        result = self.video_service.validate_for_realtime_processing(video_path)
        
        assert result['suitable'] is True
        assert 'processing_time_estimate' in result
        assert 'memory_requirements' in result
        assert 'recommended_settings' in result

    def test_validate_video_for_realtime_processing_unsuitable(self):
        """Test video validation for real-time processing with unsuitable video"""
        # Create a very large, high-resolution video
        video_path = self.create_test_video(duration=300, fps=60, width=3840, height=2160)
        
        result = self.video_service.validate_for_realtime_processing(video_path)
        
        assert result['suitable'] is False
        assert 'issues' in result
        assert len(result['issues']) > 0

    def test_get_video_processing_recommendations(self):
        """Test video processing recommendations"""
        video_path = self.create_test_video(duration=60, fps=25, width=1920, height=1080)
        
        recommendations = self.video_service.get_processing_recommendations(video_path)
        
        assert 'optimization_suggestions' in recommendations
        assert 'performance_tips' in recommendations
        assert 'quality_improvements' in recommendations

    def test_validate_video_with_mock_cv2(self):
        """Test video validation with mocked OpenCV"""
        with patch('cv2.VideoCapture') as mock_capture:
            # Mock successful video capture
            mock_video = Mock()
            mock_video.isOpened.return_value = True
            mock_video.get.return_value = 30.0  # FPS
            mock_video.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 900,  # 30 seconds at 30fps
                cv2.CAP_PROP_FRAME_WIDTH: 1920,
                cv2.CAP_PROP_FRAME_HEIGHT: 1080
            }.get(prop, 0)
            mock_capture.return_value = mock_video
            
            video_path = "test_video.mp4"
            result = self.video_service.validate_video_format(video_path)
            
            assert result['valid'] is True
            assert result['fps'] == 30.0
            assert result['duration'] == 30.0
            assert result['resolution'] == (1920, 1080)

    def test_validate_video_with_corrupted_cv2(self):
        """Test video validation with corrupted OpenCV capture"""
        with patch('cv2.VideoCapture') as mock_capture:
            # Mock corrupted video capture
            mock_video = Mock()
            mock_video.isOpened.return_value = False
            mock_capture.return_value = mock_video
            
            video_path = "corrupted_video.mp4"
            result = self.video_service.validate_video_format(video_path)
            
            assert result['valid'] is False
            assert 'error' in result

    def test_video_metadata_model_validation(self):
        """Test VideoMetadata model validation"""
        metadata = VideoMetadata(
            file_path="test.mp4",
            duration=120.5,
            fps=30.0,
            width=1920,
            height=1080,
            format="mp4",
            file_size=50000000,
            codec="h264",
            bitrate=2000000
        )
        
        assert metadata.file_path == "test.mp4"
        assert metadata.duration == 120.5
        assert metadata.fps == 30.0
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.format == "mp4"
        assert metadata.file_size == 50000000
        assert metadata.codec == "h264"
        assert metadata.bitrate == 2000000

    def test_video_metadata_serialization(self):
        """Test VideoMetadata serialization"""
        metadata = VideoMetadata(
            file_path="test.mp4",
            duration=120.5,
            fps=30.0,
            width=1920,
            height=1080,
            format="mp4",
            file_size=50000000
        )
        
        # Test to_dict
        data = metadata.to_dict()
        assert data['file_path'] == "test.mp4"
        assert data['duration'] == 120.5
        assert data['fps'] == 30.0
        
        # Test from_dict
        new_metadata = VideoMetadata.from_dict(data)
        assert new_metadata.file_path == metadata.file_path
        assert new_metadata.duration == metadata.duration
        assert new_metadata.fps == metadata.fps

    def test_video_validation_error_handling(self):
        """Test video validation error handling"""
        # Test with None path
        result = self.video_service.validate_video_format(None)
        assert result['valid'] is False
        assert 'error' in result
        
        # Test with empty string path
        result = self.video_service.validate_video_format("")
        assert result['valid'] is False
        assert 'error' in result
        
        # Test with non-string path
        result = self.video_service.validate_video_format(123)
        assert result['valid'] is False
        assert 'error' in result

    def test_video_validation_performance(self):
        """Test video validation performance"""
        import time
        
        video_path = self.create_test_video()
        
        start_time = time.time()
        result = self.video_service.validate_video_format(video_path)
        end_time = time.time()
        
        # Should complete within reasonable time (1 second)
        assert (end_time - start_time) < 1.0
        assert result['valid'] is True

    def test_concurrent_video_validation(self):
        """Test concurrent video validation"""
        import threading
        import queue
        
        video_path = self.create_test_video()
        results = queue.Queue()
        
        def validate_video():
            result = self.video_service.validate_video_format(video_path)
            results.put(result)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_video)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all results
        assert results.qsize() == 5
        while not results.empty():
            result = results.get()
            assert result['valid'] is True

