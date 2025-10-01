"""
Video format detection and audio extraction utilities.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import ffmpeg
from moviepy.editor import VideoFileClip

# Supported video formats as per constitution
SUPPORTED_VIDEO_FORMATS = {
    '.mp4': 'MP4',
    '.avi': 'AVI', 
    '.mov': 'MOV',
    '.mkv': 'MKV',
    '.webm': 'WebM',
    '.flv': 'FLV'
}

SUPPORTED_AUDIO_FORMATS = {
    '.mp3': 'MP3',
    '.wav': 'WAV',
    '.flac': 'FLAC',
    '.aac': 'AAC',
    '.ogg': 'OGG'
}

def detect_file_format(file_path: str) -> Tuple[str, str]:
    """
    Detect file format and type (video/audio).
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (file_type, format) where file_type is 'video' or 'audio'
    """
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext in SUPPORTED_VIDEO_FORMATS:
        return ('video', SUPPORTED_VIDEO_FORMATS[file_ext])
    elif file_ext in SUPPORTED_AUDIO_FORMATS:
        return ('audio', SUPPORTED_AUDIO_FORMATS[file_ext])
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def get_video_info(file_path: str) -> Dict:
    """
    Get video file information using ffmpeg.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with video information
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'audio'), None)
        
        info = {
            'duration': float(probe['format']['duration']),
            'size': int(probe['format']['size']),
            'format': probe['format']['format_name'],
            'has_video': video_stream is not None,
            'has_audio': audio_stream is not None
        }
        
        if video_stream:
            info.update({
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate'])
            })
            
        if audio_stream:
            info.update({
                'audio_codec': audio_stream['codec_name'],
                'sample_rate': int(audio_stream['sample_rate']),
                'channels': int(audio_stream['channels'])
            })
            
        return info
    except Exception as e:
        raise RuntimeError(f"Failed to get video info: {str(e)}")

def extract_audio_from_video(video_path: str, output_path: str) -> str:
    """
    Extract audio from video file using ffmpeg.
    
    Args:
        video_path: Path to input video file
        output_path: Path for output audio file
        
    Returns:
        Path to extracted audio file
    """
    try:
        # Use ffmpeg to extract audio optimized for Arabic speech recognition
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path, 
                acodec='pcm_s16le',  # 16-bit PCM
                ac=1,                # Mono for speech recognition
                ar=16000,            # Standard sample rate for Whisper
                af='highpass=f=200,lowpass=f=3400,volume=1.5'  # Simple and reliable audio processing for speech
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        if not os.path.exists(output_path):
            raise RuntimeError("Audio extraction failed - output file not created")
            
        return output_path
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg error during audio extraction: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract audio: {str(e)}")

def validate_file_constraints(file_path: str, max_duration: int = 120, 
                             max_size: int = 100 * 1024 * 1024) -> None:
    """
    Validate file against constitutional constraints.
    
    Args:
        file_path: Path to file
        max_duration: Maximum duration in seconds (default 120)
        max_size: Maximum file size in bytes (default 100MB)
        
    Raises:
        ValueError: If file violates constraints
    """
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes (max {max_size})")
    
    # Check duration for video files
    file_type, _ = detect_file_format(file_path)
    if file_type == 'video':
        info = get_video_info(file_path)
        if info['duration'] > max_duration:
            raise ValueError(f"Video too long: {info['duration']}s (max {max_duration}s)")
