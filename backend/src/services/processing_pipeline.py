"""
Processing pipeline service that orchestrates all components.
Integrates AudioProcessor, TranscriptionService, EmotionAnalyzer, and FileManager.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from .audio_processor import audio_processor
from .transcription_service import transcription_service, translation_service
from .translation_service import TranslationService
from .emotion_analyzer import emotion_analyzer
from .file_manager import file_manager
from .redis_client import redis_client
from ..models.audio_file import AudioFile, ProcessingStatus
from ..models.transcript import Transcript
from ..models.emotion_analysis import EmotionAnalysis

# Import shared state for uploaded files
from ..shared.state import uploaded_files

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """Orchestrates the complete file processing pipeline."""
    
    def __init__(self):
        self.active_processes = {}  # Track active processing tasks
        
    async def process_file(self, audio_file: AudioFile) -> Dict:
        """
        Process uploaded file through complete pipeline.
        
        Args:
            audio_file: AudioFile object with metadata
            
        Returns:
            Processing results dictionary
        """
        file_id = audio_file.id
        
        try:
            logger.info(f"Starting processing pipeline for file {file_id}")
            print(f"DEBUG: Processing pipeline started for file {file_id}")
            
            # Update status to extracting
            await self._update_processing_status(file_id, ProcessingStatus.EXTRACTING_AUDIO)
            print(f"DEBUG: Status updated to EXTRACTING_AUDIO for file {file_id}")
            
            # Step 1: Audio Processing (extraction and feature analysis)
            print(f"DEBUG: Starting audio processing for file {file_id}")
            audio_results = await self._process_audio(audio_file)
            print(f"DEBUG: Audio processing completed for file {file_id}: {audio_results}")
            
            # Update status to transcribing
            await self._update_processing_status(file_id, ProcessingStatus.TRANSCRIBING)
            print(f"DEBUG: Status updated to TRANSCRIBING for file {file_id}")
            
            # Step 2: Speech-to-Text Transcription
            print(f"DEBUG: Starting transcription for file {file_id}")
            transcript = await self._process_transcription(audio_file, audio_results["audio_path"])
            print(f"DEBUG: Transcription completed for file {file_id}: {len(transcript.text)} characters")
            
            # Update status to analyzing
            await self._update_processing_status(file_id, ProcessingStatus.ANALYZING)
            
            # Step 3: Emotion Analysis
            emotion_analysis = await self._process_emotion_analysis(transcript, audio_results["audio_path"])
            
            # Step 4: Cache all results
            await self._cache_results(file_id, {
                "audio_results": audio_results,
                "transcript": transcript.dict(),
                "emotion_analysis": emotion_analysis.dict()
            })
            
            # Update status to completed
            await self._update_processing_status(file_id, ProcessingStatus.COMPLETED)
            
            # Cleanup temporary files
            await self._cleanup_processing_files(file_id, audio_results)
            
            processing_results = {
                "file_id": file_id,
                "status": "completed",
                "audio_duration": audio_results.get("duration", 0),
                "transcript_word_count": len(transcript.words),
                "emotion_segments_count": len(emotion_analysis.segments),
                "overall_emotion": emotion_analysis.overall_emotion,
                "processing_time": audio_results.get("processing_time", 0)
            }
            
            logger.info(f"Processing completed for file {file_id}: {processing_results}")
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {str(e)}")
            await self._update_processing_status(file_id, ProcessingStatus.FAILED)
            
            # Cache error information
            await self._cache_error(file_id, str(e))
            
            raise
        finally:
            # Remove from active processes
            if file_id in self.active_processes:
                del self.active_processes[file_id]
    
    async def _process_audio(self, audio_file: AudioFile) -> Dict:
        """Process audio/video file for feature extraction."""
        try:
            file_path = file_manager.get_file_path(audio_file.id)
            if not file_path:
                raise FileNotFoundError(f"File not found: {audio_file.id}")
            
            # Process file using AudioProcessor
            audio_results = await audio_processor.process_file(file_path, audio_file.id)
            
            # Store audio path in file metadata if it's a video file
            if audio_file.file_type == "video" and "audio_path" in audio_results:
                # Cache the extracted audio path
                await file_manager.cache_processed_data(
                    audio_file.id, 
                    "audio_path", 
                    {"path": audio_results["audio_path"]}
                )
            
            return audio_results
            
        except Exception as e:
            logger.error(f"Error in audio processing: {str(e)}")
            raise
    
    async def _process_transcription(self, audio_file: AudioFile, audio_path: str) -> Transcript:
        """Process audio for speech-to-text transcription."""
        try:
            # Check if transcript is already cached
            cached_transcript = await file_manager.get_cached_data(audio_file.id, "transcript")
            if cached_transcript:
                logger.info(f"Found cached transcript for file {audio_file.id}, but forcing re-processing")
                # Force re-processing by not returning cached data
                # return Transcript(**cached_transcript)
            
            # Perform transcription
            logger.info(f"Starting transcription for file {audio_file.id} with audio path: {audio_path}")
            transcript = await transcription_service.transcribe_audio(
                audio_path, 
                audio_file.id, 
                language="ar"
            )
            logger.info(f"Transcription completed for file {audio_file.id}: {len(transcript.text)} characters")
            
            # Translate Arabic text to English
            if transcript.text:
                english_text = await translation_service.translate_text(transcript.text)
                transcript.english_text = english_text
                logger.info(f"Translated transcript to English: {len(english_text)} characters")
            
            # Cache transcript results
            await file_manager.cache_processed_data(
                audio_file.id, 
                "transcript", 
                transcript.dict()
            )
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            raise
    
    async def _process_emotion_analysis(self, transcript: Transcript, audio_path: str) -> EmotionAnalysis:
        """Process transcript and audio for emotion analysis."""
        try:
            # Check if emotion analysis is already cached
            cached_emotions = await file_manager.get_cached_data(transcript.audio_file_id, "emotions")
            if cached_emotions:
                logger.info(f"Using cached emotion analysis for file {transcript.audio_file_id}")
                return EmotionAnalysis(**cached_emotions)
            
            # Perform emotion analysis
            emotion_analysis = await emotion_analyzer.analyze_emotions(
                transcript, 
                audio_path,
                segment_duration=2.0
            )
            
            # Cache emotion analysis results
            await file_manager.cache_processed_data(
                transcript.audio_file_id, 
                "emotions", 
                emotion_analysis.dict()
            )
            
            return emotion_analysis
            
        except Exception as e:
            logger.error(f"Error in emotion analysis: {str(e)}")
            raise
    
    async def _update_processing_status(self, file_id: str, status: ProcessingStatus):
        """Update processing status in cache and broadcast via WebSocket."""
        try:
            # Update status in Redis cache
            status_data = {
                "file_id": file_id,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "progress": self._get_progress_for_status(status)
            }
            
            await redis_client.cache_processing_status(file_id, status_data)
            
            # Also update the AudioFile object in uploaded_files
            if file_id in uploaded_files:
                uploaded_files[file_id].processing_status = status
            
            # Broadcast status update via WebSocket (will be implemented in WebSocket integration)
            await self._broadcast_status_update(file_id, status_data)
            
            logger.info(f"Updated processing status for {file_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error updating processing status: {str(e)}")
    
    def _get_progress_for_status(self, status: ProcessingStatus) -> int:
        """Get progress percentage for processing status."""
        progress_map = {
            ProcessingStatus.UPLOADED: 10,
            ProcessingStatus.EXTRACTING_AUDIO: 25,
            ProcessingStatus.TRANSCRIBING: 50,
            ProcessingStatus.ANALYZING: 80,
            ProcessingStatus.COMPLETED: 100,
            ProcessingStatus.FAILED: 0
        }
        return progress_map.get(status, 0)
    
    async def _broadcast_status_update(self, file_id: str, status_data: Dict):
        """Broadcast status update via WebSocket."""
        try:
            # Import WebSocket manager here to avoid circular imports
            from ..api.websocket import processing_manager
            
            # Broadcast to all connected clients for this file
            await processing_manager.broadcast_to_file({
                "type": "status_update",
                **status_data
            }, file_id)
            
            logger.info(f"Broadcasted status update for {file_id}: {status_data}")
            
        except Exception as e:
            logger.error(f"Error broadcasting status update: {str(e)}")
            # Fallback to logging if WebSocket fails
            logger.info(f"Status update for {file_id}: {status_data}")
    
    async def _cache_results(self, file_id: str, results: Dict):
        """Cache all processing results."""
        try:
            # Cache complete results
            await file_manager.cache_processed_data(file_id, "complete_results", results)
            
            # Also cache individual components if not already cached
            if "transcript" in results:
                await file_manager.cache_processed_data(file_id, "transcript", results["transcript"])
            
            if "emotion_analysis" in results:
                await file_manager.cache_processed_data(file_id, "emotions", results["emotion_analysis"])
            
            logger.info(f"Cached processing results for file {file_id}")
            
        except Exception as e:
            logger.error(f"Error caching results: {str(e)}")
    
    async def _cache_error(self, file_id: str, error_message: str):
        """Cache error information."""
        try:
            error_data = {
                "error": error_message,
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await file_manager.cache_processed_data(file_id, "error", error_data)
            await redis_client.cache_processing_status(file_id, error_data)
            
        except Exception as e:
            logger.error(f"Error caching error information: {str(e)}")
    
    async def _cleanup_processing_files(self, file_id: str, audio_results: Dict):
        """Clean up temporary processing files."""
        try:
            # Clean up audio processor temp files
            audio_processor.cleanup_temp_files(file_id)
            
            # Clean up any other temporary files
            temp_files = [
                audio_results.get("temp_files", [])
            ]
            
            for temp_file_list in temp_files:
                if isinstance(temp_file_list, list):
                    for temp_file in temp_file_list:
                        try:
                            import os
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                logger.info(f"Cleaned up temp file: {temp_file}")
                        except Exception as e:
                            logger.warning(f"Error cleaning temp file {temp_file}: {e}")
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")
    
    async def get_processing_status(self, file_id: str) -> Optional[Dict]:
        """Get current processing status for a file."""
        try:
            # Try to get from Redis cache first
            status_data = await redis_client.get_processing_status(file_id)
            if status_data:
                return status_data
            
            # Fallback to checking if results are cached
            cached_results = await file_manager.get_cached_data(file_id, "complete_results")
            if cached_results:
                return {
                    "file_id": file_id,
                    "status": "completed",
                    "progress": 100,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Check for error cache
            error_data = await file_manager.get_cached_data(file_id, "error")
            if error_data:
                return {
                    "file_id": file_id,
                    "status": "failed",
                    "progress": 0,
                    "error": error_data.get("error"),
                    "timestamp": error_data.get("timestamp")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting processing status: {str(e)}")
            return None
    
    async def start_processing_task(self, audio_file: AudioFile):
        """Start processing task in background."""
        file_id = audio_file.id
        
        if file_id in self.active_processes:
            logger.warning(f"Processing already active for file {file_id}")
            return
        
        # Create background task
        task = asyncio.create_task(self.process_file(audio_file))
        self.active_processes[file_id] = {
            "task": task,
            "started_at": datetime.now(),
            "audio_file": audio_file
        }
        
        logger.info(f"Started background processing task for file {file_id}")
        
        return task
    
    def is_processing(self, file_id: str) -> bool:
        """Check if file is currently being processed."""
        return file_id in self.active_processes
    
    async def cancel_processing(self, file_id: str) -> bool:
        """Cancel processing for a file."""
        if file_id not in self.active_processes:
            return False
        
        try:
            task = self.active_processes[file_id]["task"]
            task.cancel()
            
            # Wait for task to be cancelled
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Clean up
            del self.active_processes[file_id]
            
            # Update status
            await self._update_processing_status(file_id, ProcessingStatus.FAILED)
            
            logger.info(f"Cancelled processing for file {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling processing for {file_id}: {e}")
            return False
    
    def get_active_processes_count(self) -> int:
        """Get count of active processing tasks."""
        return len(self.active_processes)
    
    def get_active_processes_info(self) -> Dict:
        """Get information about active processing tasks."""
        info = {}
        current_time = datetime.now()
        
        for file_id, process_info in self.active_processes.items():
            started_at = process_info["started_at"]
            duration = (current_time - started_at).total_seconds()
            
            info[file_id] = {
                "filename": process_info["audio_file"].filename,
                "started_at": started_at.isoformat(),
                "duration_seconds": duration,
                "task_done": process_info["task"].done()
            }
        
        return info

# Global processing pipeline instance
processing_pipeline = ProcessingPipeline()
