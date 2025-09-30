# Data Model: SawtFeel Arabic Audio Emotion Analysis

## Core Entities

### AudioFile
**Purpose**: Represents uploaded audio/video file with processing metadata

**Attributes**:
- `id`: string (UUID) - Unique identifier
- `filename`: string - Original filename
- `file_type`: enum (audio, video) - Type of uploaded file
- `format`: string - File format (MP3, WAV, MP4, etc.)
- `duration`: float - Duration in seconds
- `file_size`: integer - Size in bytes
- `upload_timestamp`: datetime - When file was uploaded
- `processing_status`: enum (uploaded, extracting, transcribing, analyzing, completed, failed) - Current processing state
- `file_path`: string - Temporary storage path
- `expires_at`: datetime - When file will be automatically deleted

**Validation Rules**:
- Duration must be ≤ 120 seconds (2 minutes)
- File size must be ≤ 100MB
- Format must be in supported formats list
- Expires at must be 24 hours from upload

**State Transitions**:
- uploaded → extracting (video files only)
- extracting → transcribing
- transcribing → analyzing
- analyzing → completed
- Any state → failed (on error)

### Transcript
**Purpose**: Represents time-stamped Arabic text with word-level timing

**Attributes**:
- `id`: string (UUID) - Unique identifier
- `audio_file_id`: string (UUID) - Reference to AudioFile
- `text`: string - Full Arabic transcript
- `words`: array of WordSegment - Word-level timing data
- `language`: string - Detected language (should be "ar")
- `confidence`: float - Overall transcription confidence (0-1)
- `created_at`: datetime - When transcript was generated

**WordSegment Structure**:
- `word`: string - Arabic word
- `start_time`: float - Start time in seconds
- `end_time`: float - End time in seconds
- `confidence`: float - Word-level confidence (0-1)

**Validation Rules**:
- Text must not be empty
- All words must have valid start/end times
- Start times must be in ascending order
- Confidence must be between 0 and 1

### EmotionAnalysis
**Purpose**: Represents emotional state data with timestamps and confidence scores

**Attributes**:
- `id`: string (UUID) - Unique identifier
- `audio_file_id`: string (UUID) - Reference to AudioFile
- `segments`: array of EmotionSegment - Time-based emotion data
- `overall_emotion`: string - Primary emotion for entire file
- `overall_confidence`: float - Overall confidence (0-1)
- `created_at`: datetime - When analysis was generated

**EmotionSegment Structure**:
- `start_time`: float - Start time in seconds
- `end_time`: float - End time in seconds
- `textual_emotion`: string - Emotion from text analysis
- `textual_confidence`: float - Text emotion confidence (0-1)
- `tonal_emotion`: string - Emotion from audio tone
- `tonal_confidence`: float - Tone emotion confidence (0-1)
- `combined_emotion`: string - Final combined emotion
- `combined_confidence`: float - Combined confidence (0-1)

**Emotion Types**:
- `anger` - Anger/frustration
- `sadness` - Sadness/melancholy
- `joy` - Joy/happiness
- `neutral` - Neutral/calm
- `fear` - Fear/anxiety
- `surprise` - Surprise/shock

**Validation Rules**:
- All segments must have valid time ranges
- Emotions must be from valid emotion types
- All confidence values must be between 0 and 1
- Time segments must not overlap

### PlaybackState
**Purpose**: Represents current audio position and synchronization data for UI updates

**Attributes**:
- `session_id`: string - WebSocket session identifier
- `audio_file_id`: string (UUID) - Reference to AudioFile
- `current_time`: float - Current playback position in seconds
- `is_playing`: boolean - Whether audio is currently playing
- `playback_speed`: float - Playback speed multiplier
- `last_updated`: datetime - Last state update timestamp

**Validation Rules**:
- Current time must be ≥ 0 and ≤ audio duration
- Playback speed must be > 0 and ≤ 2.0
- Session must be active (last_updated within 5 minutes)

## Relationships

### AudioFile → Transcript
- **Type**: One-to-One
- **Description**: Each audio file has exactly one transcript
- **Cascade**: Delete transcript when audio file is deleted

### AudioFile → EmotionAnalysis
- **Type**: One-to-One
- **Description**: Each audio file has exactly one emotion analysis
- **Cascade**: Delete analysis when audio file is deleted

### AudioFile → PlaybackState
- **Type**: One-to-Many
- **Description**: Each audio file can have multiple active playback sessions
- **Cascade**: Delete playback states when audio file is deleted

## Data Flow

### Upload Flow
1. User uploads file → AudioFile created with status "uploaded"
2. If video → status changes to "extracting", audio extracted
3. Audio sent to transcription → status "transcribing", Transcript created
4. Audio sent to emotion analysis → status "analyzing", EmotionAnalysis created
5. Both complete → status "completed"

### Playback Flow
1. User starts playback → PlaybackState created
2. WebSocket sends current time updates
3. Frontend queries Transcript and EmotionAnalysis for current time
4. UI updates with highlighted words and emotion gauge
5. User stops → PlaybackState marked inactive

### Cleanup Flow
1. Background job runs every hour
2. Finds AudioFiles where expires_at < now
3. Deletes file from storage
4. Cascades delete to Transcript, EmotionAnalysis, PlaybackState
5. Removes AudioFile record

## Storage Considerations

### Temporary Files
- Audio files stored in `/tmp/sawtfeel/audio/{file_id}`
- Automatically cleaned up after 24 hours
- Maximum 1GB total storage at any time

### Database
- PostgreSQL for structured data
- Redis for session data and caching
- All data automatically expires after 24 hours

### Memory Management
- Audio processing done in chunks to limit memory usage
- Large files streamed rather than loaded entirely
- Emotion analysis results cached in Redis for quick access
