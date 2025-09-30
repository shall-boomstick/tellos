"""
Upload API endpoints for SawtFeel application.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import shutil
from datetime import datetime, timedelta
import uuid

from ..models.audio_file import AudioFile, ProcessingStatus, FileType
from ..services.video_utils import detect_file_format, validate_file_constraints
from ..services.processing_pipeline import processing_pipeline
from ..services.file_manager import file_manager

router = APIRouter()

# Temporary storage for uploaded files
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import shared state for uploaded files
from ..shared.state import uploaded_files

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload audio/video file for processing.
    """
    try:
        # Validate file format
        file_type, file_format = detect_file_format(file.filename)
        
        # Read file content
        file_content = await file.read()
        
        # Validate file constraints (check content size first)
        if len(file_content) > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError("File too large (max 100MB)")
        
        # Generate file ID and store file using FileManager
        file_id = str(uuid.uuid4())
        file_path = await file_manager.store_uploaded_file(
            file_content, 
            file.filename, 
            file_id
        )
        
        # Validate file constraints
        validate_file_constraints(file_path)
        
        # Create AudioFile record
        audio_file = AudioFile(
            id=file_id,
            filename=file.filename,
            file_type=FileType.VIDEO if file_type == "video" else FileType.AUDIO,
            format=file_format,
            file_size=len(file_content),
            file_path=file_path,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        # Store in memory (for backward compatibility)
        uploaded_files[file_id] = audio_file
        
        # Start processing in background
        try:
            print(f"DEBUG: Starting processing task for file {file_id}")
            await processing_pipeline.start_processing_task(audio_file)
            print(f"DEBUG: Processing task started successfully for file {file_id}")
        except Exception as e:
            print(f"DEBUG: Error starting processing task for file {file_id}: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "file_id": file_id,
            "status": audio_file.processing_status,
            "message": "File uploaded successfully and processing started"
        }
        
    except ValueError as e:
        # Clean up file if it was created
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        if "Unsupported file format" in str(e):
            return JSONResponse(
                status_code=415,
                content={
                    "error": str(e),
                    "supported_formats": ["MP3", "WAV", "MP4", "AVI", "MOV", "MKV", "WebM", "FLV"]
                }
            )
        elif "too large" in str(e) or "too long" in str(e):
            return JSONResponse(
                status_code=413,
                content={
                    "error": str(e),
                    "max_size": 100 * 1024 * 1024  # 100MB
                }
            )
        else:
            return JSONResponse(status_code=400, content={"error": str(e)})
            
    except Exception as e:
        # Clean up file if it was created
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return JSONResponse(status_code=500, content={"error": "Upload failed"})

@router.get("/upload/{file_id}/status")
async def get_upload_status(file_id: str) -> Dict[str, Any]:
    """
    Get processing status of uploaded file.
    """
    # First check if file exists in memory
    if file_id in uploaded_files:
        audio_file = uploaded_files[file_id]
        
        # Get current processing status from pipeline
        status_data = await processing_pipeline.get_processing_status(file_id)
        
        if status_data:
            return {
                "file_id": file_id,
                "status": status_data["status"],
                "progress": status_data.get("progress", 0),
                "message": f"File is {status_data['status']}",
                "timestamp": status_data.get("timestamp", datetime.now().isoformat()),
                "is_processing": processing_pipeline.is_processing(file_id)
            }
        
        # Fallback to audio file status
        progress_map = {
            ProcessingStatus.UPLOADED: 10,
            ProcessingStatus.EXTRACTING_AUDIO: 30,
            ProcessingStatus.TRANSCRIBING: 60,
            ProcessingStatus.ANALYZING: 90,
            ProcessingStatus.COMPLETED: 100,
            ProcessingStatus.FAILED: 0
        }
        
        return {
            "file_id": file_id,
            "status": audio_file.processing_status,
            "progress": progress_map.get(audio_file.processing_status, 0),
            "message": f"File is {audio_file.processing_status}",
            "timestamp": datetime.now().isoformat(),
            "is_processing": processing_pipeline.is_processing(file_id)
        }
    
    # If not in memory, check if file exists on disk and has cached data
    file_path = file_manager.get_file_path(file_id)
    if file_path and os.path.exists(file_path):
        # Try to get processing status from cache
        status_data = await processing_pipeline.get_processing_status(file_id)
        
        if status_data:
            return {
                "file_id": file_id,
                "status": status_data["status"],
                "progress": status_data.get("progress", 0),
                "message": f"File is {status_data['status']}",
                "timestamp": status_data.get("timestamp", datetime.now().isoformat()),
                "is_processing": processing_pipeline.is_processing(file_id)
            }
        else:
            # File exists but no processing data - assume completed
            return {
                "file_id": file_id,
                "status": "completed",
                "progress": 100,
                "message": "File processing completed",
                "timestamp": datetime.now().isoformat(),
                "is_processing": False
            }
    
    # File not found anywhere
    return JSONResponse(
        status_code=404,
        content={"error": "File not found"}
    )
