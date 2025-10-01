"""
Video streaming endpoints for serving video files with range request support.
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
from pathlib import Path
import mimetypes
from datetime import datetime

from ..services.video_metadata import video_metadata_service
from ..services.file_manager import file_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video"])

# Configuration
VIDEO_STORAGE_PATH = "/tmp/videos"  # This should come from environment config
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']


def get_video_path(file_id: str) -> str:
    """
    Get the file path for a video file.
    
    Args:
        file_id: File identifier
        
    Returns:
        str: Full path to the video file
    """
    # Use FileManager to get the actual file path
    file_path = file_manager.get_file_path(file_id)
    if file_path and os.path.exists(file_path):
        return file_path
    
    # Fallback to old method if file not found in FileManager
    fallback_path = os.path.join(VIDEO_STORAGE_PATH, f"{file_id}.mp4")
    if os.path.exists(fallback_path):
        return fallback_path
    
    # If neither exists, return the FileManager path for error handling
    return file_path or fallback_path


def validate_video_file(file_path: str) -> bool:
    """
    Validate that a video file exists and is accessible.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            return False
        
        if not os.path.isfile(file_path):
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.warning(f"Video file is empty: {file_path}")
            return False
            
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"Video file too large: {file_size} bytes")
            return False
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            logger.warning(f"Unsupported video format: {file_ext}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating video file: {e}")
        return False


@router.get("/stream/{file_id}")
@router.head("/stream/{file_id}")
async def stream_video(file_id: str, request: Request):
    """
    Stream a video file with range request support.
    
    Args:
        file_id: File identifier
        request: HTTP request object
        
    Returns:
        StreamingResponse: Video stream with range support
    """
    try:
        # Get video file path
        video_path = get_video_path(file_id)
        
        # Validate file
        if not validate_video_file(video_path):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
        
        # Get file info
        file_size = os.path.getsize(video_path)
        file_name = Path(video_path).name
        
        # Get content type
        content_type, _ = mimetypes.guess_type(video_path)
        if not content_type or not content_type.startswith('video/'):
            content_type = "video/mp4"  # Default fallback
        
        # Handle HEAD requests
        if request.method == "HEAD":
            headers = {
                'Accept-Ranges': 'bytes',
                'Content-Length': str(file_size),
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=3600',
                'Content-Disposition': f'inline; filename="{file_name}"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Range, Content-Type, Accept',
                'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges',
                'X-Content-Type-Options': 'nosniff'
            }
            return Response(status_code=200, headers=headers)
        
        # Check for range request
        range_header = request.headers.get('Range')
        
        if range_header:
            # Parse range header
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # Ensure end is within file bounds
            end = min(end, file_size - 1)
            
            # Calculate content length
            content_length = end - start + 1
            
            # Create range response
            def iter_range():
                with open(video_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            response = StreamingResponse(
                iter_range(),
                status_code=206,  # Partial Content
                media_type=content_type,
                headers={
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(content_length),
                    'Cache-Control': 'public, max-age=3600',
                    'Content-Disposition': f'inline; filename="{file_name}"',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Range, Content-Type',
                    'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges'
                }
            )
            
            logger.info(f"Streaming video range {start}-{end} for file {file_id}")
            return response
        
        else:
            # Full file response
            def iter_file():
                with open(video_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            
            response = StreamingResponse(
                iter_file(),
                media_type=content_type,
                headers={
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(file_size),
                    'Cache-Control': 'public, max-age=3600',
                    'Content-Disposition': f'inline; filename="{file_name}"',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Range, Content-Type',
                    'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges'
                }
            )
            
            logger.info(f"Streaming full video for file {file_id}")
            return response
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"Error streaming video {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Error streaming video")


@router.get("/debug/{file_id}")
async def debug_video(file_id: str):
    """
    Debug endpoint to check video file details and browser compatibility.
    """
    try:
        video_path = get_video_path(file_id)
        
        if not validate_video_file(video_path):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
        
        # Get detailed video information using ffprobe
        import subprocess
        import json
        
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Could not analyze video file")
        
        probe_data = json.loads(result.stdout)
        video_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video'), None)
        audio_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'audio'), None)
        
        # Check browser compatibility
        browser_compatible = False
        if video_stream:
            codec = video_stream.get('codec_name', '').lower()
            profile = video_stream.get('profile', '').lower()
            pix_fmt = video_stream.get('pix_fmt', '').lower()
            
            browser_compatible = (
                codec == 'h264' and 
                ('baseline' in profile or 'constrained baseline' in profile or 'main' in profile) and 
                pix_fmt == 'yuv420p'
            )
        
        return {
            "file_id": file_id,
            "file_path": video_path,
            "file_size": os.path.getsize(video_path),
            "browser_compatible": browser_compatible,
            "video_stream": video_stream,
            "audio_stream": audio_stream,
            "format_info": probe_data.get('format', {}),
            "stream_url": f"/video/stream/{file_id}",
            "recommendations": {
                "direct_url": f"http://100.93.116.1:8000/video/stream/{file_id}",
                "test_page": "http://100.93.116.1:8081/test_video_playback.html"
            }
        }
        
    except Exception as e:
        logger.error(f"Error debugging video {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error debugging video: {str(e)}")


@router.get("/info/{file_id}")
async def get_video_info(file_id: str):
    """
    Get video file information and metadata.
    
    Args:
        file_id: File identifier
        
    Returns:
        Dict: Video metadata and information
    """
    try:
        # Get video file path
        video_path = get_video_path(file_id)
        
        # Validate file
        if not validate_video_file(video_path):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
        
        # Extract metadata
        metadata = await video_metadata_service.extract_metadata(video_path)
        
        # Add streaming information
        streaming_info = {
            "stream_url": f"/video/stream/{file_id}",
            "supports_range_requests": True,
            "max_file_size": MAX_FILE_SIZE,
            "supported_formats": SUPPORTED_FORMATS
        }
        
        return {
            "file_id": file_id,
            "metadata": metadata,
            "streaming": streaming_info,
            "timestamp": datetime.now().isoformat()
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"Error getting video info for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting video information")


@router.get("/thumbnail/{file_id}")
async def get_video_thumbnail(
    file_id: str, 
    timestamp: float = 0.0,
    width: int = 320,
    height: int = 240,
    format: str = 'jpg'
):
    """
    Get a thumbnail from a video at a specific timestamp.
    
    Args:
        file_id: File identifier
        timestamp: Time in seconds to capture thumbnail
        width: Thumbnail width
        height: Thumbnail height
        format: Output format (jpg, png)
        
    Returns:
        Response: Thumbnail image
    """
    try:
        # Get video file path
        video_path = get_video_path(file_id)
        
        # Validate file
        if not validate_video_file(video_path):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
        
        # Generate thumbnail
        thumbnail_path = await video_metadata_service.generate_thumbnail(
            video_path, timestamp, width, height, format
        )
        
        # Read thumbnail file
        with open(thumbnail_path, 'rb') as f:
            thumbnail_data = f.read()
        
        # Clean up temporary file
        os.remove(thumbnail_path)
        
        # Determine content type
        content_type = f"image/{format}"
        
        return Response(
            content=thumbnail_data,
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Content-Disposition': f'inline; filename="thumbnail_{file_id}.{format}"'
            }
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"Error generating thumbnail for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Error generating thumbnail")


@router.get("/thumbnails/{file_id}")
async def get_video_thumbnails(
    file_id: str,
    count: int = 5,
    width: int = 320,
    height: int = 240,
    format: str = 'jpg'
):
    """
    Get multiple thumbnails from a video at evenly spaced intervals.
    
    Args:
        file_id: File identifier
        count: Number of thumbnails to generate
        width: Thumbnail width
        height: Thumbnail height
        format: Output format (jpg, png)
        
    Returns:
        Dict: Information about generated thumbnails
    """
    try:
        # Get video file path
        video_path = get_video_path(file_id)
        
        # Validate file
        if not validate_video_file(video_path):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
        
        # Generate thumbnails
        thumbnail_paths = await video_metadata_service.generate_thumbnails(
            video_path, count, width, height, format
        )
        
        # Create thumbnail URLs
        thumbnail_urls = [
            f"/video/thumbnail/{file_id}?timestamp={i * (await video_metadata_service.extract_metadata(video_path))['duration'] / (count + 1)}&width={width}&height={height}&format={format}"
            for i in range(1, count + 1)
        ]
        
        return {
            "file_id": file_id,
            "thumbnail_count": len(thumbnail_paths),
            "thumbnail_urls": thumbnail_urls,
            "width": width,
            "height": height,
            "format": format,
            "timestamp": datetime.now().isoformat()
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        logger.error(f"Error generating thumbnails for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Error generating thumbnails")


@router.get("/validate/{file_id}")
async def validate_video(file_id: str):
    """
    Validate a video file and check for issues.
    
    Args:
        file_id: File identifier
        
    Returns:
        Dict: Validation results
    """
    try:
        # Get video file path
        video_path = get_video_path(file_id)
        
        # Validate file
        validation_result = await video_metadata_service.validate_video(video_path)
        
        return {
            "file_id": file_id,
            "validation": validation_result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error validating video {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Error validating video")


@router.get("/health")
async def health_check():
    """Health check endpoint for video streaming service."""
    return {
        "status": "healthy",
        "service": "video_streaming",
        "timestamp": datetime.now().isoformat(),
        "supported_formats": SUPPORTED_FORMATS,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
    }
