"""
Gemini-based transcription service for SawtFeel application.
Handles Arabic speech-to-text transcription using Google Gemini Flash 2.0.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from datetime import datetime
import tempfile
import json

from ..models.transcript import Transcript, WordSegment

logger = logging.getLogger(__name__)


class GeminiTranscriptionService:
    """Service for Arabic speech-to-text transcription using Gemini Flash 2.0."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GeminiTranscriptionService.
        
        Args:
            api_key: Gemini API key (will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.supported_languages = ["ar", "ar-SA", "ar-EG", "ar-AE", "ar-JO", "ar-LB"]
        
        logger.info("Initialized GeminiTranscriptionService with Gemini Flash 2.5")
    
    async def transcribe_audio(self, audio_path: str, file_id: str, language: str = "ar") -> Transcript:
        """
        Transcribe audio file to Arabic text using Gemini Flash 2.5.
        
        Args:
            audio_path: Path to audio file
            file_id: File identifier
            language: Target language (default: Arabic)
            
        Returns:
            Transcript object with word-level timing
        """
        try:
            start_time = datetime.now()
            
            logger.info(f"Transcribing audio with Gemini: {audio_path} (language: {language})")
            
            # Get audio duration for proper timing calculation
            audio_duration = await self._get_audio_duration(audio_path)
            
            # Upload audio file to Gemini
            logger.info("Uploading audio file to Gemini...")
            audio_file = genai.upload_file(path=audio_path)
            logger.info(f"Audio uploaded successfully: {audio_file.name}")
            
            # Wait for file processing
            while audio_file.state.name == "PROCESSING":
                logger.info("Waiting for Gemini to process audio...")
                await asyncio.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise RuntimeError(f"Gemini failed to process audio: {audio_file.state}")
            
            # Create comprehensive transcription prompt
            prompt = self._create_transcription_prompt(language)
            
            # Generate transcription
            logger.info("Generating transcription with Gemini...")
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, audio_file],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent transcription
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Clean up uploaded file
            try:
                genai.delete_file(audio_file.name)
                logger.info("Cleaned up uploaded audio file")
            except Exception as e:
                logger.warning(f"Could not delete uploaded file: {e}")
            
            # Process the response
            transcript_text = response.text.strip()
            logger.info(f"Gemini transcription completed: {len(transcript_text)} characters")
            
            # Clean up the response text - remove JSON formatting artifacts
            transcript_text = self._clean_gemini_response(transcript_text)
            
            # Parse and structure the response
            transcript = await self._process_gemini_response(transcript_text, file_id, language, audio_duration)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Total transcription time: {processing_time:.2f}s")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error in Gemini transcription {audio_path}: {str(e)}")
            raise
    
    def _create_transcription_prompt(self, language: str) -> str:
        """Create a comprehensive prompt for Arabic transcription."""
        if language.startswith('ar'):
            return """
Please transcribe this Arabic audio file with the following requirements:

1. **Accurate Arabic Transcription**: Provide the exact Arabic words spoken, including:
   - Proper Arabic script (not romanized)
   - Correct spelling and diacritics where clear
   - Natural speech patterns and colloquialisms

2. **Speaker Identification**: If multiple speakers, identify them as "Person 1:", "Person 2:", etc.

3. **Complete Sentences**: Preserve natural dialogue structure with complete sentences, not fragmented words

4. **Dialogue Format**: Format as a natural conversation with clear speaker turns and complete thoughts

Please provide the transcription in this exact format:

**Arabic Transcription:**

Person 1: [Complete Arabic sentence or phrase]
Person 2: [Complete Arabic sentence or phrase]
Person 1: [Complete Arabic sentence or phrase]
...

**English Translation:**

Person 1: [Complete English translation]
Person 2: [Complete English translation]
Person 1: [Complete English translation]
...

Focus on accuracy and natural dialogue flow. Preserve complete sentences and thoughts rather than breaking them into fragments.
"""
        else:
            return f"Please transcribe this audio file accurately in {language} language, preserving the natural dialogue structure."
    
    async def _process_gemini_response(self, response_text: str, file_id: str, language: str, audio_duration: float = 30.0) -> Transcript:
        """
        Process Gemini's response into a Transcript object.
        
        Args:
            response_text: Raw response from Gemini
            file_id: File identifier
            language: Language code
            
        Returns:
            Transcript object
        """
        try:
            full_text = ""
            english_text = ""
            words = []
            
            # Parse the new dialogue format
            arabic_lines = []
            english_lines = []
            
            # Split response into sections
            if "**Arabic Transcription:**" in response_text and "**English Translation:**" in response_text:
                parts = response_text.split("**English Translation:**")
                arabic_section = parts[0].replace("**Arabic Transcription:**", "").strip()
                english_section = parts[1].strip() if len(parts) > 1 else ""
                
                # Parse Arabic lines
                for line in arabic_section.split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        speaker_part = line.split(':', 1)
                        if len(speaker_part) == 2:
                            arabic_lines.append({
                                'speaker': speaker_part[0].strip(),
                                'text': speaker_part[1].strip()
                            })
                
                # Parse English lines
                for line in english_section.split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        speaker_part = line.split(':', 1)
                        if len(speaker_part) == 2:
                            english_lines.append({
                                'speaker': speaker_part[0].strip(),
                                'text': speaker_part[1].strip()
                            })
                
                # Combine into full text
                if arabic_lines:
                    full_text = ' '.join([line['text'] for line in arabic_lines])
                    english_text = ' '.join([line['text'] for line in english_lines])
                    
                    # Create segments with proper timing
                    words = self._create_dialogue_segments(arabic_lines, english_lines, audio_duration)
                
                logger.info(f"Parsed {len(arabic_lines)} Arabic lines and {len(english_lines)} English lines")
            
            # Fallback to old format or plain text
            if not full_text:
                full_text = self._clean_arabic_text(response_text)
                words = self._create_word_segments_from_text(full_text, audio_duration)
            
            # Clean up Arabic text
            full_text = self._clean_arabic_text(full_text)
            
            # Calculate overall confidence
            overall_confidence = sum(w.confidence for w in words) / len(words) if words else 0.9
            
            # Create transcript object
            transcript = Transcript(
                audio_file_id=file_id,
                text=full_text,
                english_text=english_text,
                words=words,
                language=language,
                confidence=overall_confidence
            )
            
            logger.info(f"Created transcript with {len(words)} words, confidence: {overall_confidence:.3f}")
            return transcript
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}")
            # Fallback: create basic transcript
            clean_text = self._clean_arabic_text(response_text)
            words = self._create_word_segments_from_text(clean_text, audio_duration)
            
            return Transcript(
                audio_file_id=file_id,
                text=clean_text,
                words=words,
                language=language,
                confidence=0.8
            )
    
    def _create_word_segments_from_text(self, text: str, audio_duration: float = 30.0) -> List[WordSegment]:
        """Create word segments from plain text with estimated timing based on audio duration."""
        words = []
        text_words = text.split()
        
        if not text_words:
            return words
        
        # Calculate time per word based on actual audio duration
        # Always use the full audio duration to distribute words evenly
        time_per_word = audio_duration / len(text_words)
        
        # Ensure minimum reasonable time per word (not too fast)
        min_time_per_word = 0.1  # 0.1 seconds minimum per word (very fast speech)
        time_per_word = max(min_time_per_word, time_per_word)
        
        for i, word in enumerate(text_words):
            start_time = i * time_per_word
            end_time = start_time + time_per_word
            
            word_segment = WordSegment(
                word=word.strip(),
                start_time=start_time,
                end_time=end_time,
                confidence=0.9  # High confidence for Gemini
            )
            words.append(word_segment)
        
        return words
    
    def _clean_arabic_text(self, text: str) -> str:
        """Clean and normalize Arabic text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('```json', '').replace('```', '')
        text = text.replace('\n', ' ').replace('\r', '')
        
        # Remove non-Arabic characters except spaces and punctuation
        import re
        # Keep Arabic characters, spaces, and basic punctuation
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\.\,\!\?\:\;]', '', text)
        
        return text.strip()
    
    def _create_dialogue_segments(self, arabic_lines: list, english_lines: list, audio_duration: float) -> List[WordSegment]:
        """Create word segments from structured dialogue lines."""
        words = []
        
        # Calculate time per line
        time_per_line = audio_duration / len(arabic_lines) if arabic_lines else 1.0
        
        for i, arabic_line in enumerate(arabic_lines):
            line_start_time = i * time_per_line
            arabic_text = arabic_line['text']
            english_text = ""
            
            # Find matching English line
            if i < len(english_lines):
                english_text = english_lines[i]['text']
            
            # Split Arabic text into words
            arabic_words = arabic_text.split()
            time_per_word = time_per_line / len(arabic_words) if arabic_words else 0.1
            
            for j, word in enumerate(arabic_words):
                word_start = line_start_time + (j * time_per_word)
                word_end = word_start + time_per_word
                
                word_segment = WordSegment(
                    word=word.strip(),
                    start_time=word_start,
                    end_time=word_end,
                    confidence=0.95,
                    # Add English translation as metadata if needed
                    metadata={'english_translation': english_text} if english_text else {}
                )
                words.append(word_segment)
        
        return words
    
    def _clean_gemini_response(self, response_text: str) -> str:
        """Clean up Gemini response by extracting actual content from JSON format."""
        try:
            import re
            
            # First, try to extract Arabic text directly using regex
            arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\.\,\!\?\:\;]+'
            arabic_matches = re.findall(arabic_pattern, response_text)
            
            if arabic_matches:
                # Join all Arabic text parts
                cleaned = ' '.join(arabic_matches)
                # Clean up extra whitespace and punctuation
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                # Remove standalone punctuation
                cleaned = re.sub(r'^[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+$', '', cleaned).strip()
                
                if len(cleaned) > 10:  # Has meaningful content
                    logger.info(f"Extracted Arabic text: {len(cleaned)} characters")
                    return cleaned
            
            # Fallback: try to parse JSON structure
            try:
                import json
                # Remove markdown code blocks
                if '```json' in response_text:
                    start = response_text.find('```json') + 7
                    end = response_text.rfind('```')
                    if end > start:
                        json_text = response_text[start:end].strip()
                        data = json.loads(json_text)
                        if 'full_text' in data:
                            logger.info(f"Extracted from JSON full_text: {len(data['full_text'])} characters")
                            return data['full_text']
            except:
                pass
            
            # Final fallback: return original text
            logger.warning("Could not extract clean Arabic text, returning original")
            return response_text
            
        except Exception as e:
            logger.warning(f"Error cleaning Gemini response: {e}")
            return response_text
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using librosa."""
        try:
            import librosa
            # Load just the metadata to get duration
            duration = librosa.get_duration(path=audio_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")
            return duration
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}, using default 30s")
            return 30.0


# Global Gemini transcription service instance
gemini_transcription_service = None

def get_gemini_service() -> GeminiTranscriptionService:
    """Get or create the global Gemini transcription service."""
    global gemini_transcription_service
    if gemini_transcription_service is None:
        gemini_transcription_service = GeminiTranscriptionService()
    return gemini_transcription_service
