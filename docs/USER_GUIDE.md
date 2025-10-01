# User Guide: Real-Time Video Translation and Emotion Analysis

This guide will help you get started with the Real-Time Video Translation and Emotion Analysis interface. Whether you're a first-time user or looking to explore advanced features, this guide has you covered.

## Table of Contents

- [Getting Started](#getting-started)
- [Interface Overview](#interface-overview)
- [Video Upload and Playback](#video-upload-and-playback)
- [Translation Features](#translation-features)
- [Emotion Analysis](#emotion-analysis)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Accessibility Features](#accessibility-features)
- [Settings and Customization](#settings-and-customization)
- [Troubleshooting](#troubleshooting)
- [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### First Launch

1. **Open the Application**: Navigate to `http://localhost:3000` in your web browser
2. **Check System Requirements**: Ensure your browser supports WebRTC and WebSocket connections
3. **Enable Permissions**: Allow camera and microphone access if prompted

### System Requirements

- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Internet**: Stable internet connection for real-time processing
- **Hardware**: Modern CPU with at least 4GB RAM recommended

## Interface Overview

The interface is divided into several main sections:

### Main Video Player
- **Video Display**: Shows your uploaded video with real-time processing
- **Playback Controls**: Play, pause, seek, volume, and fullscreen controls
- **Progress Bar**: Shows current position and allows seeking

### Translation Panel
- **Live Translation**: Real-time translation of spoken content
- **Language Selection**: Choose target language for translation
- **Confidence Scores**: Shows translation accuracy

### Emotion Analysis Gauge
- **Real-Time Emotions**: Live emotion detection and analysis
- **Emotion Chart**: Visual representation of emotional changes over time
- **Confidence Indicators**: Shows analysis confidence levels

### Control Panel
- **File Upload**: Upload new video files
- **Settings**: Access configuration options
- **Help**: View keyboard shortcuts and help information

## Video Upload and Playback

### Uploading a Video

1. **Click Upload Button**: Click the "Upload Video" button or press `U`
2. **Select File**: Choose a video file from your computer
3. **Supported Formats**: MP4, AVI, MOV, WebM (recommended: MP4)
4. **File Size**: Maximum 500MB for optimal performance

### Video Playback Controls

#### Basic Controls
- **Play/Pause**: Click the play button or press `Space`
- **Seek**: Drag the progress bar or use arrow keys (`←`/`→`)
- **Volume**: Use the volume slider or arrow keys (`↑`/`↓`)
- **Mute**: Click the mute button or press `M`
- **Fullscreen**: Click the fullscreen button or press `F`

#### Advanced Controls
- **Speed Control**: Adjust playback speed (0.5x to 2x)
- **Quality Settings**: Choose video quality if multiple options available
- **Subtitle Toggle**: Show/hide subtitles if available

### Video Navigation

- **Jump to Start**: Press `0` or click the beginning of the progress bar
- **Jump to End**: Press `End` or click the end of the progress bar
- **Seek Forward**: Press `→` (10 seconds) or `Shift + →` (30 seconds)
- **Seek Backward**: Press `←` (10 seconds) or `Shift + ←` (30 seconds)

## Translation Features

### Real-Time Translation

The system automatically transcribes and translates spoken content in real-time:

1. **Automatic Detection**: Speech is automatically detected and transcribed
2. **Language Recognition**: Source language is automatically identified
3. **Translation**: Content is translated to your selected target language
4. **Display**: Translation appears below the video with confidence scores

### Language Selection

1. **Open Language Menu**: Click the language selector or press `L`
2. **Choose Target Language**: Select from available languages
3. **Supported Languages**: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, and more

### Translation Controls

- **Toggle Translation**: Press `T` to show/hide translation
- **Repeat Translation**: Press `R` to repeat the last translation
- **Export Translation**: Click the export button to save translations
- **Clear Translation**: Click the clear button to remove all translations

### Translation Quality

- **Confidence Scores**: Each translation shows a confidence percentage
- **High Confidence**: 90%+ indicates very reliable translation
- **Medium Confidence**: 70-89% indicates good translation with minor uncertainty
- **Low Confidence**: Below 70% indicates uncertain translation

## Emotion Analysis

### Real-Time Emotion Detection

The system analyzes facial expressions and emotions in real-time:

1. **Face Detection**: Automatically detects faces in the video
2. **Emotion Analysis**: Analyzes facial expressions for emotions
3. **Real-Time Updates**: Emotions update as the video plays
4. **Confidence Scoring**: Shows how confident the analysis is

### Emotion Types

The system can detect various emotions:

- **Positive Emotions**: Happy, Joy, Excitement, Surprise
- **Negative Emotions**: Sad, Angry, Fear, Disgust
- **Neutral Emotions**: Calm, Neutral, Contemplative
- **Complex Emotions**: Confused, Frustrated, Proud, Embarrassed

### Emotion Display

- **Gauge Display**: Visual gauge showing current dominant emotion
- **Confidence Bar**: Shows how confident the analysis is
- **Emotion History**: Chart showing emotional changes over time
- **Multiple Emotions**: Can detect multiple emotions simultaneously

### Emotion Controls

- **Toggle Analysis**: Press `E` to enable/disable emotion analysis
- **Toggle Chart**: Press `C` to show/hide emotion chart
- **Export Data**: Click export to save emotion analysis data
- **Clear Data**: Click clear to remove all emotion data

## Keyboard Shortcuts

### Video Controls
- `Space`: Play/Pause video
- `←`: Seek backward 10 seconds
- `→`: Seek forward 10 seconds
- `↑`: Volume up
- `↓`: Volume down
- `M`: Toggle mute
- `F`: Toggle fullscreen
- `0`: Jump to beginning
- `End`: Jump to end

### Translation Controls
- `T`: Toggle translation display
- `L`: Cycle through languages
- `R`: Repeat last translation

### Emotion Analysis
- `E`: Toggle emotion analysis
- `C`: Toggle emotion chart

### Interface Controls
- `H`: Show/hide help overlay
- `S`: Show/hide settings panel
- `U`: Open file upload dialog
- `I`: Show video information
- `D`: Toggle debug mode
- `Esc`: Close all modals and overlays

### Navigation
- `Tab`: Focus next element
- `Shift + Tab`: Focus previous element
- `Enter`: Activate focused element

## Accessibility Features

### Screen Reader Support

The interface is fully compatible with screen readers:

- **ARIA Labels**: All interactive elements have descriptive labels
- **Live Regions**: Real-time updates are announced to screen readers
- **Focus Management**: Proper focus handling and navigation
- **Keyboard Navigation**: Complete keyboard accessibility

### Visual Accessibility

- **High Contrast Mode**: Automatic detection and support
- **Color Blind Support**: Color-coded information also uses patterns and text
- **Font Size**: Adjustable font sizes for better readability
- **Focus Indicators**: Clear visual focus indicators

### Motor Accessibility

- **Keyboard Only**: Complete functionality without mouse
- **Large Click Targets**: Buttons and controls are appropriately sized
- **Customizable Timing**: Adjustable timeouts for user interactions
- **Voice Control**: Compatible with voice control software

## Settings and Customization

### Display Settings

1. **Open Settings**: Click the settings button or press `S`
2. **Display Options**:
   - Translation font size
   - Emotion gauge sensitivity
   - Video quality preferences
   - Theme selection (light/dark)

### Processing Settings

1. **Translation Settings**:
   - Default target language
   - Confidence threshold
   - Translation speed
   - Auto-translate toggle

2. **Emotion Analysis Settings**:
   - Analysis sensitivity
   - Update frequency
   - Chart display options
   - Face detection accuracy

### Performance Settings

1. **Caching Options**:
   - Cache size limit
   - Cache duration
   - Auto-cleanup settings

2. **Processing Options**:
   - Worker thread count
   - Batch processing size
   - Memory usage limits

### Accessibility Settings

1. **Keyboard Settings**:
   - Custom keyboard shortcuts
   - Repeat key settings
   - Focus behavior

2. **Visual Settings**:
   - High contrast mode
   - Color scheme
   - Font preferences

## Troubleshooting

### Common Issues

#### Video Not Playing
- **Check Format**: Ensure video format is supported (MP4 recommended)
- **Check Size**: Large files may take time to load
- **Check Browser**: Ensure browser supports video playback
- **Check Internet**: Stable connection required for processing

#### Translation Not Working
- **Check Audio**: Ensure video has audio track
- **Check Language**: Verify source language is supported
- **Check Settings**: Ensure translation is enabled
- **Check Microphone**: Some browsers require microphone access

#### Emotion Analysis Not Working
- **Check Video Quality**: Ensure video is clear and well-lit
- **Check Face Visibility**: Ensure faces are visible in the video
- **Check Settings**: Ensure emotion analysis is enabled
- **Check Processing**: High-resolution videos may take longer to process

#### Performance Issues
- **Close Other Tabs**: Free up browser memory
- **Check Internet**: Ensure stable connection
- **Reduce Quality**: Lower video quality for better performance
- **Clear Cache**: Clear browser cache and cookies

### Error Messages

#### "Connection Lost"
- Check internet connection
- Refresh the page
- Check if the server is running

#### "Video Format Not Supported"
- Convert video to MP4 format
- Use a different video file
- Check video codec compatibility

#### "Translation Service Unavailable"
- Check internet connection
- Wait a moment and try again
- Check if translation service is running

#### "Emotion Analysis Failed"
- Check video quality
- Ensure faces are visible
- Try with a different video

### Getting Help

1. **Check Help**: Press `H` to view the help overlay
2. **Check Console**: Open browser developer tools for error messages
3. **Check Logs**: Look for error messages in the application logs
4. **Contact Support**: Reach out to support team with specific error details

## Tips and Best Practices

### For Best Video Quality

1. **Use MP4 Format**: MP4 provides the best compatibility and performance
2. **Optimal Resolution**: 720p or 1080p works best for most use cases
3. **Good Lighting**: Ensure video is well-lit for better emotion analysis
4. **Clear Audio**: Use videos with clear, audible speech for better translation

### For Best Translation Results

1. **Clear Speech**: Use videos with clear, well-articulated speech
2. **Single Speaker**: One speaker at a time works best
3. **Minimal Background Noise**: Reduce background noise for better accuracy
4. **Appropriate Language**: Ensure the source language is correctly detected

### For Best Emotion Analysis

1. **Face Visibility**: Ensure faces are clearly visible in the video
2. **Good Lighting**: Well-lit videos provide better emotion detection
3. **Frontal View**: Front-facing faces are analyzed more accurately
4. **Stable Video**: Avoid shaky or blurry video for better results

### Performance Optimization

1. **Close Unused Tabs**: Free up browser memory
2. **Use Wired Connection**: Wired internet provides more stable performance
3. **Regular Updates**: Keep browser and application updated
4. **Clear Cache**: Regularly clear browser cache for optimal performance

### Accessibility Best Practices

1. **Use Keyboard Navigation**: Learn and use keyboard shortcuts
2. **Enable Screen Reader**: Use screen reader for better navigation
3. **Adjust Settings**: Customize settings for your specific needs
4. **Take Breaks**: Take regular breaks to avoid eye strain

### Data Privacy

1. **Local Processing**: Video processing happens locally when possible
2. **Secure Transmission**: All data transmission is encrypted
3. **No Storage**: Video files are not permanently stored on servers
4. **User Control**: You control what data is processed and when

## Advanced Features

### Batch Processing

- Upload multiple videos for batch processing
- Process videos overnight or during off-peak hours
- Export results for all videos at once

### API Integration

- Use the REST API for programmatic access
- Integrate with other applications
- Customize processing workflows

### Custom Models

- Train custom translation models
- Fine-tune emotion analysis for specific use cases
- Integrate with external AI services

### Collaboration Features

- Share videos and results with team members
- Collaborative annotation and analysis
- Real-time collaboration on analysis results

## Support and Resources

### Documentation
- [API Documentation](API.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Configuration Guide](CONFIGURATION.md)

### Community
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)
- [User Forum](https://forum.example.com)

### Training and Support
- [Video Tutorials](https://youtube.com/your-channel)
- [Live Training Sessions](https://training.example.com)
- [Email Support](mailto:support@example.com)

---

*This user guide is regularly updated. Check back for the latest information and new features.*

