"""
Real-time processing orchestrator for coordinating transcription and emotion analysis.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import uuid

from .streaming_transcription_service import streaming_transcription_service
from .streaming_emotion_service import streaming_emotion_service
from ..models.realtime_transcript import TranscriptUpdate
from ..models.realtime_emotion import EmotionUpdate
from ..models.playback_state import PlaybackState, PlaybackStatus, SyncStatus

logger = logging.getLogger(__name__)


class RealtimeProcessor:
    """Orchestrates real-time transcription and emotion analysis processing."""
    
    def __init__(self):
        """Initialize the real-time processor."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.sync_tolerance = 0.5  # 500ms tolerance for synchronization
        
    async def initialize(self):
        """Initialize the processing services."""
        try:
            logger.info("Initializing real-time processing services")
            await streaming_transcription_service.initialize()
            await streaming_emotion_service.initialize()
            logger.info("Real-time processing services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize real-time processing services: {e}")
            raise
    
    async def start_processing(
        self, 
        file_id: str, 
        audio_path: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Start real-time processing for a file.
        
        Args:
            file_id: Unique file identifier
            audio_path: Path to the audio file
            session_id: Optional session identifier (generated if not provided)
            
        Returns:
            str: Session identifier for this processing session
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting real-time processing for file {file_id} (session: {session_id})")
            
            # Initialize session
            self.active_sessions[session_id] = {
                "file_id": file_id,
                "audio_path": audio_path,
                "started_at": datetime.now(),
                "is_active": True,
                "transcription_active": False,
                "emotion_active": False,
                "playback_state": PlaybackState(
                    file_id=file_id,
                    session_id=session_id,
                    current_time=0.0,
                    duration=0.0,
                    status=PlaybackStatus.STOPPED
                )
            }
            
            # Start both transcription and emotion analysis
            transcription_task = asyncio.create_task(
                self._run_transcription(session_id, file_id, audio_path)
            )
            emotion_task = asyncio.create_task(
                self._run_emotion_analysis(session_id, file_id, audio_path)
            )
            
            # Store tasks for cleanup
            self.active_sessions[session_id]["transcription_task"] = transcription_task
            self.active_sessions[session_id]["emotion_task"] = emotion_task
            
            logger.info(f"Real-time processing started for session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting real-time processing: {e}")
            raise
    
    async def _run_transcription(self, session_id: str, file_id: str, audio_path: str):
        """Run transcription processing for a session."""
        try:
            self.active_sessions[session_id]["transcription_active"] = True
            
            async for transcript_update in streaming_transcription_service.start_streaming(
                file_id, session_id, audio_path
            ):
                if not self.active_sessions.get(session_id, {}).get("is_active", False):
                    break
                
                # Process the transcript update
                await self._process_transcript_update(session_id, transcript_update)
                
        except Exception as e:
            logger.error(f"Error in transcription processing for session {session_id}: {e}")
        finally:
            self.active_sessions[session_id]["transcription_active"] = False
    
    async def _run_emotion_analysis(self, session_id: str, file_id: str, audio_path: str):
        """Run emotion analysis processing for a session."""
        try:
            self.active_sessions[session_id]["emotion_active"] = True
            
            async for emotion_update in streaming_emotion_service.start_streaming(
                file_id, session_id, audio_path
            ):
                if not self.active_sessions.get(session_id, {}).get("is_active", False):
                    break
                
                # Process the emotion update
                await self._process_emotion_update(session_id, emotion_update)
                
        except Exception as e:
            logger.error(f"Error in emotion analysis processing for session {session_id}: {e}")
        finally:
            self.active_sessions[session_id]["emotion_active"] = False
    
    async def _process_transcript_update(self, session_id: str, transcript_update: TranscriptUpdate):
        """Process a transcript update and update playback state."""
        try:
            if session_id not in self.active_sessions:
                return
            
            session = self.active_sessions[session_id]
            playback_state = session["playback_state"]
            
            # Update playback state with transcript timing
            transcript = transcript_update.transcript
            playback_state.current_time = transcript.end_time
            playback_state.duration = max(playback_state.duration, transcript.end_time)
            
            # Update sync status
            playback_state.transcript_sync = True
            playback_state.last_sync_time = datetime.now()
            
            logger.debug(f"Processed transcript update for session {session_id}: {transcript.text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing transcript update: {e}")
    
    async def _process_emotion_update(self, session_id: str, emotion_update: EmotionUpdate):
        """Process an emotion update and update playback state."""
        try:
            if session_id not in self.active_sessions:
                return
            
            session = self.active_sessions[session_id]
            playback_state = session["playback_state"]
            
            # Update playback state with emotion timing
            emotion = emotion_update.emotion
            playback_state.current_time = emotion.end_time
            playback_state.duration = max(playback_state.duration, emotion.end_time)
            
            # Update sync status
            playback_state.emotion_sync = True
            playback_state.last_sync_time = datetime.now()
            
            logger.debug(f"Processed emotion update for session {session_id}: {emotion.emotion_type}")
            
        except Exception as e:
            logger.error(f"Error processing emotion update: {e}")
    
    async def update_playback_state(
        self, 
        session_id: str, 
        current_time: float,
        status: PlaybackStatus,
        is_seeking: bool = False
    ) -> PlaybackState:
        """
        Update playback state and check synchronization.
        
        Args:
            session_id: Session identifier
            current_time: Current playback time
            status: Playback status
            is_seeking: Whether the user is seeking
            
        Returns:
            PlaybackState: Updated playback state
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            playback_state = session["playback_state"]
            
            # Update playback state
            playback_state.current_time = current_time
            playback_state.status = status
            playback_state.is_playing = status == PlaybackStatus.PLAYING
            playback_state.is_paused = status == PlaybackStatus.PAUSED
            playback_state.is_seeking = is_seeking
            
            # Check synchronization
            await self._check_synchronization(session_id, playback_state)
            
            return playback_state
            
        except Exception as e:
            logger.error(f"Error updating playback state: {e}")
            raise
    
    async def _check_synchronization(self, session_id: str, playback_state: PlaybackState):
        """Check and update synchronization status."""
        try:
            current_time = playback_state.current_time
            last_sync_time = playback_state.last_sync_time
            
            if last_sync_time is None:
                playback_state.sync_status = SyncStatus.UNSYNCED
                return
            
            # Calculate time since last sync
            time_since_sync = (datetime.now() - last_sync_time).total_seconds()
            
            # Check if we're within sync tolerance
            if time_since_sync <= self.sync_tolerance:
                playback_state.sync_status = SyncStatus.SYNCED
                playback_state.sync_offset = 0.0
            else:
                playback_state.sync_status = SyncStatus.UNSYNCED
                playback_state.sync_offset = time_since_sync
                
        except Exception as e:
            logger.error(f"Error checking synchronization: {e}")
            playback_state.sync_status = SyncStatus.ERROR
    
    async def get_playback_state(self, session_id: str) -> Optional[PlaybackState]:
        """
        Get current playback state for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            PlaybackState: Current playback state or None if session not found
        """
        if session_id not in self.active_sessions:
            return None
        
        return self.active_sessions[session_id]["playback_state"]
    
    async def stop_processing(self, session_id: str) -> bool:
        """
        Stop real-time processing for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Mark session as inactive
            session["is_active"] = False
            
            # Cancel tasks
            if "transcription_task" in session:
                session["transcription_task"].cancel()
            if "emotion_task" in session:
                session["emotion_task"].cancel()
            
            # Stop streaming services
            await streaming_transcription_service.stop_streaming(session_id)
            await streaming_emotion_service.stop_streaming(session_id)
            
            # Update playback state
            playback_state = session["playback_state"]
            playback_state.status = PlaybackStatus.STOPPED
            playback_state.is_playing = False
            playback_state.is_paused = True
            
            logger.info(f"Stopped real-time processing for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping processing for session {session_id}: {e}")
            return False
    
    async def pause_processing(self, session_id: str) -> bool:
        """
        Pause real-time processing for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if paused successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            playback_state = session["playback_state"]
            
            # Update playback state
            playback_state.status = PlaybackStatus.PAUSED
            playback_state.is_playing = False
            playback_state.is_paused = True
            
            logger.info(f"Paused real-time processing for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing processing for session {session_id}: {e}")
            return False
    
    async def resume_processing(self, session_id: str) -> bool:
        """
        Resume real-time processing for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            playback_state = session["playback_state"]
            
            # Update playback state
            playback_state.status = PlaybackStatus.PLAYING
            playback_state.is_playing = True
            playback_state.is_paused = False
            
            logger.info(f"Resumed real-time processing for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming processing for session {session_id}: {e}")
            return False
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Session status information or None if session not found
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        playback_state = session["playback_state"]
        
        return {
            "session_id": session_id,
            "file_id": session["file_id"],
            "is_active": session["is_active"],
            "transcription_active": session["transcription_active"],
            "emotion_active": session["emotion_active"],
            "started_at": session["started_at"].isoformat(),
            "playback_state": {
                "current_time": playback_state.current_time,
                "duration": playback_state.duration,
                "status": playback_state.status,
                "sync_status": playback_state.sync_status,
                "transcript_sync": playback_state.transcript_sync,
                "emotion_sync": playback_state.emotion_sync
            }
        }
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List[str]: Active session IDs
        """
        return [
            session_id for session_id, session in self.active_sessions.items()
            if session.get("is_active", False)
        ]


# Create global instance
realtime_processor = RealtimeProcessor()
