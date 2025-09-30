"""
Processing API endpoints for SawtFeel application.
"""

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)
from datetime import datetime

from ..models.transcript import Transcript, WordSegment
from ..models.emotion_analysis import EmotionAnalysis, EmotionSegment, EmotionType
from ..models.audio_file import ProcessingStatus
from ..shared.state import uploaded_files  # Import shared storage
from ..services.file_manager import file_manager
from ..services.processing_pipeline import processing_pipeline

router = APIRouter()

# Mock data storage for demonstration (replace with database in production)
transcripts: Dict[str, Transcript] = {}
emotion_analyses: Dict[str, EmotionAnalysis] = {}

@router.get("/processing/{file_id}/transcript")
async def get_transcript(
    file_id: str = Path(..., description="File identifier")
) -> Dict[str, Any]:
    """
    Get transcribed text with word-level timestamps.
    """
    # Check if file exists in memory first
    if file_id in uploaded_files:
        audio_file = uploaded_files[file_id]
        
        # Check if processing is complete
        if audio_file.processing_status != ProcessingStatus.COMPLETED:
            return JSONResponse(
                status_code=409,
                content={
                    "error": "Transcript not yet available",
                    "status": audio_file.processing_status
                }
            )
    else:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        # File exists on disk, assume processing is complete
        audio_file = None
    
    # Try to get transcript from cache first
    cached_transcript = await file_manager.get_cached_data(file_id, "transcript")
    
    if cached_transcript:
        transcript = Transcript(**cached_transcript)
        logger.info(f"Using cached transcript for file {file_id}")
    else:
        # No cached data available - this means processing didn't complete properly
        logger.warning(f"No cached transcript found for file {file_id}, processing may have failed")
        return JSONResponse(
            status_code=404,
            content={"error": "Transcript not available - processing may have failed"}
        )
    
    # Add English translation if not present
    english_text = transcript.english_text
    if not english_text and transcript.text:
        # Import translation service
        from ..services.translation_service import TranslationService
        translation_service = TranslationService()
        english_text = await translation_service.translate_text(transcript.text)
        logger.info(f"Added English translation on-the-fly: {len(english_text)} characters")
    
    return {
        "file_id": file_id,
        "text": transcript.text,
        "english_text": english_text,
        "words": [word.dict() for word in transcript.words],
        "language": transcript.language,
        "overall_confidence": transcript.confidence
    }

@router.get("/processing/{file_id}/emotions")
async def get_emotions(
    file_id: str = Path(..., description="File identifier")
) -> Dict[str, Any]:
    """
    Get emotion analysis data with timestamps.
    """
    # Check if file exists in memory first
    if file_id in uploaded_files:
        audio_file = uploaded_files[file_id]
        
        # Check if processing is complete
        if audio_file.processing_status != ProcessingStatus.COMPLETED:
            return JSONResponse(
                status_code=409,
                content={
                    "error": "Analysis not yet available",
                    "status": audio_file.processing_status
                }
            )
    else:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        # File exists on disk, assume processing is complete
        audio_file = None
    
    # Try to get emotion analysis from cache first
    cached_emotions = await file_manager.get_cached_data(file_id, "emotions")
    
    if cached_emotions:
        analysis = EmotionAnalysis(**cached_emotions)
    elif file_id in emotion_analyses:
        # Use mock data if available
        analysis = emotion_analyses[file_id]
    else:
        # Create mock emotion analysis for demonstration if no real data available
        mock_analysis = EmotionAnalysis(
            audio_file_id=file_id,
            segments=[
                EmotionSegment(
                    start_time=0.0,
                    end_time=2.0,
                    textual_emotion=EmotionType.NEUTRAL,
                    textual_confidence=0.85,
                    tonal_emotion=EmotionType.NEUTRAL,
                    tonal_confidence=0.78,
                    combined_emotion=EmotionType.NEUTRAL,
                    combined_confidence=0.82
                ),
                EmotionSegment(
                    start_time=2.0,
                    end_time=4.8,
                    textual_emotion=EmotionType.JOY,
                    textual_confidence=0.72,
                    tonal_emotion=EmotionType.NEUTRAL,
                    tonal_confidence=0.68,
                    combined_emotion=EmotionType.NEUTRAL,
                    combined_confidence=0.70
                )
            ],
            overall_emotion=EmotionType.NEUTRAL,
            overall_confidence=0.76
        )
        emotion_analyses[file_id] = mock_analysis
        analysis = mock_analysis
    
    return {
        "file_id": file_id,
        "overall_emotion": analysis.overall_emotion,
        "overall_confidence": analysis.overall_confidence,
        "segments": [
            {
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "textual_emotion": segment.textual_emotion,
                "textual_confidence": segment.textual_confidence,
                "tonal_emotion": segment.tonal_emotion,
                "tonal_confidence": segment.tonal_confidence,
                "combined_emotion": segment.combined_emotion,
                "combined_confidence": segment.combined_confidence
            }
            for segment in analysis.segments
        ]
    }

@router.get("/processing/{file_id}/audio-url")
async def get_audio_url(
    file_id: str = Path(..., description="File identifier")
) -> Dict[str, Any]:
    """
    Get the URL for streaming the processed audio file.
    """
    # Check if file exists in memory first
    if file_id in uploaded_files:
        audio_file = uploaded_files[file_id]
    else:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
        # Create a minimal audio file object for disk-based files
        from ..models.audio_file import AudioFile, FileType
        audio_file = AudioFile(
            id=file_id,
            filename="unknown",
            file_type=FileType.AUDIO,  # Default to audio
            format="unknown",
            file_size=0,
            file_path=file_path
        )
    
    # Try to get audio path from cache (for extracted audio from video)
    cached_audio_path = await file_manager.get_cached_data(file_id, "audio_path")
    
    if cached_audio_path and "path" in cached_audio_path:
        audio_file_path = cached_audio_path["path"]
    else:
        # For audio files, use the original file path
        # For video files, we need to check if processing completed
        if audio_file.file_type == "video":
            # If it's a video file and no cached audio path, processing might not be complete
            return JSONResponse(
                status_code=404,
                content={"error": "Audio extraction not completed yet"}
            )
        audio_file_path = audio_file.file_path
    
    # Check if file is accessible
    if not os.path.exists(audio_file_path):
        # If it's a cached audio path that doesn't exist, try the original file
        if cached_audio_path and "path" in cached_audio_path:
            # Cached audio was cleaned up, use original file
            audio_file_path = audio_file.file_path
            if not os.path.exists(audio_file_path):
                raise HTTPException(
                    status_code=404,
                    detail={"error": "Audio file not found on disk"}
                )
        else:
            raise HTTPException(
                status_code=404,
                detail={"error": "Audio file not found on disk"}
            )
    
    # Serve the audio file URL
    audio_url = f"/api/files/{file_id}/audio"
    
    return {
        "file_id": file_id,
        "audio_url": audio_url,
        "duration": audio_file.duration or 30.0,  # Mock duration if not available
        "format": "wav"  # Extracted audio format
    }

@router.get("/files/{file_id}/audio")
async def serve_audio_file(
    file_id: str = Path(..., description="File identifier")
):
    """
    Serve the audio file for streaming.
    """
    # Check if file exists in memory first
    if file_id in uploaded_files:
        audio_file = uploaded_files[file_id]
    else:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        # Create a minimal audio file object for disk-based files
        from ..models.audio_file import AudioFile, FileType
        audio_file = AudioFile(
            id=file_id,
            filename="unknown",
            file_type=FileType.AUDIO,  # Default to audio
            format="unknown",
            file_size=0,
            file_path=file_path
        )
    
    # Try to get audio path from cache (for extracted audio from video)
    cached_audio_path = await file_manager.get_cached_data(file_id, "audio_path")
    
    if cached_audio_path and "path" in cached_audio_path:
        audio_file_path = cached_audio_path["path"]
    else:
        # For audio files, use the original file path
        # For video files, we need to check if processing completed
        if audio_file.file_type == "video":
            # If it's a video file and no cached audio path, processing might not be complete
            raise HTTPException(
                status_code=404,
                detail="Audio extraction not completed yet"
            )
        audio_file_path = audio_file.file_path
    
    # Check if file is accessible
    if not os.path.exists(audio_file_path):
        # If it's a cached audio path that doesn't exist, try the original file
        if cached_audio_path and "path" in cached_audio_path:
            # Cached audio was cleaned up, use original file
            audio_file_path = audio_file.file_path
            if not os.path.exists(audio_file_path):
                raise HTTPException(
                    status_code=404,
                    detail="Audio file not found on disk"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail="Audio file not found on disk"
            )
    
    # For a full implementation, this would stream the file
    # For now, return file info
    return {
        "message": "Audio streaming endpoint",
        "file_path": audio_file_path,
        "note": "In production, this would stream the actual audio file"
    }
