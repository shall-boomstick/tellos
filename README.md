# SawtFeel - Arabic Audio Emotion Analysis

SawtFeel is a web application that analyzes Arabic audio/video files to provide real-time emotion visualization. The system uses a dual-path AI pipeline combining textual emotion analysis (from transcribed Arabic text) and tonal emotion analysis (from audio features) to create a synchronized emotion gauge with transcript highlighting.

## Features

- **Video/Audio Upload**: Support for MP4, AVI, MOV, MKV, WebM, FLV, MP3, WAV formats
- **Real-time Processing**: Live progress updates during file processing
- **Arabic Speech Recognition**: Automatic transcription with word-level timestamps
- **Emotion Analysis**: Dual-path analysis (text + audio tone) with confidence scores
- **Dark/Light Theme**: Responsive design with theme switching
- **Mobile Optimized**: Touch-friendly interface for mobile devices

## Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance API with automatic documentation
- **WebSocket**: Real-time communication for processing updates
- **AI/ML Stack**: Whisper for transcription, Transformers for emotion analysis
- **Video Processing**: FFmpeg for audio extraction, LibROSA for analysis
- **Redis**: Session management and caching

### Frontend (React/Vite)
- **React**: Component-based UI with hooks
- **Vite**: Fast development and optimized builds
- **Responsive Design**: Mobile-first CSS with dark/light themes
- **Real-time Updates**: WebSocket integration for live progress

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd tellos
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Upload File**: 
   - Drag and drop or select an Arabic audio/video file
   - Maximum duration: 2 minutes
   - Maximum size: 100MB

2. **Processing**:
   - Watch real-time progress updates
   - Processing stages: Upload → Extract → Transcribe → Analyze

3. **Results**:
   - View emotion analysis with confidence scores
   - Read Arabic transcript with word-level timing
   - Play audio with synchronized emotion visualization

## Testing

The application includes comprehensive test coverage:

### Contract Tests
```bash
cd backend
pytest tests/contract/ -v
```

### Integration Tests
```bash
# Test with sample video
pytest tests/integration/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Performance Requirements

- **Video Processing**: Within 1.5x real-time duration
- **Audio Extraction**: <50ms latency
- **Emotion Analysis**: <200ms processing time
- **Memory Usage**: Constant during continuous processing
- **File Constraints**: 2-minute max duration, 100MB max size

## Constitutional Compliance

This application follows the Tellos Constitution v1.1.0:
- ✅ Video-first architecture with real-time audio extraction
- ✅ CLI interface support for all processing features
- ✅ Test-first development with comprehensive coverage
- ✅ Integration testing for all critical paths
- ✅ Observability with structured logging and metrics

## API Documentation

The backend provides OpenAPI documentation at `/docs` when running. Key endpoints:

- `POST /api/upload`: Upload audio/video file
- `GET /api/upload/{id}/status`: Get processing status
- `GET /api/processing/{id}/transcript`: Get transcription results
- `GET /api/processing/{id}/emotions`: Get emotion analysis
- `WS /ws/processing/{id}`: Real-time processing updates
- `WS /ws/playback/{id}`: Real-time playback synchronization

## Development Status

### Completed ✅
- Project structure and dependencies
- File upload and validation
- Basic UI with dark/light themes
- Contract tests for all APIs
- Docker containerization
- Constitutional compliance validation

### In Progress 🚧
- AI/ML integration (Whisper + Transformers)
- WebSocket real-time communication
- Audio player with synchronization
- Emotion gauge visualization
- Complete integration testing

### Planned 📋
- Performance optimization
- Comprehensive error handling
- Production deployment
- User documentation
- Accessibility improvements

## Contributing

1. Follow TDD approach: Write tests first
2. Ensure constitutional compliance
3. Test with `videos/aggression.mp4` sample
4. Maintain mobile responsiveness
5. Update task list in `specs/001-lets-create-our/tasks.md`

## License

This project is part of the Tellos system and follows the project's governance model.
