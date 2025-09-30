<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0
Modified principles: I. Audio-First Architecture → I. Video-First Architecture
Added sections: Video Processing Standards, Real-time Streaming Requirements, Translation & Analysis Standards
Removed sections: N/A
Templates requiring updates: ✅ plan-template.md, ✅ tasks-template.md
Follow-up TODOs: None
-->

# Tellos Constitution

## Core Principles

### I. Video-First Architecture
Every component MUST be designed for video file processing with real-time audio extraction; Video files are the primary source of audio data; All data structures MUST support streaming video processing; Memory management MUST be optimized for continuous video-to-audio conversion; Real-time translation and analysis MUST operate on extracted audio streams.

### II. CLI Interface
Every video processing feature MUST expose functionality via CLI; Video input/output protocol: video files → extracted audio → real-time analysis/translation → stdout, errors → stderr; Support JSON + human-readable formats for analysis results; Video format detection and audio extraction MUST be automatic; Real-time streaming output MUST be supported.

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced; Video processing tests MUST use sample video files; Real-time streaming tests MUST validate latency requirements; Translation accuracy tests MUST use known test datasets.

### IV. Integration Testing
Focus areas requiring integration tests: Video format compatibility, Real-time video-to-audio extraction, Streaming translation pipelines, Cross-platform video handling, Memory leak detection during continuous video processing, Translation accuracy validation.

### V. Observability & Performance
Structured logging required for video processing and translation metrics; Processing time MUST be logged for each video segment; Memory usage MUST be monitored during continuous video processing; Translation accuracy metrics MUST be tracked and reported; Real-time streaming latency MUST be measured and logged.

## Video Processing Standards

### Supported Video Formats
MUST support: MP4, AVI, MOV, MKV, WebM, FLV; MUST provide video-to-audio extraction capabilities; MUST handle various video codecs (H.264, H.265, VP9, AV1); MUST support variable frame rates and resolutions.

### Audio Extraction Requirements
Audio extraction from video MUST preserve original quality; Extraction MUST be real-time capable; Processing MUST be deterministic given same video input; MUST handle video files of any reasonable size; MUST support streaming extraction without full file loading.

## Real-time Streaming Requirements

### Streaming Performance
Video processing MUST complete within 1.5x real-time duration; Audio extraction latency MUST be under 50ms; Translation processing MUST complete within 200ms; Memory usage MUST remain constant during continuous streaming; MUST support concurrent processing of multiple video streams.

### Translation & Analysis Standards
Translation accuracy MUST be measurable and testable; Analysis results MUST be reproducible; Processing MUST be deterministic given same input; Confidence scores MUST be provided for all translations; Results MUST be validated against known test datasets.

## Quality Standards

### Video Processing Quality
Video-to-audio extraction quality MUST be measurable and testable; Audio quality preservation MUST be validated against original video; Processing accuracy MUST be reproducible across different video formats; Quality metrics MUST be tracked and reported.

### Translation Quality
Translation accuracy MUST be measurable and testable; False positive rates MUST be documented and minimized; Translation confidence scores MUST be provided; Results MUST be validated against known test datasets; Language detection accuracy MUST be validated.

## Development Workflow

### Code Review Requirements
All video processing code MUST be reviewed by someone with video/audio domain expertise; Performance impact MUST be assessed for all changes; Memory usage changes MUST be documented; Video processing quality impact MUST be evaluated; Translation accuracy impact MUST be assessed.

### Testing Gates
Unit tests MUST cover all video processing functions; Integration tests MUST validate end-to-end video-to-audio pipelines; Performance tests MUST verify streaming speed requirements; Quality tests MUST validate extraction and translation accuracy; Real-time streaming tests MUST validate latency requirements.

## Governance

Constitution supersedes all other practices; Amendments require documentation, approval, migration plan; All PRs/reviews must verify compliance; Complexity must be justified; Video processing and translation requirements cannot be relaxed without explicit approval.

**Version**: 1.1.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27