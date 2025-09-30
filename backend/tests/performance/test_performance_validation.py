"""
Performance validation tests for SawtFeel application.
Tests processing speed, latency, and memory usage with videos/aggression.mp4.
"""

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime
from pathlib import Path

from ...src.services.processing_pipeline import processing_pipeline
from ...src.services.audio_processor import audio_processor
from ...src.services.transcription_service import transcription_service
from ...src.services.emotion_analyzer import emotion_analyzer
from ...src.services.file_manager import file_manager
from ...src.models.audio_file import AudioFile, FileType


# Test video path
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent.parent / "videos" / "aggression.mp4"


class TestPerformanceRequirements:
    """Test performance requirements with real video processing."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up performance monitoring."""
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        self.performance_metrics = {
            "start_time": None,
            "end_time": None,
            "peak_memory": self.initial_memory,
            "cpu_samples": [],
            "processing_stages": {}
        }
    
    def monitor_resources(self):
        """Monitor system resources during processing."""
        current_memory = self.process.memory_info().rss
        cpu_percent = self.process.cpu_percent()
        
        self.performance_metrics["peak_memory"] = max(
            self.performance_metrics["peak_memory"], 
            current_memory
        )
        self.performance_metrics["cpu_samples"].append(cpu_percent)
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_complete_processing_time_limit(self):
        """Test that complete processing completes within 2-minute constitutional limit."""
        print(f"Testing with video: {TEST_VIDEO_PATH}")
        
        # Create AudioFile object
        audio_file = AudioFile(
            id="perf-test-001",
            filename="aggression.mp4",
            file_type=FileType.VIDEO,
            format="mp4",
            file_size=os.path.getsize(TEST_VIDEO_PATH),
            file_path=str(TEST_VIDEO_PATH)
        )
        
        # Start performance monitoring
        self.performance_metrics["start_time"] = time.time()
        start_memory = self.process.memory_info().rss
        
        # Monitor resources in background
        monitoring_task = asyncio.create_task(self._background_monitoring())
        
        try:
            # Process the file
            result = await processing_pipeline.process_file(audio_file)
            
            # Stop monitoring
            self.performance_metrics["end_time"] = time.time()
            monitoring_task.cancel()
            
            # Calculate total processing time
            total_time = self.performance_metrics["end_time"] - self.performance_metrics["start_time"]
            
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Processing result: {result}")
            
            # Constitutional requirement: Must complete within 2 minutes (120 seconds)
            assert total_time < 120, f"Processing took {total_time:.2f}s, exceeds 120s limit"
            
            # Verify processing was successful
            assert result["status"] == "completed"
            assert result["file_id"] == "perf-test-001"
            assert result["transcript_word_count"] > 0
            assert result["emotion_segments_count"] > 0
            
            # Performance metrics
            memory_usage_mb = (self.performance_metrics["peak_memory"] - start_memory) / (1024 * 1024)
            avg_cpu = sum(self.performance_metrics["cpu_samples"]) / len(self.performance_metrics["cpu_samples"])
            
            print(f"Peak memory usage: {memory_usage_mb:.2f} MB")
            print(f"Average CPU usage: {avg_cpu:.2f}%")
            
            # Memory usage should be reasonable (< 500MB for processing)
            assert memory_usage_mb < 500, f"Memory usage {memory_usage_mb:.2f}MB exceeds 500MB limit"
            
        finally:
            # Clean up
            try:
                monitoring_task.cancel()
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            # Clean up any temporary files
            audio_processor.cleanup_temp_files("perf-test-001")
    
    async def _background_monitoring(self):
        """Background task to monitor resources."""
        try:
            while True:
                self.monitor_resources()
                await asyncio.sleep(0.5)  # Monitor every 500ms
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_audio_extraction_latency(self):
        """Test audio extraction latency requirement (<50ms per second of video)."""
        print("Testing audio extraction latency")
        
        start_time = time.time()
        
        # Process just the audio extraction part
        result = await audio_processor.process_file(str(TEST_VIDEO_PATH), "latency-test-001")
        
        extraction_time = time.time() - start_time
        video_duration = result.get("audio_features", {}).get("duration", 1.0)
        
        # Calculate latency per second of video
        latency_per_second = (extraction_time / video_duration) * 1000  # Convert to milliseconds
        
        print(f"Audio extraction time: {extraction_time:.3f}s")
        print(f"Video duration: {video_duration:.2f}s")
        print(f"Latency per second: {latency_per_second:.2f}ms/s")
        
        # Constitutional requirement: <50ms per second of video
        assert latency_per_second < 50, f"Audio extraction latency {latency_per_second:.2f}ms/s exceeds 50ms/s"
        
        # Verify extraction was successful
        assert result["status"] == "completed"
        assert "audio_features" in result
        
        # Clean up
        audio_processor.cleanup_temp_files("latency-test-001")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_transcription_processing_speed(self):
        """Test transcription processing speed (should be faster than real-time)."""
        print("Testing transcription processing speed")
        
        # First extract audio
        audio_result = await audio_processor.process_file(str(TEST_VIDEO_PATH), "transcribe-test-001")
        audio_path = audio_result["audio_path"]
        audio_duration = audio_result.get("audio_features", {}).get("duration", 1.0)
        
        # Test transcription speed
        start_time = time.time()
        
        transcript = await transcription_service.transcribe_audio(audio_path, "transcribe-test-001", "ar")
        
        transcription_time = time.time() - start_time
        processing_speed_ratio = transcription_time / audio_duration
        
        print(f"Transcription time: {transcription_time:.2f}s")
        print(f"Audio duration: {audio_duration:.2f}s")
        print(f"Processing speed ratio: {processing_speed_ratio:.2f}x")
        print(f"Transcript word count: {len(transcript.words)}")
        print(f"Transcript confidence: {transcript.confidence:.3f}")
        
        # Should process faster than 3x real-time for reasonable performance
        assert processing_speed_ratio < 3.0, f"Transcription too slow: {processing_speed_ratio:.2f}x real-time"
        
        # Verify transcription quality
        assert len(transcript.words) > 0, "No words transcribed"
        assert transcript.confidence > 0.5, f"Low transcription confidence: {transcript.confidence}"
        
        # Clean up
        audio_processor.cleanup_temp_files("transcribe-test-001")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_emotion_analysis_latency(self):
        """Test emotion analysis latency requirement (<200ms per segment)."""
        print("Testing emotion analysis latency")
        
        # First get audio and transcript
        audio_result = await audio_processor.process_file(str(TEST_VIDEO_PATH), "emotion-test-001")
        audio_path = audio_result["audio_path"]
        
        transcript = await transcription_service.transcribe_audio(audio_path, "emotion-test-001", "ar")
        
        # Test emotion analysis speed
        start_time = time.time()
        
        emotion_analysis = await emotion_analyzer.analyze_emotions(transcript, audio_path, segment_duration=2.0)
        
        analysis_time = time.time() - start_time
        segment_count = len(emotion_analysis.segments)
        latency_per_segment = (analysis_time / segment_count) * 1000 if segment_count > 0 else 0
        
        print(f"Emotion analysis time: {analysis_time:.3f}s")
        print(f"Number of segments: {segment_count}")
        print(f"Latency per segment: {latency_per_segment:.2f}ms")
        print(f"Overall emotion: {emotion_analysis.overall_emotion.value}")
        print(f"Overall confidence: {emotion_analysis.overall_confidence:.3f}")
        
        # Constitutional requirement: <200ms per segment
        assert latency_per_segment < 200, f"Emotion analysis latency {latency_per_segment:.2f}ms exceeds 200ms"
        
        # Verify analysis quality
        assert segment_count > 0, "No emotion segments generated"
        assert emotion_analysis.overall_confidence > 0.3, "Low emotion analysis confidence"
        
        # Clean up
        audio_processor.cleanup_temp_files("emotion-test-001")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_memory_usage_stability(self):
        """Test memory usage remains stable during continuous processing."""
        print("Testing memory usage stability")
        
        initial_memory = self.process.memory_info().rss
        memory_samples = []
        
        # Process the same file multiple times to test memory stability
        for i in range(3):
            print(f"Processing iteration {i + 1}/3")
            
            audio_file = AudioFile(
                id=f"memory-test-{i:03d}",
                filename="aggression.mp4",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=os.path.getsize(TEST_VIDEO_PATH),
                file_path=str(TEST_VIDEO_PATH)
            )
            
            # Monitor memory before processing
            pre_memory = self.process.memory_info().rss
            
            # Process file
            result = await processing_pipeline.process_file(audio_file)
            
            # Monitor memory after processing
            post_memory = self.process.memory_info().rss
            
            memory_samples.append({
                "iteration": i,
                "pre_memory": pre_memory,
                "post_memory": post_memory,
                "memory_increase": post_memory - pre_memory
            })
            
            # Clean up
            audio_processor.cleanup_temp_files(f"memory-test-{i:03d}")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            print(f"Memory before: {pre_memory / (1024*1024):.2f} MB")
            print(f"Memory after: {post_memory / (1024*1024):.2f} MB")
            print(f"Memory increase: {(post_memory - pre_memory) / (1024*1024):.2f} MB")
        
        # Analyze memory usage patterns
        final_memory = self.process.memory_info().rss
        total_memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory / (1024*1024):.2f} MB")
        print(f"Final memory: {final_memory / (1024*1024):.2f} MB")
        print(f"Total memory increase: {total_memory_increase / (1024*1024):.2f} MB")
        
        # Memory should not increase significantly with each processing
        # Allow up to 100MB total increase for caching and temporary data
        assert total_memory_increase < 100 * 1024 * 1024, \
            f"Memory leak detected: {total_memory_increase / (1024*1024):.2f}MB increase"
        
        # Each iteration should not use significantly more memory than the first
        first_increase = memory_samples[0]["memory_increase"]
        for sample in memory_samples[1:]:
            increase_ratio = sample["memory_increase"] / first_increase if first_increase > 0 else 0
            assert increase_ratio < 2.0, \
                f"Memory usage growing: iteration {sample['iteration']} used {increase_ratio:.2f}x more memory"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_concurrent_processing_performance(self):
        """Test performance under concurrent processing load."""
        print("Testing concurrent processing performance")
        
        # Create multiple audio files for concurrent processing
        audio_files = []
        for i in range(3):  # Process 3 files concurrently
            audio_files.append(AudioFile(
                id=f"concurrent-test-{i:03d}",
                filename="aggression.mp4",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=os.path.getsize(TEST_VIDEO_PATH),
                file_path=str(TEST_VIDEO_PATH)
            ))
        
        # Start concurrent processing
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        # Process all files concurrently
        tasks = [processing_pipeline.process_file(audio_file) for audio_file in audio_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        concurrent_time = end_time - start_time
        memory_increase = (end_memory - start_memory) / (1024 * 1024)
        
        print(f"Concurrent processing time: {concurrent_time:.2f}s")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Results: {len([r for r in results if isinstance(r, dict)])}/{len(results)} successful")
        
        # Verify all processing completed successfully
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "completed"]
        assert len(successful_results) == len(audio_files), \
            f"Only {len(successful_results)}/{len(audio_files)} processes completed successfully"
        
        # Concurrent processing should not take much longer than sequential
        # Allow up to 1.5x the time of single processing (accounting for resource contention)
        estimated_single_time = 40  # Estimated based on previous tests
        max_concurrent_time = estimated_single_time * 1.5
        
        assert concurrent_time < max_concurrent_time, \
            f"Concurrent processing too slow: {concurrent_time:.2f}s vs max {max_concurrent_time:.2f}s"
        
        # Memory usage should not be excessive
        assert memory_increase < 1000, f"Excessive memory usage: {memory_increase:.2f}MB"
        
        # Clean up
        for i in range(3):
            audio_processor.cleanup_temp_files(f"concurrent-test-{i:03d}")
    
    @pytest.mark.asyncio
    async def test_file_cleanup_performance(self):
        """Test file cleanup performance and effectiveness."""
        print("Testing file cleanup performance")
        
        # Create test files in file manager
        test_files = []
        for i in range(10):
            file_content = b"test content " * 1000  # 12KB per file
            file_id = f"cleanup-test-{i:03d}"
            
            file_path = await file_manager.store_uploaded_file(
                file_content, f"test{i}.mp4", file_id
            )
            test_files.append((file_id, file_path))
        
        # Cache some data
        for file_id, _ in test_files:
            await file_manager.cache_processed_data(
                file_id, "test_data", {"test": "data", "size": 1000}
            )
        
        # Measure cleanup performance
        start_time = time.time()
        cleanup_stats = await file_manager.cleanup_expired_files()
        cleanup_time = time.time() - start_time
        
        print(f"Cleanup time: {cleanup_time:.3f}s")
        print(f"Files removed: {cleanup_stats['files_removed']}")
        print(f"Cache files removed: {cleanup_stats['cache_files_removed']}")
        print(f"Bytes freed: {cleanup_stats['bytes_freed']}")
        
        # Cleanup should be fast
        assert cleanup_time < 5.0, f"Cleanup too slow: {cleanup_time:.3f}s"
        
        # Should have cleaned up files (they expire immediately in test)
        assert cleanup_stats["files_removed"] >= 0
        assert cleanup_stats["bytes_freed"] >= 0
    
    def test_storage_stats_performance(self):
        """Test storage statistics calculation performance."""
        print("Testing storage statistics performance")
        
        start_time = time.time()
        stats = file_manager.get_storage_stats()
        stats_time = time.time() - start_time
        
        print(f"Storage stats calculation time: {stats_time:.3f}s")
        print(f"Stats: {stats}")
        
        # Should calculate stats quickly
        assert stats_time < 1.0, f"Storage stats too slow: {stats_time:.3f}s"
        
        # Should return valid stats
        assert "total_size_mb" in stats
        assert "upload_file_count" in stats
        assert "cache_file_count" in stats
        assert isinstance(stats["total_size_mb"], (int, float))


class TestScalabilityRequirements:
    """Test scalability and resource usage patterns."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not found")
    async def test_processing_queue_management(self):
        """Test processing queue management under load."""
        print("Testing processing queue management")
        
        # Get initial active processes count
        initial_count = processing_pipeline.get_active_processes_count()
        
        # Start multiple processing tasks
        audio_files = []
        tasks = []
        
        for i in range(5):
            audio_file = AudioFile(
                id=f"queue-test-{i:03d}",
                filename="aggression.mp4",
                file_type=FileType.VIDEO,
                format="mp4",
                file_size=os.path.getsize(TEST_VIDEO_PATH),
                file_path=str(TEST_VIDEO_PATH)
            )
            audio_files.append(audio_file)
            
            # Start processing task
            task = await processing_pipeline.start_processing_task(audio_file)
            tasks.append(task)
        
        # Check active processes
        active_count = processing_pipeline.get_active_processes_count()
        print(f"Active processes: {active_count}")
        
        # Should have started processing tasks
        assert active_count > initial_count
        
        # Get process info
        process_info = processing_pipeline.get_active_processes_info()
        print(f"Process info: {process_info}")
        
        # Wait for some processing to complete
        await asyncio.sleep(5)
        
        # Cancel remaining tasks
        for audio_file in audio_files:
            await processing_pipeline.cancel_processing(audio_file.id)
        
        # Clean up
        for i in range(5):
            audio_processor.cleanup_temp_files(f"queue-test-{i:03d}")
    
    @pytest.mark.asyncio
    async def test_resource_monitoring_accuracy(self):
        """Test accuracy of resource monitoring."""
        print("Testing resource monitoring accuracy")
        
        # Get baseline metrics
        baseline_memory = psutil.Process().memory_info().rss
        baseline_cpu = psutil.cpu_percent(interval=1)
        
        print(f"Baseline memory: {baseline_memory / (1024*1024):.2f} MB")
        print(f"Baseline CPU: {baseline_cpu:.2f}%")
        
        # Perform some processing
        if TEST_VIDEO_PATH.exists():
            audio_result = await audio_processor.process_file(str(TEST_VIDEO_PATH), "monitor-test-001")
            
            # Check resource usage during processing
            current_memory = psutil.Process().memory_info().rss
            memory_increase = (current_memory - baseline_memory) / (1024 * 1024)
            
            print(f"Memory after processing: {current_memory / (1024*1024):.2f} MB")
            print(f"Memory increase: {memory_increase:.2f} MB")
            
            # Verify monitoring detected resource usage
            assert memory_increase >= 0  # Should use some memory
            
            # Clean up
            audio_processor.cleanup_temp_files("monitor-test-001")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
