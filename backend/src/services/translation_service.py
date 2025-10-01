"""
TranslationService for SawtFeel application.
Handles Arabic to English translation using Google Translate API.
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for translating Arabic text to English."""
    
    def __init__(self):
        """Initialize TranslationService."""
        self.base_url = "https://translate.googleapis.com/translate_a/single"
        self.params = {
            'client': 'gtx',
            'sl': 'ar',  # source language (Arabic)
            'tl': 'en',  # target language (English)
            'dt': 't'
        }
        
        logger.info("Initializing TranslationService")
    
    async def translate_text(self, arabic_text: str) -> str:
        """
        Translate Arabic text to English.
        
        Args:
            arabic_text: Arabic text to translate
            
        Returns:
            English translation
        """
        try:
            if not arabic_text or not arabic_text.strip():
                return ""
            
            # Clean the text
            clean_text = arabic_text.strip()
            
            # Handle repetitive single words (like "او" repeated many times)
            words = clean_text.split()
            # Check if it's mostly repetitive (at least 90% same word)
            if len(words) > 5:
                word_counts = {}
                for word in words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                
                # Find the most common word
                most_common_word = max(word_counts, key=word_counts.get)
                most_common_count = word_counts[most_common_word]
                
                # If the most common word appears in at least 90% of positions, treat as repetitive
                if most_common_count >= len(words) * 0.9:
                    # If it's the same word repeated many times, translate just one instance
                    single_word = most_common_word
                    logger.info(f"Detected repetitive text, translating single instance: {single_word}")
                    
                    # Translate just one instance
                    response = requests.get(
                        self.base_url,
                        params={
                            **self.params,
                            'q': single_word
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result and len(result) > 0 and result[0] and result[0][0]:
                            translated_word = result[0][0][0]
                            # Repeat the translated word the same number of times
                            translated_text = ' '.join([translated_word] * len(words))
                            logger.info(f"Translated repetitive text: {len(words)} instances of '{single_word}' -> '{translated_word}'")
                            return translated_text
                        else:
                            logger.warning("Failed to extract translation from repetitive text response")
                            return clean_text
                    else:
                        logger.warning(f"Translation API error for repetitive text: {response.status_code}")
                        return clean_text
            
            # Make translation request for normal text
            response = requests.get(
                self.base_url,
                params={
                    **self.params,
                    'q': clean_text
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Translation API error: {response.status_code}")
                return clean_text  # Return original text if translation fails
            
            # Parse response
            result = response.json()
            
            if result and len(result) > 0 and result[0]:
                # Extract translated text from the response
                translated_parts = []
                for part in result[0]:
                    if part and len(part) > 0:
                        translated_parts.append(part[0])
                
                translated_text = ''.join(translated_parts).strip()
                
                if translated_text and translated_text != clean_text:
                    logger.info(f"Translated {len(clean_text)} chars Arabic to {len(translated_text)} chars English")
                    return translated_text
                else:
                    logger.warning("Translation returned same text or empty result")
                    return clean_text
            else:
                logger.warning("Translation API returned unexpected format")
                return clean_text
                
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return arabic_text  # Return original text if translation fails
    
    async def translate_words(self, words: List[Dict]) -> List[Dict]:
        """
        Translate word segments from Arabic to English.
        
        Args:
            words: List of word segments with Arabic text
            
        Returns:
            List of word segments with English translations
        """
        try:
            if not words:
                return words
            
            # Extract Arabic text from words
            arabic_text = ' '.join([word.get('word', '') for word in words])
            
            # Translate the full text
            english_text = await self.translate_text(arabic_text)
            
            # Split English text back into words (simple approach)
            english_words = english_text.split()
            
            # Update word segments with English translations
            translated_words = []
            for i, word in enumerate(words):
                translated_word = {
                    **word,
                    'word': english_words[i] if i < len(english_words) else word.get('word', ''),
                    'original_word': word.get('word', '')  # Keep original Arabic word
                }
                translated_words.append(translated_word)
            
            return translated_words
            
        except Exception as e:
            logger.error(f"Error translating words: {str(e)}")
            return words  # Return original words if translation fails


# Global translation service instance
translation_service = TranslationService()
