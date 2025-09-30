"""
Redis client for session data and caching.
"""

import json
import redis
import os
from typing import Any, Optional
from datetime import timedelta

class RedisClient:
    """Redis client for session management and caching."""
    
    def __init__(self, host: str = None, port: int = 6379, db: int = 0):
        """Initialize Redis client."""
        # Use environment variable or default to Docker service name
        if host is None:
            host = os.getenv('REDIS_HOST', 'redis')
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        
    async def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return self.client.ping()
        except Exception:
            return False
    
    async def set_session_data(self, session_id: str, data: dict, 
                              expire_hours: int = 24) -> None:
        """
        Set session data with expiration.
        
        Args:
            session_id: Unique session identifier
            data: Session data to store
            expire_hours: Expiration time in hours
        """
        self.client.setex(
            f"session:{session_id}",
            timedelta(hours=expire_hours),
            json.dumps(data)
        )
    
    async def get_session_data(self, session_id: str) -> Optional[dict]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        data = self.client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session data."""
        self.client.delete(f"session:{session_id}")
    
    async def cache_processing_status(self, file_id: str, status: dict) -> None:
        """Cache file processing status."""
        self.client.setex(
            f"processing:{file_id}",
            timedelta(hours=24),
            json.dumps(status)
        )
    
    async def get_processing_status(self, file_id: str) -> Optional[dict]:
        """Get cached processing status."""
        data = self.client.get(f"processing:{file_id}")
        if data:
            return json.loads(data)
        return None
    
    async def cache_analysis_results(self, file_id: str, results: dict) -> None:
        """Cache analysis results."""
        self.client.setex(
            f"results:{file_id}",
            timedelta(hours=24),
            json.dumps(results)
        )
    
    async def get_analysis_results(self, file_id: str) -> Optional[dict]:
        """Get cached analysis results."""
        data = self.client.get(f"results:{file_id}")
        if data:
            return json.loads(data)
        return None

# Global Redis client instance
redis_client = RedisClient()
