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

