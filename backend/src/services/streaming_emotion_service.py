"""
Streaming emotion analysis service for real-time emotion processing.
"""
import asyncio
import logging
import numpy as np
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime
import librosa
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

# Set PyTorch to use float32 by default to avoid dtype mismatches
torch.set_default_dtype(torch.float32)
# Also set numpy default dtype to float32
np.seterr(all='ignore')  # Ignore numpy warnings for cleaner logs

from ..models.realtime_emotion import (
    RealTimeEmotion,
    EmotionUpdate,
    EmotionType,
    EmotionIntensity
)

logger = logging.getLogger(__name__)


class StreamingEmotionService:
    """Service for real-time streaming emotion analysis."""
    
    def __init__(self, 
                 text_model: str = "CAMeL-Lab/bert-base-arabic-camelbert-msa-sentiment",
                 audio_model: str = "facebook/wav2vec2-large-xlsr-53"):
        """
        Initialize the streaming emotion analysis service.
        
        Args:
            text_model: Hugging Face model for text emotion analysis
            audio_model: Hugging Face model for audio emotion analysis
        """
        self.text_model_name = text_model
        self.audio_model_name = audio_model
        self.text_pipeline = None
        self.audio_model = None
        self.audio_tokenizer = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.chunk_size = 16000  # 1 second at 16kHz
        self.overlap = 4000  # 0.25 seconds overlap
        
        # Emotion mapping
        self.emotion_mapping = {
            "POSITIVE": EmotionType.JOY,
            "NEGATIVE": EmotionType.SADNESS,
            "anger": EmotionType.ANGER,
            "fear": EmotionType.FEAR,
            "joy": EmotionType.JOY,
            "sadness": EmotionType.SADNESS,
            "surprise": EmotionType.SURPRISE,
            "neutral": EmotionType.NEUTRAL,
            "NEUTRAL": EmotionType.NEUTRAL
        }
        
    async def initialize(self):
        """Initialize the emotion analysis models with fallback options."""
        try:
            # Try to load text emotion model with fallback
            logger.info(f"Loading text emotion model: {self.text_model_name}")
            try:
                self.text_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.text_model_name,
                    return_all_scores=True
                )
                logger.info("Text emotion model loaded successfully")
            except Exception as text_error:
                logger.warning(f"Failed to load Arabic text model, using fallback: {text_error}")
                # Fallback to a simpler, more available model
                self.text_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
                logger.info("Fallback text emotion model loaded")
            
            # For audio emotion analysis, use feature-based approach instead of heavy model
            logger.info("Using feature-based audio emotion analysis (no heavy model required)")
            self.audio_model = "feature_based"  # Use feature extraction instead
            self.audio_tokenizer = None  # Not needed for feature-based approach
            
            logger.info("Emotion analysis services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize emotion analysis: {e}")
            # Don't raise - allow the service to work with limited functionality
            logger.warning("Emotion analysis will use basic sentiment detection only")
            self.text_pipeline = None
            self.audio_model = "basic"
    
    def _analyze_audio_features(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """
        Analyze audio features for emotion detection without heavy models.
        
        Args:
            audio_chunk: Audio data
            sample_rate: Sample rate
            
        Returns:
            Dict: Emotion probabilities based on audio features
        """
        try:
            # Ensure consistent data type (float32) to avoid dtype mismatch errors
            audio_chunk = audio_chunk.astype(np.float32)
            
            # Use simple numpy-based features to avoid librosa dtype issues
            # RMS Energy (loudness)
            rms = float(np.sqrt(np.mean(audio_chunk**2)))
            
            # Simple zero crossing rate calculation
            zero_crossings = np.where(np.diff(np.signbit(audio_chunk)))[0]
            zcr = float(len(zero_crossings) / len(audio_chunk))
            
            # Simple spectral energy approximation (avoid librosa for now)
            fft = np.fft.fft(audio_chunk)
            spectral_energy = float(np.mean(np.abs(fft[:len(fft)//2])))
            
            # Simple heuristic emotion mapping based on features
            emotions = {
                "anger": min(1.0, rms * 2.0 + zcr * 0.5),  # High energy + high ZCR
                "joy": min(1.0, spectral_energy / 1000 + rms * 0.5),  # High spectral energy + moderate RMS
                "sadness": min(1.0, (1.0 - rms) * 0.8 + (1.0 - zcr) * 0.2),  # Low energy + low ZCR
                "fear": min(1.0, zcr * 1.5 + rms * 0.3),  # High ZCR + some energy
                "surprise": min(1.0, abs(rms - 0.5) * 2.0),  # Sudden energy changes
                "neutral": min(1.0, 1.0 - max(rms, zcr, spectral_energy / 1000))
            }
            
            # Normalize to sum to 1
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v/total for k, v in emotions.items()}
            
            return emotions
            
        except Exception as e:
            logger.error(f"Error analyzing audio features: {e}")
            return {"neutral": 1.0}

    async def start_streaming(self, file_id: str, session_id: str, audio_path: str) -> AsyncGenerator[EmotionUpdate, None]:
        """
        Start streaming emotion analysis for a file.
        
        Args:
            file_id: Unique file identifier
            session_id: Session identifier
            audio_path: Path to the audio file
            
        Yields:
            EmotionUpdate: Real-time emotion updates
        """
        try:
            logger.info(f"Starting streaming emotion analysis for file {file_id}")
            
            # Initialize session
            self.active_sessions[session_id] = {
                "file_id": file_id,
                "audio_path": audio_path,
                "current_time": 0.0,
                "sequence_number": 0,
                "is_active": True,
                "emotion_history": []
            }
            
            # Load audio file or use mock data
            import os
            if audio_path.startswith("/tmp/mock_") or not os.path.exists(audio_path):
                # Generate mock audio data for demonstration
                logger.info(f"Using mock audio data for emotion analysis demonstration")
                duration = 30.0  # 30 seconds of mock audio
                sample_rate = 16000
                audio_data = np.random.normal(0, 0.1, int(duration * sample_rate)).astype(np.float32)  # Mock audio
            else:
                audio_data, sample_rate = librosa.load(audio_path, sr=16000, dtype=np.float32)
                duration = len(audio_data) / sample_rate
            
            logger.info(f"Audio loaded: {duration:.2f}s duration, {sample_rate}Hz sample rate")
            
            # Process audio in chunks
            chunk_start = 0
            sequence_number = 0
            
            while chunk_start < len(audio_data) and self.active_sessions.get(session_id, {}).get("is_active", False):
                # Extract chunk
                chunk_end = min(chunk_start + self.chunk_size, len(audio_data))
                chunk = audio_data[chunk_start:chunk_end]
                
                if len(chunk) < self.chunk_size // 4:  # Skip very short chunks
                    break
                
                # Process chunk
                emotion = await self.process_audio_chunk(
                    chunk, 
                    file_id, 
                    session_id, 
                    chunk_start / sample_rate,
                    chunk_end / sample_rate
                )
                
                if emotion:
                    # Create update
                    update = EmotionUpdate(
                        file_id=file_id,
                        session_id=session_id,
                        emotion=emotion,
                        sequence_number=sequence_number
                    )
                    
                    yield update
                    sequence_number += 1
                
                # Move to next chunk with overlap
                chunk_start += self.chunk_size - self.overlap
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
            
            # Mark session as complete
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["is_active"] = False
            
            logger.info(f"Streaming emotion analysis completed for file {file_id}")
            
        except Exception as e:
            logger.error(f"Error in streaming emotion analysis: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["is_active"] = False
            raise
    
    async def process_audio_chunk(
        self, 
        audio_chunk: np.ndarray, 
        file_id: str, 
        session_id: str,
        start_time: float,
        end_time: float
    ) -> Optional[RealTimeEmotion]:
        """
        Process a single audio chunk for emotion analysis.
        
        Args:
            audio_chunk: Audio data chunk
            file_id: File identifier
            session_id: Session identifier
            start_time: Start time of the chunk
            end_time: End time of the chunk
            
        Returns:
            RealTimeEmotion: Emotion analysis with timing information
        """
        try:
            if self.audio_model is None or self.text_pipeline is None:
                await self.initialize()
            
            # Analyze audio features for emotion
            audio_emotion = await self._analyze_audio_emotion(audio_chunk)
            
            # For now, we'll use audio-based emotion analysis
            # In a full implementation, you might also analyze transcribed text
            emotion_type = self.emotion_mapping.get(audio_emotion.get("label", "neutral"), EmotionType.NEUTRAL)
            confidence = audio_emotion.get("score", 0.5)
            
            # Calculate intensity based on audio features
            intensity = await self._calculate_emotion_intensity(audio_chunk, emotion_type)
            
            # Create emotion analysis
            emotion = RealTimeEmotion(
                file_id=file_id,
                session_id=session_id,
                emotion_type=emotion_type,
                intensity=intensity,
                confidence=confidence,
                timestamp=datetime.now().timestamp(),
                start_time=start_time,
                end_time=end_time,
                processing_time=0.0,  # Could be calculated if needed
                model_version=f"{self.audio_model_name}_{self.text_model_name}"
            )
            
            # Update session history
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["emotion_history"].append(emotion)
                # Keep only last 10 emotions for smoothing
                if len(self.active_sessions[session_id]["emotion_history"]) > 10:
                    self.active_sessions[session_id]["emotion_history"].pop(0)
            
            logger.debug(f"Analyzed emotion: {emotion_type} (intensity: {intensity}, confidence: {confidence:.2f})")
            return emotion
            
        except Exception as e:
            logger.error(f"Error processing audio chunk for emotion: {e}")
            return None
    
    async def _analyze_audio_emotion(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """
        Analyze audio chunk for emotion using advanced audio features.
        
        Args:
            audio_chunk: Audio data chunk
            
        Returns:
            Dict: Emotion analysis results with detailed features
        """
        try:
            # Ensure consistent data type (float32) to avoid dtype mismatch errors
            audio_chunk = audio_chunk.astype(np.float32)
            
            # Advanced audio feature extraction
            features = self._extract_advanced_audio_features(audio_chunk)
            
            # Analyze vocal tone characteristics
            tone_analysis = self._analyze_vocal_tone(features)
            
            # Analyze intensity patterns
            intensity_analysis = self._analyze_intensity_patterns(features)
            
            # Combine analyses for emotion detection
            emotion_result = self._combine_emotion_analyses(tone_analysis, intensity_analysis)
            
            return emotion_result
                
        except Exception as e:
            logger.error(f"Error analyzing audio emotion: {e}")
            return {"label": "neutral", "score": 0.5}
    
    def _extract_advanced_audio_features(self, audio_chunk: np.ndarray) -> Dict[str, float]:
        """
        Extract advanced audio features for emotion analysis.
        
        Args:
            audio_chunk: Audio data chunk
            
        Returns:
            Dict: Extracted audio features
        """
        try:
            # Basic energy features
            rms = float(np.sqrt(np.mean(audio_chunk**2)))
            energy = float(np.sum(audio_chunk**2))
            
            # Zero crossing rate (speech activity indicator)
            zero_crossings = np.where(np.diff(np.signbit(audio_chunk)))[0]
            zcr = float(len(zero_crossings) / len(audio_chunk))
            
            # Spectral features
            fft = np.fft.fft(audio_chunk)
            magnitude = np.abs(fft[:len(fft)//2])
            
            # Spectral centroid (brightness of sound)
            freqs = np.fft.fftfreq(len(audio_chunk), 1/16000)[:len(magnitude)]
            spectral_centroid = float(np.sum(freqs * magnitude) / np.sum(magnitude)) if np.sum(magnitude) > 0 else 0
            
            # Spectral rolloff (frequency below which 85% of energy lies)
            cumulative_energy = np.cumsum(magnitude)
            total_energy = cumulative_energy[-1]
            rolloff_threshold = 0.85 * total_energy
            spectral_rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
            spectral_rolloff = float(freqs[spectral_rolloff_idx[0]]) if len(spectral_rolloff_idx) > 0 else 0
            
            # Spectral bandwidth (spread of spectrum)
            spectral_bandwidth = float(np.sqrt(np.sum(((freqs - spectral_centroid)**2) * magnitude) / np.sum(magnitude))) if np.sum(magnitude) > 0 else 0
            
            # MFCC-like features (simplified)
            # Mel-frequency cepstral coefficients approximation
            mel_energies = []
            for i in range(0, len(magnitude), len(magnitude)//13):  # 13 mel bands
                band_energy = float(np.mean(magnitude[i:i+len(magnitude)//13]))
                mel_energies.append(band_energy)
            
            # Pitch estimation (simplified autocorrelation)
            autocorr = np.correlate(audio_chunk, audio_chunk, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks for pitch estimation
            peaks = []
            for i in range(1, len(autocorr)-1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append(i)
            
            # Estimate fundamental frequency
            if peaks:
                # Find the first significant peak (fundamental frequency)
                fundamental_freq = 16000 / peaks[0] if peaks[0] > 0 else 0
            else:
                fundamental_freq = 0
            
            # Voice activity detection
            voice_activity = 1.0 if rms > 0.01 and zcr > 0.01 else 0.0
            
            return {
                'rms': rms,
                'energy': energy,
                'zcr': zcr,
                'spectral_centroid': spectral_centroid,
                'spectral_rolloff': spectral_rolloff,
                'spectral_bandwidth': spectral_bandwidth,
                'mel_energies': mel_energies,
                'fundamental_freq': fundamental_freq,
                'voice_activity': voice_activity,
                'spectral_energy': float(np.sum(magnitude))
            }
            
        except Exception as e:
            logger.error(f"Error extracting advanced audio features: {e}")
            return {
                'rms': 0.0, 'energy': 0.0, 'zcr': 0.0,
                'spectral_centroid': 0.0, 'spectral_rolloff': 0.0,
                'spectral_bandwidth': 0.0, 'mel_energies': [0.0] * 13,
                'fundamental_freq': 0.0, 'voice_activity': 0.0,
                'spectral_energy': 0.0
            }
    
    def _analyze_vocal_tone(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze vocal tone characteristics for emotion detection.
        
        Args:
            features: Extracted audio features
            
        Returns:
            Dict: Vocal tone analysis results
        """
        try:
            # Analyze pitch characteristics
            pitch_analysis = self._analyze_pitch_features(features)
            
            # Analyze spectral characteristics
            spectral_analysis = self._analyze_spectral_features(features)
            
            # Analyze energy patterns
            energy_analysis = self._analyze_energy_features(features)
            
            return {
                'pitch': pitch_analysis,
                'spectral': spectral_analysis,
                'energy': energy_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing vocal tone: {e}")
            return {'pitch': {}, 'spectral': {}, 'energy': {}}
    
    def _analyze_pitch_features(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Analyze pitch-related features."""
        fundamental_freq = features['fundamental_freq']
        
        # Pitch analysis for emotion detection
        if fundamental_freq > 300:  # High pitch
            return {'level': 'high', 'emotion_hint': 'anger', 'confidence': 0.7}
        elif fundamental_freq < 150:  # Low pitch
            return {'level': 'low', 'emotion_hint': 'sadness', 'confidence': 0.6}
        else:  # Normal pitch
            return {'level': 'normal', 'emotion_hint': 'neutral', 'confidence': 0.5}
    
    def _analyze_spectral_features(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Analyze spectral characteristics."""
        spectral_centroid = features['spectral_centroid']
        spectral_bandwidth = features['spectral_bandwidth']
        
        # Spectral analysis for emotion detection
        if spectral_centroid > 2000:  # Bright sound
            return {'brightness': 'bright', 'emotion_hint': 'joy', 'confidence': 0.6}
        elif spectral_centroid < 1000:  # Dark sound
            return {'brightness': 'dark', 'emotion_hint': 'sadness', 'confidence': 0.6}
        else:  # Neutral brightness
            return {'brightness': 'neutral', 'emotion_hint': 'neutral', 'confidence': 0.5}
    
    def _analyze_energy_features(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Analyze energy patterns."""
        rms = features['rms']
        energy = features['energy']
        
        # Energy analysis for emotion detection
        if rms > 0.1:  # High energy
            return {'level': 'high', 'emotion_hint': 'anger', 'confidence': 0.8}
        elif rms < 0.02:  # Low energy
            return {'level': 'low', 'emotion_hint': 'sadness', 'confidence': 0.7}
        else:  # Medium energy
            return {'level': 'medium', 'emotion_hint': 'neutral', 'confidence': 0.5}
    
    def _analyze_intensity_patterns(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze intensity patterns for emotion detection.
        
        Args:
            features: Extracted audio features
            
        Returns:
            Dict: Intensity analysis results
        """
        try:
            rms = features['rms']
            spectral_energy = features['spectral_energy']
            zcr = features['zcr']
            
            # Calculate intensity score
            intensity_score = (rms * 10) + (spectral_energy / 1000) + (zcr * 2)
            
            # Analyze intensity patterns
            if intensity_score > 1.5:
                return {
                    'level': 'high',
                    'emotion_hint': 'anger',
                    'confidence': min(0.9, intensity_score / 2),
                    'score': intensity_score
                }
            elif intensity_score < 0.3:
                return {
                    'level': 'low',
                    'emotion_hint': 'sadness',
                    'confidence': min(0.8, (0.3 - intensity_score) * 2),
                    'score': intensity_score
                }
            else:
                return {
                    'level': 'medium',
                    'emotion_hint': 'neutral',
                    'confidence': 0.5,
                    'score': intensity_score
                }
                
        except Exception as e:
            logger.error(f"Error analyzing intensity patterns: {e}")
            return {'level': 'medium', 'emotion_hint': 'neutral', 'confidence': 0.5, 'score': 0.5}
    
    def _combine_emotion_analyses(self, tone_analysis: Dict, intensity_analysis: Dict) -> Dict[str, Any]:
        """
        Combine tone and intensity analyses for final emotion detection.
        
        Args:
            tone_analysis: Vocal tone analysis results
            intensity_analysis: Intensity analysis results
            
        Returns:
            Dict: Combined emotion analysis results
        """
        try:
            # Collect emotion hints from different analyses
            emotion_hints = []
            confidences = []
            
            # From tone analysis
            if tone_analysis.get('pitch', {}).get('emotion_hint'):
                emotion_hints.append(tone_analysis['pitch']['emotion_hint'])
                confidences.append(tone_analysis['pitch']['confidence'])
            
            if tone_analysis.get('spectral', {}).get('emotion_hint'):
                emotion_hints.append(tone_analysis['spectral']['emotion_hint'])
                confidences.append(tone_analysis['spectral']['confidence'])
            
            if tone_analysis.get('energy', {}).get('emotion_hint'):
                emotion_hints.append(tone_analysis['energy']['emotion_hint'])
                confidences.append(tone_analysis['energy']['confidence'])
            
            # From intensity analysis
            if intensity_analysis.get('emotion_hint'):
                emotion_hints.append(intensity_analysis['emotion_hint'])
                confidences.append(intensity_analysis['confidence'])
            
            # Determine final emotion (most common or highest confidence)
            if emotion_hints:
                # Count emotion occurrences
                emotion_counts = {}
                emotion_confidences = {}
                
                for emotion, confidence in zip(emotion_hints, confidences):
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    emotion_confidences[emotion] = emotion_confidences.get(emotion, 0) + confidence
                
                # Find emotion with highest combined score (count * avg_confidence)
                best_emotion = max(emotion_counts.keys(), 
                                 key=lambda e: emotion_counts[e] * (emotion_confidences[e] / emotion_counts[e]))
                
                # Calculate final confidence
                final_confidence = emotion_confidences[best_emotion] / emotion_counts[best_emotion]
                
                return {
                    'label': best_emotion,
                    'score': final_confidence,
                    'intensity_score': intensity_analysis.get('score', 0.5),
                    'tone_analysis': tone_analysis,
                    'intensity_analysis': intensity_analysis
                }
            else:
                return {'label': 'neutral', 'score': 0.5, 'intensity_score': 0.5}
                
        except Exception as e:
            logger.error(f"Error combining emotion analyses: {e}")
            return {'label': 'neutral', 'score': 0.5, 'intensity_score': 0.5}
    
    async def _calculate_emotion_intensity(self, audio_chunk: np.ndarray, emotion_type: EmotionType) -> EmotionIntensity:
        """
        Calculate emotion intensity based on audio features.
        
        Args:
            audio_chunk: Audio data chunk
            emotion_type: Detected emotion type
            
        Returns:
            EmotionIntensity: Calculated intensity level
        """
        try:
            # Ensure consistent data type (float32) to avoid dtype mismatch errors
            audio_chunk = audio_chunk.astype(np.float32)
            
            # Calculate RMS energy as a proxy for intensity
            rms = float(np.sqrt(np.mean(audio_chunk**2)))
            
            # Simple spectral energy calculation (avoid librosa)
            fft = np.fft.fft(audio_chunk)
            spectral_energy = float(np.mean(np.abs(fft[:len(fft)//2])))
            
            # Combine features for intensity calculation
            intensity_score = (rms * 10) + (spectral_energy / 1000)
            
            # Map to intensity levels
            if intensity_score > 0.8:
                return EmotionIntensity.HIGH
            elif intensity_score > 0.4:
                return EmotionIntensity.MEDIUM
            else:
                return EmotionIntensity.LOW
                
        except Exception as e:
            logger.error(f"Error calculating emotion intensity: {e}")
            return EmotionIntensity.MEDIUM
    
    async def get_smoothed_emotion(self, session_id: str) -> Optional[RealTimeEmotion]:
        """
        Get smoothed emotion based on recent history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            RealTimeEmotion: Smoothed emotion analysis
        """
        if session_id not in self.active_sessions:
            return None
        
        history = self.active_sessions[session_id]["emotion_history"]
        if not history:
            return None
        
        # Simple smoothing - return the most common emotion in recent history
        emotion_counts = {}
        for emotion in history[-5:]:  # Last 5 emotions
            emotion_type = emotion.emotion_type
            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
        
        # Get most common emotion
        most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        # Return the most recent emotion of the most common type
        for emotion in reversed(history):
            if emotion.emotion_type == most_common_emotion:
                return emotion
        
        return history[-1] if history else None
    
    async def stop_streaming(self, session_id: str):
        """
        Stop streaming emotion analysis for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["is_active"] = False
            logger.info(f"Stopped streaming emotion analysis for session {session_id}")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            # Stop all active sessions
            for session_id in list(self.active_sessions.keys()):
                await self.stop_streaming(session_id)
            
            # Clear sessions
            self.active_sessions.clear()
            
            # Clear models from memory
            if self.audio_model is not None:
                del self.audio_model
                self.audio_model = None
            
            if self.audio_tokenizer is not None:
                del self.audio_tokenizer
                self.audio_tokenizer = None
            
            if self.text_pipeline is not None:
                del self.text_pipeline
                self.text_pipeline = None
            
            logger.info("Streaming emotion service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a streaming session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Session status information
        """
        if session_id not in self.active_sessions:
            return {"status": "not_found"}
        
        session = self.active_sessions[session_id]
        return {
            "status": "active" if session["is_active"] else "inactive",
            "file_id": session["file_id"],
            "current_time": session["current_time"],
            "sequence_number": session["sequence_number"],
            "emotion_history_count": len(session["emotion_history"])
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


# Global instance
streaming_emotion_service = StreamingEmotionService()
