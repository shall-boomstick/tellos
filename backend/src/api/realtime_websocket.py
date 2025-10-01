"""
Real-time WebSocket endpoints for live transcription and emotion analysis.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.routing import APIRouter

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
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
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_session(self, message: Dict[str, Any], session_id: str):
        """Send a message to all connections in a session."""
        if session_id in self.session_connections:
            connection_id = self.session_connections[session_id]
            await self.send_personal_message(message, connection_id)
    
    def register_session(self, session_id: str, connection_id: str):
        """Register a session with a connection."""
        self.session_connections[session_id] = connection_id


manager = ConnectionManager()

# Test endpoint to verify routing
@router.get("/test")
async def test_endpoint():
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
    # Simplified version for testing
    await websocket.accept()
    logger.info(f"SIMPLE: WebSocket accepted for {file_id}")
    
    # Send a test message immediately
    await websocket.send_text(json.dumps({
        "type": "test",
        "message": "Hello from realtime WebSocket!",
        "file_id": file_id,
        "timestamp": datetime.now().isoformat()
    }))
    logger.info(f"SIMPLE: Test message sent for {file_id}")
    
    # Keep connection alive for a bit
    try:
        while True:
            await asyncio.sleep(1)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }))
    except Exception as e:
        logger.info(f"SIMPLE: WebSocket closed for {file_id}: {e}")
    
    return
    
    try:
        # First accept the connection
        await manager.connect(websocket, connection_id)
        logger.info(f"WebSocket connection accepted for file: {file_id}")
        logger.info(f"DEBUG: Starting WebSocket setup for {file_id}")
        
        # Check if the audio file exists (from processing pipeline)
        import os
        audio_path = None
        
        # Try multiple possible audio file paths
        possible_paths = [
            f"/tmp/{file_id}_extracted.wav",  # Standard extraction path
            f"/tmp/audio_{file_id}.wav",      # Alternative path
            f"/tmp/{file_id}.wav",            # Simple path
            f"/app/temp_uploads/{file_id}_extracted.wav"  # Alternative location
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                audio_path = path
                logger.info(f"Found audio file at: {audio_path}")
                break
        
        if not audio_path:
            # No audio file found - this is normal if processing isn't complete yet
            logger.info(f"No audio file found for {file_id}, will use mock data for demonstration")
            await manager.send_personal_message({
                "type": "info",
                "message": f"Audio file not ready yet. Using demonstration data for real-time features.",
                "file_id": file_id,
                "timestamp": datetime.now().isoformat()
            }, connection_id)
            
            # Use a mock path - the services will handle this gracefully
            audio_path = f"/tmp/mock_{file_id}.wav"
        
        logger.info(f"Using audio path: {audio_path}")
        
        # Initialize real-time processor (with error handling)
        try:
            await realtime_processor.initialize()
            logger.info("Real-time processor initialized successfully")
        except Exception as init_error:
            logger.error(f"Failed to initialize real-time processor: {init_error}")
            await manager.send_personal_message({
                "type": "error",
                "message": f"Failed to initialize real-time processing: {str(init_error)}",
                "file_id": file_id,
                "timestamp": datetime.now().isoformat()
            }, connection_id)
        
        # Start real-time processing if audio file exists
        if audio_path and os.path.exists(audio_path):
            try:
                session_id = await realtime_processor.start_processing(file_id, audio_path)
                manager.register_session(session_id, connection_id)
                logger.info(f"Real-time processing started for session: {session_id}")
            except Exception as proc_error:
                logger.error(f"Failed to start real-time processing: {proc_error}")
                # Use mock session as fallback
                session_id = "mock_session_" + file_id
                manager.register_session(session_id, connection_id)
                await manager.send_personal_message({
                    "type": "error", 
                    "message": f"Real-time processing unavailable: {str(proc_error)}",
                    "file_id": file_id,
                    "timestamp": datetime.now().isoformat()
                }, connection_id)
        else:
            # Use mock session if no audio file
            session_id = "mock_session_" + file_id
            manager.register_session(session_id, connection_id)
            logger.info(f"Using mock session (no audio file): {session_id}")
        
        # Send initial status
        logger.info(f"DEBUG: Sending initial status for {file_id}")
        await manager.send_personal_message({
            "type": "status",
            "message": "Real-time processing started",
            "session_id": session_id,
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        }, connection_id)
        logger.info(f"DEBUG: Initial status sent for {file_id}")
        
        # Start background tasks for streaming data
        logger.info(f"Starting streaming tasks for session {session_id}")
        transcription_task = asyncio.create_task(
            stream_transcription_data(websocket, session_id, file_id)
        )
        emotion_task = asyncio.create_task(
            stream_emotion_data(websocket, session_id, file_id)
        )
        logger.info(f"Streaming tasks created for session {session_id}")
        
        # Handle incoming messages concurrently with streaming tasks
        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await handle_websocket_message(websocket, session_id, message)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }, connection_id)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    }, connection_id)
        finally:
            # Cancel streaming tasks when WebSocket closes
            if 'transcription_task' in locals():
                transcription_task.cancel()
            if 'emotion_task' in locals():
                emotion_task.cancel()
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        }, connection_id)
    
    finally:
        # Cleanup
        if session_id:
            await realtime_processor.stop_processing(session_id)
        
        # Cancel background tasks
        if 'transcription_task' in locals():
            transcription_task.cancel()
        if 'emotion_task' in locals():
            emotion_task.cancel()
        
        manager.disconnect(connection_id)


async def stream_transcription_data(websocket: WebSocket, session_id: str, file_id: str):
    """Stream transcription data to WebSocket."""
    try:
        # This would normally get the audio path from file storage
        audio_path = f"/tmp/audio_{file_id}.wav"
        
        # Temporarily send mock transcript data to test WebSocket connection
        logger.info(f"Starting mock transcript streaming for {file_id}")
        for i in range(5):
            try:
                mock_data = {
                    "type": "transcript",
                    "file_id": file_id,
                    "session_id": session_id,
                    "text": f"نص تجريبي للترجمة الفورية - الجزء {i+1}",
                    "timestamp": datetime.now().isoformat(),
                    "start_time": i * 2.0,
                    "end_time": (i + 1) * 2.0,
                    "confidence": 0.9,
                    "is_final": True
                }
                logger.info(f"Sending transcript data: {mock_data}")
                await websocket.send_text(json.dumps(mock_data))
                await asyncio.sleep(2)  # Send every 2 seconds
            except Exception as e:
                logger.error(f"Error sending transcript data: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in transcription streaming: {e}")


async def stream_emotion_data(websocket: WebSocket, session_id: str, file_id: str):
    """Stream emotion analysis data to WebSocket."""
    try:
        # This would normally get the audio path from file storage
        audio_path = f"/tmp/audio_{file_id}.wav"
        
        # Temporarily send mock emotion data to test WebSocket connection
        logger.info(f"Starting mock emotion streaming for {file_id}")
        emotions = ["joy", "neutral", "anger", "sadness", "surprise"]
        for i in range(5):
            try:
                mock_data = {
                    "type": "emotion",
                    "file_id": file_id,
                    "session_id": session_id,
                    "emotion_type": emotions[i % len(emotions)],
                    "intensity": "medium",
                    "confidence": 0.8,
                    "timestamp": datetime.now().isoformat(),
                    "start_time": i * 2.0,
                    "end_time": (i + 1) * 2.0
                }
                logger.info(f"Sending emotion data: {mock_data}")
                await websocket.send_text(json.dumps(mock_data))
                await asyncio.sleep(2)  # Send every 2 seconds
            except Exception as e:
                logger.error(f"Error sending emotion data: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in emotion streaming: {e}")


async def handle_websocket_message(websocket: WebSocket, session_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    try:
        message_type = message.get("type")
        
        if message_type == "playback_update":
            # Handle playback state updates
            current_time = message.get("current_time", 0.0)
            status = message.get("status", "stopped")
            is_seeking = message.get("is_seeking", False)
            
            # Convert status string to enum
            playback_status = PlaybackStatus.STOPPED
            if status == "playing":
                playback_status = PlaybackStatus.PLAYING
            elif status == "paused":
                playback_status = PlaybackStatus.PAUSED
            
            # Update playback state
            playback_state = await realtime_processor.update_playback_state(
                session_id, current_time, playback_status, is_seeking
            )
            
            # Send updated state back
            await manager.send_personal_message({
                "type": "playback_state",
                "data": playback_state.dict(),
                "timestamp": datetime.now().isoformat()
            }, session_id)
        
        elif message_type == "pause":
            # Pause processing
            await realtime_processor.pause_processing(session_id)
            await manager.send_personal_message({
                "type": "status",
                "message": "Processing paused",
                "timestamp": datetime.now().isoformat()
            }, session_id)
        
        elif message_type == "resume":
            # Resume processing
            await realtime_processor.resume_processing(session_id)
            await manager.send_personal_message({
                "type": "status",
                "message": "Processing resumed",
                "timestamp": datetime.now().isoformat()
            }, session_id)
        
        elif message_type == "seek":
            # Handle seeking
            seek_time = message.get("time", 0.0)
            # Update playback state with seek time
            playback_state = await realtime_processor.update_playback_state(
                session_id, seek_time, PlaybackStatus.PLAYING, is_seeking=True
            )
            
            await manager.send_personal_message({
                "type": "seek_complete",
                "data": playback_state.dict(),
                "timestamp": datetime.now().isoformat()
            }, session_id)
        
        else:
            # Unknown message type
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, session_id)
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Error handling message: {str(e)}"
        }, session_id)


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a real-time processing session."""
    try:
        status = realtime_processor.get_session_status(session_id)
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/active")
async def get_active_sessions():
    """Get list of active processing sessions."""
    try:
        active_sessions = realtime_processor.get_active_sessions()
        return {
            "active_sessions": active_sessions,
            "count": len(active_sessions),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause a processing session."""
    try:
        success = await realtime_processor.pause_processing(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "message": "Session paused successfully",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error pausing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume a processing session."""
    try:
        success = await realtime_processor.resume_processing(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "message": "Session resumed successfully",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error resuming session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def stop_session(session_id: str):
    """Stop a processing session."""
    try:
        success = await realtime_processor.stop_processing(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "message": "Session stopped successfully",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
