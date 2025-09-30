"""
EmotionAnalyzer service for SawtFeel application.
Handles dual-path emotion analysis (textual + tonal) using Hugging Face Transformers.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import librosa
from sklearn.preprocessing import StandardScaler
import joblib
import os

from ..models.emotion_analysis import EmotionAnalysis, EmotionSegment, EmotionType
from ..models.transcript import Transcript

logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    """Service for dual-path emotion analysis."""
    
    def __init__(self, 
                 text_model: str = "CAMeL-Lab/bert-base-arabic-camelbert-msa-sentiment",
                 audio_model: str = "facebook/wav2vec2-large-xlsr-53",
                 device: Optional[str] = None):
        """
        Initialize EmotionAnalyzer.
        
        Args:
            text_model: Hugging Face model for text emotion analysis
            audio_model: Hugging Face model for audio emotion analysis
            device: Device to run on (cuda, cpu, or None for auto)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.text_model_name = text_model
        self.audio_model_name = audio_model
        
        # Model instances (loaded lazily)
        self.text_tokenizer = None
        self.text_model = None
        self.text_pipeline = None
        self.audio_model = None
        
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
        
        logger.info(f"Initializing EmotionAnalyzer with device={self.device}")
    
    def _load_text_model(self):
        """Load text emotion analysis model."""
        if self.text_pipeline is None:
            logger.info(f"Loading text emotion model: {self.text_model_name}")
            try:
                # Try to load Arabic emotion analysis model
                self.text_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.text_model_name,
                    tokenizer=self.text_model_name,
                    device=0 if self.device == "cuda" else -1
                )
                logger.info("Text emotion model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load specified model, using default: {e}")
                # Fallback to a simpler model
                self.text_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=0 if self.device == "cuda" else -1
                )
    
    def _load_audio_model(self):
        """Load audio emotion analysis model."""
        if self.audio_model is None:
            logger.info(f"Loading audio emotion model: {self.audio_model_name}")
            try:
                # For now, we'll use a feature-based approach
                # In production, you'd load a trained emotion recognition model
                logger.info("Using feature-based audio emotion analysis")
                self.audio_model = "feature_based"  # Placeholder
            except Exception as e:
                logger.error(f"Failed to load audio model: {e}")
                self.audio_model = "feature_based"
    
    async def analyze_emotions(self, 
                             transcript: Transcript, 
                             audio_path: str, 
                             segment_duration: float = 2.0) -> EmotionAnalysis:
        """
        Perform dual-path emotion analysis on transcript and audio.
        
        Args:
            transcript: Transcript with word-level timing
            audio_path: Path to audio file
            segment_duration: Duration of analysis segments
            
        Returns:
            EmotionAnalysis with time-based segments
        """
        try:
            start_time = datetime.now()
            
            # Load models
            self._load_text_model()
            self._load_audio_model()
            
            logger.info(f"Analyzing emotions for file: {transcript.audio_file_id}")
            
            # Create time-based segments
            segments = self._create_analysis_segments(transcript, audio_path, segment_duration)
            
            # Analyze each segment
            emotion_segments = []
            for segment in segments:
                emotion_segment = await self._analyze_segment(segment)
                emotion_segments.append(emotion_segment)
            
            # Calculate overall emotion
            overall_emotion, overall_confidence = self._calculate_overall_emotion(emotion_segments)
            
            # Create EmotionAnalysis object
            emotion_analysis = EmotionAnalysis(
                audio_file_id=transcript.audio_file_id,
                segments=emotion_segments,
                overall_emotion=overall_emotion,
                overall_confidence=overall_confidence
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Emotion analysis completed in {processing_time:.2f}s")
            
            return emotion_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing emotions: {str(e)}")
            raise
    
    def _create_analysis_segments(self, 
                                transcript: Transcript, 
                                audio_path: str, 
                                segment_duration: float) -> List[Dict]:
        """Create segments for emotion analysis."""
        if not transcript.words:
            return []
        
        # Load audio for tonal analysis
        y, sr = librosa.load(audio_path, sr=16000)
        total_duration = len(y) / sr
        
        segments = []
        segment_samples = int(segment_duration * sr)
        
        # Create time-based segments
        for start_time in np.arange(0, total_duration, segment_duration):
            end_time = min(start_time + segment_duration, total_duration)
            
            # Get words in this time segment
            segment_words = [
                word for word in transcript.words
                if word.start_time >= start_time and word.end_time <= end_time
            ]
            
            # Get audio data for this segment
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            segment_audio = y[start_sample:end_sample]
            
            # Combine text from words in segment
            segment_text = " ".join([word.word for word in segment_words])
            
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "text": segment_text,
                "words": segment_words,
                "audio_data": segment_audio,
                "sample_rate": sr
            })
        
        logger.info(f"Created {len(segments)} analysis segments")
        return segments
    
    async def _analyze_segment(self, segment: Dict) -> EmotionSegment:
        """Analyze emotion for a single segment."""
        # Textual emotion analysis
        textual_emotion, textual_confidence = await self._analyze_text_emotion(segment["text"])
        
        # Tonal emotion analysis
        tonal_emotion, tonal_confidence = await self._analyze_audio_emotion(
            segment["audio_data"], segment["sample_rate"]
        )
        
        # Combine emotions using weighted average
        combined_emotion, combined_confidence = self._fuse_emotions(
            textual_emotion, textual_confidence,
            tonal_emotion, tonal_confidence
        )
        
        return EmotionSegment(
            start_time=segment["start_time"],
            end_time=segment["end_time"],
            textual_emotion=textual_emotion,
            textual_confidence=textual_confidence,
            tonal_emotion=tonal_emotion,
            tonal_confidence=tonal_confidence,
            combined_emotion=combined_emotion,
            combined_confidence=combined_confidence
        )
    
    async def _analyze_text_emotion(self, text: str) -> Tuple[EmotionType, float]:
        """Analyze emotion from text."""
        if not text or not text.strip():
            return EmotionType.NEUTRAL, 0.5
        
        try:
            # Use text pipeline for sentiment analysis
            results = self.text_pipeline(text)
            
            if results:
                result = results[0] if isinstance(results, list) else results
                label = result.get("label", "NEUTRAL")
                score = result.get("score", 0.5)
                
                # Map label to emotion
                emotion = self.emotion_mapping.get(label, EmotionType.NEUTRAL)
                confidence = min(1.0, max(0.1, score))
                
                return emotion, confidence
            
        except Exception as e:
            logger.warning(f"Error in text emotion analysis: {e}")
        
        return EmotionType.NEUTRAL, 0.5
    
    async def _analyze_audio_emotion(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[EmotionType, float]:
        """Analyze emotion from audio features."""
        if len(audio_data) == 0:
            return EmotionType.NEUTRAL, 0.5
        
        try:
            # Extract audio features for emotion analysis
            features = self._extract_emotion_features(audio_data, sample_rate)
            
            # Simple rule-based emotion detection based on audio features
            # In production, this would use a trained ML model
            emotion, confidence = self._classify_audio_emotion(features)
            
            return emotion, confidence
            
        except Exception as e:
            logger.warning(f"Error in audio emotion analysis: {e}")
            return EmotionType.NEUTRAL, 0.5
    
    def _extract_emotion_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        """Extract audio features relevant for emotion analysis."""
        # Ensure minimum length
        if len(audio_data) < sample_rate * 0.1:  # Less than 0.1 seconds
            return self._get_default_features()
        
        try:
            # Energy features
            rms = librosa.feature.rms(y=audio_data)[0]
            energy_mean = np.mean(rms)
            energy_std = np.std(rms)
            
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]
            
            # Pitch features
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # Tempo
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            zcr_mean = np.mean(zcr)
            
            # MFCCs (first 13 coefficients)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)
            
            features = {
                "energy_mean": float(energy_mean),
                "energy_std": float(energy_std),
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "pitch_mean": float(pitch_mean),
                "tempo": float(tempo),
                "zcr_mean": float(zcr_mean),
                "mfcc_means": mfcc_means.tolist()
            }
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting audio features: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict:
        """Return default features for error cases."""
        return {
            "energy_mean": 0.0,
            "energy_std": 0.0,
            "spectral_centroid_mean": 0.0,
            "spectral_bandwidth_mean": 0.0,
            "spectral_rolloff_mean": 0.0,
            "pitch_mean": 0.0,
            "tempo": 0.0,
            "zcr_mean": 0.0,
            "mfcc_means": [0.0] * 13
        }
    
    def _classify_audio_emotion(self, features: Dict) -> Tuple[EmotionType, float]:
        """Classify emotion based on audio features using simple rules."""
        # Simple rule-based classification
        # In production, this would use a trained ML model
        
        energy = features.get("energy_mean", 0.0)
        pitch = features.get("pitch_mean", 0.0)
        tempo = features.get("tempo", 0.0)
        spectral_centroid = features.get("spectral_centroid_mean", 0.0)
        
        # Normalize features (rough approximation)
        energy_norm = min(1.0, energy * 10)  # Assuming typical range
        pitch_norm = min(1.0, pitch / 500) if pitch > 0 else 0  # Assuming typical range
        tempo_norm = min(1.0, tempo / 200) if tempo > 0 else 0  # Assuming typical range
        
        # Simple emotion classification rules
        if energy_norm > 0.7 and pitch_norm > 0.6:
            # High energy and pitch -> anger or excitement
            return EmotionType.ANGER, 0.7
        elif energy_norm < 0.3 and pitch_norm < 0.4:
            # Low energy and pitch -> sadness
            return EmotionType.SADNESS, 0.6
        elif tempo_norm > 0.8:
            # Fast tempo -> joy or excitement
            return EmotionType.JOY, 0.6
        elif spectral_centroid > 2000:
            # High spectral centroid -> surprise or fear
            return EmotionType.SURPRISE, 0.5
        else:
            # Default to neutral
            return EmotionType.NEUTRAL, 0.8
    
    def _fuse_emotions(self, 
                      text_emotion: EmotionType, text_conf: float,
                      audio_emotion: EmotionType, audio_conf: float) -> Tuple[EmotionType, float]:
        """Fuse textual and tonal emotion predictions."""
        # Weight by confidence scores
        text_weight = text_conf
        audio_weight = audio_conf
        total_weight = text_weight + audio_weight
        
        if total_weight == 0:
            return EmotionType.NEUTRAL, 0.5
        
        # If emotions match, boost confidence
        if text_emotion == audio_emotion:
            combined_confidence = min(1.0, (text_conf + audio_conf) / 2 * 1.2)
            return text_emotion, combined_confidence
        
        # If emotions differ, choose the one with higher confidence
        if text_conf > audio_conf:
            combined_confidence = text_conf * 0.8  # Slightly reduce due to disagreement
            return text_emotion, combined_confidence
        else:
            combined_confidence = audio_conf * 0.8
            return audio_emotion, combined_confidence
    
    def _calculate_overall_emotion(self, segments: List[EmotionSegment]) -> Tuple[EmotionType, float]:
        """Calculate overall emotion from all segments."""
        if not segments:
            return EmotionType.NEUTRAL, 0.5
        
        # Weight by segment duration and confidence
        emotion_scores = {}
        total_weight = 0
        
        for segment in segments:
            duration = segment.end_time - segment.start_time
            weight = duration * segment.combined_confidence
            
            emotion = segment.combined_emotion
            if emotion not in emotion_scores:
                emotion_scores[emotion] = 0
            
            emotion_scores[emotion] += weight
            total_weight += weight
        
        if total_weight == 0:
            return EmotionType.NEUTRAL, 0.5
        
        # Normalize scores
        for emotion in emotion_scores:
            emotion_scores[emotion] /= total_weight
        
        # Find dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        return dominant_emotion[0], dominant_emotion[1]
    
    def get_emotion_timeline(self, emotion_analysis: EmotionAnalysis, 
                           time_resolution: float = 0.1) -> List[Dict]:
        """
        Generate high-resolution emotion timeline for visualization.
        
        Args:
            emotion_analysis: EmotionAnalysis object
            time_resolution: Time resolution in seconds
            
        Returns:
            List of emotion data points for timeline
        """
        if not emotion_analysis.segments:
            return []
        
        timeline = []
        total_duration = emotion_analysis.segments[-1].end_time
        
        for t in np.arange(0, total_duration, time_resolution):
            # Find segment for this time point
            current_segment = None
            for segment in emotion_analysis.segments:
                if segment.start_time <= t <= segment.end_time:
                    current_segment = segment
                    break
            
            if current_segment:
                timeline.append({
                    "time": t,
                    "emotion": current_segment.combined_emotion.value,
                    "confidence": current_segment.combined_confidence,
                    "textual_emotion": current_segment.textual_emotion.value,
                    "tonal_emotion": current_segment.tonal_emotion.value
                })
            else:
                # Interpolate or use neutral
                timeline.append({
                    "time": t,
                    "emotion": EmotionType.NEUTRAL.value,
                    "confidence": 0.5,
                    "textual_emotion": EmotionType.NEUTRAL.value,
                    "tonal_emotion": EmotionType.NEUTRAL.value
                })
        
        return timeline
    
    def cleanup_resources(self):
        """Clean up model resources."""
        if self.text_pipeline is not None:
            del self.text_pipeline
            self.text_pipeline = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Cleaned up emotion analyzer resources")

# Global emotion analyzer instance
emotion_analyzer = EmotionAnalyzer()
