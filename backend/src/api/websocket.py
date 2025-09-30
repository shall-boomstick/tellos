"""
WebSocket handlers for SawtFeel application.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path
import json
import asyncio
import os
import logging
from typing import Dict, List
from datetime import datetime

from ..models.playback_state import playback_manager
from ..api.upload import uploaded_files
from ..services.processing_pipeline import processing_pipeline
from ..services.file_manager import file_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections
processing_connections: Dict[str, List[WebSocket]] = {}
playback_connections: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, file_id: str):
        """Accept WebSocket connection and add to active connections."""
        await websocket.accept()
        if file_id not in self.active_connections:
            self.active_connections[file_id] = []
        self.active_connections[file_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, file_id: str):
        """Remove WebSocket connection."""
        if file_id in self.active_connections:
            if websocket in self.active_connections[file_id]:
                self.active_connections[file_id].remove(websocket)
            if not self.active_connections[file_id]:
                del self.active_connections[file_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass  # Connection might be closed
    
    async def broadcast_to_file(self, message: dict, file_id: str):
        """Send message to all connections for a specific file."""
        if file_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[file_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[file_id].remove(connection)

# Connection managers
processing_manager = ConnectionManager()
playback_manager_ws = ConnectionManager()

@router.websocket("/ws/processing/{file_id}")
async def websocket_processing_endpoint(
    websocket: WebSocket,
    file_id: str = Path(..., description="File identifier")
):
    """
    WebSocket endpoint for processing updates.
    """
    # Check if file exists in memory first
    if file_id not in uploaded_files:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            await websocket.close(code=4004, reason="File not found")
            return
        # File exists on disk, create minimal audio file object
        from ..models.audio_file import AudioFile, FileType, ProcessingStatus
        audio_file = AudioFile(
            id=file_id,
            filename="unknown",
            file_type=FileType.AUDIO,
            format="unknown",
            file_size=0,
            file_path=file_path,
            processing_status=ProcessingStatus.COMPLETED
        )
    else:
        audio_file = uploaded_files[file_id]
    
    await processing_manager.connect(websocket, file_id)
    
    # Send initial connection message
    await processing_manager.send_personal_message({
        "type": "connected",
        "file_id": file_id,
        "timestamp": datetime.now().isoformat()
    }, websocket)
    
    try:
        
        # Send initial status
        await processing_manager.send_personal_message({
            "type": "status_update",
            "file_id": file_id,
            "status": audio_file.processing_status.value,
            "message": f"File is {audio_file.processing_status.value}",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Send real-time processing updates if file is being processed
        if processing_pipeline.is_processing(file_id):
            await send_real_time_processing_updates(websocket, file_id)
        elif audio_file.processing_status.value == "completed":
            # File is already completed, send completion message
            await processing_manager.send_personal_message({
                "type": "completed",
                "file_id": file_id,
                "message": "Processing completed successfully",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        elif audio_file.processing_status.value not in ["completed", "failed"]:
            await simulate_processing_updates(websocket, file_id)
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await processing_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        processing_manager.disconnect(websocket, file_id)

@router.websocket("/ws/playback/{file_id}")
async def websocket_playback_endpoint(
    websocket: WebSocket,
    file_id: str = Path(..., description="File identifier")
):
    """
    WebSocket endpoint for playback synchronization.
    """
    # Check if file exists in memory first
    if file_id not in uploaded_files:
        # Check if file exists on disk
        file_path = file_manager.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            await websocket.close(code=4004, reason="File not found")
            return
    
    await playback_manager_ws.connect(websocket, file_id)
    
    # Create playback session
    session = playback_manager.create_session(file_id)
    
    # Send initial connection message
    await playback_manager_ws.send_personal_message({
        "type": "connected",
        "file_id": file_id,
        "session_id": session.session_id,
        "timestamp": datetime.now().isoformat()
    }, websocket)
    
    try:
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "time_update":
                    # Update playback position
                    current_time = message.get("current_time", 0)
                    is_playing = message.get("is_playing", False)
                    
                    session.update_position(current_time)
                    session.set_playing_state(is_playing)
                    
                    # Broadcast to other connections
                    await playback_manager_ws.broadcast_to_file({
                        "type": "time_update",
                        "file_id": file_id,
                        "current_time": current_time,
                        "is_playing": is_playing,
                        "timestamp": datetime.now().isoformat()
                    }, file_id)
                    
                    # Send real emotion update for current time
                    await send_real_emotion_update(file_id, current_time)
                    
                    # Send real transcript update for current time
                    await send_real_transcript_update(file_id, current_time)
                
                elif message.get("type") == "play":
                    session.set_playing_state(True)
                    await playback_manager_ws.broadcast_to_file({
                        "type": "play",
                        "file_id": file_id,
                        "timestamp": datetime.now().isoformat()
                    }, file_id)
                
                elif message.get("type") == "pause":
                    session.set_playing_state(False)
                    await playback_manager_ws.broadcast_to_file({
                        "type": "pause",
                        "file_id": file_id,
                        "timestamp": datetime.now().isoformat()
                    }, file_id)
                
                elif message.get("type") == "seek":
                    seek_time = message.get("time", 0)
                    session.update_position(seek_time)
                    await playback_manager_ws.broadcast_to_file({
                        "type": "seek",
                        "file_id": file_id,
                        "time": seek_time,
                        "timestamp": datetime.now().isoformat()
                    }, file_id)
                
            except WebSocketDisconnect:
                break
            except Exception:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        playback_manager_ws.disconnect(websocket, file_id)
        playback_manager.remove_session(session.session_id)

async def send_real_time_processing_updates(websocket: WebSocket, file_id: str):
    """Send real-time processing updates from pipeline."""
    while processing_pipeline.is_processing(file_id):
        try:
            # Get current processing status
            status_data = await processing_pipeline.get_processing_status(file_id)
            
            if status_data:
                await processing_manager.send_personal_message({
                    "type": "progress_update",
                    "file_id": file_id,
                    "status": status_data["status"],
                    "progress": status_data["progress"],
                    "message": f"Processing: {status_data['status']}",
                    "timestamp": status_data["timestamp"]
                }, websocket)
                
                # Check if completed
                if status_data["status"] in ["completed", "failed"]:
                    await processing_manager.send_personal_message({
                        "type": "completed" if status_data["status"] == "completed" else "error",
                        "file_id": file_id,
                        "message": "Processing completed successfully" if status_data["status"] == "completed" else "Processing failed",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    break
            
            await asyncio.sleep(1)  # Check every second
            
        except Exception as e:
            logger.error(f"Error sending real-time updates: {e}")
            break

async def simulate_processing_updates(websocket: WebSocket, file_id: str):
    """Simulate processing progress updates (fallback)."""
    audio_file = uploaded_files[file_id]
    
    stages = [
        ("extracting", 30, "Extracting audio from video..."),
        ("transcribing", 60, "Transcribing Arabic speech..."),
        ("analyzing", 90, "Analyzing emotions..."),
        ("completed", 100, "Processing complete!")
    ]
    
    for status, progress, message in stages:
        await asyncio.sleep(2)  # Simulate processing time
        
        # Send progress update
        await processing_manager.send_personal_message({
            "type": "progress_update",
            "file_id": file_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        if status == "completed":
            await processing_manager.send_personal_message({
                "type": "completed",
                "file_id": file_id,
                "message": "File processing completed successfully",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            break

async def send_real_emotion_update(file_id: str, current_time: float):
    """Send real emotion update for current playback time."""
    try:
        # Get real emotion analysis from cache
        cached_emotions = await file_manager.get_cached_data(file_id, "emotions")
        
        if cached_emotions:
            from ..models.emotion_analysis import EmotionAnalysis
            analysis = EmotionAnalysis(**cached_emotions)
            
            # Find emotion segment for current time
            current_segment = analysis.get_emotion_at_time(current_time)
            
            if current_segment:
                message = {
                    "type": "emotion_update",
                    "file_id": file_id,
                    "current_time": current_time,
                    "emotion": current_segment.combined_emotion.value,
                    "confidence": current_segment.combined_confidence,
                    "textual_emotion": current_segment.textual_emotion.value,
                    "tonal_emotion": current_segment.tonal_emotion.value,
                    "timestamp": datetime.now().isoformat()
                }
                
                await playback_manager_ws.broadcast_to_file(message, file_id)
                return
        
        # Fallback to mock data
        await send_emotion_update(file_id, current_time)
        
    except Exception as e:
        logger.error(f"Error sending real emotion update: {e}")
        await send_emotion_update(file_id, current_time)

async def send_real_transcript_update(file_id: str, current_time: float):
    """Send real transcript update for current playback time."""
    try:
        # Get real transcript from cache
        cached_transcript = await file_manager.get_cached_data(file_id, "transcript")
        
        if cached_transcript:
            from ..models.transcript import Transcript
            transcript = Transcript(**cached_transcript)
            
            # Find current word
            current_word = "..."
            word_index = -1
            
            for i, word in enumerate(transcript.words):
                if current_time >= word.start_time and current_time <= word.end_time:
                    current_word = word.word
                    word_index = i
                    break
                elif current_time < word.start_time:
                    # Use previous word if we're between words
                    if i > 0:
                        current_word = transcript.words[i-1].word
                        word_index = i-1
                    break
            
            message = {
                "type": "transcript_update",
                "file_id": file_id,
                "current_time": current_time,
                "current_word": current_word,
                "word_index": word_index,
                "timestamp": datetime.now().isoformat()
            }
            
            await playback_manager_ws.broadcast_to_file(message, file_id)
            return
        
        # Fallback to mock data
        await send_transcript_update(file_id, current_time)
        
    except Exception as e:
        logger.error(f"Error sending real transcript update: {e}")
        await send_transcript_update(file_id, current_time)

async def send_emotion_update(file_id: str, current_time: float):
    """Send mock emotion update for current playback time."""
    # Mock emotion data based on time
    emotions = ["neutral", "joy", "anger", "sadness", "fear", "surprise"]
    emotion_index = int(current_time / 5) % len(emotions)
    emotion = emotions[emotion_index]
    confidence = 0.7 + (current_time % 1) * 0.3  # Vary confidence
    
    message = {
        "type": "emotion_update",
        "file_id": file_id,
        "current_time": current_time,
        "emotion": emotion,
        "confidence": min(confidence, 1.0),
        "timestamp": datetime.now().isoformat()
    }
    
    await playback_manager_ws.broadcast_to_file(message, file_id)

async def send_transcript_update(file_id: str, current_time: float):
    """Send mock transcript update for current playback time."""
    # Mock transcript data
    words = ["هذا", "نص", "تجريبي", "باللغة", "العربية", "لتحليل", "المشاعر"]
    word_times = [0.0, 0.5, 1.0, 1.8, 2.5, 3.2, 4.0]
    
    # Find current word
    current_word = "..."
    word_index = -1
    
    for i, time in enumerate(word_times):
        if current_time >= time:
            current_word = words[i] if i < len(words) else "..."
            word_index = i
        else:
            break
    
    message = {
        "type": "transcript_update",
        "file_id": file_id,
        "current_time": current_time,
        "current_word": current_word,
        "word_index": word_index,
        "timestamp": datetime.now().isoformat()
    }
    
    await playback_manager_ws.broadcast_to_file(message, file_id)
