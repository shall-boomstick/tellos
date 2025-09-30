"""
TranscriptionService for SawtFeel application.
Handles Arabic speech-to-text transcription using OpenAI Whisper.
"""

import os
import tempfile
import logging
from typing import Dict, List, Optional, Tuple
import whisper
import torch
from datetime import datetime
import numpy as np

from ..models.transcript import Transcript, WordSegment

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for Arabic speech-to-text transcription."""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        """
        Initialize TranscriptionService.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cuda, cpu, or None for auto)
        """
        self.model_size = model_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.supported_languages = ["ar", "ar-SA", "ar-EG", "ar-AE", "ar-JO", "ar-LB"]
        
        logger.info(f"Initializing TranscriptionService with model={model_size}, device={self.device}")
    
    def _load_model(self):
        """Load Whisper model if not already loaded."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper model loaded successfully")
    
    async def transcribe_audio(self, audio_path: str, file_id: str, language: str = "ar") -> Transcript:
        """
        Transcribe audio file to Arabic text with word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            file_id: File identifier
            language: Target language (default: Arabic)
            
        Returns:
            Transcript object with word-level timing
        """
        try:
            start_time = datetime.now()
            
            # Load model if needed
            self._load_model()
            
            logger.info(f"Transcribing audio: {audio_path} (language: {language})")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                verbose=False,
                temperature=0.0,  # Deterministic results
                best_of=1,
                beam_size=5,
                patience=1.0,
                length_penalty=1.0,
                suppress_tokens="-1",
                initial_prompt="",
                condition_on_previous_text=True,
                fp16=torch.cuda.is_available(),
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6
            )
            
            # Process results
            transcript = self._process_transcription_result(result, file_id, language)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Transcription completed in {processing_time:.2f}s")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_path}: {str(e)}")
            raise
    
    def _process_transcription_result(self, result: Dict, file_id: str, language: str) -> Transcript:
        """
        Process Whisper transcription result into Transcript object.
        
        Args:
            result: Whisper transcription result
            file_id: File identifier
            language: Detected/specified language
            
        Returns:
            Transcript object
        """
        # Extract full text
        full_text = result.get("text", "").strip()
        
        # Extract word-level information
        words = []
        overall_confidence_scores = []
        
        for segment in result.get("segments", []):
            segment_words = segment.get("words", [])
            
            for word_info in segment_words:
                word_text = word_info.get("word", "").strip()
                start_time = word_info.get("start", 0.0)
                end_time = word_info.get("end", 0.0)
                
                # Calculate confidence from probability if available
                confidence = self._calculate_word_confidence(word_info, segment)
                
                if word_text and end_time > start_time:
                    word_segment = WordSegment(
                        word=word_text,
                        start_time=start_time,
                        end_time=end_time,
                        confidence=confidence
                    )
                    words.append(word_segment)
                    overall_confidence_scores.append(confidence)
        
        # Calculate overall confidence
        overall_confidence = (
            sum(overall_confidence_scores) / len(overall_confidence_scores)
            if overall_confidence_scores else 0.0
        )
        
        # Validate and clean up Arabic text
        full_text = self._clean_arabic_text(full_text)
        
        # Create transcript object
        transcript = Transcript(
            audio_file_id=file_id,
            text=full_text,
            words=words,
            language=self._normalize_language_code(language),
            confidence=overall_confidence
        )
        
        logger.info(f"Processed transcript: {len(words)} words, confidence={overall_confidence:.3f}")
        
        return transcript
    
    def _calculate_word_confidence(self, word_info: Dict, segment: Dict) -> float:
        """Calculate confidence score for a word."""
        # Try to get word-level probability
        if "probability" in word_info:
            return min(1.0, max(0.0, word_info["probability"]))
        
        # Fallback to segment-level confidence
        if "avg_logprob" in segment:
            # Convert log probability to confidence (rough approximation)
            log_prob = segment["avg_logprob"]
            confidence = np.exp(log_prob)
            return min(1.0, max(0.1, confidence))  # Clamp between 0.1 and 1.0
        
        # Default confidence if no probability information
        return 0.8
    
    def _clean_arabic_text(self, text: str) -> str:
        """Clean and normalize Arabic text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common transcription artifacts
        artifacts = ["♪", "♫", "♩", "♬", "[Music]", "[Applause]", "[Laughter]"]
        for artifact in artifacts:
            text = text.replace(artifact, "")
        
        # Normalize Arabic characters
        text = self._normalize_arabic_chars(text)
        
        return text.strip()
    
    def _normalize_arabic_chars(self, text: str) -> str:
        """Normalize Arabic character variations."""
        # Common Arabic character normalizations
        normalizations = {
            'أ': 'ا',  # Alef with hamza above -> Alef
            'إ': 'ا',  # Alef with hamza below -> Alef  
            'آ': 'ا',  # Alef with madda -> Alef
            'ة': 'ه',  # Teh marbuta -> Heh
            'ي': 'ى',  # Yeh -> Alef maksura (in some contexts)
        }
        
        # Apply normalizations selectively (preserve meaning)
        for original, normalized in normalizations.items():
            # Only normalize in specific contexts to avoid changing meaning
            pass  # Skip aggressive normalization for now
        
        return text
    
    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code to supported format."""
        if language.lower().startswith('ar'):
            return language.lower()
        return "ar"  # Default to Arabic
    
    def detect_language(self, audio_path: str) -> Tuple[str, float]:
        """
        Detect language of audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            self._load_model()
            
            # Load audio for language detection
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            confidence = probs[detected_language]
            
            logger.info(f"Detected language: {detected_language} (confidence: {confidence:.3f})")
            
            return detected_language, confidence
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return "ar", 0.5  # Default to Arabic with medium confidence
    
    def validate_transcription_quality(self, transcript: Transcript) -> Dict:
        """
        Validate transcription quality metrics.
        
        Args:
            transcript: Transcript to validate
            
        Returns:
            Dictionary with quality metrics
        """
        words = transcript.words
        
        if not words:
            return {
                "word_count": 0,
                "avg_confidence": 0.0,
                "low_confidence_ratio": 1.0,
                "timing_consistency": 0.0,
                "is_acceptable": False
            }
        
        # Calculate metrics
        confidences = [word.confidence for word in words]
        avg_confidence = sum(confidences) / len(confidences)
        
        low_confidence_count = sum(1 for conf in confidences if conf < 0.7)
        low_confidence_ratio = low_confidence_count / len(confidences)
        
        # Check timing consistency
        timing_gaps = []
        for i in range(1, len(words)):
            gap = words[i].start_time - words[i-1].end_time
            timing_gaps.append(gap)
        
        # Calculate timing consistency (fewer large gaps = better)
        large_gaps = sum(1 for gap in timing_gaps if gap > 1.0)  # Gaps > 1 second
        timing_consistency = 1.0 - (large_gaps / len(timing_gaps)) if timing_gaps else 1.0
        
        # Overall quality assessment
        is_acceptable = (
            len(words) >= 3 and  # At least 3 words
            avg_confidence >= 0.6 and  # Reasonable confidence
            low_confidence_ratio <= 0.5 and  # Not too many low-confidence words
            timing_consistency >= 0.8  # Good timing consistency
        )
        
        return {
            "word_count": len(words),
            "avg_confidence": avg_confidence,
            "low_confidence_ratio": low_confidence_ratio,
            "timing_consistency": timing_consistency,
            "is_acceptable": is_acceptable
        }
    
    def get_transcription_segments(self, transcript: Transcript, segment_duration: float = 2.0) -> List[Dict]:
        """
        Group transcript words into time-based segments.
        
        Args:
            transcript: Transcript to segment
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of transcript segments
        """
        if not transcript.words:
            return []
        
        segments = []
        current_segment = {
            "start_time": 0.0,
            "end_time": segment_duration,
            "words": [],
            "text": ""
        }
        
        for word in transcript.words:
            # Check if word fits in current segment
            if word.start_time < current_segment["end_time"]:
                current_segment["words"].append(word)
            else:
                # Finalize current segment
                if current_segment["words"]:
                    current_segment["text"] = " ".join([w.word for w in current_segment["words"]])
                    current_segment["start_time"] = current_segment["words"][0].start_time
                    current_segment["end_time"] = current_segment["words"][-1].end_time
                    segments.append(current_segment)
                
                # Start new segment
                current_segment = {
                    "start_time": word.start_time,
                    "end_time": word.start_time + segment_duration,
                    "words": [word],
                    "text": ""
                }
        
        # Add final segment
        if current_segment["words"]:
            current_segment["text"] = " ".join([w.word for w in current_segment["words"]])
            current_segment["start_time"] = current_segment["words"][0].start_time
            current_segment["end_time"] = current_segment["words"][-1].end_time
            segments.append(current_segment)
        
        logger.info(f"Created {len(segments)} transcript segments")
        
        return segments
    
    def cleanup_resources(self):
        """Clean up model resources."""
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Cleaned up transcription model resources")

# Global transcription service instance
transcription_service = TranscriptionService()

# Import and create translation service instance
from .translation_service import TranslationService
translation_service = TranslationService()
