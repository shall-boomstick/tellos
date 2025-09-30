"""
Shared application state.
This module contains shared data structures that need to be accessed
by multiple modules without creating circular imports.
"""

from typing import Dict
from ..models.audio_file import AudioFile

# Global storage for uploaded files
# In production, this should be replaced with a proper database
uploaded_files: Dict[str, AudioFile] = {}
