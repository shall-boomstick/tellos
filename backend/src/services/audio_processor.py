"""
AudioProcessor service for SawtFeel application.
Handles video-to-audio extraction and audio feature extraction.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import librosa
import numpy as np
import ffmpeg
from datetime import datetime
import logging

from .video_utils import detect_file_format, get_video_info, extract_audio_from_video

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Service for processing audio and video files."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize AudioProcessor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.supported_sample_rates = [16000, 22050, 44100, 48000]
        self.target_sample_rate = 16000  # Optimal for speech recognition
        
    async def process_file(self, file_path: str, file_id: str) -> Dict:
        """
        Process uploaded file (video or audio) for analysis.
        
        Args:
            file_path: Path to uploaded file
            file_id: Unique file identifier
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Detect file type and format
            file_type, file_format = detect_file_format(file_path)
            
            logger.info(f"Processing {file_type} file: {file_path} (format: {file_format})")
            
            # Process based on file type
            if file_type == "video":
                return await self._process_video_file(file_path, file_id)
            elif file_type == "audio":
                return await self._process_audio_file(file_path, file_id)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    async def _process_video_file(self, video_path: str, file_id: str) -> Dict:
        """Process video file and extract audio."""
        start_time = datetime.now()
        
        # Get video information
        video_info = get_video_info(video_path)
        
        # Extract audio from video
        audio_output_path = os.path.join(
            self.temp_dir, 
            f"{file_id}_extracted.wav"
        )
        
        logger.info(f"Extracting audio from video: {video_path}")
        extracted_audio_path = extract_audio_from_video(video_path, audio_output_path)
        
        # Process the extracted audio
        audio_features = await self._extract_audio_features(extracted_audio_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "file_id": file_id,
            "file_type": "video",
            "original_path": video_path,
            "audio_path": extracted_audio_path,
            "video_info": video_info,
            "audio_features": audio_features,
            "processing_time": processing_time,
            "status": "completed"
        }
    
    async def _process_audio_file(self, audio_path: str, file_id: str) -> Dict:
        """Process audio file directly."""
        start_time = datetime.now()
        
        logger.info(f"Processing audio file: {audio_path}")
        
        # Extract audio features
        audio_features = await self._extract_audio_features(audio_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "file_id": file_id,
            "file_type": "audio",
            "original_path": audio_path,
            "audio_path": audio_path,  # Same as original for audio files
            "audio_features": audio_features,
            "processing_time": processing_time,
            "status": "completed"
        }
    
    async def _extract_audio_features(self, audio_path: str) -> Dict:
        """
        Extract audio features for emotion analysis.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with extracted features
        """
        try:
            # Load audio file with librosa
            y, sr = librosa.load(audio_path, sr=self.target_sample_rate)
            
            # Basic audio information
            duration = len(y) / sr
            
            # Extract features for emotion analysis
            features = {
                "duration": duration,
                "sample_rate": sr,
                "samples": len(y),
                "rms_energy": self._extract_rms_energy(y),
                "spectral_features": self._extract_spectral_features(y, sr),
                "temporal_features": self._extract_temporal_features(y, sr),
                "pitch_features": self._extract_pitch_features(y, sr)
            }
            
            logger.info(f"Extracted audio features: duration={duration:.2f}s, sr={sr}")
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {str(e)}")
            raise
    
    def _extract_rms_energy(self, y: np.ndarray) -> Dict:
        """Extract RMS energy features."""
        rms = librosa.feature.rms(y=y)[0]
        
        return {
            "mean": float(np.mean(rms)),
            "std": float(np.std(rms)),
            "max": float(np.max(rms)),
            "min": float(np.min(rms))
        }
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract spectral features."""
        # Spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        # Spectral bandwidth
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        
        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        return {
            "spectral_centroid": {
                "mean": float(np.mean(spectral_centroid)),
                "std": float(np.std(spectral_centroid))
            },
            "spectral_bandwidth": {
                "mean": float(np.mean(spectral_bandwidth)),
                "std": float(np.std(spectral_bandwidth))
            },
            "spectral_rolloff": {
                "mean": float(np.mean(spectral_rolloff)),
                "std": float(np.std(spectral_rolloff))
            },
            "zero_crossing_rate": {
                "mean": float(np.mean(zcr)),
                "std": float(np.std(zcr))
            }
        }
    
    def _extract_temporal_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract temporal features."""
        # Tempo and beat tracking
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Onset detection
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        
        return {
            "tempo": float(tempo),
            "beat_count": len(beats),
            "onset_count": len(onsets),
            "onset_rate": len(onsets) / (len(y) / sr) if len(y) > 0 else 0
        }
    
    def _extract_pitch_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract pitch-related features."""
        # Fundamental frequency (F0)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7')
        )
        
        # Remove NaN values
        f0_clean = f0[~np.isnan(f0)]
        
        if len(f0_clean) > 0:
            pitch_features = {
                "f0_mean": float(np.mean(f0_clean)),
                "f0_std": float(np.std(f0_clean)),
                "f0_max": float(np.max(f0_clean)),
                "f0_min": float(np.min(f0_clean)),
                "voiced_ratio": float(np.sum(voiced_flag) / len(voiced_flag))
            }
        else:
            pitch_features = {
                "f0_mean": 0.0,
                "f0_std": 0.0,
                "f0_max": 0.0,
                "f0_min": 0.0,
                "voiced_ratio": 0.0
            }
        
        return pitch_features
    
    def get_audio_segments(self, audio_path: str, segment_duration: float = 2.0) -> list:
        """
        Segment audio file for time-based analysis.
        
        Args:
            audio_path: Path to audio file
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of audio segments with timestamps
        """
        try:
            y, sr = librosa.load(audio_path, sr=self.target_sample_rate)
            total_duration = len(y) / sr
            
            segments = []
            segment_samples = int(segment_duration * sr)
            
            for start_sample in range(0, len(y), segment_samples):
                end_sample = min(start_sample + segment_samples, len(y))
                start_time = start_sample / sr
                end_time = end_sample / sr
                
                segment_audio = y[start_sample:end_sample]
                
                segments.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "audio_data": segment_audio,
                    "sample_rate": sr
                })
            
            logger.info(f"Created {len(segments)} segments from {total_duration:.2f}s audio")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error segmenting audio: {str(e)}")
            raise
    
    def cleanup_temp_files(self, file_id: str):
        """Clean up temporary files for a specific file ID."""
        try:
            temp_patterns = [
                f"{file_id}_extracted.wav",
                f"{file_id}_processed.wav",
                f"{file_id}_segments_*.wav"
            ]
            
            for pattern in temp_patterns:
                temp_path = os.path.join(self.temp_dir, pattern)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up temp files for {file_id}: {str(e)}")
    
    def validate_audio_quality(self, audio_path: str) -> Dict:
        """
        Validate audio quality for processing.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            y, sr = librosa.load(audio_path, sr=None)  # Keep original sample rate
            
            # Calculate quality metrics
            duration = len(y) / sr
            rms = librosa.feature.rms(y=y)[0]
            mean_rms = np.mean(rms)
            
            # Dynamic range
            dynamic_range = 20 * np.log10(np.max(np.abs(y)) / (np.mean(np.abs(y)) + 1e-10))
            
            # Signal-to-noise ratio estimation
            # Simple approach: compare energy in speech vs silence regions
            energy = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            energy_threshold = np.percentile(energy, 30)  # Bottom 30% as "silence"
            
            speech_energy = energy[energy > energy_threshold]
            noise_energy = energy[energy <= energy_threshold]
            
            if len(noise_energy) > 0:
                snr_estimate = 10 * np.log10(np.mean(speech_energy) / (np.mean(noise_energy) + 1e-10))
            else:
                snr_estimate = float('inf')
            
            quality_metrics = {
                "duration": duration,
                "sample_rate": sr,
                "mean_rms": float(mean_rms),
                "dynamic_range_db": float(dynamic_range),
                "snr_estimate_db": float(snr_estimate),
                "is_acceptable": (
                    duration > 0.5 and  # At least 0.5 seconds
                    mean_rms > 0.001 and  # Not silent
                    dynamic_range > 10  # Reasonable dynamic range
                )
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error validating audio quality: {str(e)}")
            return {
                "duration": 0,
                "sample_rate": 0,
                "mean_rms": 0,
                "dynamic_range_db": 0,
                "snr_estimate_db": 0,
                "is_acceptable": False,
                "error": str(e)
            }

# Global audio processor instance
audio_processor = AudioProcessor()
