# Real-Time Video Translation and Emotion Analysis Interface

A comprehensive real-time video processing system that provides live translation and emotion analysis capabilities with a modern, accessible web interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Performance](#performance)
- [Accessibility](#accessibility)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

This system provides real-time video processing capabilities including:

- **Live Video Streaming**: Process video files in real-time with smooth playback
- **Real-Time Translation**: Automatic transcription and translation of spoken content
- **Emotion Analysis**: AI-powered emotion detection and analysis
- **Accessible Interface**: Full keyboard navigation and screen reader support
- **Performance Optimization**: Efficient caching and processing strategies

## Features

### Core Functionality

- **Video Processing**: Support for multiple video formats (MP4, AVI, MOV)
- **Real-Time Translation**: Multi-language support with confidence scoring
- **Emotion Analysis**: Facial emotion detection with real-time updates
- **WebSocket Communication**: Low-latency real-time data streaming
- **Caching System**: Intelligent caching for improved performance

### User Interface

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Accessibility**: WCAG 2.1 AA compliant interface
- **Real-Time Updates**: Live synchronization of video, translation, and emotion data
- **Customizable Settings**: User-configurable display and processing options

### Performance

- **Optimized Processing**: Efficient video and audio processing pipelines
- **Memory Management**: Smart memory usage and garbage collection
- **Caching Strategies**: Multiple caching layers for optimal performance
- **Load Balancing**: Automatic scaling based on system load

## Architecture

### Backend Components

```
backend/
├── src/
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── api/             # REST API endpoints
│   └── utils/           # Utility functions
├── tests/               # Test suites
└── requirements.txt     # Python dependencies
```

### Frontend Components

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API and WebSocket services
│   ├── store/          # State management
│   └── utils/          # Utility functions
├── tests/              # Test suites
└── package.json        # Node.js dependencies
```

### Key Services

- **VideoMetadataService**: Video file validation and metadata extraction
- **StreamingTranscriptionService**: Real-time audio transcription
- **StreamingEmotionService**: Real-time emotion analysis
- **RealtimeProcessor**: Main processing orchestrator
- **CacheService**: Multi-layer caching system

## Processing Pipeline: From Upload to Analysis

### Overview

Our system processes Arabic audio/video files through a sophisticated pipeline that combines speech recognition, translation, and dual-path emotion analysis. Here's the complete journey from upload to final analysis:

### 1. File Upload & Validation

**Input Requirements:**
- **Supported Formats**: MP4, AVI, MOV, MKV, WebM, FLV (video) and MP3, WAV (audio)
- **Maximum Duration**: 2 minutes
- **Maximum Size**: 100MB
- **Language**: Arabic audio content

**Processing Steps:**
1. File validation and format verification
2. Temporary storage in `/tmp/uploads/`
3. Audio extraction from video files using FFmpeg
4. Audio preprocessing (normalization, resampling to 16kHz)

### 2. Speech Recognition & Transcription

**Model Used:**
- **Whisper Model**: `openai/whisper-medium` (configurable via `TRANSCRIPTION_SERVICE` env var)
- **Fallback Option**: Google Gemini Flash 2.5 (when `TRANSCRIPTION_SERVICE=gemini`)
- **Language**: Optimized for Arabic speech recognition
- **Segmentation**: 2-second overlapping segments for real-time processing

**Process:**
1. Audio chunking into 2-second segments with 0.5-second overlap
2. Transcription using configured service (Whisper or Gemini)
3. Confidence scoring for each transcription
4. Temporal alignment with original audio timestamps

**Service Configuration:**
- **Default**: Whisper Medium model (`openai/whisper-medium`)
- **Environment Variable**: `TRANSCRIPTION_SERVICE` (default: "whisper")
- **Gemini Option**: Set `TRANSCRIPTION_SERVICE=gemini` to use Google Gemini Flash 2.5
- **Fallback**: If Gemini fails, automatically falls back to Whisper

**Output:**
```json
{
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 2.0,
      "arabic_text": "السلام عليكم",
      "english_text": "Peace be upon you",
      "confidence": 0.95
    }
  ]
}
```

### 3. Dual-Path Emotion Analysis

Our emotion analysis uses a sophisticated dual-path approach combining textual and tonal analysis:

#### 3.1 Textual Emotion Analysis

**Primary Model:**
- **Arabic BERT**: `CAMeL-Lab/bert-base-arabic-camelbert-msa-sentiment`
- **Specialization**: Modern Standard Arabic (MSA) sentiment analysis
- **Fallback Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest`

**Process:**
1. Arabic text preprocessing and normalization
2. Sentiment classification (POSITIVE/NEGATIVE/NEUTRAL)
3. Confidence scoring for each prediction
4. Emotion mapping to standard emotion types

#### 3.2 Tonal Emotion Analysis

**Approach**: Feature-based audio analysis (no heavy neural networks)

**Audio Features Extracted:**
- **Energy Features**: RMS energy, energy variance
- **Spectral Features**: Spectral centroid, bandwidth, rolloff
- **Pitch Features**: Fundamental frequency analysis
- **Rhythm Features**: Tempo detection, beat tracking
- **Other Features**: Zero crossing rate, MFCCs

**Libraries Used:**
- **Librosa**: Advanced audio feature extraction
- **NumPy**: Numerical computations
- **Rule-based Classification**: Heuristic emotion mapping

**Process:**
1. Audio feature extraction for each 2-second segment
2. Vocal tone analysis (pitch, energy, spectral characteristics)
3. Intensity pattern analysis
4. Rule-based emotion classification

#### 3.3 Combined Emotion Analysis

**Integration Method:**
1. Weighted combination of textual and tonal confidence scores
2. Temporal smoothing across segments
3. Confidence-weighted emotion selection

**Emotion Types Detected:**
- **JOY** (happiness, excitement)
- **SADNESS** (sorrow, melancholy)  
- **ANGER** (aggression, frustration)
- **FEAR** (anxiety, worry)
- **SURPRISE** (shock, amazement)
- **NEUTRAL** (calm, balanced)

**Output:**
```json
{
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 2.0,
      "textual_emotion": "neutral",
      "textual_confidence": 0.75,
      "tonal_emotion": "joy",
      "tonal_confidence": 0.6,
      "combined_emotion": "neutral",
      "combined_confidence": 0.68
    }
  ]
}
```

### 4. Real-Time Processing & Streaming

**WebSocket Architecture:**
- **Real-time Updates**: Live emotion and translation data
- **Session Management**: Individual user sessions with state tracking
- **Caching**: Intelligent caching for performance optimization

**Processing Pipeline:**
1. **Chunk Processing**: 2-second audio chunks with overlap
2. **Parallel Analysis**: Simultaneous transcription and emotion analysis
3. **Real-time Streaming**: WebSocket updates to frontend
4. **State Management**: Session-based processing state tracking

### 5. Caching & Performance Optimization

**Caching Strategy:**
- **File-level Caching**: Complete results cached per file
- **Segment-level Caching**: Individual processing results
- **Model Caching**: Pre-loaded models for faster inference
- **Redis Storage**: Session and temporary data storage

**Performance Optimizations:**
- **Lazy Loading**: Models loaded only when needed
- **Feature-based Audio**: Avoids heavy neural networks for audio
- **Async Processing**: Non-blocking I/O operations
- **Memory Management**: Efficient resource utilization

### 6. Assumptions & Limitations

#### Technical Assumptions:
1. **Audio Quality**: Assumes clear, audible Arabic speech
2. **Language**: Optimized for Modern Standard Arabic (MSA)
3. **Duration**: 2-minute limit ensures processing efficiency
4. **Format**: Standard audio/video formats with good compression

#### Model Assumptions:
1. **Arabic BERT**: Assumes MSA dialect (may not work well with regional dialects)
2. **Whisper**: Assumes clear pronunciation and minimal background noise
3. **Audio Features**: Assumes human speech (not music or environmental sounds)
4. **Emotion Mapping**: Assumes standard emotion categories apply across cultures

#### Processing Assumptions:
1. **Real-time**: Assumes 2-second segments provide sufficient context
2. **Overlap**: Assumes 0.5-second overlap prevents emotion boundary issues
3. **Combination**: Assumes textual and tonal emotions can be meaningfully combined
4. **Caching**: Assumes file-level caching is sufficient for performance

### 7. Error Handling & Fallbacks

**Graceful Degradation:**
1. **Model Failures**: Fallback to simpler models or rule-based analysis
2. **Processing Errors**: Continue with available data
3. **Network Issues**: Retry mechanisms and offline processing
4. **Resource Constraints**: Adaptive quality reduction

**Quality Assurance:**
- Confidence scoring for all outputs
- Validation of processing results
- Error logging and monitoring
- User feedback mechanisms

### 8. Output Format

**Final Results Structure:**
```json
{
  "file_id": "uuid",
  "overall_emotion": "neutral",
  "overall_confidence": 0.89,
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 2.0,
      "arabic_text": "السلام عليكم",
      "english_text": "Peace be upon you",
      "textual_emotion": "neutral",
      "textual_confidence": 0.75,
      "tonal_emotion": "joy",
      "tonal_confidence": 0.6,
      "combined_emotion": "neutral",
      "combined_confidence": 0.68
    }
  ],
  "processing_metadata": {
    "models_used": ["whisper-medium", "camelbert-msa-sentiment"],
    "processing_time": 45.2,
    "segments_processed": 15
  }
}
```

This comprehensive pipeline ensures accurate, real-time emotion analysis while maintaining performance and reliability.

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Docker (optional)
- FFmpeg (for video processing)

### Backend Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tellos
```

2. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
python -m alembic upgrade head
```

### Frontend Installation

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

### Docker Installation

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## Usage

### Starting the Application

1. Start the backend:
```bash
cd backend
python main.py
```

2. Start the frontend:
```bash
cd frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:3000`

### Basic Usage

1. **Upload Video**: Click the upload button or drag and drop a video file
2. **Play Video**: Use the video player controls or keyboard shortcuts
3. **View Translation**: Real-time translation appears below the video
4. **Monitor Emotions**: Emotion analysis is displayed in the gauge component
5. **Adjust Settings**: Use the settings panel to customize the interface

### Keyboard Shortcuts

- `Space`: Play/Pause video
- `←/→`: Seek backward/forward (10 seconds)
- `↑/↓`: Volume up/down
- `M`: Toggle mute
- `F`: Toggle fullscreen
- `T`: Toggle translation display
- `E`: Toggle emotion analysis
- `H`: Show help
- `S`: Show settings
- `U`: Open file upload
- `Esc`: Close modals/overlays

## API Documentation

### REST API Endpoints

#### Video Processing

- `POST /api/video/upload` - Upload video file
- `GET /api/video/{id}/metadata` - Get video metadata
- `GET /api/video/{id}/stream` - Stream video content
- `DELETE /api/video/{id}` - Delete video file

#### Translation

- `POST /api/translation/translate` - Translate text
- `GET /api/translation/languages` - Get supported languages
- `POST /api/translation/batch` - Batch translation

#### Emotion Analysis

- `POST /api/emotion/analyze` - Analyze emotion from image
- `GET /api/emotion/history` - Get emotion analysis history
- `POST /api/emotion/batch` - Batch emotion analysis

### WebSocket API

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime');
```

#### Message Types

- `transcription`: Real-time transcription data
- `translation`: Real-time translation data
- `emotion`: Real-time emotion analysis data
- `video_progress`: Video playback progress
- `error`: Error messages

#### Example Usage

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'transcription':
      updateTranscription(data.data);
      break;
    case 'translation':
      updateTranslation(data.data);
      break;
    case 'emotion':
      updateEmotion(data.data);
      break;
  }
};
```

## Configuration

### Backend Configuration

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./app.db

# API Keys
OPENAI_API_KEY=your_openai_key
GOOGLE_TRANSLATE_API_KEY=your_google_key

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Processing
MAX_WORKERS=4
BATCH_SIZE=10
CACHE_TTL=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### Frontend Configuration

Create a `.env.local` file in the frontend directory:

```env
# API
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Features
REACT_APP_ENABLE_TRANSLATION=true
REACT_APP_ENABLE_EMOTION_ANALYSIS=true
REACT_APP_ENABLE_ACCESSIBILITY=true

# Performance
REACT_APP_CACHE_SIZE=1000
REACT_APP_DEBOUNCE_DELAY=300
```

## Performance

### Optimization Features

- **Caching**: Multi-layer caching system for improved performance
- **Memory Management**: Automatic memory cleanup and optimization
- **Load Balancing**: Dynamic worker scaling based on system load
- **Batch Processing**: Efficient batch processing for multiple operations

### Performance Monitoring

Use the performance optimization script:

```bash
python scripts/optimize_performance.py --monitor
```

### Performance Metrics

- **Video Processing**: < 2 seconds per frame
- **Translation**: < 1 second per request
- **Emotion Analysis**: < 0.5 seconds per frame
- **Memory Usage**: < 500MB under normal load
- **CPU Usage**: < 80% under normal load

## Accessibility

### Features

- **Keyboard Navigation**: Full keyboard support for all functionality
- **Screen Reader Support**: ARIA labels and live regions
- **High Contrast Mode**: Automatic detection and support
- **Reduced Motion**: Respects user preferences
- **Focus Management**: Proper focus handling and trapping

### Testing Accessibility

```bash
# Run accessibility tests
npm run test:accessibility

# Run with screen reader
npm run test:screen-reader
```

## Testing

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test

# Performance tests
python scripts/run_performance_tests.py

# End-to-end tests
npm run test:e2e
```

### Test Coverage

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All major workflows
- **Performance Tests**: Load and stress testing
- **Accessibility Tests**: WCAG 2.1 AA compliance

## Deployment

### Production Deployment

1. **Backend Deployment**:
```bash
# Build Docker image
docker build -t tellos-backend ./backend

# Run with production settings
docker run -d -p 8000:8000 tellos-backend
```

2. **Frontend Deployment**:
```bash
# Build for production
npm run build

# Serve with nginx
nginx -s reload
```

### Environment Variables

Set the following environment variables in production:

```env
# Production settings
DEBUG=False
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
```

### Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics at `/metrics`
- **Logs**: Structured logging with correlation IDs

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Follow ESLint configuration
- **TypeScript**: Use strict mode
- **Tests**: Write descriptive test names

### Commit Messages

Use conventional commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@example.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and updates.

## Roadmap

- [ ] Mobile app support
- [ ] Additional language support
- [ ] Advanced emotion analysis
- [ ] Real-time collaboration
- [ ] Cloud deployment options

