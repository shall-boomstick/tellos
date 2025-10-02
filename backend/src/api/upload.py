"""
Upload API endpoints for SawtFeel application.
"""

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import asyncio
from datetime import datetime, timedelta
import uuid

from ..models.audio_file import AudioFile, ProcessingStatus, FileType
from ..services.video_utils import detect_file_format, validate_file_constraints
from ..services.processing_pipeline import processing_pipeline
from ..services.file_manager import file_manager

# Import shared state for uploaded files
from ..shared.state import uploaded_files

router = APIRouter()

# Temporary storage for uploaded files
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload audio/video file for processing.
    """
    try:
        print(f"DEBUG: Upload request - filename: {file.filename}, content_type: {file.content_type}")
        
        # Check if filename is provided
        if not file.filename:
            raise ValueError("No filename provided")
        
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
        except Exception:
            pass

        if "Unsupported file format" in str(e):
            return JSONResponse(
                status_code=415,
                content={
                    "error": str(e),
                    "supported_formats": [
                        "MP3", "WAV", "MP4", "AVI", "MOV", "MKV", "WebM", "FLV"
                    ]
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
        except Exception:
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

@router.get("/upload/files")
async def list_uploaded_files() -> Dict[str, Any]:
    """
    List all uploaded files with their metadata.
    """
    try:
        files_list = []
        
        # Get files from memory (active sessions)
        for file_id, audio_file in uploaded_files.items():
            file_info = {
                "file_id": file_id,
                "filename": audio_file.filename,
                "file_type": audio_file.file_type.value if hasattr(audio_file.file_type, 'value') else str(audio_file.file_type),
                "file_size": audio_file.file_size,
                "upload_time": audio_file.upload_timestamp.isoformat(),
                "expires_at": audio_file.expires_at.isoformat(),
                "status": audio_file.processing_status.value if hasattr(audio_file.processing_status, 'value') else str(audio_file.processing_status),
                "progress": 0,
                "is_processing": False,
                "transcription_service": audio_file.transcription_service.value if audio_file.transcription_service and hasattr(audio_file.transcription_service, 'value') else str(audio_file.transcription_service) if audio_file.transcription_service else None
            }
            files_list.append(file_info)
        
        # Get files from disk (completed files not in memory)
        try:
            disk_files = file_manager.get_all_file_metadata()
            for file_id, metadata in disk_files.items():
                # Skip if already in memory
                if file_id in uploaded_files:
                    continue

                # Check if file still exists on disk
                if os.path.exists(metadata["stored_path"]):
                    # Determine file type
                    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
                    filename_lower = metadata["original_filename"].lower()
                    file_type = "video" if any(ext in filename_lower for ext in video_extensions) else "audio"

                    file_info = {
                        "file_id": file_id,
                        "filename": metadata["original_filename"],
                        "file_type": file_type,
                        "file_size": metadata["file_size"],
                        "upload_time": metadata["upload_time"],
                        "expires_at": metadata["expires_at"],
                        "status": "completed",
                        "progress": 100,
                        "is_processing": False,
                        "transcription_service": metadata.get("transcription_service")
                    }
                    files_list.append(file_info)
        except Exception as e:
            print(f"Error loading disk files: {e}")
            # Continue with memory files only if disk loading fails
        
        # Sort by upload time (newest first)
        files_list.sort(key=lambda x: x["upload_time"], reverse=True)
        
        return {
            "files": files_list,
            "total_count": len(files_list),
            "message": f"Found {len(files_list)} uploaded files"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to list files: {str(e)}"}
        )

@router.delete("/upload/{file_id}")
async def delete_uploaded_file(file_id: str) -> Dict[str, Any]:
    """
    Delete an uploaded file and its associated data.
    """
    try:
        deleted_items = []
        
        # Remove from memory
        if file_id in uploaded_files:
            del uploaded_files[file_id]
            deleted_items.append("memory")

        # Remove from disk
        file_path = file_manager.get_file_path(file_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            deleted_items.append("disk")

        # Remove from file manager metadata
        file_manager.remove_file_metadata(file_id)
        deleted_items.append("metadata")

        # Remove cached processing data
        await file_manager.clear_cached_data(file_id)
        deleted_items.append("cache")
        
        return {
            "file_id": file_id,
            "deleted_items": deleted_items,
            "message": f"File {file_id} deleted successfully"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to delete file: {str(e)}"}
        )
