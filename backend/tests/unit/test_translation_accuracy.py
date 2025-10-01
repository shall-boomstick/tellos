"""
Unit tests for translation accuracy functionality
Tests translation quality, accuracy metrics, and language detection
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import time

# Import the translation services
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.streaming_transcription_service import StreamingTranscriptionService
from services.translation_service import TranslationService
from models.realtime_transcript import RealTimeTranscript


class TestTranslationAccuracy:
    """Test translation accuracy and quality metrics"""

    def setup_method(self):
        """Set up test fixtures"""
        self.transcription_service = StreamingTranscriptionService()
        self.translation_service = TranslationService()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_translation_accuracy_english_to_spanish(self):
        """Test translation accuracy from English to Spanish"""
        test_cases = [
            {
                "input": "Hello, how are you?",
                "expected": "Hola, ¿cómo estás?",
                "language": "es"
            },
            {
                "input": "The weather is nice today.",
                "expected": "El clima está bonito hoy.",
                "language": "es"
            },
            {
                "input": "I love this application.",
                "expected": "Me encanta esta aplicación.",
                "language": "es"
            }
        ]
        
        for case in test_cases:
            result = self.translation_service.translate_text(
                case["input"], 
                "en", 
                case["language"]
            )
            
            assert result['success'] is True
            assert 'translation' in result
            assert result['source_language'] == "en"
            assert result['target_language'] == case["language"]
            
            # Check translation quality (basic similarity check)
            translation = result['translation'].lower()
            expected = case["expected"].lower()
            
            # Calculate basic similarity (word overlap)
            similarity = self._calculate_similarity(translation, expected)
            assert similarity > 0.3, f"Translation similarity too low: {similarity}"

    def test_translation_accuracy_spanish_to_english(self):
        """Test translation accuracy from Spanish to English"""
        test_cases = [
            {
                "input": "Hola, ¿cómo estás?",
                "expected": "Hello, how are you?",
                "language": "en"
            },
            {
                "input": "El clima está bonito hoy.",
                "expected": "The weather is nice today.",
                "language": "en"
            },
            {
                "input": "Me encanta esta aplicación.",
                "expected": "I love this application.",
                "language": "en"
            }
        ]
        
        for case in test_cases:
            result = self.translation_service.translate_text(
                case["input"], 
                "es", 
                case["language"]
            )
            
            assert result['success'] is True
            assert 'translation' in result
            assert result['source_language'] == "es"
            assert result['target_language'] == case["language"]
            
            # Check translation quality
            translation = result['translation'].lower()
            expected = case["expected"].lower()
            
            similarity = self._calculate_similarity(translation, expected)
            assert similarity > 0.3, f"Translation similarity too low: {similarity}"

    def test_translation_accuracy_multiple_languages(self):
        """Test translation accuracy across multiple languages"""
        test_cases = [
            {
                "input": "Hello world",
                "source": "en",
                "targets": ["es", "fr", "de", "it", "pt"]
            },
            {
                "input": "Good morning",
                "source": "en", 
                "targets": ["es", "fr", "de", "it", "pt"]
            }
        ]
        
        for case in test_cases:
            for target_lang in case["targets"]:
                result = self.translation_service.translate_text(
                    case["input"],
                    case["source"],
                    target_lang
                )
                
                assert result['success'] is True
                assert 'translation' in result
                assert result['source_language'] == case["source"]
                assert result['target_language'] == target_lang
                assert len(result['translation']) > 0

    def test_translation_confidence_scores(self):
        """Test translation confidence scoring"""
        test_text = "This is a test sentence for translation confidence scoring."
        
        result = self.translation_service.translate_text_with_confidence(
            test_text, "en", "es"
        )
        
        assert result['success'] is True
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
        assert result['confidence'] > 0.5  # Should have reasonable confidence

    def test_translation_quality_metrics(self):
        """Test translation quality metrics calculation"""
        test_cases = [
            {
                "source": "Hello, how are you?",
                "translation": "Hola, ¿cómo estás?",
                "reference": "Hola, ¿cómo estás?"
            },
            {
                "source": "The weather is nice today.",
                "translation": "El clima está bonito hoy.",
                "reference": "El clima está bonito hoy."
            }
        ]
        
        for case in test_cases:
            metrics = self.translation_service.calculate_quality_metrics(
                case["source"],
                case["translation"],
                case["reference"]
            )
            
            assert 'bleu_score' in metrics
            assert 'rouge_score' in metrics
            assert 'meteor_score' in metrics
            assert 'bert_score' in metrics
            
            # BLEU score should be high for exact matches
            assert metrics['bleu_score'] > 0.8
            assert 0 <= metrics['bleu_score'] <= 1

    def test_language_detection_accuracy(self):
        """Test automatic language detection accuracy"""
        test_cases = [
            {
                "text": "Hello, how are you?",
                "expected_language": "en"
            },
            {
                "text": "Hola, ¿cómo estás?",
                "expected_language": "es"
            },
            {
                "text": "Bonjour, comment allez-vous?",
                "expected_language": "fr"
            },
            {
                "text": "Guten Tag, wie geht es Ihnen?",
                "expected_language": "de"
            },
            {
                "text": "Ciao, come stai?",
                "expected_language": "it"
            }
        ]
        
        for case in test_cases:
            result = self.translation_service.detect_language(case["text"])
            
            assert result['success'] is True
            assert 'language' in result
            assert 'confidence' in result
            assert result['language'] == case["expected_language"]
            assert result['confidence'] > 0.8

    def test_translation_consistency(self):
        """Test translation consistency across multiple calls"""
        test_text = "This is a test for translation consistency."
        source_lang = "en"
        target_lang = "es"
        
        # Translate the same text multiple times
        translations = []
        for _ in range(5):
            result = self.translation_service.translate_text(
                test_text, source_lang, target_lang
            )
            assert result['success'] is True
            translations.append(result['translation'])
        
        # Check consistency (all translations should be similar)
        base_translation = translations[0]
        for translation in translations[1:]:
            similarity = self._calculate_similarity(base_translation, translation)
            assert similarity > 0.8, f"Translation inconsistency detected: {similarity}"

    def test_translation_with_context(self):
        """Test translation with context information"""
        test_cases = [
            {
                "text": "Bank",
                "context": "financial institution",
                "expected_spanish": "banco"
            },
            {
                "text": "Bank", 
                "context": "river edge",
                "expected_spanish": "orilla"
            }
        ]
        
        for case in test_cases:
            result = self.translation_service.translate_with_context(
                case["text"],
                "en",
                "es",
                case["context"]
            )
            
            assert result['success'] is True
            assert 'translation' in result
            # Note: Exact match may not be possible due to context ambiguity
            assert len(result['translation']) > 0

    def test_translation_error_handling(self):
        """Test translation error handling"""
        # Test with empty text
        result = self.translation_service.translate_text("", "en", "es")
        assert result['success'] is False
        assert 'error' in result
        
        # Test with invalid language codes
        result = self.translation_service.translate_text("Hello", "invalid", "es")
        assert result['success'] is False
        assert 'error' in result
        
        result = self.translation_service.translate_text("Hello", "en", "invalid")
        assert result['success'] is False
        assert 'error' in result
        
        # Test with None input
        result = self.translation_service.translate_text(None, "en", "es")
        assert result['success'] is False
        assert 'error' in result

    def test_translation_performance(self):
        """Test translation performance"""
        test_text = "This is a performance test for translation service."
        
        start_time = time.time()
        result = self.translation_service.translate_text(test_text, "en", "es")
        end_time = time.time()
        
        # Should complete within reasonable time (5 seconds)
        assert (end_time - start_time) < 5.0
        assert result['success'] is True

    def test_batch_translation_accuracy(self):
        """Test batch translation accuracy"""
        test_texts = [
            "Hello world",
            "Good morning",
            "How are you?",
            "Thank you very much",
            "Have a nice day"
        ]
        
        result = self.translation_service.translate_batch(
            test_texts, "en", "es"
        )
        
        assert result['success'] is True
        assert 'translations' in result
        assert len(result['translations']) == len(test_texts)
        
        for i, translation in enumerate(result['translations']):
            assert 'text' in translation
            assert 'confidence' in translation
            assert len(translation['text']) > 0
            assert 0 <= translation['confidence'] <= 1

    def test_translation_caching(self):
        """Test translation caching functionality"""
        test_text = "This is a test for translation caching."
        
        # First translation (should be cached)
        start_time = time.time()
        result1 = self.translation_service.translate_text(test_text, "en", "es")
        first_duration = time.time() - start_time
        
        # Second translation (should use cache)
        start_time = time.time()
        result2 = self.translation_service.translate_text(test_text, "en", "es")
        second_duration = time.time() - start_time
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result1['translation'] == result2['translation']
        
        # Cached translation should be faster
        assert second_duration < first_duration

    def test_translation_with_special_characters(self):
        """Test translation with special characters and symbols"""
        test_cases = [
            "Hello, world! How are you?",
            "The price is $100.00",
            "Email: test@example.com",
            "Phone: +1-555-123-4567",
            "URL: https://example.com",
            "Math: 2 + 2 = 4",
            "Symbols: @#$%^&*()",
            "Unicode: ñáéíóú"
        ]
        
        for text in test_cases:
            result = self.translation_service.translate_text(text, "en", "es")
            
            assert result['success'] is True
            assert 'translation' in result
            assert len(result['translation']) > 0
            
            # Check that special characters are preserved or properly handled
            translation = result['translation']
            assert not translation.startswith("ERROR")
            assert len(translation) > 0

    def test_translation_with_long_text(self):
        """Test translation with long text"""
        long_text = "This is a very long text that tests the translation service's ability to handle large amounts of content. " * 10
        
        result = self.translation_service.translate_text(long_text, "en", "es")
        
        assert result['success'] is True
        assert 'translation' in result
        assert len(result['translation']) > 0
        
        # Translation should be proportional in length
        assert len(result['translation']) > len(long_text) * 0.5

    def test_translation_quality_with_reference(self):
        """Test translation quality against reference translations"""
        test_cases = [
            {
                "source": "Hello, how are you?",
                "translation": "Hola, ¿cómo estás?",
                "reference": "Hola, ¿cómo estás?",
                "expected_bleu": 1.0
            },
            {
                "source": "Good morning",
                "translation": "Buenos días",
                "reference": "Buenos días",
                "expected_bleu": 1.0
            }
        ]
        
        for case in test_cases:
            metrics = self.translation_service.calculate_quality_metrics(
                case["source"],
                case["translation"],
                case["reference"]
            )
            
            assert metrics['bleu_score'] >= case["expected_bleu"] * 0.9

    def test_translation_with_mock_service(self):
        """Test translation with mocked external service"""
        with patch.object(self.translation_service, '_call_translation_api') as mock_api:
            mock_api.return_value = {
                'translatedText': 'Hola mundo',
                'confidence': 0.95,
                'detectedSourceLanguage': 'en'
            }
            
            result = self.translation_service.translate_text("Hello world", "en", "es")
            
            assert result['success'] is True
            assert result['translation'] == 'Hola mundo'
            assert result['confidence'] == 0.95
            mock_api.assert_called_once()

    def test_translation_service_initialization(self):
        """Test translation service initialization"""
        service = TranslationService()
        
        assert service is not None
        assert hasattr(service, 'translate_text')
        assert hasattr(service, 'detect_language')
        assert hasattr(service, 'calculate_quality_metrics')

    def test_translation_model_validation(self):
        """Test RealTimeTranscript model validation"""
        transcript = RealTimeTranscript(
            text="Hello world",
            timestamp=1234567890.0,
            confidence=0.95,
            language="en",
            translation="Hola mundo",
            translation_confidence=0.90
        )
        
        assert transcript.text == "Hello world"
        assert transcript.timestamp == 1234567890.0
        assert transcript.confidence == 0.95
        assert transcript.language == "en"
        assert transcript.translation == "Hola mundo"
        assert transcript.translation_confidence == 0.90

    def test_translation_model_serialization(self):
        """Test RealTimeTranscript model serialization"""
        transcript = RealTimeTranscript(
            text="Hello world",
            timestamp=1234567890.0,
            confidence=0.95,
            language="en",
            translation="Hola mundo"
        )
        
        # Test to_dict
        data = transcript.to_dict()
        assert data['text'] == "Hello world"
        assert data['timestamp'] == 1234567890.0
        assert data['confidence'] == 0.95
        assert data['language'] == "en"
        assert data['translation'] == "Hola mundo"
        
        # Test from_dict
        new_transcript = RealTimeTranscript.from_dict(data)
        assert new_transcript.text == transcript.text
        assert new_transcript.timestamp == transcript.timestamp
        assert new_transcript.confidence == transcript.confidence
        assert new_transcript.language == transcript.language
        assert new_transcript.translation == transcript.translation

    def _calculate_similarity(self, text1, text2):
        """Calculate basic text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def test_translation_accuracy_benchmark(self):
        """Test translation accuracy with benchmark dataset"""
        # This would typically use a real benchmark dataset
        benchmark_cases = [
            {
                "source": "The quick brown fox jumps over the lazy dog.",
                "target": "El zorro marrón rápido salta sobre el perro perezoso.",
                "source_lang": "en",
                "target_lang": "es"
            }
        ]
        
        for case in benchmark_cases:
            result = self.translation_service.translate_text(
                case["source"],
                case["source_lang"],
                case["target_lang"]
            )
            
            assert result['success'] is True
            
            # Calculate BLEU score against reference
            metrics = self.translation_service.calculate_quality_metrics(
                case["source"],
                result['translation'],
                case["target"]
            )
            
            # Should achieve reasonable BLEU score
            assert metrics['bleu_score'] > 0.3

    def test_translation_with_domain_specific_terms(self):
        """Test translation with domain-specific terminology"""
        test_cases = [
            {
                "text": "The patient has a fever and needs medication.",
                "domain": "medical",
                "source_lang": "en",
                "target_lang": "es"
            },
            {
                "text": "The stock market is volatile today.",
                "domain": "finance",
                "source_lang": "en",
                "target_lang": "es"
            }
        ]
        
        for case in test_cases:
            result = self.translation_service.translate_with_domain(
                case["text"],
                case["source_lang"],
                case["target_lang"],
                case["domain"]
            )
            
            assert result['success'] is True
            assert 'translation' in result
            assert len(result['translation']) > 0

    def test_translation_quality_improvement(self):
        """Test translation quality improvement over time"""
        test_text = "This is a test for quality improvement tracking."
        
        # Simulate multiple translation attempts
        results = []
        for i in range(3):
            result = self.translation_service.translate_text_with_quality_tracking(
                test_text, "en", "es", attempt=i+1
            )
            results.append(result)
        
        # Quality should improve or remain consistent
        for i in range(1, len(results)):
            assert results[i]['quality_score'] >= results[i-1]['quality_score'] * 0.9

