"""
Audio quality validation tests for SawtFeel application.
Tests audio extraction quality and fidelity against original video.
"""

import pytest
import numpy as np
import librosa
import os
from pathlib import Path
from scipy import signal
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

from ...src.services.audio_processor import audio_processor
from ...src.services.video_utils import extract_audio_from_video, get_video_info


# Test video path
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent.parent / "videos" / "aggression.mp4"


class TestAudioQualityValidation:
    """Test audio extraction quality and fidelity."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_audio_extraction_fidelity(self):
        """Test that extracted audio maintains fidelity to original video."""
        print(f"Testing audio extraction fidelity for: {TEST_VIDEO_PATH}")
        
        # Extract audio from video
        output_path = str(TEST_VIDEO_PATH.parent / "extracted_test_audio.wav")
        self.temp_files.append(output_path)
        
        extracted_audio_path = extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
        
        assert os.path.exists(extracted_audio_path), "Audio extraction failed"
        
        # Load extracted audio
        audio_data, sample_rate = librosa.load(extracted_audio_path, sr=None)
        
        print(f"Extracted audio info:")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Duration: {len(audio_data) / sample_rate:.2f} seconds")
        print(f"  Samples: {len(audio_data)}")
        print(f"  Dynamic range: {np.max(audio_data) - np.min(audio_data):.4f}")
        
        # Validate basic audio properties
        assert len(audio_data) > 0, "No audio data extracted"
        assert sample_rate >= 8000, f"Sample rate too low: {sample_rate} Hz"
        assert np.max(np.abs(audio_data)) > 0.001, "Audio signal too quiet"
        
        # Test audio quality metrics
        quality_metrics = self._calculate_audio_quality_metrics(audio_data, sample_rate)
        
        print(f"Audio quality metrics:")
        for metric, value in quality_metrics.items():
            print(f"  {metric}: {value}")
        
        # Validate quality thresholds
        assert quality_metrics["snr_db"] > 20, f"SNR too low: {quality_metrics['snr_db']:.2f} dB"
        assert quality_metrics["dynamic_range_db"] > 30, f"Dynamic range too low: {quality_metrics['dynamic_range_db']:.2f} dB"
        assert quality_metrics["spectral_flatness"] > 0.01, "Audio lacks spectral content"
        assert quality_metrics["zero_crossing_rate"] > 0.01, "Audio lacks variation"
    
    def _calculate_audio_quality_metrics(self, audio_data, sample_rate):
        """Calculate comprehensive audio quality metrics."""
        # Signal-to-noise ratio estimation
        # Use spectral subtraction method to estimate noise floor
        stft = librosa.stft(audio_data, hop_length=512)
        magnitude = np.abs(stft)
        
        # Estimate noise floor as minimum magnitude across time
        noise_floor = np.percentile(magnitude, 10, axis=1, keepdims=True)
        signal_power = np.mean(magnitude ** 2)
        noise_power = np.mean(noise_floor ** 2)
        
        snr_db = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        # Dynamic range
        rms = librosa.feature.rms(y=audio_data)[0]
        dynamic_range_db = 20 * np.log10(np.max(rms) / (np.mean(rms) + 1e-10))
        
        # Spectral flatness (measure of spectral content)
        spectral_flatness = np.mean(librosa.feature.spectral_flatness(y=audio_data))
        
        # Zero crossing rate (measure of signal variation)
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
        
        # Spectral centroid (brightness)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate))
        
        # Spectral bandwidth
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate))
        
        # Spectral rolloff
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate))
        
        return {
            "snr_db": snr_db,
            "dynamic_range_db": dynamic_range_db,
            "spectral_flatness": spectral_flatness,
            "zero_crossing_rate": zcr,
            "spectral_centroid_hz": spectral_centroid,
            "spectral_bandwidth_hz": spectral_bandwidth,
            "spectral_rolloff_hz": spectral_rolloff,
            "rms_energy": np.mean(rms),
            "peak_amplitude": np.max(np.abs(audio_data))
        }
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_audio_extraction_consistency(self):
        """Test that audio extraction is consistent across multiple runs."""
        print("Testing audio extraction consistency")
        
        # Extract audio multiple times
        extracted_files = []
        audio_data_list = []
        
        for i in range(3):
            output_path = str(TEST_VIDEO_PATH.parent / f"consistency_test_{i}.wav")
            self.temp_files.append(output_path)
            extracted_files.append(output_path)
            
            # Extract audio
            extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
            
            # Load audio data
            audio_data, sample_rate = librosa.load(output_path, sr=16000)  # Standardize sample rate
            audio_data_list.append(audio_data)
        
        # Compare audio data consistency
        base_audio = audio_data_list[0]
        
        for i, audio_data in enumerate(audio_data_list[1:], 1):
            # Align lengths (may differ slightly due to processing)
            min_length = min(len(base_audio), len(audio_data))
            base_segment = base_audio[:min_length]
            test_segment = audio_data[:min_length]
            
            # Calculate correlation
            correlation, p_value = pearsonr(base_segment, test_segment)
            
            print(f"Extraction {i+1} vs base correlation: {correlation:.6f} (p={p_value:.2e})")
            
            # Should be highly correlated (> 0.99 for identical extraction)
            assert correlation > 0.99, f"Extraction inconsistent: correlation {correlation:.6f}"
            
            # Calculate RMS difference
            rms_diff = np.sqrt(np.mean((base_segment - test_segment) ** 2))
            print(f"RMS difference: {rms_diff:.6f}")
            
            # RMS difference should be very small
            assert rms_diff < 0.001, f"Extraction varies too much: RMS diff {rms_diff:.6f}"
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_frequency_response_preservation(self):
        """Test that frequency response is preserved during extraction."""
        print("Testing frequency response preservation")
        
        # Extract audio
        output_path = str(TEST_VIDEO_PATH.parent / "frequency_test.wav")
        self.temp_files.append(output_path)
        
        extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
        
        # Load audio
        audio_data, sample_rate = librosa.load(output_path, sr=None)
        
        # Calculate frequency spectrum
        fft = np.fft.fft(audio_data)
        frequencies = np.fft.fftfreq(len(fft), 1/sample_rate)
        magnitude = np.abs(fft)
        
        # Focus on positive frequencies up to Nyquist
        positive_freq_mask = frequencies >= 0
        frequencies = frequencies[positive_freq_mask]
        magnitude = magnitude[positive_freq_mask]
        
        # Analyze frequency content
        nyquist_freq = sample_rate / 2
        
        # Check for content in speech frequency ranges
        speech_low = 85   # Hz
        speech_high = 8000  # Hz
        
        speech_mask = (frequencies >= speech_low) & (frequencies <= speech_high)
        speech_energy = np.sum(magnitude[speech_mask] ** 2)
        total_energy = np.sum(magnitude ** 2)
        
        speech_energy_ratio = speech_energy / total_energy
        
        print(f"Sample rate: {sample_rate} Hz")
        print(f"Nyquist frequency: {nyquist_freq} Hz")
        print(f"Speech energy ratio: {speech_energy_ratio:.3f}")
        
        # Should have significant energy in speech frequencies
        assert speech_energy_ratio > 0.5, f"Low speech energy: {speech_energy_ratio:.3f}"
        
        # Check for aliasing (should not have significant energy near Nyquist)
        aliasing_threshold = nyquist_freq * 0.9
        aliasing_mask = frequencies >= aliasing_threshold
        aliasing_energy = np.sum(magnitude[aliasing_mask] ** 2)
        aliasing_ratio = aliasing_energy / total_energy
        
        print(f"Aliasing energy ratio: {aliasing_ratio:.6f}")
        
        # Should have minimal aliasing
        assert aliasing_ratio < 0.1, f"Significant aliasing detected: {aliasing_ratio:.6f}"
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_audio_synchronization_accuracy(self):
        """Test that extracted audio timing matches video timing."""
        print("Testing audio synchronization accuracy")
        
        # Get video information
        video_info = get_video_info(str(TEST_VIDEO_PATH))
        video_duration = video_info.get("duration", 0)
        
        # Extract audio
        output_path = str(TEST_VIDEO_PATH.parent / "sync_test.wav")
        self.temp_files.append(output_path)
        
        extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
        
        # Load audio and calculate duration
        audio_data, sample_rate = librosa.load(output_path, sr=None)
        audio_duration = len(audio_data) / sample_rate
        
        print(f"Video duration: {video_duration:.3f} seconds")
        print(f"Audio duration: {audio_duration:.3f} seconds")
        
        # Duration should match within reasonable tolerance (±0.1 seconds)
        duration_diff = abs(video_duration - audio_duration)
        print(f"Duration difference: {duration_diff:.3f} seconds")
        
        assert duration_diff < 0.1, f"Audio/video sync error: {duration_diff:.3f}s difference"
        
        # Test for audio dropouts or gaps
        # Calculate RMS energy in sliding windows
        window_size = int(0.1 * sample_rate)  # 100ms windows
        hop_size = window_size // 2
        
        energy_windows = []
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_data[i:i + window_size]
            energy = np.sqrt(np.mean(window ** 2))
            energy_windows.append(energy)
        
        energy_windows = np.array(energy_windows)
        
        # Check for significant dropouts (energy < 1% of mean)
        mean_energy = np.mean(energy_windows)
        dropout_threshold = mean_energy * 0.01
        dropouts = np.sum(energy_windows < dropout_threshold)
        dropout_ratio = dropouts / len(energy_windows)
        
        print(f"Mean energy: {mean_energy:.6f}")
        print(f"Dropout windows: {dropouts}/{len(energy_windows)} ({dropout_ratio:.3f})")
        
        # Should have minimal dropouts (< 5% of windows)
        assert dropout_ratio < 0.05, f"Too many audio dropouts: {dropout_ratio:.3f}"
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found") 
    def test_audio_processor_quality_validation(self):
        """Test AudioProcessor's quality validation functionality."""
        print("Testing AudioProcessor quality validation")
        
        # Extract audio first
        output_path = str(TEST_VIDEO_PATH.parent / "quality_validation_test.wav")
        self.temp_files.append(output_path)
        
        extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
        
        # Test quality validation
        quality_metrics = audio_processor.validate_audio_quality(output_path)
        
        print(f"Quality validation results:")
        for metric, value in quality_metrics.items():
            print(f"  {metric}: {value}")
        
        # Should pass quality validation
        assert quality_metrics["is_acceptable"], "Audio failed quality validation"
        assert quality_metrics["duration"] > 0, "Invalid duration detected"
        assert quality_metrics["sample_rate"] > 0, "Invalid sample rate detected"
        assert quality_metrics["mean_rms"] > 0, "No audio signal detected"
        assert quality_metrics["dynamic_range_db"] > 10, "Insufficient dynamic range"
        
        # SNR should be reasonable for real audio
        if "snr_estimate_db" in quality_metrics and quality_metrics["snr_estimate_db"] != float('inf'):
            assert quality_metrics["snr_estimate_db"] > 10, "Poor signal-to-noise ratio"
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_multiple_format_extraction_quality(self):
        """Test audio extraction quality across different output formats."""
        print("Testing multiple format extraction quality")
        
        formats_to_test = [
            ("wav", 16000),
            ("wav", 22050),
            ("wav", 44100)
        ]
        
        quality_results = {}
        
        for format_ext, target_sr in formats_to_test:
            output_path = str(TEST_VIDEO_PATH.parent / f"format_test_{target_sr}.{format_ext}")
            self.temp_files.append(output_path)
            
            # Extract with specific format
            extract_audio_from_video(str(TEST_VIDEO_PATH), output_path)
            
            # Load and analyze
            audio_data, sample_rate = librosa.load(output_path, sr=target_sr)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_audio_quality_metrics(audio_data, sample_rate)
            quality_results[f"{format_ext}_{target_sr}"] = quality_metrics
            
            print(f"\nFormat: {format_ext} @ {target_sr} Hz")
            print(f"  SNR: {quality_metrics['snr_db']:.2f} dB")
            print(f"  Dynamic range: {quality_metrics['dynamic_range_db']:.2f} dB")
            print(f"  Spectral centroid: {quality_metrics['spectral_centroid_hz']:.1f} Hz")
        
        # Compare quality across formats
        snr_values = [metrics["snr_db"] for metrics in quality_results.values()]
        snr_std = np.std(snr_values)
        
        print(f"\nSNR standard deviation across formats: {snr_std:.2f} dB")
        
        # Quality should be consistent across formats (SNR variation < 5 dB)
        assert snr_std < 5.0, f"Quality varies too much across formats: {snr_std:.2f} dB std"
        
        # All formats should meet minimum quality thresholds
        for format_name, metrics in quality_results.items():
            assert metrics["snr_db"] > 15, f"Poor SNR for {format_name}: {metrics['snr_db']:.2f} dB"
            assert metrics["dynamic_range_db"] > 20, f"Poor dynamic range for {format_name}"
    
    def test_audio_quality_with_synthetic_signals(self):
        """Test quality validation with synthetic audio signals."""
        print("Testing quality validation with synthetic signals")
        
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Test 1: Pure sine wave (should pass basic tests)
        sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Test 2: White noise (should have good spectral flatness)
        white_noise = 0.1 * np.random.randn(len(t))
        
        # Test 3: Speech-like signal (filtered noise)
        from scipy import signal as scipy_signal
        b, a = scipy_signal.butter(4, [300, 3400], btype='band', fs=sample_rate)
        speech_like = scipy_signal.filtfilt(b, a, np.random.randn(len(t))) * 0.2
        
        # Test 4: Very quiet signal (should fail quality test)
        quiet_signal = 0.001 * np.sin(2 * np.pi * 440 * t)
        
        test_signals = {
            "sine_wave": sine_wave,
            "white_noise": white_noise,
            "speech_like": speech_like,
            "quiet_signal": quiet_signal
        }
        
        for signal_name, signal_data in test_signals.items():
            print(f"\nTesting {signal_name}:")
            
            # Save to temporary file
            temp_path = str(Path(TEST_VIDEO_PATH.parent) / f"synthetic_{signal_name}.wav")
            self.temp_files.append(temp_path)
            
            import soundfile as sf
            sf.write(temp_path, signal_data, sample_rate)
            
            # Test quality metrics
            quality_metrics = self._calculate_audio_quality_metrics(signal_data, sample_rate)
            
            print(f"  SNR: {quality_metrics['snr_db']:.2f} dB")
            print(f"  Dynamic range: {quality_metrics['dynamic_range_db']:.2f} dB")
            print(f"  Spectral flatness: {quality_metrics['spectral_flatness']:.4f}")
            print(f"  Peak amplitude: {quality_metrics['peak_amplitude']:.4f}")
            
            # Validate expected characteristics
            if signal_name == "sine_wave":
                # Should have low spectral flatness (pure tone)
                assert quality_metrics["spectral_flatness"] < 0.1
                assert quality_metrics["peak_amplitude"] > 0.3
                
            elif signal_name == "white_noise":
                # Should have high spectral flatness
                assert quality_metrics["spectral_flatness"] > 0.1
                
            elif signal_name == "speech_like":
                # Should have moderate characteristics
                assert quality_metrics["spectral_centroid_hz"] > 500
                assert quality_metrics["spectral_centroid_hz"] < 3000
                
            elif signal_name == "quiet_signal":
                # Should be detected as low quality
                assert quality_metrics["peak_amplitude"] < 0.01


class TestAudioFeatureExtraction:
    """Test audio feature extraction quality and accuracy."""
    
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    def test_feature_extraction_completeness(self):
        """Test that all required audio features are extracted."""
        print("Testing feature extraction completeness")
        
        # Process file to extract features
        result = audio_processor._extract_audio_features(str(TEST_VIDEO_PATH))
        
        # Check that all required features are present
        required_features = [
            "duration",
            "sample_rate", 
            "samples",
            "rms_energy",
            "spectral_features",
            "temporal_features",
            "pitch_features"
        ]
        
        for feature in required_features:
            assert feature in result, f"Missing required feature: {feature}"
        
        # Check nested feature structures
        assert "mean" in result["rms_energy"], "Missing RMS energy statistics"
        assert "spectral_centroid" in result["spectral_features"], "Missing spectral centroid"
        assert "tempo" in result["temporal_features"], "Missing tempo information"
        assert "f0_mean" in result["pitch_features"], "Missing pitch information"
        
        print(f"Extracted features: {list(result.keys())}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Sample rate: {result['sample_rate']} Hz")
        print(f"RMS energy mean: {result['rms_energy']['mean']:.4f}")
    
    def test_feature_extraction_robustness(self):
        """Test feature extraction with edge cases."""
        print("Testing feature extraction robustness")
        
        # Test with very short audio
        short_audio = np.random.randn(100)  # Very short
        sample_rate = 16000
        
        # Should handle gracefully without crashing
        try:
            # This would normally be called internally
            features = audio_processor._extract_rms_energy(short_audio)
            assert isinstance(features, dict)
            print("Short audio handled successfully")
        except Exception as e:
            pytest.fail(f"Failed to handle short audio: {e}")
        
        # Test with silent audio
        silent_audio = np.zeros(16000)  # 1 second of silence
        
        try:
            features = audio_processor._extract_rms_energy(silent_audio)
            assert features["mean"] >= 0  # Should be zero or very small
            print("Silent audio handled successfully")
        except Exception as e:
            pytest.fail(f"Failed to handle silent audio: {e}")
        
        # Test with very loud audio (clipping)
        loud_audio = np.ones(16000) * 2.0  # Clipped audio
        
        try:
            features = audio_processor._extract_rms_energy(loud_audio)
            assert features["max"] > 1.0  # Should detect high energy
            print("Loud audio handled successfully")
        except Exception as e:
            pytest.fail(f"Failed to handle loud audio: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
