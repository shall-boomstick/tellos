"""
Emotion analysis accuracy validation tests for SawtFeel application.
Tests emotion detection accuracy with known test data and validation metrics.
"""

import pytest
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple

from ...src.services.emotion_analyzer import emotion_analyzer
from ...src.services.transcription_service import transcription_service
from ...src.services.audio_processor import audio_processor
from ...src.models.emotion_analysis import EmotionType
from ...src.models.transcript import Transcript, WordSegment


# Test video path
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent.parent / "videos" / "aggression.mp4"


class TestEmotionAnalysisAccuracy:
    """Test emotion analysis accuracy and validation."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_files = []
        
        # Define expected emotion patterns for test data
        self.expected_emotions = {
            "aggression.mp4": {
                "primary_emotions": [EmotionType.ANGER, EmotionType.NEUTRAL],
                "expected_confidence": 0.6,  # Minimum expected confidence
                "dominant_emotion": EmotionType.ANGER,
                "emotion_transitions": True,  # Should have emotion changes over time
                "min_segments": 3  # Minimum number of emotion segments
            }
        }
        
        # Define test phrases with expected emotions (Arabic)
        self.test_phrases = {
            "أنا سعيد جداً اليوم": EmotionType.JOY,
            "هذا مؤسف للغاية": EmotionType.SADNESS, 
            "أنا غاضب من هذا الأمر": EmotionType.ANGER,
            "أخاف من هذا الشيء": EmotionType.FEAR,
            "ما هذا المفاجأة الرائعة": EmotionType.SURPRISE,
            "الطقس جميل اليوم": EmotionType.NEUTRAL
        }
    
    def teardown_method(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_text_emotion_analysis_accuracy(self):
        """Test accuracy of text-based emotion analysis."""
        print("Testing text emotion analysis accuracy")
        
        correct_predictions = 0
        total_predictions = 0
        emotion_confusion_matrix = {}
        
        for phrase, expected_emotion in self.test_phrases.items():
            print(f"\nTesting phrase: '{phrase}'")
            print(f"Expected emotion: {expected_emotion.value}")
            
            # Analyze text emotion
            predicted_emotion, confidence = await emotion_analyzer._analyze_text_emotion(phrase)
            
            print(f"Predicted emotion: {predicted_emotion.value}")
            print(f"Confidence: {confidence:.3f}")
            
            # Track predictions for confusion matrix
            if expected_emotion not in emotion_confusion_matrix:
                emotion_confusion_matrix[expected_emotion] = {}
            if predicted_emotion not in emotion_confusion_matrix[expected_emotion]:
                emotion_confusion_matrix[expected_emotion][predicted_emotion] = 0
            
            emotion_confusion_matrix[expected_emotion][predicted_emotion] += 1
            
            # Check if prediction is correct
            if predicted_emotion == expected_emotion:
                correct_predictions += 1
            total_predictions += 1
            
            # Confidence should be reasonable
            assert confidence > 0.3, f"Very low confidence: {confidence:.3f}"
        
        # Calculate accuracy
        accuracy = correct_predictions / total_predictions
        print(f"\nText emotion analysis accuracy: {accuracy:.3f} ({correct_predictions}/{total_predictions})")
        
        # Print confusion matrix
        print("\nConfusion Matrix:")
        all_emotions = set(self.test_phrases.values()) | set(
            pred for preds in emotion_confusion_matrix.values() for pred in preds.keys()
        )
        
        for expected in sorted(all_emotions, key=lambda x: x.value):
            for predicted in sorted(all_emotions, key=lambda x: x.value):
                count = emotion_confusion_matrix.get(expected, {}).get(predicted, 0)
                if count > 0:
                    print(f"  {expected.value} -> {predicted.value}: {count}")
        
        # Minimum accuracy threshold (should be > 50% for basic emotion detection)
        assert accuracy > 0.5, f"Text emotion analysis accuracy too low: {accuracy:.3f}"
    
    @pytest.mark.asyncio
    async def test_audio_emotion_analysis_patterns(self):
        """Test audio emotion analysis with synthetic patterns."""
        print("Testing audio emotion analysis patterns")
        
        # Generate synthetic audio patterns for different emotions
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        synthetic_patterns = {
            "high_energy_fast": {
                # High energy, fast tempo (anger/excitement)
                "audio": self._generate_high_energy_audio(t, sample_rate),
                "expected_category": ["anger", "excitement", "joy"]
            },
            "low_energy_slow": {
                # Low energy, slow tempo (sadness)
                "audio": self._generate_low_energy_audio(t, sample_rate),
                "expected_category": ["sadness", "neutral"]
            },
            "variable_energy": {
                # Variable energy (surprise/fear)
                "audio": self._generate_variable_energy_audio(t, sample_rate),
                "expected_category": ["surprise", "fear", "neutral"]
            }
        }
        
        correct_classifications = 0
        total_classifications = 0
        
        for pattern_name, pattern_data in synthetic_patterns.items():
            print(f"\nTesting pattern: {pattern_name}")
            
            audio_data = pattern_data["audio"]
            expected_categories = pattern_data["expected_category"]
            
            # Analyze audio emotion
            predicted_emotion, confidence = await emotion_analyzer._analyze_audio_emotion(
                audio_data, sample_rate
            )
            
            print(f"Predicted emotion: {predicted_emotion.value}")
            print(f"Confidence: {confidence:.3f}")
            print(f"Expected categories: {expected_categories}")
            
            # Check if prediction is in expected category
            if predicted_emotion.value in expected_categories:
                correct_classifications += 1
            total_classifications += 1
            
            # Confidence should be reasonable
            assert confidence > 0.3, f"Very low confidence for {pattern_name}: {confidence:.3f}"
        
        # Calculate accuracy
        accuracy = correct_classifications / total_classifications
        print(f"\nAudio emotion pattern accuracy: {accuracy:.3f} ({correct_classifications}/{total_classifications})")
        
        # Should correctly classify at least some patterns
        assert accuracy > 0.3, f"Audio emotion analysis accuracy too low: {accuracy:.3f}"
    
    def _generate_high_energy_audio(self, t, sample_rate):
        """Generate high-energy audio pattern."""
        # High amplitude, high frequency components, fast modulation
        base_freq = 800  # Higher base frequency
        modulation_freq = 10  # Fast modulation
        
        signal = 0.7 * np.sin(2 * np.pi * base_freq * t)
        signal += 0.3 * np.sin(2 * np.pi * (base_freq * 2) * t)  # Harmonic
        signal *= (1 + 0.5 * np.sin(2 * np.pi * modulation_freq * t))  # Amplitude modulation
        
        # Add noise for roughness
        signal += 0.1 * np.random.randn(len(t))
        
        return signal
    
    def _generate_low_energy_audio(self, t, sample_rate):
        """Generate low-energy audio pattern."""
        # Low amplitude, low frequency components, slow changes
        base_freq = 200  # Lower base frequency
        modulation_freq = 0.5  # Slow modulation
        
        signal = 0.3 * np.sin(2 * np.pi * base_freq * t)
        signal *= (1 + 0.2 * np.sin(2 * np.pi * modulation_freq * t))  # Slow amplitude modulation
        
        # Apply low-pass filtering effect
        from scipy import signal as scipy_signal
        b, a = scipy_signal.butter(2, 1000, fs=sample_rate)
        signal = scipy_signal.filtfilt(b, a, signal)
        
        return signal
    
    def _generate_variable_energy_audio(self, t, sample_rate):
        """Generate variable energy audio pattern."""
        # Sudden changes in amplitude and frequency
        signal = np.zeros_like(t)
        
        # Create segments with different characteristics
        segment_size = len(t) // 4
        
        for i in range(4):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, len(t))
            segment_t = t[start_idx:end_idx]
            
            if i % 2 == 0:  # High energy segments
                freq = 600 + i * 200
                amplitude = 0.6 + i * 0.1
            else:  # Low energy segments
                freq = 300 - i * 50
                amplitude = 0.2 + i * 0.05
            
            signal[start_idx:end_idx] = amplitude * np.sin(2 * np.pi * freq * segment_t)
        
        return signal
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_real_video_emotion_accuracy(self):
        """Test emotion analysis accuracy with real video data."""
        print(f"Testing emotion analysis accuracy with: {TEST_VIDEO_PATH}")
        
        video_name = TEST_VIDEO_PATH.name
        expected_data = self.expected_emotions.get(video_name, {})
        
        if not expected_data:
            pytest.skip(f"No expected emotion data for {video_name}")
        
        # Process the video file
        audio_result = await audio_processor.process_file(str(TEST_VIDEO_PATH), "accuracy-test-001")
        audio_path = audio_result["audio_path"]
        
        # Get transcript
        transcript = await transcription_service.transcribe_audio(audio_path, "accuracy-test-001", "ar")
        
        # Analyze emotions
        emotion_analysis = await emotion_analyzer.analyze_emotions(transcript, audio_path, segment_duration=2.0)
        
        print(f"Analysis results:")
        print(f"  Overall emotion: {emotion_analysis.overall_emotion.value}")
        print(f"  Overall confidence: {emotion_analysis.overall_confidence:.3f}")
        print(f"  Number of segments: {len(emotion_analysis.segments)}")
        
        # Validate against expected data
        expected_primary = expected_data["primary_emotions"]
        expected_confidence = expected_data["expected_confidence"]
        expected_dominant = expected_data["dominant_emotion"]
        expected_transitions = expected_data["emotion_transitions"]
        expected_min_segments = expected_data["min_segments"]
        
        # Check overall emotion is in expected primary emotions
        assert emotion_analysis.overall_emotion in expected_primary, \
            f"Unexpected overall emotion: {emotion_analysis.overall_emotion.value} not in {[e.value for e in expected_primary]}"
        
        # Check confidence meets minimum threshold
        assert emotion_analysis.overall_confidence >= expected_confidence, \
            f"Confidence too low: {emotion_analysis.overall_confidence:.3f} < {expected_confidence}"
        
        # Check minimum number of segments
        assert len(emotion_analysis.segments) >= expected_min_segments, \
            f"Too few emotion segments: {len(emotion_analysis.segments)} < {expected_min_segments}"
        
        # Check for emotion transitions if expected
        if expected_transitions:
            unique_emotions = set(segment.combined_emotion for segment in emotion_analysis.segments)
            assert len(unique_emotions) > 1, "No emotion transitions detected"
            print(f"  Detected emotions: {[e.value for e in unique_emotions]}")
        
        # Analyze segment-level accuracy
        segment_emotions = [segment.combined_emotion for segment in emotion_analysis.segments]
        dominant_emotion = max(set(segment_emotions), key=segment_emotions.count)
        
        print(f"  Dominant emotion from segments: {dominant_emotion.value}")
        
        # Dominant emotion should match expected
        if expected_dominant:
            assert dominant_emotion == expected_dominant, \
                f"Wrong dominant emotion: {dominant_emotion.value} != {expected_dominant.value}"
        
        # Calculate segment confidence statistics
        segment_confidences = [segment.combined_confidence for segment in emotion_analysis.segments]
        avg_segment_confidence = np.mean(segment_confidences)
        min_segment_confidence = np.min(segment_confidences)
        
        print(f"  Average segment confidence: {avg_segment_confidence:.3f}")
        print(f"  Minimum segment confidence: {min_segment_confidence:.3f}")
        
        # Segment confidences should be reasonable
        assert avg_segment_confidence > 0.5, f"Low average segment confidence: {avg_segment_confidence:.3f}"
        assert min_segment_confidence > 0.3, f"Very low minimum segment confidence: {min_segment_confidence:.3f}"
        
        # Clean up
        audio_processor.cleanup_temp_files("accuracy-test-001")
    
    @pytest.mark.asyncio
    async def test_emotion_fusion_accuracy(self):
        """Test accuracy of textual and tonal emotion fusion."""
        print("Testing emotion fusion accuracy")
        
        # Test cases with different agreement levels
        fusion_test_cases = [
            {
                "name": "perfect_agreement",
                "text_emotion": EmotionType.JOY,
                "text_confidence": 0.8,
                "audio_emotion": EmotionType.JOY,
                "audio_confidence": 0.7,
                "expected_emotion": EmotionType.JOY,
                "expected_confidence_boost": True
            },
            {
                "name": "text_dominant",
                "text_emotion": EmotionType.ANGER,
                "text_confidence": 0.9,
                "audio_emotion": EmotionType.NEUTRAL,
                "audio_confidence": 0.6,
                "expected_emotion": EmotionType.ANGER,
                "expected_confidence_boost": False
            },
            {
                "name": "audio_dominant",
                "text_emotion": EmotionType.NEUTRAL,
                "text_confidence": 0.5,
                "audio_emotion": EmotionType.SADNESS,
                "audio_confidence": 0.8,
                "expected_emotion": EmotionType.SADNESS,
                "expected_confidence_boost": False
            },
            {
                "name": "disagreement",
                "text_emotion": EmotionType.JOY,
                "text_confidence": 0.6,
                "audio_emotion": EmotionType.SADNESS,
                "audio_confidence": 0.6,
                "expected_emotion": None,  # Either could win
                "expected_confidence_boost": False
            }
        ]
        
        for test_case in fusion_test_cases:
            print(f"\nTesting fusion case: {test_case['name']}")
            
            fused_emotion, fused_confidence = emotion_analyzer._fuse_emotions(
                test_case["text_emotion"], test_case["text_confidence"],
                test_case["audio_emotion"], test_case["audio_confidence"]
            )
            
            print(f"  Text: {test_case['text_emotion'].value} ({test_case['text_confidence']:.2f})")
            print(f"  Audio: {test_case['audio_emotion'].value} ({test_case['audio_confidence']:.2f})")
            print(f"  Fused: {fused_emotion.value} ({fused_confidence:.2f})")
            
            # Check expected emotion (if specified)
            if test_case["expected_emotion"]:
                assert fused_emotion == test_case["expected_emotion"], \
                    f"Wrong fused emotion: {fused_emotion.value} != {test_case['expected_emotion'].value}"
            
            # Check confidence behavior
            max_input_confidence = max(test_case["text_confidence"], test_case["audio_confidence"])
            
            if test_case["expected_confidence_boost"]:
                # Perfect agreement should boost confidence
                assert fused_confidence > max_input_confidence, \
                    f"Expected confidence boost: {fused_confidence:.2f} <= {max_input_confidence:.2f}"
            else:
                # Disagreement should reduce confidence
                if test_case["name"] == "disagreement":
                    assert fused_confidence <= max_input_confidence, \
                        f"Expected confidence reduction: {fused_confidence:.2f} > {max_input_confidence:.2f}"
            
            # Fused confidence should be within valid range
            assert 0.0 <= fused_confidence <= 1.0, f"Invalid confidence: {fused_confidence:.2f}"
    
    @pytest.mark.asyncio
    async def test_emotion_temporal_consistency(self):
        """Test temporal consistency of emotion analysis."""
        print("Testing emotion temporal consistency")
        
        # Create mock transcript with consistent emotional content
        consistent_words = [
            WordSegment(word="أنا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="سعيد", start_time=0.5, end_time=1.0, confidence=0.92),
            WordSegment(word="جداً", start_time=1.0, end_time=1.5, confidence=0.88),
            WordSegment(word="اليوم", start_time=1.5, end_time=2.0, confidence=0.90),
            WordSegment(word="والحمد", start_time=2.0, end_time=2.5, confidence=0.87),
            WordSegment(word="لله", start_time=2.5, end_time=3.0, confidence=0.93)
        ]
        
        consistent_transcript = Transcript(
            audio_file_id="consistency-test-001",
            text="أنا سعيد جداً اليوم والحمد لله",
            words=consistent_words,
            language="ar",
            confidence=0.91
        )
        
        # Generate consistent positive audio
        sample_rate = 16000
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Positive/happy audio characteristics
        happy_audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # Pleasant frequency
        happy_audio += 0.2 * np.sin(2 * np.pi * 880 * t)  # Harmonic
        happy_audio *= (1 + 0.3 * np.sin(2 * np.pi * 2 * t))  # Moderate modulation
        
        # Save temporary audio file
        temp_audio_path = Path(TEST_VIDEO_PATH.parent) / "consistency_test.wav"
        self.temp_files.append(temp_audio_path)
        
        import soundfile as sf
        sf.write(str(temp_audio_path), happy_audio, sample_rate)
        
        # Analyze emotions with small segments for temporal resolution
        emotion_analysis = await emotion_analyzer.analyze_emotions(
            consistent_transcript, str(temp_audio_path), segment_duration=1.0
        )
        
        print(f"Temporal consistency analysis:")
        print(f"  Number of segments: {len(emotion_analysis.segments)}")
        print(f"  Overall emotion: {emotion_analysis.overall_emotion.value}")
        
        # Check segment emotions
        segment_emotions = []
        for i, segment in enumerate(emotion_analysis.segments):
            print(f"  Segment {i}: {segment.combined_emotion.value} ({segment.combined_confidence:.2f})")
            segment_emotions.append(segment.combined_emotion)
        
        # Calculate consistency metrics
        unique_emotions = set(segment_emotions)
        emotion_changes = sum(1 for i in range(1, len(segment_emotions)) 
                            if segment_emotions[i] != segment_emotions[i-1])
        
        consistency_ratio = 1.0 - (emotion_changes / max(len(segment_emotions) - 1, 1))
        
        print(f"  Unique emotions: {len(unique_emotions)}")
        print(f"  Emotion changes: {emotion_changes}")
        print(f"  Consistency ratio: {consistency_ratio:.2f}")
        
        # For consistent positive content, should have reasonable consistency
        # Allow some variation but not excessive changes
        assert consistency_ratio > 0.5, f"Poor temporal consistency: {consistency_ratio:.2f}"
        
        # Should detect positive emotion overall
        assert emotion_analysis.overall_emotion in [EmotionType.JOY, EmotionType.NEUTRAL], \
            f"Failed to detect positive emotion: {emotion_analysis.overall_emotion.value}"
    
    def test_emotion_confidence_calibration(self):
        """Test that emotion confidence scores are well-calibrated."""
        print("Testing emotion confidence calibration")
        
        # Test confidence calculation for different scenarios
        confidence_test_cases = [
            {
                "name": "high_certainty",
                "text_conf": 0.95,
                "audio_conf": 0.90,
                "agreement": True,
                "expected_range": (0.85, 1.0)
            },
            {
                "name": "moderate_certainty", 
                "text_conf": 0.70,
                "audio_conf": 0.65,
                "agreement": True,
                "expected_range": (0.60, 0.85)
            },
            {
                "name": "low_certainty",
                "text_conf": 0.40,
                "audio_conf": 0.35,
                "agreement": True,
                "expected_range": (0.30, 0.60)
            },
            {
                "name": "disagreement",
                "text_conf": 0.80,
                "audio_conf": 0.75,
                "agreement": False,
                "expected_range": (0.50, 0.80)
            }
        ]
        
        for test_case in confidence_test_cases:
            print(f"\nTesting confidence case: {test_case['name']}")
            
            if test_case["agreement"]:
                # Same emotion
                fused_emotion, fused_confidence = emotion_analyzer._fuse_emotions(
                    EmotionType.JOY, test_case["text_conf"],
                    EmotionType.JOY, test_case["audio_conf"]
                )
            else:
                # Different emotions
                fused_emotion, fused_confidence = emotion_analyzer._fuse_emotions(
                    EmotionType.JOY, test_case["text_conf"],
                    EmotionType.SADNESS, test_case["audio_conf"]
                )
            
            expected_min, expected_max = test_case["expected_range"]
            
            print(f"  Fused confidence: {fused_confidence:.3f}")
            print(f"  Expected range: ({expected_min:.2f}, {expected_max:.2f})")
            
            # Check confidence is in expected range
            assert expected_min <= fused_confidence <= expected_max, \
                f"Confidence out of range: {fused_confidence:.3f} not in ({expected_min:.2f}, {expected_max:.2f})"
            
            # Confidence should always be valid
            assert 0.0 <= fused_confidence <= 1.0, f"Invalid confidence: {fused_confidence:.3f}"


class TestEmotionAnalysisRobustness:
    """Test robustness and edge cases of emotion analysis."""
    
    @pytest.mark.asyncio
    async def test_empty_input_handling(self):
        """Test handling of empty or invalid inputs."""
        print("Testing empty input handling")
        
        # Test empty text
        emotion, confidence = await emotion_analyzer._analyze_text_emotion("")
        assert emotion == EmotionType.NEUTRAL
        assert confidence == 0.5
        
        # Test empty audio
        empty_audio = np.array([])
        emotion, confidence = await emotion_analyzer._analyze_audio_emotion(empty_audio, 16000)
        assert emotion == EmotionType.NEUTRAL
        assert confidence == 0.5
        
        print("Empty input handling: PASSED")
    
    @pytest.mark.asyncio
    async def test_noise_robustness(self):
        """Test robustness to noisy audio input."""
        print("Testing noise robustness")
        
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Clean signal
        clean_signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Add varying levels of noise
        noise_levels = [0.1, 0.3, 0.5, 0.8]
        
        for noise_level in noise_levels:
            noisy_signal = clean_signal + noise_level * np.random.randn(len(clean_signal))
            
            # Should still produce valid emotion analysis
            emotion, confidence = await emotion_analyzer._analyze_audio_emotion(noisy_signal, sample_rate)
            
            print(f"  Noise level {noise_level}: {emotion.value} ({confidence:.2f})")
            
            # Should produce valid results even with noise
            assert isinstance(emotion, EmotionType)
            assert 0.0 <= confidence <= 1.0
            
            # Confidence should decrease with more noise
            if noise_level > 0.5:
                assert confidence < 0.8, f"Confidence too high for noisy signal: {confidence:.2f}"
    
    def test_extreme_audio_values(self):
        """Test handling of extreme audio values."""
        print("Testing extreme audio values")
        
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        
        extreme_cases = {
            "all_zeros": np.zeros(samples),
            "all_ones": np.ones(samples),
            "very_large": np.ones(samples) * 100,
            "very_small": np.ones(samples) * 1e-10,
            "alternating": np.array([(-1)**i for i in range(samples)]),
        }
        
        for case_name, audio_data in extreme_cases.items():
            print(f"  Testing {case_name}")
            
            # Should handle gracefully without crashing
            try:
                features = emotion_analyzer._extract_emotion_features(audio_data, sample_rate)
                assert isinstance(features, dict)
                print(f"    {case_name}: OK")
            except Exception as e:
                pytest.fail(f"Failed to handle {case_name}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
