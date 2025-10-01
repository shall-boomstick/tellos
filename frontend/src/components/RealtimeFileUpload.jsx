import React, { useCallback, useState } from 'react';
import { Card, Button, Alert, ProgressBar } from 'react-bootstrap';

const RealtimeFileUpload = ({ onFileSelect, isProcessing }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  // Handle drag events
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  // Handle file input change
  const handleFileInputChange = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }, []);

  // Handle file selection
  const handleFile = useCallback(async (file) => {
    try {
      setError(null);
      setUploadProgress(0);

      // Validate file
      if (!file) {
        throw new Error('No file selected');
      }

      // Check file type
      const allowedTypes = [
        'video/mp4',
        'video/avi',
        'video/mov',
        'video/mkv',
        'video/webm',
        'video/flv',
        'video/wmv',
        'audio/mp3',
        'audio/wav',
        'audio/m4a',
        'audio/ogg'
      ];

      if (!allowedTypes.includes(file.type)) {
        throw new Error('Unsupported file type. Please upload a video or audio file.');
      }

      // Check file size (500MB limit)
      const maxSize = 500 * 1024 * 1024; // 500MB
      if (file.size > maxSize) {
        throw new Error('File too large. Please upload a file smaller than 500MB.');
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Call parent handler
      await onFileSelect(file);
      
      // Complete progress
      setUploadProgress(100);
      setTimeout(() => setUploadProgress(0), 1000);

    } catch (err) {
      setError(err.message);
      setUploadProgress(0);
    }
  }, [onFileSelect]);

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Card className="file-upload-card">
      <Card.Body className="p-4">
        <div className="text-center mb-4">
          <h5 className="card-title">Upload Video or Audio File</h5>
          <p className="text-muted">
            Drag and drop your file here, or click to browse
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="danger" className="mb-3">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Upload Progress */}
        {uploadProgress > 0 && (
          <div className="mb-3">
            <div className="d-flex justify-content-between mb-1">
              <small>Uploading...</small>
              <small>{uploadProgress}%</small>
            </div>
            <ProgressBar now={uploadProgress} animated />
          </div>
        )}

        {/* Drop Zone */}
        <div
          className={`drop-zone ${dragActive ? 'drag-active' : ''} ${isProcessing ? 'processing' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: '2px dashed #dee2e6',
            borderRadius: '0.375rem',
            padding: '2rem',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            backgroundColor: dragActive ? '#f8f9fa' : 'white',
            borderColor: dragActive ? '#007bff' : '#dee2e6'
          }}
          onClick={() => {
            if (!isProcessing) {
              document.getElementById('file-input').click();
            }
          }}
        >
          <input
            id="file-input"
            type="file"
            accept="video/*,audio/*"
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
            disabled={isProcessing}
          />

          {isProcessing ? (
            <div>
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Processing...</span>
              </div>
              <h6>Processing your file...</h6>
              <p className="text-muted">Please wait while we prepare your video for real-time analysis</p>
            </div>
          ) : (
            <div>
              <i className="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
              <h6>Choose a file or drag it here</h6>
              <p className="text-muted mb-3">
                Supported formats: MP4, AVI, MOV, MKV, WebM, FLV, WMV, MP3, WAV, M4A, OGG
              </p>
              <Button variant="outline-primary" size="lg">
                <i className="fas fa-folder-open me-2"></i>
                Browse Files
              </Button>
            </div>
          )}
        </div>

        {/* File Requirements */}
        <div className="mt-4">
          <h6 className="mb-2">File Requirements:</h6>
          <ul className="list-unstyled text-muted small">
            <li><i className="fas fa-check text-success me-2"></i>Maximum file size: 500MB</li>
            <li><i className="fas fa-check text-success me-2"></i>Supported video formats: MP4, AVI, MOV, MKV, WebM, FLV, WMV</li>
            <li><i className="fas fa-check text-success me-2"></i>Supported audio formats: MP3, WAV, M4A, OGG</li>
            <li><i className="fas fa-check text-success me-2"></i>For best results, use clear audio with minimal background noise</li>
          </ul>
        </div>

        {/* Tips */}
        <div className="mt-3">
          <div className="alert alert-info">
            <h6 className="alert-heading">
              <i className="fas fa-lightbulb me-2"></i>
              Tips for Best Results
            </h6>
            <ul className="mb-0 small">
              <li>Ensure your video has clear audio for accurate transcription</li>
              <li>Minimize background noise and music</li>
              <li>Use videos with single speakers for better emotion analysis</li>
              <li>Longer videos may take more time to process</li>
            </ul>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default RealtimeFileUpload;
