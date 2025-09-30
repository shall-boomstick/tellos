"""
FileManager service for SawtFeel application.
Handles file storage, caching, cleanup, and lifecycle management.
"""

import os
import shutil
import tempfile
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiofiles
import json

from ..models.audio_file import AudioFile

logger = logging.getLogger(__name__)

class FileManager:
    """Service for managing uploaded files and temporary storage."""
    
    def __init__(self, 
                 upload_dir: str = "temp_uploads",
                 cache_dir: str = "cache",
                 max_file_age_hours: int = 24,
                 max_cache_size_mb: int = 1000):
        """
        Initialize FileManager.
        
        Args:
            upload_dir: Directory for uploaded files
            cache_dir: Directory for cached processed files
            max_file_age_hours: Maximum age of files before cleanup (hours)
            max_cache_size_mb: Maximum cache size in MB
        """
        self.upload_dir = Path(upload_dir)
        self.cache_dir = Path(cache_dir)
        self.max_file_age = timedelta(hours=max_file_age_hours)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # File metadata storage
        self.metadata_file = self.cache_dir / "file_metadata.json"
        self.file_metadata = self._load_metadata()
        
        logger.info(f"FileManager initialized: upload_dir={self.upload_dir}, cache_dir={self.cache_dir}")
    
    def _load_metadata(self) -> Dict:
        """Load file metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Save file metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.file_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    async def store_uploaded_file(self, file_content: bytes, filename: str, file_id: str) -> str:
        """
        Store uploaded file and return file path.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            file_id: Unique file identifier
            
        Returns:
            Path to stored file
        """
        try:
            # Generate safe filename
            safe_filename = self._generate_safe_filename(filename, file_id)
            file_path = self.upload_dir / safe_filename
            
            # Write file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(file_content)
            
            # Store metadata
            self.file_metadata[file_id] = {
                "original_filename": filename,
                "stored_path": str(file_path),
                "file_hash": file_hash,
                "upload_time": datetime.now().isoformat(),
                "file_size": len(file_content),
                "expires_at": (datetime.now() + self.max_file_age).isoformat()
            }
            self._save_metadata()
            
            logger.info(f"Stored file: {filename} -> {file_path} ({len(file_content)} bytes)")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error storing file {filename}: {e}")
            raise
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path for a given file ID."""
        metadata = self.file_metadata.get(file_id)
        if metadata:
            file_path = metadata["stored_path"]
            if os.path.exists(file_path):
                return file_path
            else:
                logger.warning(f"File not found on disk: {file_path}")
                # Clean up stale metadata
                del self.file_metadata[file_id]
                self._save_metadata()
        
        return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information for a given file ID."""
        metadata = self.file_metadata.get(file_id)
        if metadata:
            # Check if file still exists
            if os.path.exists(metadata["stored_path"]):
                return metadata.copy()
            else:
                # Clean up stale metadata
                del self.file_metadata[file_id]
                self._save_metadata()
        
        return None
    
    async def cache_processed_data(self, file_id: str, data_type: str, data: Dict) -> str:
        """
        Cache processed data (transcript, emotions, etc.).
        
        Args:
            file_id: File identifier
            data_type: Type of data (transcript, emotions, features)
            data: Data to cache
            
        Returns:
            Path to cached file
        """
        try:
            cache_filename = f"{file_id}_{data_type}.json"
            cache_path = self.cache_dir / cache_filename
            
            # Add timestamp to data
            data_with_meta = {
                "cached_at": datetime.now().isoformat(),
                "file_id": file_id,
                "data_type": data_type,
                "data": data
            }
            
            # Write cache file
            async with aiofiles.open(cache_path, 'w') as f:
                await f.write(json.dumps(data_with_meta, indent=2, default=str))
            
            logger.info(f"Cached {data_type} data for file {file_id}")
            
            return str(cache_path)
            
        except Exception as e:
            logger.error(f"Error caching data for {file_id}: {e}")
            raise
    
    async def get_cached_data(self, file_id: str, data_type: str) -> Optional[Dict]:
        """
        Retrieve cached processed data.
        
        Args:
            file_id: File identifier
            data_type: Type of data to retrieve
            
        Returns:
            Cached data or None if not found
        """
        try:
            cache_filename = f"{file_id}_{data_type}.json"
            cache_path = self.cache_dir / cache_filename
            
            if cache_path.exists():
                async with aiofiles.open(cache_path, 'r') as f:
                    content = await f.read()
                    cached_data = json.loads(content)
                
                # Check if cache is still valid (within file age limit)
                cached_at = datetime.fromisoformat(cached_data["cached_at"])
                if datetime.now() - cached_at < self.max_file_age:
                    return cached_data["data"]
                else:
                    # Cache expired, remove it
                    cache_path.unlink()
                    logger.info(f"Removed expired cache: {cache_path}")
            
        except Exception as e:
            logger.warning(f"Error retrieving cached data for {file_id}: {e}")
        
        return None
    
    def _generate_safe_filename(self, original_filename: str, file_id: str) -> str:
        """Generate safe filename for storage."""
        # Extract extension
        path = Path(original_filename)
        extension = path.suffix.lower()
        
        # Create safe filename with file ID
        safe_filename = f"{file_id}_{path.stem[:50]}{extension}"
        
        # Remove any unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        return safe_filename
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    async def cleanup_expired_files(self) -> Dict[str, int]:
        """
        Clean up expired files and return cleanup statistics.
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Starting cleanup of expired files")
        
        stats = {
            "files_removed": 0,
            "cache_files_removed": 0,
            "bytes_freed": 0,
            "errors": 0
        }
        
        current_time = datetime.now()
        expired_file_ids = []
        
        # Check uploaded files
        for file_id, metadata in self.file_metadata.items():
            try:
                expires_at = datetime.fromisoformat(metadata["expires_at"])
                if current_time > expires_at:
                    expired_file_ids.append(file_id)
            except Exception as e:
                logger.warning(f"Error parsing expiry for {file_id}: {e}")
                expired_file_ids.append(file_id)  # Remove problematic entries
        
        # Remove expired files
        for file_id in expired_file_ids:
            try:
                await self._remove_file_and_cache(file_id, stats)
            except Exception as e:
                logger.error(f"Error removing expired file {file_id}: {e}")
                stats["errors"] += 1
        
        # Clean up orphaned cache files
        await self._cleanup_orphaned_cache_files(stats)
        
        # Enforce cache size limit
        await self._enforce_cache_size_limit(stats)
        
        logger.info(f"Cleanup completed: {stats}")
        
        return stats
    
    async def _remove_file_and_cache(self, file_id: str, stats: Dict):
        """Remove file and associated cache entries."""
        metadata = self.file_metadata.get(file_id)
        
        if metadata:
            # Remove original file
            file_path = metadata["stored_path"]
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                stats["files_removed"] += 1
                stats["bytes_freed"] += file_size
                logger.info(f"Removed expired file: {file_path}")
        
        # Remove cache files
        cache_patterns = [
            f"{file_id}_transcript.json",
            f"{file_id}_emotions.json",
            f"{file_id}_features.json",
            f"{file_id}_audio.wav"
        ]
        
        for pattern in cache_patterns:
            cache_path = self.cache_dir / pattern
            if cache_path.exists():
                cache_size = cache_path.stat().st_size
                cache_path.unlink()
                stats["cache_files_removed"] += 1
                stats["bytes_freed"] += cache_size
        
        # Remove metadata
        if file_id in self.file_metadata:
            del self.file_metadata[file_id]
        
        self._save_metadata()
    
    async def _cleanup_orphaned_cache_files(self, stats: Dict):
        """Clean up cache files without corresponding metadata."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                # Extract file ID from cache filename
                filename = cache_file.stem
                if '_' in filename:
                    file_id = filename.split('_')[0]
                    
                    # Check if metadata exists
                    if file_id not in self.file_metadata:
                        cache_size = cache_file.stat().st_size
                        cache_file.unlink()
                        stats["cache_files_removed"] += 1
                        stats["bytes_freed"] += cache_size
                        logger.info(f"Removed orphaned cache file: {cache_file}")
        
        except Exception as e:
            logger.error(f"Error cleaning orphaned cache files: {e}")
            stats["errors"] += 1
    
    async def _enforce_cache_size_limit(self, stats: Dict):
        """Enforce maximum cache size by removing oldest files."""
        try:
            # Calculate current cache size
            total_size = sum(
                f.stat().st_size 
                for f in self.cache_dir.rglob('*') 
                if f.is_file()
            )
            
            if total_size <= self.max_cache_size:
                return
            
            logger.info(f"Cache size {total_size} exceeds limit {self.max_cache_size}, cleaning up")
            
            # Get all cache files with modification times
            cache_files = []
            for cache_file in self.cache_dir.rglob('*'):
                if cache_file.is_file():
                    cache_files.append((cache_file.stat().st_mtime, cache_file))
            
            # Sort by modification time (oldest first)
            cache_files.sort()
            
            # Remove oldest files until under limit
            for mtime, cache_file in cache_files:
                if total_size <= self.max_cache_size:
                    break
                
                try:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    total_size -= file_size
                    stats["cache_files_removed"] += 1
                    stats["bytes_freed"] += file_size
                    logger.info(f"Removed old cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Error removing cache file {cache_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error enforcing cache size limit: {e}")
            stats["errors"] += 1
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        try:
            # Calculate upload directory size
            upload_size = sum(
                f.stat().st_size 
                for f in self.upload_dir.rglob('*') 
                if f.is_file()
            )
            
            # Calculate cache directory size
            cache_size = sum(
                f.stat().st_size 
                for f in self.cache_dir.rglob('*') 
                if f.is_file()
            )
            
            # Count files
            upload_files = len([f for f in self.upload_dir.rglob('*') if f.is_file()])
            cache_files = len([f for f in self.cache_dir.rglob('*') if f.is_file()])
            
            # Count by file age
            current_time = datetime.now()
            recent_files = 0
            old_files = 0
            
            for file_id, metadata in self.file_metadata.items():
                try:
                    upload_time = datetime.fromisoformat(metadata["upload_time"])
                    age = current_time - upload_time
                    
                    if age < timedelta(hours=1):
                        recent_files += 1
                    elif age > timedelta(hours=12):
                        old_files += 1
                except Exception:
                    pass
            
            return {
                "upload_directory_size_mb": round(upload_size / (1024 * 1024), 2),
                "cache_directory_size_mb": round(cache_size / (1024 * 1024), 2),
                "total_size_mb": round((upload_size + cache_size) / (1024 * 1024), 2),
                "upload_file_count": upload_files,
                "cache_file_count": cache_files,
                "metadata_entries": len(self.file_metadata),
                "recent_files_count": recent_files,
                "old_files_count": old_files,
                "cache_size_limit_mb": round(self.max_cache_size / (1024 * 1024), 2)
            }
        
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}
    
    async def verify_file_integrity(self, file_id: str) -> bool:
        """Verify file integrity using stored hash."""
        try:
            metadata = self.file_metadata.get(file_id)
            if not metadata:
                return False
            
            file_path = metadata["stored_path"]
            if not os.path.exists(file_path):
                return False
            
            # Read file and calculate hash
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            current_hash = self._calculate_file_hash(content)
            stored_hash = metadata["file_hash"]
            
            return current_hash == stored_hash
            
        except Exception as e:
            logger.error(f"Error verifying file integrity for {file_id}: {e}")
            return False
    
    def schedule_cleanup_task(self, interval_hours: int = 1):
        """Schedule periodic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)  # Convert to seconds
                    await self.cleanup_expired_files()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        # Start cleanup task
        asyncio.create_task(cleanup_loop())
        logger.info(f"Scheduled cleanup task every {interval_hours} hours")

# Global file manager instance
file_manager = FileManager()
