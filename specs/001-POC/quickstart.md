# Quickstart Guide: SawtFeel Arabic Audio Emotion Analysis

## Overview
SawtFeel is a web application that analyzes Arabic audio/video files to provide real-time emotion visualization. This guide walks through the complete user journey and system behavior.

## Prerequisites
- Modern web browser (Chrome, Firefox, Safari)
- Arabic audio or video file (MP3, WAV, MP4, AVI, MOV, MKV, WebM, FLV)
- File duration: maximum 2 minutes
- File size: maximum 100MB

## User Journey

### Step 1: Access the Application
1. Open web browser and navigate to SawtFeel application
2. Verify the application loads with:
   - File upload area
   - Dark/light theme toggle
   - Mobile-responsive layout

### Step 2: Upload File
1. Click "Choose File" or drag and drop audio/video file
2. Verify file validation:
   - Supported format check
   - Duration check (≤ 2 minutes)
   - Size check (≤ 100MB)
3. Click "Upload" button
4. Observe progress indicator showing processing stages

### Step 3: Processing Pipeline
The system automatically processes the file through these stages:

#### Stage 1: File Ingestion
- **Duration**: 1-5 seconds
- **Status**: "Uploaded"
- **User sees**: Progress indicator at 10%

#### Stage 2: Audio Extraction (Video files only)
- **Duration**: 2-10 seconds
- **Status**: "Extracting audio"
- **User sees**: Progress indicator at 30%

#### Stage 3: Transcription
- **Duration**: 10-30 seconds
- **Status**: "Transcribing Arabic speech"
- **User sees**: Progress indicator at 60%

#### Stage 4: Emotion Analysis
- **Duration**: 15-45 seconds
- **Status**: "Analyzing emotions"
- **User sees**: Progress indicator at 90%

#### Stage 5: Completion
- **Duration**: 1-2 seconds
- **Status**: "Completed"
- **User sees**: Progress indicator at 100%, main dashboard appears

### Step 4: Main Dashboard
Once processing is complete, the main dashboard displays:

#### Audio Player
- Play/pause button
- Progress bar with scrubber
- Time display (current/total)
- Volume control
- Playback speed control

#### Emotion Gauge
- Visual representation of current emotion
- Color-coded emotions:
  - 🔴 Anger (red)
  - 🔵 Sadness (blue)
  - 🟡 Joy (yellow)
  - ⚪ Neutral (gray)
  - 🟣 Fear (purple)
  - 🟠 Surprise (orange)
- Confidence indicator
- Real-time updates during playback

#### Transcript Panel
- Full Arabic transcript
- Current word highlighted
- Scrollable text
- Word-level timestamps
- Confidence scores

### Step 5: Playback Interaction

#### Basic Playback
1. Click play button
2. Observe:
   - Audio plays
   - Emotion gauge updates in real-time
   - Transcript words highlight in sync
   - Progress bar advances

#### Scrubbing
1. Click and drag progress bar to different position
2. Observe:
   - Audio jumps to new position
   - Emotion gauge updates instantly
   - Transcript highlighting updates instantly
   - All elements stay synchronized

#### Pause/Resume
1. Click pause button
2. Observe:
   - Audio stops
   - Emotion gauge shows current emotion
   - Transcript highlighting stops
3. Click play button
4. Observe:
   - Audio resumes from same position
   - All elements resume synchronization

### Step 6: Theme Switching
1. Click theme toggle button
2. Observe:
   - Interface switches between dark and light themes
   - All components update colors
   - Theme preference persists during session

### Step 7: Mobile Experience
1. Resize browser to mobile dimensions (320px width)
2. Observe:
   - Layout adapts to mobile screen
   - Touch-friendly controls
   - Readable text sizes
   - Proper spacing and margins

## Error Scenarios

### Invalid File Format
1. Upload unsupported file (e.g., .txt, .docx)
2. **Expected**: Error message "Unsupported file format. Please upload MP3, WAV, MP4, AVI, MOV, MKV, WebM, or FLV files."

### File Too Large
1. Upload file larger than 100MB
2. **Expected**: Error message "File too large. Maximum size is 100MB."

### File Too Long
1. Upload audio longer than 2 minutes
2. **Expected**: Error message "File too long. Maximum duration is 2 minutes."

### Processing Failure
1. Upload corrupted file
2. **Expected**: Error message "Processing failed. Please try a different file."

### Network Issues
1. Disconnect internet during processing
2. **Expected**: Error message "Connection lost. Please check your internet connection and try again."

## Success Criteria

### Functional Requirements
- ✅ File upload accepts supported formats
- ✅ Video files automatically extract audio
- ✅ Arabic speech transcribed with timestamps
- ✅ Emotion analysis provides real-time updates
- ✅ Audio player controls work correctly
- ✅ Transcript highlighting synchronizes with audio
- ✅ Emotion gauge updates in real-time
- ✅ Scrubbing updates all elements instantly
- ✅ Theme switching works properly
- ✅ Mobile layout is responsive

### Performance Requirements
- ✅ 2-minute file processes within 3 minutes total
- ✅ Audio extraction completes within 10 seconds
- ✅ Emotion analysis completes within 45 seconds
- ✅ Real-time updates have <100ms latency
- ✅ UI remains responsive during processing

### Quality Requirements
- ✅ Transcription accuracy >80% for clear Arabic speech
- ✅ Emotion detection provides meaningful results
- ✅ Error messages are user-friendly
- ✅ Interface is intuitive and accessible
- ✅ Mobile experience is smooth and usable

## Troubleshooting

### Common Issues
1. **File not uploading**: Check file format and size
2. **Processing stuck**: Refresh page and try again
3. **Audio not playing**: Check browser audio permissions
4. **Transcript not showing**: Wait for processing to complete
5. **Emotion gauge not updating**: Check WebSocket connection

### Browser Compatibility
- Chrome 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

### Mobile Compatibility
- iOS Safari 14+
- Android Chrome 90+
- Responsive design works on screens 320px+ wide
