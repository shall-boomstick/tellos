# API Documentation

This document provides comprehensive documentation for the Real-Time Video Translation and Emotion Analysis API.

## Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [Error Handling](#error-handling)
- [Video Processing API](#video-processing-api)
- [Translation API](#translation-api)
- [Emotion Analysis API](#emotion-analysis-api)
- [WebSocket API](#websocket-api)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)

## Authentication

The API uses API key authentication. Include your API key in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

1. Register for an account at the API portal
2. Navigate to the API Keys section
3. Generate a new API key
4. Store the key securely

## Base URL

All API requests should be made to:

```
https://api.example.com/v1
```

For local development:

```
http://localhost:8000/api/v1
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request is invalid",
    "details": {
      "field": "video_file",
      "reason": "File format not supported"
    }
  },
  "timestamp": "2023-12-07T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Video Processing API

### Upload Video

Upload a video file for processing.

```http
POST /videos/upload
Content-Type: multipart/form-data
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Video file to upload |
| `metadata` | Object | No | Additional video metadata |

#### Example Request

```bash
curl -X POST "https://api.example.com/v1/videos/upload" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@video.mp4" \
  -F 'metadata={"title":"My Video","description":"Test video"}'
```

#### Response

```json
{
  "video_id": "vid_123456789",
  "status": "uploaded",
  "metadata": {
    "filename": "video.mp4",
    "size": 1048576,
    "duration": 120.5,
    "format": "mp4",
    "resolution": {
      "width": 1920,
      "height": 1080
    },
    "fps": 30
  },
  "upload_url": "https://api.example.com/v1/videos/vid_123456789/stream",
  "created_at": "2023-12-07T10:30:00Z"
}
```

### Get Video Metadata

Retrieve metadata for a specific video.

```http
GET /videos/{video_id}/metadata
```

#### Response

```json
{
  "video_id": "vid_123456789",
  "metadata": {
    "filename": "video.mp4",
    "size": 1048576,
    "duration": 120.5,
    "format": "mp4",
    "resolution": {
      "width": 1920,
      "height": 1080
    },
    "fps": 30,
    "codec": "h264",
    "bitrate": 2000000
  },
  "status": "processed",
  "created_at": "2023-12-07T10:30:00Z",
  "updated_at": "2023-12-07T10:35:00Z"
}
```

### Stream Video

Stream video content for playback.

```http
GET /videos/{video_id}/stream
Range: bytes=0-1023
```

#### Response Headers

```
Content-Type: video/mp4
Content-Length: 1048576
Accept-Ranges: bytes
Content-Range: bytes 0-1023/1048576
```

### Delete Video

Delete a video and all associated data.

```http
DELETE /videos/{video_id}
```

#### Response

```json
{
  "video_id": "vid_123456789",
  "status": "deleted",
  "deleted_at": "2023-12-07T10:40:00Z"
}
```

## Translation API

### Translate Text

Translate text from one language to another.

```http
POST /translation/translate
Content-Type: application/json
```

#### Request Body

```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "es",
  "options": {
    "confidence_threshold": 0.8,
    "include_alternatives": true
  }
}
```

#### Response

```json
{
  "translation_id": "trans_123456789",
  "source_text": "Hello, how are you?",
  "translated_text": "Hola, ¿cómo estás?",
  "source_language": "en",
  "target_language": "es",
  "confidence": 0.95,
  "alternatives": [
    {
      "text": "Hola, ¿cómo te encuentras?",
      "confidence": 0.88
    }
  ],
  "processing_time": 0.5,
  "created_at": "2023-12-07T10:30:00Z"
}
```

### Batch Translation

Translate multiple texts in a single request.

```http
POST /translation/batch
Content-Type: application/json
```

#### Request Body

```json
{
  "texts": [
    "Hello, how are you?",
    "What is your name?",
    "Nice to meet you"
  ],
  "source_language": "en",
  "target_language": "es"
}
```

#### Response

```json
{
  "batch_id": "batch_123456789",
  "translations": [
    {
      "text": "Hello, how are you?",
      "translation": "Hola, ¿cómo estás?",
      "confidence": 0.95
    },
    {
      "text": "What is your name?",
      "translation": "¿Cuál es tu nombre?",
      "confidence": 0.92
    },
    {
      "text": "Nice to meet you",
      "translation": "Mucho gusto conocerte",
      "confidence": 0.88
    }
  ],
  "processing_time": 1.2,
  "created_at": "2023-12-07T10:30:00Z"
}
```

### Get Supported Languages

Retrieve list of supported languages.

```http
GET /translation/languages
```

#### Response

```json
{
  "languages": [
    {
      "code": "en",
      "name": "English",
      "native_name": "English"
    },
    {
      "code": "es",
      "name": "Spanish",
      "native_name": "Español"
    },
    {
      "code": "fr",
      "name": "French",
      "native_name": "Français"
    }
  ],
  "total": 50
}
```

### Detect Language

Automatically detect the language of input text.

```http
POST /translation/detect
Content-Type: application/json
```

#### Request Body

```json
{
  "text": "Hola, ¿cómo estás?"
}
```

#### Response

```json
{
  "language": "es",
  "confidence": 0.98,
  "alternatives": [
    {
      "language": "ca",
      "confidence": 0.02
    }
  ]
}
```

## Emotion Analysis API

### Analyze Emotion

Analyze emotions from an image or video frame.

```http
POST /emotion/analyze
Content-Type: multipart/form-data
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Image or video frame to analyze |
| `options` | Object | No | Analysis options |

#### Example Request

```bash
curl -X POST "https://api.example.com/v1/emotion/analyze" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "image=@frame.jpg" \
  -F 'options={"include_confidence":true,"include_alternatives":true}'
```

#### Response

```json
{
  "analysis_id": "emotion_123456789",
  "emotions": [
    {
      "emotion": "happy",
      "confidence": 0.85,
      "intensity": "high"
    },
    {
      "emotion": "joy",
      "confidence": 0.72,
      "intensity": "medium"
    }
  ],
  "dominant_emotion": "happy",
  "overall_confidence": 0.85,
  "face_detected": true,
  "bounding_box": {
    "x": 100,
    "y": 150,
    "width": 200,
    "height": 250
  },
  "processing_time": 0.3,
  "created_at": "2023-12-07T10:30:00Z"
}
```

### Batch Emotion Analysis

Analyze emotions from multiple images.

```http
POST /emotion/batch
Content-Type: multipart/form-data
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `images` | File[] | Yes | Array of images to analyze |
| `options` | Object | No | Analysis options |

#### Response

```json
{
  "batch_id": "emotion_batch_123456789",
  "analyses": [
    {
      "image_id": "img_1",
      "emotions": [
        {
          "emotion": "happy",
          "confidence": 0.85
        }
      ],
      "dominant_emotion": "happy",
      "confidence": 0.85
    },
    {
      "image_id": "img_2",
      "emotions": [
        {
          "emotion": "sad",
          "confidence": 0.78
        }
      ],
      "dominant_emotion": "sad",
      "confidence": 0.78
    }
  ],
  "processing_time": 0.8,
  "created_at": "2023-12-07T10:30:00Z"
}
```

### Get Emotion History

Retrieve emotion analysis history for a video.

```http
GET /emotion/history?video_id={video_id}&start_time={start}&end_time={end}
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | String | Yes | Video ID |
| `start_time` | Number | No | Start timestamp (seconds) |
| `end_time` | Number | No | End timestamp (seconds) |
| `limit` | Number | No | Maximum number of results (default: 100) |

#### Response

```json
{
  "video_id": "vid_123456789",
  "emotions": [
    {
      "timestamp": 0.0,
      "emotions": [
        {
          "emotion": "happy",
          "confidence": 0.85
        }
      ],
      "dominant_emotion": "happy",
      "confidence": 0.85
    },
    {
      "timestamp": 1.0,
      "emotions": [
        {
          "emotion": "sad",
          "confidence": 0.78
        }
      ],
      "dominant_emotion": "sad",
      "confidence": 0.78
    }
  ],
  "total": 120,
  "has_more": false
}
```

## WebSocket API

### Connection

Connect to the WebSocket endpoint for real-time updates:

```javascript
const ws = new WebSocket('wss://api.example.com/ws/realtime');
```

### Authentication

Send authentication message after connection:

```json
{
  "type": "auth",
  "api_key": "YOUR_API_KEY"
}
```

### Message Types

#### Transcription Message

```json
{
  "type": "transcription",
  "data": {
    "text": "Hello, how are you?",
    "timestamp": 10.5,
    "confidence": 0.95,
    "language": "en"
  }
}
```

#### Translation Message

```json
{
  "type": "translation",
  "data": {
    "text": "Hello, how are you?",
    "translation": "Hola, ¿cómo estás?",
    "timestamp": 10.5,
    "confidence": 0.92,
    "source_language": "en",
    "target_language": "es"
  }
}
```

#### Emotion Message

```json
{
  "type": "emotion",
  "data": {
    "timestamp": 10.5,
    "emotions": [
      {
        "emotion": "happy",
        "confidence": 0.85
      }
    ],
    "dominant_emotion": "happy",
    "confidence": 0.85,
    "face_detected": true
  }
}
```

#### Video Progress Message

```json
{
  "type": "video_progress",
  "data": {
    "current_time": 10.5,
    "duration": 120.0,
    "percentage": 8.75
  }
}
```

#### Error Message

```json
{
  "type": "error",
  "data": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to process video frame",
    "timestamp": "2023-12-07T10:30:00Z"
  }
}
```

### Sending Messages

#### Start Processing

```json
{
  "type": "start_processing",
  "data": {
    "video_id": "vid_123456789",
    "options": {
      "enable_translation": true,
      "enable_emotion_analysis": true,
      "target_language": "es"
    }
  }
}
```

#### Stop Processing

```json
{
  "type": "stop_processing",
  "data": {
    "video_id": "vid_123456789"
  }
}
```

#### Seek Video

```json
{
  "type": "seek",
  "data": {
    "video_id": "vid_123456789",
    "timestamp": 30.0
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Video Upload | 10 requests | 1 minute |
| Translation | 100 requests | 1 minute |
| Emotion Analysis | 50 requests | 1 minute |
| WebSocket | 1 connection | per user |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_time": "2023-12-07T11:00:00Z"
    }
  }
}
```

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

class VideoTranslationAPI {
  constructor(apiKey, baseURL = 'https://api.example.com/v1') {
    this.apiKey = apiKey;
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async uploadVideo(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const response = await this.client.post('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return response.data;
  }

  async translateText(text, sourceLang, targetLang) {
    const response = await this.client.post('/translation/translate', {
      text,
      source_language: sourceLang,
      target_language: targetLang
    });

    return response.data;
  }

  async analyzeEmotion(image) {
    const formData = new FormData();
    formData.append('image', image);

    const response = await this.client.post('/emotion/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return response.data;
  }
}

// Usage
const api = new VideoTranslationAPI('your-api-key');
const result = await api.translateText('Hello', 'en', 'es');
console.log(result.translated_text); // "Hola"
```

### Python

```python
import requests
import json

class VideoTranslationAPI:
    def __init__(self, api_key, base_url='https://api.example.com/v1'):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def upload_video(self, file_path, metadata=None):
        url = f'{self.base_url}/videos/upload'
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'metadata': json.dumps(metadata or {})}
            
            response = requests.post(url, files=files, data=data, headers={'Authorization': f'Bearer {self.api_key}'})
            response.raise_for_status()
            
        return response.json()

    def translate_text(self, text, source_lang, target_lang):
        url = f'{self.base_url}/translation/translate'
        data = {
            'text': text,
            'source_language': source_lang,
            'target_language': target_lang
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        
        return response.json()

    def analyze_emotion(self, image_path):
        url = f'{self.base_url}/emotion/analyze'
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            
            response = requests.post(url, files=files, headers={'Authorization': f'Bearer {self.api_key}'})
            response.raise_for_status()
            
        return response.json()

# Usage
api = VideoTranslationAPI('your-api-key')
result = api.translate_text('Hello', 'en', 'es')
print(result['translated_text'])  # "Hola"
```

### WebSocket Example

```javascript
class RealtimeVideoAPI {
  constructor(apiKey, wsURL = 'wss://api.example.com/ws/realtime') {
    this.apiKey = apiKey;
    this.wsURL = wsURL;
    this.ws = null;
  }

  connect() {
    this.ws = new WebSocket(this.wsURL);
    
    this.ws.onopen = () => {
      // Authenticate
      this.ws.send(JSON.stringify({
        type: 'auth',
        api_key: this.apiKey
      }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'transcription':
        this.onTranscription(data.data);
        break;
      case 'translation':
        this.onTranslation(data.data);
        break;
      case 'emotion':
        this.onEmotion(data.data);
        break;
      case 'error':
        this.onError(data.data);
        break;
    }
  }

  startProcessing(videoId, options = {}) {
    this.ws.send(JSON.stringify({
      type: 'start_processing',
      data: {
        video_id: videoId,
        options
      }
    }));
  }

  stopProcessing(videoId) {
    this.ws.send(JSON.stringify({
      type: 'stop_processing',
      data: {
        video_id: videoId
      }
    }));
  }

  // Event handlers (override in your implementation)
  onTranscription(data) {
    console.log('Transcription:', data);
  }

  onTranslation(data) {
    console.log('Translation:', data);
  }

  onEmotion(data) {
    console.log('Emotion:', data);
  }

  onError(data) {
    console.error('Error:', data);
  }
}

// Usage
const api = new RealtimeVideoAPI('your-api-key');
api.connect();
api.startProcessing('vid_123456789', {
  enable_translation: true,
  enable_emotion_analysis: true,
  target_language: 'es'
});
```

## Changelog

### Version 1.0.0 (2023-12-07)

- Initial API release
- Video upload and processing
- Real-time translation
- Emotion analysis
- WebSocket support
- Rate limiting
- Comprehensive error handling

---

*For more information, visit our [documentation site](https://docs.example.com) or contact support at [support@example.com](mailto:support@example.com).*

