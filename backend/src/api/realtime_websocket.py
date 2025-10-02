"""
Real-time WebSocket endpoints for SawtFeel application.
Handles live transcription and emotion analysis streaming.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

def json_serializer(obj):
    """Custom JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

import uuid

from ..services.realtime_processor import realtime_processor
from ..services.streaming_transcription_service import streaming_transcription_service
from ..services.streaming_emotion_service import streaming_emotion_service
from ..models.realtime_transcript import TranscriptUpdate
from ..models.realtime_emotion import EmotionUpdate
from ..models.playback_state import PlaybackState, PlaybackStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["realtime"])

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """Manages WebSocket connections and real-time data streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection established: {connection_id}")
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from session mapping
        session_id = None
        for sid, cid in self.session_connections.items():
            if cid == connection_id:
                session_id = sid
                break
        
        if session_id:
            del self.session_connections[session_id]
            # Stop real-time processing for this session
            asyncio.create_task(realtime_processor.stop_processing(session_id))
        
        logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(
                    json.dumps(message, default=json_serializer)
                )
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
    
    async def broadcast_to_file(self, message: Dict[str, Any], file_id: str):
        """Broadcast a message to all connections for a specific file."""
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message, default=json_serializer))
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")

# Global connection manager
manager = ConnectionManager()

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify the router is working."""
    logger.info("TEST: Test endpoint called!")
    return {"message": "Realtime WebSocket router is working"}

@router.websocket("/realtime/{file_id}")
async def websocket_realtime(websocket: WebSocket, file_id: str):
    """
    WebSocket endpoint for real-time transcription and emotion analysis.
    
    Args:
        websocket: WebSocket connection
        file_id: File identifier for processing
    """
    await websocket.accept()
    logger.info(f"WebSocket accepted for {file_id}")
    
    try:
        # Load processed emotion data
        from ..services.file_manager import file_manager
        emotion_data = await file_manager.get_cached_data(file_id, "emotions")
        
        if not emotion_data:
            logger.warning(f"No emotion data found for file {file_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No emotion data available for this file",
                "file_id": file_id,
                "timestamp": datetime.now().isoformat()
            }))
            return
        
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Emotion analysis ready",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send emotion data
        if emotion_data.get("segments"):
            await websocket.send_text(json.dumps({
                "type": "emotion_data",
                "data": emotion_data,
                "file_id": file_id,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Keep connection alive and send periodic updates
        current_time = 0
        while True:
            await asyncio.sleep(0.5)  # Update every 500ms
            
            # Find current emotion based on time
            current_emotion = None
            if emotion_data.get("segments"):
                for segment in emotion_data["segments"]:
                    if segment.get("start_time", 0) <= current_time <= segment.get("end_time", 0):
                        current_emotion = segment
                        break
            
            # Send current emotion update
            if current_emotion:
                await websocket.send_text(json.dumps({
                    "type": "emotion_update",
                    "emotion": {
                        "emotion_type": current_emotion.get("combined_emotion", "neutral"),
                        "confidence": current_emotion.get("combined_confidence", 0.5),
                        "intensity": current_emotion.get("combined_confidence", 0.5),  # Use confidence as intensity
                        "start_time": current_emotion.get("start_time", 0),
                        "end_time": current_emotion.get("end_time", 0),
                        "timestamp": current_time
                    },
                    "file_id": file_id,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Increment time (simulate playback)
            current_time += 0.5
            
            # Stop after 30 seconds for demo
            if current_time > 30:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for {file_id}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error: {str(e)}",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }))
    finally:
        logger.info(f"WebSocket closed for {file_id}")

async def stream_transcription_data(websocket: WebSocket, session_id: str, file_id: str):
    """Stream transcription data for a session."""
    try:
        # This would stream real transcription data
        # For now, just send a placeholder
        await asyncio.sleep(1)
        await websocket.send_text(json.dumps({
            "type": "transcript_update",
            "data": {
                "text": "Sample transcription data",
                "timestamp": time.time()
            },
            "session_id": session_id
        }))
    except Exception as e:
        logger.error(f"Error streaming transcription data: {e}")

async def stream_emotion_data(websocket: WebSocket, session_id: str, file_id: str):
    """Stream emotion data for a session."""
    try:
        # This would stream real emotion data
        # For now, just send a placeholder
        await asyncio.sleep(1)
        await websocket.send_text(json.dumps({
            "type": "emotion_update",
            "data": {
                "emotion": "neutral",
                "confidence": 0.8,
                "intensity": 0.5,
                "timestamp": time.time()
            },
            "session_id": session_id
        }))
    except Exception as e:
        logger.error(f"Error streaming emotion data: {e}")

async def handle_websocket_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    try:
        message_type = message.get("type")
        
        if message_type == "playback_update":
            # Handle playback state updates
            playback_data = message.get("data", {})
            await realtime_processor.update_playback_state(
                session_id,
                playback_data.get("current_time", 0),
                PlaybackStatus.PLAYING if playback_data.get("is_playing") else PlaybackStatus.PAUSED,
                playback_data.get("is_seeking", False)
            )
            
        elif message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a specific session."""
    try:
        playback_state = await realtime_processor.get_playback_state(session_id)
        return {
            "session_id": session_id,
            "playback_state": playback_state,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/sessions")
async def get_active_sessions():
    """Get list of active sessions."""
    try:
        sessions = list(manager.session_connections.keys())
        return {
            "active_sessions": sessions,
            "count": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/sessions/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause a session."""
    try:
        await realtime_processor.pause_processing(session_id)
        return {"message": f"Session {session_id} paused"}
    except Exception as e:
        logger.error(f"Error pausing session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume a session."""
    try:
        await realtime_processor.resume_processing(session_id)
        return {"message": f"Session {session_id} resumed"}
    except Exception as e:
        logger.error(f"Error resuming session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop a session."""
    try:
        await realtime_processor.stop_processing(session_id)
        return {"message": f"Session {session_id} stopped"}
    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )