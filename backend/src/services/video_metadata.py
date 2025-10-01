"""
Video metadata service for extracting video information and generating thumbnails.
"""
import os
import tempfile
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import ffmpeg
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class VideoMetadataService:
    """Service for extracting video metadata and generating thumbnails."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the video metadata service.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
        self.thumbnail_formats = ['.jpg', '.jpeg', '.png']
        
    async def extract_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict: Video metadata including duration, resolution, format, etc.
        """
        try:
            logger.info(f"Extracting metadata from video: {video_path}")
            
            # Check if file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Get basic file information
            file_info = self._get_file_info(video_path)
            
            # Get video stream information
            video_info = await self._get_video_stream_info(video_path)
            
            # Get audio stream information
            audio_info = await self._get_audio_stream_info(video_path)
            
            # Combine all metadata
            metadata = {
                **file_info,
                **video_info,
                **audio_info,
                "extracted_at": datetime.now().isoformat(),
                "metadata_version": "1.0"
            }
            
            logger.info(f"Metadata extracted successfully: {metadata['duration']:.2f}s, {metadata['width']}x{metadata['height']}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            raise
    
    def _get_file_info(self, video_path: str) -> Dict[str, Any]:
        """Get basic file information."""
        try:
            file_path = Path(video_path)
            stat = file_path.stat()
            
            return {
                "filename": file_path.name,
                "file_extension": file_path.suffix.lower(),
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    async def _get_video_stream_info(self, video_path: str) -> Dict[str, Any]:
        """Get video stream information using ffmpeg."""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                return {"has_video": False}
            
            # Extract video properties
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            duration = float(video_stream.get('duration', 0))
            fps = eval(video_stream.get('r_frame_rate', '0/1'))  # Convert fraction to float
            bitrate = int(video_stream.get('bit_rate', 0))
            codec = video_stream.get('codec_name', 'unknown')
            
            # Calculate aspect ratio
            aspect_ratio = round(width / height, 2) if height > 0 else 0
            
            # Determine quality level
            quality = self._determine_video_quality(width, height, bitrate)
            
            return {
                "has_video": True,
                "width": width,
                "height": height,
                "duration": duration,
                "fps": fps,
                "bitrate": bitrate,
                "bitrate_mbps": round(bitrate / (1024 * 1024), 2) if bitrate > 0 else 0,
                "codec": codec,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "pixel_format": video_stream.get('pix_fmt', 'unknown'),
                "profile": video_stream.get('profile', 'unknown'),
                "level": video_stream.get('level', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting video stream info: {e}")
            return {"has_video": False, "error": str(e)}
    
    async def _get_audio_stream_info(self, video_path: str) -> Dict[str, Any]:
        """Get audio stream information using ffmpeg."""
        try:
            probe = ffmpeg.probe(video_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                return {"has_audio": False}
            
            # Extract audio properties
            sample_rate = int(audio_stream.get('sample_rate', 0))
            channels = int(audio_stream.get('channels', 0))
            bitrate = int(audio_stream.get('bit_rate', 0))
            codec = audio_stream.get('codec_name', 'unknown')
            
            return {
                "has_audio": True,
                "sample_rate": sample_rate,
                "channels": channels,
                "bitrate": bitrate,
                "bitrate_kbps": round(bitrate / 1024, 2) if bitrate > 0 else 0,
                "codec": codec,
                "channel_layout": audio_stream.get('channel_layout', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting audio stream info: {e}")
            return {"has_audio": False, "error": str(e)}
    
    def _determine_video_quality(self, width: int, height: int, bitrate: int) -> str:
        """Determine video quality based on resolution and bitrate."""
        if width >= 3840 and height >= 2160:
            return "4K"
        elif width >= 1920 and height >= 1080:
            if bitrate > 5000000:  # 5 Mbps
                return "1080p_high"
            else:
                return "1080p"
        elif width >= 1280 and height >= 720:
            if bitrate > 3000000:  # 3 Mbps
                return "720p_high"
            else:
                return "720p"
        elif width >= 854 and height >= 480:
            return "480p"
        elif width >= 640 and height >= 360:
            return "360p"
        else:
            return "low"
    
    async def generate_thumbnail(
        self, 
        video_path: str, 
        timestamp: float = 0.0,
        width: int = 320,
        height: int = 240,
        format: str = 'jpg'
    ) -> str:
        """
        Generate a thumbnail from a video at a specific timestamp.
        
        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to capture thumbnail
            width: Thumbnail width
            height: Thumbnail height
            format: Output format (jpg, png)
            
        Returns:
            str: Path to the generated thumbnail
        """
        try:
            logger.info(f"Generating thumbnail at {timestamp}s for video: {video_path}")
            
            # Generate unique filename
            thumbnail_id = str(uuid.uuid4())
            thumbnail_filename = f"thumbnail_{thumbnail_id}.{format}"
            thumbnail_path = os.path.join(self.temp_dir, thumbnail_filename)
            
            # Generate thumbnail using ffmpeg
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output(thumbnail_path, vframes=1, s=f"{width}x{height}")
                .overwrite_output()
                .run(quiet=True)
            )
            
            if not os.path.exists(thumbnail_path):
                raise RuntimeError("Thumbnail generation failed")
            
            logger.info(f"Thumbnail generated: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise
    
    async def generate_thumbnails(
        self, 
        video_path: str, 
        count: int = 5,
        width: int = 320,
        height: int = 240,
        format: str = 'jpg'
    ) -> List[str]:
        """
        Generate multiple thumbnails from a video at evenly spaced intervals.
        
        Args:
            video_path: Path to the video file
            count: Number of thumbnails to generate
            width: Thumbnail width
            height: Thumbnail height
            format: Output format (jpg, png)
            
        Returns:
            List[str]: Paths to the generated thumbnails
        """
        try:
            logger.info(f"Generating {count} thumbnails for video: {video_path}")
            
            # Get video duration
            metadata = await self.extract_metadata(video_path)
            duration = metadata.get('duration', 0)
            
            if duration <= 0:
                raise ValueError("Cannot determine video duration")
            
            # Calculate timestamps
            interval = duration / (count + 1)  # Avoid 0 and end
            timestamps = [interval * (i + 1) for i in range(count)]
            
            # Generate thumbnails
            thumbnail_paths = []
            for i, timestamp in enumerate(timestamps):
                thumbnail_path = await self.generate_thumbnail(
                    video_path, timestamp, width, height, format
                )
                thumbnail_paths.append(thumbnail_path)
            
            logger.info(f"Generated {len(thumbnail_paths)} thumbnails")
            return thumbnail_paths
            
        except Exception as e:
            logger.error(f"Error generating thumbnails: {e}")
            raise
    
    async def validate_video(self, video_path: str) -> Dict[str, Any]:
        """
        Validate a video file and check for issues.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict: Validation results
        """
        try:
            logger.info(f"Validating video: {video_path}")
            
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Check file existence
            if not os.path.exists(video_path):
                validation_result["is_valid"] = False
                validation_result["errors"].append("File does not exist")
                return validation_result
            
            # Check file extension
            file_ext = Path(video_path).suffix.lower()
            if file_ext not in self.supported_formats:
                validation_result["warnings"].append(f"Unsupported format: {file_ext}")
                validation_result["recommendations"].append(f"Consider converting to MP4 format")
            
            # Extract metadata to check for issues
            try:
                metadata = await self.extract_metadata(video_path)
                
                # Check video properties
                if not metadata.get('has_video', False):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append("No video stream found")
                
                if not metadata.get('has_audio', False):
                    validation_result["warnings"].append("No audio stream found")
                
                # Check duration
                duration = metadata.get('duration', 0)
                if duration <= 0:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append("Invalid or zero duration")
                elif duration > 3600:  # 1 hour
                    validation_result["warnings"].append("Very long video (>1 hour)")
                
                # Check resolution
                width = metadata.get('width', 0)
                height = metadata.get('height', 0)
                if width < 320 or height < 240:
                    validation_result["warnings"].append("Low resolution video")
                    validation_result["recommendations"].append("Consider using higher resolution for better quality")
                
                # Check file size
                file_size_mb = metadata.get('file_size_mb', 0)
                if file_size_mb > 500:  # 500 MB
                    validation_result["warnings"].append("Large file size")
                    validation_result["recommendations"].append("Consider compressing the video")
                
            except Exception as e:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Failed to extract metadata: {str(e)}")
            
            logger.info(f"Video validation completed: {'valid' if validation_result['is_valid'] else 'invalid'}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "recommendations": []
            }
    
    def cleanup_thumbnails(self, thumbnail_paths: List[str]):
        """
        Clean up generated thumbnail files.
        
        Args:
            thumbnail_paths: List of thumbnail file paths
        """
        try:
            for thumbnail_path in thumbnail_paths:
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                    logger.debug(f"Cleaned up thumbnail: {thumbnail_path}")
        except Exception as e:
            logger.error(f"Error cleaning up thumbnails: {e}")


# Global instance
video_metadata_service = VideoMetadataService()
