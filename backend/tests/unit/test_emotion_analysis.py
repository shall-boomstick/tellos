"""
Unit tests for emotion analysis functionality
Tests emotion detection accuracy, model performance, and analysis capabilities
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import numpy as np
import cv2
import json
import time

# Import the emotion analysis services
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.streaming_emotion_service import StreamingEmotionService
from models.realtime_emotion import RealTimeEmotion


class TestEmotionAnalysis:
    """Test emotion analysis functionality and accuracy"""

    def setup_method(self):
        """Set up test fixtures"""
        self.emotion_service = StreamingEmotionService()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_image(self, width=640, height=480, color=(128, 128, 128)):
        """Create a test image for emotion analysis"""
        image = np.full((height, width, 3), color, dtype=np.uint8)
        return image

    def create_test_face_image(self, emotion="neutral"):
        """Create a test image with a simulated face"""
        # Create a simple face-like pattern
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Face outline
        cv2.ellipse(image, (320, 240), (150, 200), 0, 0, 360, (255, 220, 177), -1)
        
        # Eyes
        cv2.circle(image, (280, 200), 20, (0, 0, 0), -1)
        cv2.circle(image, (360, 200), 20, (0, 0, 0), -1)
        
        # Nose
        cv2.ellipse(image, (320, 240), (10, 15), 0, 0, 360, (200, 180, 150), -1)
        
        # Mouth based on emotion
        if emotion == "happy":
            cv2.ellipse(image, (320, 280), (30, 15), 0, 0, 180, (0, 0, 0), 2)
        elif emotion == "sad":
            cv2.ellipse(image, (320, 280), (30, 15), 0, 180, 360, (0, 0, 0), 2)
        elif emotion == "angry":
            cv2.line(image, (300, 270), (340, 270), (0, 0, 0), 3)
        else:  # neutral
            cv2.line(image, (300, 280), (340, 280), (0, 0, 0), 2)
        
        return image

    def test_emotion_detection_accuracy(self):
        """Test emotion detection accuracy with known test cases"""
        test_cases = [
            {
                "emotion": "happy",
                "expected_emotions": ["happy", "joy", "positive"]
            },
            {
                "emotion": "sad",
                "expected_emotions": ["sad", "sorrow", "negative"]
            },
            {
                "emotion": "angry",
                "expected_emotions": ["angry", "anger", "negative"]
            },
            {
                "emotion": "neutral",
                "expected_emotions": ["neutral", "calm"]
            }
        ]
        
        for case in test_cases:
            image = self.create_test_face_image(case["emotion"])
            
            result = self.emotion_service.analyze_emotion(image)
            
            assert result['success'] is True
            assert 'emotions' in result
            assert 'dominant_emotion' in result
            assert 'confidence' in result
            
            # Check if expected emotions are detected
            detected_emotions = [emotion['emotion'] for emotion in result['emotions']]
            has_expected = any(
                expected in detected_emotions 
                for expected in case["expected_emotions"]
            )
            assert has_expected, f"Expected emotions {case['expected_emotions']} not found in {detected_emotions}"

    def test_emotion_confidence_scores(self):
        """Test emotion confidence scoring"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion(image)
        
        assert result['success'] is True
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
        
        # Check individual emotion confidences
        for emotion in result['emotions']:
            assert 'confidence' in emotion
            assert 0 <= emotion['confidence'] <= 1

    def test_emotion_analysis_with_multiple_faces(self):
        """Test emotion analysis with multiple faces in image"""
        # Create image with multiple faces
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # First face (happy)
        cv2.ellipse(image, (160, 240), (80, 100), 0, 0, 360, (255, 220, 177), -1)
        cv2.circle(image, (140, 200), 15, (0, 0, 0), -1)
        cv2.circle(image, (180, 200), 15, (0, 0, 0), -1)
        cv2.ellipse(image, (160, 280), (20, 10), 0, 0, 180, (0, 0, 0), 2)
        
        # Second face (sad)
        cv2.ellipse(image, (480, 240), (80, 100), 0, 0, 360, (255, 220, 177), -1)
        cv2.circle(image, (460, 200), 15, (0, 0, 0), -1)
        cv2.circle(image, (500, 200), 15, (0, 0, 0), -1)
        cv2.ellipse(image, (480, 280), (20, 10), 0, 180, 360, (0, 0, 0), 2)
        
        result = self.emotion_service.analyze_emotion(image)
        
        assert result['success'] is True
        assert 'faces' in result
        assert len(result['faces']) >= 1
        
        for face in result['faces']:
            assert 'emotions' in face
            assert 'confidence' in face
            assert 'bounding_box' in face

    def test_emotion_analysis_with_no_face(self):
        """Test emotion analysis with no face detected"""
        # Create image without faces
        image = self.create_test_image()
        
        result = self.emotion_service.analyze_emotion(image)
        
        assert result['success'] is True
        assert 'faces' in result
        assert len(result['faces']) == 0
        assert 'message' in result

    def test_emotion_analysis_performance(self):
        """Test emotion analysis performance"""
        image = self.create_test_face_image("happy")
        
        start_time = time.time()
        result = self.emotion_service.analyze_emotion(image)
        end_time = time.time()
        
        # Should complete within reasonable time (2 seconds)
        assert (end_time - start_time) < 2.0
        assert result['success'] is True

    def test_emotion_analysis_with_different_image_sizes(self):
        """Test emotion analysis with different image sizes"""
        sizes = [(320, 240), (640, 480), (1280, 720), (1920, 1080)]
        
        for width, height in sizes:
            image = self.create_test_face_image("happy")
            # Resize image
            image = cv2.resize(image, (width, height))
            
            result = self.emotion_service.analyze_emotion(image)
            
            assert result['success'] is True
            assert 'emotions' in result

    def test_emotion_analysis_with_different_image_formats(self):
        """Test emotion analysis with different image formats"""
        image = self.create_test_face_image("happy")
        
        # Test with different color spaces
        formats = [
            ("BGR", image),
            ("RGB", cv2.cvtColor(image, cv2.COLOR_BGR2RGB)),
            ("GRAY", cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        ]
        
        for format_name, format_image in formats:
            result = self.emotion_service.analyze_emotion(format_image)
            
            assert result['success'] is True
            assert 'emotions' in result

    def test_emotion_analysis_batch_processing(self):
        """Test batch emotion analysis"""
        images = [
            self.create_test_face_image("happy"),
            self.create_test_face_image("sad"),
            self.create_test_face_image("angry"),
            self.create_test_face_image("neutral")
        ]
        
        result = self.emotion_service.analyze_emotions_batch(images)
        
        assert result['success'] is True
        assert 'results' in result
        assert len(result['results']) == len(images)
        
        for i, emotion_result in enumerate(result['results']):
            assert 'emotions' in emotion_result
            assert 'confidence' in emotion_result

    def test_emotion_analysis_error_handling(self):
        """Test emotion analysis error handling"""
        # Test with None input
        result = self.emotion_service.analyze_emotion(None)
        assert result['success'] is False
        assert 'error' in result
        
        # Test with invalid image
        invalid_image = np.array([])
        result = self.emotion_service.analyze_emotion(invalid_image)
        assert result['success'] is False
        assert 'error' in result
        
        # Test with empty image
        empty_image = np.zeros((0, 0, 3), dtype=np.uint8)
        result = self.emotion_service.analyze_emotion(empty_image)
        assert result['success'] is False
        assert 'error' in result

    def test_emotion_analysis_with_mock_model(self):
        """Test emotion analysis with mocked model"""
        with patch.object(self.emotion_service, '_load_model') as mock_load:
            mock_model = Mock()
            mock_model.predict.return_value = np.array([[0.1, 0.8, 0.05, 0.05]])
            mock_load.return_value = mock_model
            
            image = self.create_test_face_image("happy")
            result = self.emotion_service.analyze_emotion(image)
            
            assert result['success'] is True
            assert 'emotions' in result
            mock_model.predict.assert_called_once()

    def test_emotion_analysis_model_validation(self):
        """Test RealTimeEmotion model validation"""
        emotion = RealTimeEmotion(
            timestamp=1234567890.0,
            emotions=[
                {"emotion": "happy", "confidence": 0.8},
                {"emotion": "joy", "confidence": 0.7},
                {"emotion": "neutral", "confidence": 0.2}
            ],
            dominant_emotion="happy",
            confidence=0.8,
            face_detected=True,
            bounding_box=[100, 100, 200, 200]
        )
        
        assert emotion.timestamp == 1234567890.0
        assert len(emotion.emotions) == 3
        assert emotion.dominant_emotion == "happy"
        assert emotion.confidence == 0.8
        assert emotion.face_detected is True
        assert emotion.bounding_box == [100, 100, 200, 200]

    def test_emotion_analysis_model_serialization(self):
        """Test RealTimeEmotion model serialization"""
        emotion = RealTimeEmotion(
            timestamp=1234567890.0,
            emotions=[
                {"emotion": "happy", "confidence": 0.8},
                {"emotion": "joy", "confidence": 0.7}
            ],
            dominant_emotion="happy",
            confidence=0.8
        )
        
        # Test to_dict
        data = emotion.to_dict()
        assert data['timestamp'] == 1234567890.0
        assert len(data['emotions']) == 2
        assert data['dominant_emotion'] == "happy"
        assert data['confidence'] == 0.8
        
        # Test from_dict
        new_emotion = RealTimeEmotion.from_dict(data)
        assert new_emotion.timestamp == emotion.timestamp
        assert new_emotion.emotions == emotion.emotions
        assert new_emotion.dominant_emotion == emotion.dominant_emotion
        assert new_emotion.confidence == emotion.confidence

    def test_emotion_analysis_consistency(self):
        """Test emotion analysis consistency across multiple calls"""
        image = self.create_test_face_image("happy")
        
        # Analyze the same image multiple times
        results = []
        for _ in range(5):
            result = self.emotion_service.analyze_emotion(image)
            assert result['success'] is True
            results.append(result)
        
        # Check consistency (dominant emotion should be the same)
        dominant_emotions = [result['dominant_emotion'] for result in results]
        assert len(set(dominant_emotions)) <= 2  # Allow some variation

    def test_emotion_analysis_with_face_detection(self):
        """Test emotion analysis with face detection"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion_with_face_detection(image)
        
        assert result['success'] is True
        assert 'faces_detected' in result
        assert result['faces_detected'] > 0
        assert 'emotions' in result

    def test_emotion_analysis_quality_metrics(self):
        """Test emotion analysis quality metrics"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion_with_quality_metrics(image)
        
        assert result['success'] is True
        assert 'quality_metrics' in result
        
        metrics = result['quality_metrics']
        assert 'face_quality' in metrics
        assert 'lighting_quality' in metrics
        assert 'blur_detection' in metrics
        assert 'pose_estimation' in metrics

    def test_emotion_analysis_with_historical_data(self):
        """Test emotion analysis with historical data context"""
        # Simulate historical emotion data
        historical_emotions = [
            RealTimeEmotion(timestamp=1234567890.0, emotions=[{"emotion": "happy", "confidence": 0.8}], dominant_emotion="happy", confidence=0.8),
            RealTimeEmotion(timestamp=1234567891.0, emotions=[{"emotion": "happy", "confidence": 0.7}], dominant_emotion="happy", confidence=0.7),
            RealTimeEmotion(timestamp=1234567892.0, emotions=[{"emotion": "neutral", "confidence": 0.6}], dominant_emotion="neutral", confidence=0.6)
        ]
        
        image = self.create_test_face_image("happy")
        result = self.emotion_service.analyze_emotion_with_context(image, historical_emotions)
        
        assert result['success'] is True
        assert 'emotions' in result
        assert 'trend_analysis' in result
        assert 'emotion_transition' in result

    def test_emotion_analysis_with_demographics(self):
        """Test emotion analysis with demographic information"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion_with_demographics(image)
        
        assert result['success'] is True
        assert 'emotions' in result
        assert 'demographics' in result
        
        demographics = result['demographics']
        assert 'age_range' in demographics
        assert 'gender' in demographics
        assert 'ethnicity' in demographics

    def test_emotion_analysis_with_audio_cues(self):
        """Test emotion analysis with audio cues"""
        image = self.create_test_face_image("happy")
        audio_features = {
            'pitch': 200.0,
            'volume': 0.7,
            'speech_rate': 150.0,
            'spectral_centroid': 1000.0
        }
        
        result = self.emotion_service.analyze_emotion_with_audio(image, audio_features)
        
        assert result['success'] is True
        assert 'emotions' in result
        assert 'multimodal_confidence' in result
        assert 'audio_emotions' in result

    def test_emotion_analysis_benchmark(self):
        """Test emotion analysis with benchmark dataset"""
        # This would typically use a real benchmark dataset
        benchmark_cases = [
            {
                "image": self.create_test_face_image("happy"),
                "expected_emotion": "happy",
                "expected_confidence": 0.7
            },
            {
                "image": self.create_test_face_image("sad"),
                "expected_emotion": "sad",
                "expected_confidence": 0.7
            }
        ]
        
        for case in benchmark_cases:
            result = self.emotion_service.analyze_emotion(case["image"])
            
            assert result['success'] is True
            assert result['dominant_emotion'] == case["expected_emotion"]
            assert result['confidence'] >= case["expected_confidence"]

    def test_emotion_analysis_with_real_time_streaming(self):
        """Test emotion analysis with real-time streaming"""
        # Simulate video frames
        frames = [
            self.create_test_face_image("happy"),
            self.create_test_face_image("sad"),
            self.create_test_face_image("angry"),
            self.create_test_face_image("neutral")
        ]
        
        results = []
        for frame in frames:
            result = self.emotion_service.analyze_emotion_streaming(frame)
            results.append(result)
        
        assert len(results) == len(frames)
        for result in results:
            assert result['success'] is True
            assert 'emotions' in result

    def test_emotion_analysis_with_caching(self):
        """Test emotion analysis with caching"""
        image = self.create_test_face_image("happy")
        
        # First analysis (should be cached)
        start_time = time.time()
        result1 = self.emotion_service.analyze_emotion(image)
        first_duration = time.time() - start_time
        
        # Second analysis (should use cache)
        start_time = time.time()
        result2 = self.emotion_service.analyze_emotion(image)
        second_duration = time.time() - start_time
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result1['dominant_emotion'] == result2['dominant_emotion']
        
        # Cached analysis should be faster
        assert second_duration < first_duration

    def test_emotion_analysis_with_custom_model(self):
        """Test emotion analysis with custom model"""
        # Mock custom model
        custom_model = Mock()
        custom_model.predict.return_value = np.array([[0.2, 0.6, 0.1, 0.1]])
        
        image = self.create_test_face_image("happy")
        result = self.emotion_service.analyze_emotion_with_custom_model(image, custom_model)
        
        assert result['success'] is True
        assert 'emotions' in result
        custom_model.predict.assert_called_once()

    def test_emotion_analysis_with_emotion_categories(self):
        """Test emotion analysis with emotion categories"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion_by_categories(image)
        
        assert result['success'] is True
        assert 'basic_emotions' in result
        assert 'compound_emotions' in result
        assert 'emotion_categories' in result

    def test_emotion_analysis_with_temporal_analysis(self):
        """Test emotion analysis with temporal analysis"""
        # Simulate emotion sequence over time
        emotion_sequence = [
            {"timestamp": 0, "emotion": "neutral", "confidence": 0.8},
            {"timestamp": 1, "emotion": "happy", "confidence": 0.7},
            {"timestamp": 2, "emotion": "happy", "confidence": 0.9},
            {"timestamp": 3, "emotion": "sad", "confidence": 0.6}
        ]
        
        result = self.emotion_service.analyze_emotion_temporal(emotion_sequence)
        
        assert result['success'] is True
        assert 'emotion_trends' in result
        assert 'emotion_transitions' in result
        assert 'temporal_patterns' in result

    def test_emotion_analysis_with_validation(self):
        """Test emotion analysis with validation checks"""
        image = self.create_test_face_image("happy")
        
        result = self.emotion_service.analyze_emotion_with_validation(image)
        
        assert result['success'] is True
        assert 'validation_results' in result
        
        validation = result['validation_results']
        assert 'face_detection_valid' in validation
        assert 'emotion_confidence_valid' in validation
        assert 'image_quality_valid' in validation

