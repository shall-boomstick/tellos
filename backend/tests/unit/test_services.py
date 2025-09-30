"""
Unit tests for all backend services in SawtFeel application.
Tests service logic, error handling, and integration points.
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.services.audio_processor import AudioProcessor
from src.services.transcription_service import TranscriptionService
from src.services.emotion_analyzer import EmotionAnalyzer
from src.services.file_manager import FileManager
from src.services.processing_pipeline import ProcessingPipeline
from src.models.audio_file import AudioFile, ProcessingStatus, FileType
from src.models.transcript import Transcript, WordSegment
from src.models.emotion_analysis import EmotionAnalysis, EmotionSegment, EmotionType


class TestAudioProcessor:
    """Test cases for AudioProcessor service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = AudioProcessor(temp_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_process_file_audio_valid(self):
        """Test processing a valid audio file."""
        # Create mock audio file
        test_file = os.path.join(self.temp_dir, "test.wav")
        with open(test_file, "wb") as f:
            f.write(b"fake audio data")
        
        with patch('...src.services.video_utils.detect_file_format') as mock_detect:
            mock_detect.return_value = ("audio", "wav")
            
            with patch.object(self.processor, '_extract_audio_features') as mock_features:
                mock_features.return_value = {
                    "duration": 10.0,
                    "sample_rate": 16000,
                    "rms_energy": {"mean": 0.1, "std": 0.05}
                }
                
                result = await self.processor.process_file(test_file, "test-123")
                
                assert result["file_id"] == "test-123"
                assert result["file_type"] == "audio"
                assert result["status"] == "completed"
                assert "processing_time" in result
                assert "audio_features" in result
    
    @pytest.mark.asyncio
    async def test_process_file_video_valid(self):
        """Test processing a valid video file."""
        # Create mock video file
        test_file = os.path.join(self.temp_dir, "test.mp4")
        with open(test_file, "wb") as f:
            f.write(b"fake video data")
        
        with patch('...src.services.video_utils.detect_file_format') as mock_detect:
            mock_detect.return_value = ("video", "mp4")
            
            with patch('...src.services.video_utils.get_video_info') as mock_info:
                mock_info.return_value = {"duration": 30.0, "fps": 25}
                
                with patch('...src.services.video_utils.extract_audio_from_video') as mock_extract:
                    extracted_path = os.path.join(self.temp_dir, "extracted.wav")
                    with open(extracted_path, "wb") as f:
                        f.write(b"extracted audio")
                    mock_extract.return_value = extracted_path
                    
                    with patch.object(self.processor, '_extract_audio_features') as mock_features:
                        mock_features.return_value = {
                            "duration": 30.0,
                            "sample_rate": 16000,
                            "rms_energy": {"mean": 0.15, "std": 0.08}
                        }
                        
                        result = await self.processor.process_file(test_file, "test-123")
                        
                        assert result["file_id"] == "test-123"
                        assert result["file_type"] == "video"
                        assert result["status"] == "completed"
                        assert result["audio_path"] == extracted_path
                        assert "video_info" in result
    
    @pytest.mark.asyncio
    async def test_process_file_invalid_type(self):
        """Test processing file with invalid type."""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("not a media file")
        
        with patch('...src.services.video_utils.detect_file_format') as mock_detect:
            mock_detect.return_value = ("text", "txt")
            
            with pytest.raises(ValueError, match="Unsupported file type"):
                await self.processor.process_file(test_file, "test-123")
    
    def test_extract_audio_features_valid(self):
        """Test extracting audio features from valid audio data."""
        # Mock librosa functions
        with patch('librosa.load') as mock_load:
            mock_load.return_value = ([0.1, 0.2, -0.1, 0.3] * 1000, 16000)
            
            with patch('librosa.feature.rms') as mock_rms:
                mock_rms.return_value = [[0.1, 0.15, 0.12, 0.18]]
                
                with patch('librosa.feature.spectral_centroid') as mock_centroid:
                    mock_centroid.return_value = [[1000, 1200, 800, 1500]]
                    
                    with patch('librosa.beat.beat_track') as mock_beat:
                        mock_beat.return_value = (120, [0, 1, 2, 3])
                        
                        with patch('librosa.pyin') as mock_pyin:
                            mock_pyin.return_value = ([200, 220, 180, 240], [True, True, True, True], [0.9, 0.8, 0.85, 0.95])
                            
                            features = self.processor._extract_audio_features("fake_path")
                            
                            assert "duration" in features
                            assert "sample_rate" in features
                            assert "rms_energy" in features
                            assert "spectral_features" in features
                            assert "temporal_features" in features
                            assert "pitch_features" in features
    
    def test_validate_audio_quality_good(self):
        """Test audio quality validation for good quality audio."""
        with patch('librosa.load') as mock_load:
            mock_load.return_value = ([0.1, 0.2, -0.1, 0.3] * 8000, 16000)  # 2 seconds
            
            with patch('librosa.feature.rms') as mock_rms:
                mock_rms.return_value = [[0.1, 0.15, 0.12, 0.18]]
                
                quality = self.processor.validate_audio_quality("fake_path")
                
                assert quality["is_acceptable"] is True
                assert quality["duration"] > 0.5
                assert quality["mean_rms"] > 0.001
                assert quality["dynamic_range_db"] > 10
    
    def test_validate_audio_quality_poor(self):
        """Test audio quality validation for poor quality audio."""
        with patch('librosa.load') as mock_load:
            mock_load.return_value = ([0.001] * 1000, 16000)  # Very quiet, short
            
            with patch('librosa.feature.rms') as mock_rms:
                mock_rms.return_value = [[0.0001, 0.0001, 0.0001, 0.0001]]
                
                quality = self.processor.validate_audio_quality("fake_path")
                
                assert quality["is_acceptable"] is False
                assert quality["duration"] < 0.5 or quality["mean_rms"] < 0.001


class TestTranscriptionService:
    """Test cases for TranscriptionService service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TranscriptionService(model_size="base")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_valid(self):
        """Test transcribing valid Arabic audio."""
        test_audio_path = "fake_audio.wav"
        
        # Mock Whisper model and result
        mock_model = Mock()
        mock_result = {
            "text": "مرحبا بك في تطبيق تحليل المشاعر",
            "segments": [
                {
                    "words": [
                        {"word": "مرحبا", "start": 0.0, "end": 0.5, "probability": 0.95},
                        {"word": "بك", "start": 0.5, "end": 1.0, "probability": 0.92},
                        {"word": "في", "start": 1.0, "end": 1.3, "probability": 0.88},
                        {"word": "تطبيق", "start": 1.3, "end": 2.0, "probability": 0.90},
                        {"word": "تحليل", "start": 2.0, "end": 2.8, "probability": 0.87},
                        {"word": "المشاعر", "start": 2.8, "end": 3.5, "probability": 0.93}
                    ],
                    "avg_logprob": -0.2
                }
            ]
        }
        
        mock_model.transcribe.return_value = mock_result
        self.service.model = mock_model
        
        transcript = await self.service.transcribe_audio(test_audio_path, "test-123", "ar")
        
        assert transcript.audio_file_id == "test-123"
        assert transcript.text == "مرحبا بك في تطبيق تحليل المشاعر"
        assert transcript.language == "ar"
        assert len(transcript.words) == 6
        assert transcript.words[0].word == "مرحبا"
        assert transcript.words[0].start_time == 0.0
        assert transcript.words[0].end_time == 0.5
        assert transcript.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_result(self):
        """Test transcribing audio with empty result."""
        test_audio_path = "fake_audio.wav"
        
        mock_model = Mock()
        mock_result = {
            "text": "",
            "segments": []
        }
        
        mock_model.transcribe.return_value = mock_result
        self.service.model = mock_model
        
        transcript = await self.service.transcribe_audio(test_audio_path, "test-123", "ar")
        
        assert transcript.text == ""
        assert len(transcript.words) == 0
        assert transcript.confidence == 0.0
    
    def test_detect_language_arabic(self):
        """Test language detection for Arabic audio."""
        with patch('whisper.load_audio') as mock_load_audio:
            mock_load_audio.return_value = [0.1, 0.2, -0.1] * 1000
            
            with patch('whisper.pad_or_trim') as mock_pad:
                mock_pad.return_value = [0.1, 0.2, -0.1] * 1000
                
                with patch('whisper.log_mel_spectrogram') as mock_mel:
                    mock_mel.return_value = Mock()
                    mock_mel.return_value.to.return_value = Mock()
                    
                    mock_model = Mock()
                    mock_model.detect_language.return_value = (None, {"ar": 0.95, "en": 0.03, "fr": 0.02})
                    mock_model.device = "cpu"
                    self.service.model = mock_model
                    
                    language, confidence = self.service.detect_language("fake_audio.wav")
                    
                    assert language == "ar"
                    assert confidence == 0.95
    
    def test_validate_transcription_quality_good(self):
        """Test transcription quality validation for good transcript."""
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
            WordSegment(word="بك", start_time=0.5, end_time=1.0, confidence=0.92),
            WordSegment(word="في", start_time=1.0, end_time=1.3, confidence=0.88),
            WordSegment(word="تطبيق", start_time=1.3, end_time=2.0, confidence=0.90)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك في تطبيق",
            words=words,
            language="ar",
            confidence=0.91
        )
        
        quality = self.service.validate_transcription_quality(transcript)
        
        assert quality["is_acceptable"] is True
        assert quality["word_count"] == 4
        assert quality["avg_confidence"] > 0.8
        assert quality["low_confidence_ratio"] < 0.5
        assert quality["timing_consistency"] > 0.8
    
    def test_validate_transcription_quality_poor(self):
        """Test transcription quality validation for poor transcript."""
        words = [
            WordSegment(word="...", start_time=0.0, end_time=0.5, confidence=0.3),
            WordSegment(word="um", start_time=0.5, end_time=1.0, confidence=0.2)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="... um",
            words=words,
            language="ar",
            confidence=0.25
        )
        
        quality = self.service.validate_transcription_quality(transcript)
        
        assert quality["is_acceptable"] is False
        assert quality["avg_confidence"] < 0.6
        assert quality["low_confidence_ratio"] > 0.5


class TestEmotionAnalyzer:
    """Test cases for EmotionAnalyzer service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = EmotionAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_emotions_valid(self):
        """Test emotion analysis with valid transcript and audio."""
        # Create test transcript
        words = [
            WordSegment(word="مرحبا", start_time=0.0, end_time=1.0, confidence=0.95),
            WordSegment(word="بك", start_time=1.0, end_time=2.0, confidence=0.92),
            WordSegment(word="يا", start_time=2.0, end_time=3.0, confidence=0.88),
            WordSegment(word="صديقي", start_time=3.0, end_time=4.0, confidence=0.90)
        ]
        
        transcript = Transcript(
            audio_file_id="test-123",
            text="مرحبا بك يا صديقي",
            words=words,
            language="ar",
            confidence=0.91
        )
        
        # Mock audio loading
        with patch('librosa.load') as mock_load:
            mock_load.return_value = ([0.1, 0.2, -0.1, 0.3] * 2000, 16000)  # 4 seconds
            
            # Mock text emotion analysis
            with patch.object(self.analyzer, '_analyze_text_emotion') as mock_text:
                mock_text.return_value = (EmotionType.JOY, 0.85)
                
                # Mock audio emotion analysis
                with patch.object(self.analyzer, '_analyze_audio_emotion') as mock_audio:
                    mock_audio.return_value = (EmotionType.NEUTRAL, 0.75)
                    
                    analysis = await self.analyzer.analyze_emotions(transcript, "fake_audio.wav", 2.0)
                    
                    assert analysis.audio_file_id == "test-123"
                    assert len(analysis.segments) == 2  # 4 seconds / 2 second segments
                    assert analysis.overall_emotion in [EmotionType.JOY, EmotionType.NEUTRAL]
                    assert analysis.overall_confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_text_emotion_positive(self):
        """Test text emotion analysis for positive Arabic text."""
        # Mock text pipeline
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.85}]
        self.analyzer.text_pipeline = mock_pipeline
        
        emotion, confidence = await self.analyzer._analyze_text_emotion("مرحبا بك يا صديقي")
        
        assert emotion == EmotionType.JOY
        assert confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_analyze_text_emotion_negative(self):
        """Test text emotion analysis for negative Arabic text."""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.78}]
        self.analyzer.text_pipeline = mock_pipeline
        
        emotion, confidence = await self.analyzer._analyze_text_emotion("أنا حزين جداً")
        
        assert emotion == EmotionType.SADNESS
        assert confidence == 0.78
    
    @pytest.mark.asyncio
    async def test_analyze_text_emotion_empty(self):
        """Test text emotion analysis for empty text."""
        emotion, confidence = await self.analyzer._analyze_text_emotion("")
        
        assert emotion == EmotionType.NEUTRAL
        assert confidence == 0.5
    
    @pytest.mark.asyncio
    async def test_analyze_audio_emotion_valid(self):
        """Test audio emotion analysis with valid features."""
        audio_data = [0.1, 0.2, -0.1, 0.3] * 1000
        sample_rate = 16000
        
        with patch.object(self.analyzer, '_extract_emotion_features') as mock_features:
            mock_features.return_value = {
                "energy_mean": 0.8,  # High energy
                "pitch_mean": 300,   # High pitch
                "tempo": 150,        # Fast tempo
                "spectral_centroid_mean": 2500
            }
            
            emotion, confidence = await self.analyzer._analyze_audio_emotion(audio_data, sample_rate)
            
            assert emotion == EmotionType.ANGER  # High energy + high pitch
            assert confidence == 0.7
    
    def test_fuse_emotions_agreement(self):
        """Test emotion fusion when text and audio agree."""
        emotion, confidence = self.analyzer._fuse_emotions(
            EmotionType.JOY, 0.8,
            EmotionType.JOY, 0.7
        )
        
        assert emotion == EmotionType.JOY
        assert confidence > 0.8  # Boosted due to agreement
    
    def test_fuse_emotions_disagreement(self):
        """Test emotion fusion when text and audio disagree."""
        emotion, confidence = self.analyzer._fuse_emotions(
            EmotionType.JOY, 0.9,
            EmotionType.SADNESS, 0.6
        )
        
        assert emotion == EmotionType.JOY  # Higher confidence wins
        assert confidence < 0.9  # Reduced due to disagreement
    
    def test_get_emotion_timeline_valid(self):
        """Test generating emotion timeline."""
        segments = [
            EmotionSegment(
                start_time=0.0, end_time=2.0,
                textual_emotion=EmotionType.JOY, textual_confidence=0.8,
                tonal_emotion=EmotionType.JOY, tonal_confidence=0.7,
                combined_emotion=EmotionType.JOY, combined_confidence=0.75
            ),
            EmotionSegment(
                start_time=2.0, end_time=4.0,
                textual_emotion=EmotionType.SADNESS, textual_confidence=0.6,
                tonal_emotion=EmotionType.SADNESS, tonal_confidence=0.8,
                combined_emotion=EmotionType.SADNESS, combined_confidence=0.7
            )
        ]
        
        analysis = EmotionAnalysis(
            audio_file_id="test-123",
            segments=segments,
            overall_emotion=EmotionType.NEUTRAL,
            overall_confidence=0.72
        )
        
        timeline = self.analyzer.get_emotion_timeline(analysis, time_resolution=1.0)
        
        assert len(timeline) == 4  # 4 seconds / 1 second resolution
        assert timeline[0]["emotion"] == "joy"
        assert timeline[2]["emotion"] == "sadness"
        assert all("confidence" in point for point in timeline)


class TestFileManager:
    """Test cases for FileManager service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = tempfile.mkdtemp()
        self.manager = FileManager(
            upload_dir=self.temp_dir,
            cache_dir=self.cache_dir,
            max_file_age_hours=1,
            max_cache_size_mb=10
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
    
    @pytest.mark.asyncio
    async def test_store_uploaded_file_valid(self):
        """Test storing a valid uploaded file."""
        file_content = b"test file content"
        filename = "test.mp4"
        file_id = "test-123"
        
        file_path = await self.manager.store_uploaded_file(file_content, filename, file_id)
        
        assert os.path.exists(file_path)
        assert file_id in self.manager.file_metadata
        
        metadata = self.manager.file_metadata[file_id]
        assert metadata["original_filename"] == filename
        assert metadata["file_size"] == len(file_content)
        assert "file_hash" in metadata
        assert "upload_time" in metadata
    
    def test_get_file_path_valid(self):
        """Test getting file path for existing file."""
        # Create test file and metadata
        test_file = os.path.join(self.temp_dir, "test_file.mp4")
        with open(test_file, "w") as f:
            f.write("test content")
        
        file_id = "test-123"
        self.manager.file_metadata[file_id] = {
            "stored_path": test_file,
            "original_filename": "test.mp4"
        }
        
        path = self.manager.get_file_path(file_id)
        assert path == test_file
    
    def test_get_file_path_missing(self):
        """Test getting file path for non-existent file."""
        path = self.manager.get_file_path("nonexistent")
        assert path is None
    
    @pytest.mark.asyncio
    async def test_cache_processed_data_valid(self):
        """Test caching processed data."""
        file_id = "test-123"
        data_type = "transcript"
        data = {"text": "مرحبا", "confidence": 0.9}
        
        cache_path = await self.manager.cache_processed_data(file_id, data_type, data)
        
        assert os.path.exists(cache_path)
        
        # Verify cached content
        with open(cache_path, 'r') as f:
            cached_content = json.load(f)
        
        assert cached_content["file_id"] == file_id
        assert cached_content["data_type"] == data_type
        assert cached_content["data"] == data
        assert "cached_at" in cached_content
    
    @pytest.mark.asyncio
    async def test_get_cached_data_valid(self):
        """Test retrieving valid cached data."""
        file_id = "test-123"
        data_type = "emotions"
        data = {"overall_emotion": "joy", "confidence": 0.85}
        
        # Cache the data first
        await self.manager.cache_processed_data(file_id, data_type, data)
        
        # Retrieve it
        retrieved_data = await self.manager.get_cached_data(file_id, data_type)
        
        assert retrieved_data == data
    
    @pytest.mark.asyncio
    async def test_get_cached_data_expired(self):
        """Test retrieving expired cached data."""
        file_id = "test-123"
        data_type = "transcript"
        
        # Create expired cache file
        cache_filename = f"{file_id}_{data_type}.json"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        expired_data = {
            "cached_at": (datetime.now() - timedelta(hours=25)).isoformat(),
            "file_id": file_id,
            "data_type": data_type,
            "data": {"text": "expired"}
        }
        
        with open(cache_path, 'w') as f:
            json.dump(expired_data, f)
        
        # Try to retrieve expired data
        retrieved_data = await self.manager.get_cached_data(file_id, data_type)
        
        assert retrieved_data is None
        assert not os.path.exists(cache_path)  # Should be cleaned up
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_files(self):
        """Test cleaning up expired files."""
        # Create expired file metadata
        expired_file_id = "expired-123"
        expired_file_path = os.path.join(self.temp_dir, "expired.mp4")
        
        with open(expired_file_path, "w") as f:
            f.write("expired content")
        
        self.manager.file_metadata[expired_file_id] = {
            "stored_path": expired_file_path,
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "file_size": 100
        }
        
        # Run cleanup
        stats = await self.manager.cleanup_expired_files()
        
        assert stats["files_removed"] == 1
        assert stats["bytes_freed"] >= 100
        assert not os.path.exists(expired_file_path)
        assert expired_file_id not in self.manager.file_metadata
    
    def test_get_storage_stats(self):
        """Test getting storage statistics."""
        # Create test files
        test_file1 = os.path.join(self.temp_dir, "test1.mp4")
        test_file2 = os.path.join(self.cache_dir, "cache1.json")
        
        with open(test_file1, "w") as f:
            f.write("test content 1")
        with open(test_file2, "w") as f:
            f.write("cached content")
        
        stats = self.manager.get_storage_stats()
        
        assert "upload_directory_size_mb" in stats
        assert "cache_directory_size_mb" in stats
        assert "total_size_mb" in stats
        assert "upload_file_count" in stats
        assert "cache_file_count" in stats
        assert stats["upload_file_count"] >= 1
        assert stats["cache_file_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_valid(self):
        """Test file integrity verification for valid file."""
        file_content = b"test file content"
        file_id = "test-123"
        
        # Store file
        await self.manager.store_uploaded_file(file_content, "test.mp4", file_id)
        
        # Verify integrity
        is_valid = await self.manager.verify_file_integrity(file_id)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_corrupted(self):
        """Test file integrity verification for corrupted file."""
        file_content = b"test file content"
        file_id = "test-123"
        
        # Store file
        file_path = await self.manager.store_uploaded_file(file_content, "test.mp4", file_id)
        
        # Corrupt the file
        with open(file_path, "w") as f:
            f.write("corrupted content")
        
        # Verify integrity
        is_valid = await self.manager.verify_file_integrity(file_id)
        
        assert is_valid is False


class TestProcessingPipeline:
    """Test cases for ProcessingPipeline service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = ProcessingPipeline()
    
    @pytest.mark.asyncio
    async def test_process_file_complete_workflow(self):
        """Test complete file processing workflow."""
        # Create test audio file
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        # Mock all services
        with patch('...src.services.audio_processor.audio_processor') as mock_audio:
            mock_audio.process_file = AsyncMock(return_value={
                "file_id": "test-123",
                "file_type": "video",
                "audio_path": "/tmp/extracted.wav",
                "processing_time": 2.5,
                "status": "completed"
            })
            
            with patch('...src.services.transcription_service.transcription_service') as mock_transcript:
                mock_transcript.transcribe_audio = AsyncMock(return_value=Transcript(
                    audio_file_id="test-123",
                    text="مرحبا بك",
                    words=[
                        WordSegment(word="مرحبا", start_time=0.0, end_time=0.5, confidence=0.95),
                        WordSegment(word="بك", start_time=0.5, end_time=1.0, confidence=0.92)
                    ],
                    language="ar",
                    confidence=0.93
                ))
                
                with patch('...src.services.emotion_analyzer.emotion_analyzer') as mock_emotion:
                    mock_emotion.analyze_emotions = AsyncMock(return_value=EmotionAnalysis(
                        audio_file_id="test-123",
                        segments=[
                            EmotionSegment(
                                start_time=0.0, end_time=2.0,
                                textual_emotion=EmotionType.JOY, textual_confidence=0.8,
                                tonal_emotion=EmotionType.NEUTRAL, tonal_confidence=0.7,
                                combined_emotion=EmotionType.JOY, combined_confidence=0.75
                            )
                        ],
                        overall_emotion=EmotionType.JOY,
                        overall_confidence=0.75
                    ))
                    
                    with patch.object(self.pipeline, '_cache_results') as mock_cache:
                        mock_cache.return_value = None
                        
                        with patch.object(self.pipeline, '_update_processing_status') as mock_update:
                            mock_update.return_value = None
                            
                            with patch.object(self.pipeline, '_cleanup_processing_files') as mock_cleanup:
                                mock_cleanup.return_value = None
                                
                                result = await self.pipeline.process_file(audio_file)
                                
                                assert result["file_id"] == "test-123"
                                assert result["status"] == "completed"
                                assert result["transcript_word_count"] == 2
                                assert result["emotion_segments_count"] == 1
                                assert result["overall_emotion"] == "joy"
    
    @pytest.mark.asyncio
    async def test_process_file_error_handling(self):
        """Test error handling in processing pipeline."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        # Mock audio processor to raise exception
        with patch('...src.services.audio_processor.audio_processor') as mock_audio:
            mock_audio.process_file = AsyncMock(side_effect=Exception("Audio processing failed"))
            
            with patch.object(self.pipeline, '_update_processing_status') as mock_update:
                mock_update.return_value = None
                
                with patch.object(self.pipeline, '_cache_error') as mock_cache_error:
                    mock_cache_error.return_value = None
                    
                    with pytest.raises(Exception, match="Audio processing failed"):
                        await self.pipeline.process_file(audio_file)
    
    @pytest.mark.asyncio
    async def test_start_processing_task(self):
        """Test starting background processing task."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        with patch.object(self.pipeline, 'process_file') as mock_process:
            mock_process.return_value = {"status": "completed"}
            
            task = await self.pipeline.start_processing_task(audio_file)
            
            assert audio_file.id in self.pipeline.active_processes
            assert self.pipeline.is_processing(audio_file.id)
    
    @pytest.mark.asyncio
    async def test_cancel_processing(self):
        """Test cancelling processing task."""
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        # Start processing
        with patch.object(self.pipeline, 'process_file') as mock_process:
            # Create a task that will run indefinitely
            mock_process.side_effect = lambda x: asyncio.sleep(10)
            
            await self.pipeline.start_processing_task(audio_file)
            
            # Cancel processing
            with patch.object(self.pipeline, '_update_processing_status') as mock_update:
                mock_update.return_value = None
                
                success = await self.pipeline.cancel_processing(audio_file.id)
                
                assert success is True
                assert not self.pipeline.is_processing(audio_file.id)
    
    def test_get_active_processes_info(self):
        """Test getting active processes information."""
        # Simulate active process
        audio_file = AudioFile(
            id="test-123",
            filename="test.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=1024000,
            file_path="/tmp/test.mp4"
        )
        
        self.pipeline.active_processes["test-123"] = {
            "task": Mock(),
            "started_at": datetime.now() - timedelta(seconds=30),
            "audio_file": audio_file
        }
        
        info = self.pipeline.get_active_processes_info()
        
        assert "test-123" in info
        assert info["test-123"]["filename"] == "test.mp4"
        assert info["test-123"]["duration_seconds"] >= 30
        assert "started_at" in info["test-123"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
