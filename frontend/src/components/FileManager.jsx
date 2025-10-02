import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Spinner, Badge, Modal, Row, Col } from 'react-bootstrap';
import { uploadAPI } from '../services/api';

const FileManager = ({ onFileSelect, isProcessing }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Load files on component mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await uploadAPI.listFiles();
      setFiles(response.data.files || []);
    } catch (err) {
      console.error('Error loading files:', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file) => {
    const fileData = {
      file_id: file.file_id,
      filename: file.filename,
      status: file.status,
      uploadedAt: file.upload_time
    };
    onFileSelect(fileData);
  };

  const handleDeleteFile = async () => {
    if (!fileToDelete) return;

    try {
      setDeleting(true);
      await uploadAPI.deleteFile(fileToDelete.file_id);
      
      // Remove from local state
      setFiles(prev => prev.filter(f => f.file_id !== fileToDelete.file_id));
      setShowDeleteModal(false);
      setFileToDelete(null);
    } catch (err) {
      console.error('Error deleting file:', err);
      setError('Failed to delete file. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusBadge = (status, isProcessing) => {
    const statusConfig = {
      'uploaded': { variant: 'secondary', text: 'Uploaded' },
      'extracting': { variant: 'info', text: 'Extracting' },
      'transcribing': { variant: 'warning', text: 'Transcribing' },
      'analyzing': { variant: 'primary', text: 'Analyzing' },
      'completed': { variant: 'success', text: 'Completed' },
      'failed': { variant: 'danger', text: 'Failed' }
    };

    const config = statusConfig[status] || { variant: 'secondary', text: status };
    
    return (
      <Badge bg={config.variant} className="me-2">
        {isProcessing && <Spinner size="sm" className="me-1" />}
        {config.text}
      </Badge>
    );
  };

  const getFileTypeIcon = (fileType) => {
    return fileType === 'video' ? '🎥' : '🎵';
  };

  return (
    <div className="file-manager">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h5 className="mb-0">
          <i className="fas fa-folder-open me-2"></i>
          File Manager
        </h5>
        <div className="d-flex gap-2">
          <Button
            variant="outline-primary"
            size="sm"
            onClick={loadFiles}
            disabled={loading}
          >
            <i className="fas fa-sync-alt me-1"></i>
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowUploadModal(true)}
            disabled={isProcessing}
          >
            <i className="fas fa-upload me-1"></i>
            Upload New
          </Button>
        </div>
      </div>

      {/* Content */}
      <div>
        {/* Error Display */}
        {error && (
          <Alert variant="danger" className="mb-3" dismissible onClose={() => setError(null)}>
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-4">
            <Spinner animation="border" />
            <p className="mt-2 text-muted">Loading files...</p>
          </div>
        )}

        {/* Files List */}
        {!loading && (
        <>
          {files.length === 0 ? (
            <Card>
              <Card.Body className="text-center py-5">
                <i className="fas fa-folder-open fa-3x text-muted mb-3"></i>
                <h5 className="text-muted">No files uploaded yet</h5>
                <p className="text-muted mb-3">
                  Upload your first Arabic audio or video file to get started
                </p>
                <Button
                  variant="primary"
                  onClick={() => setShowUploadModal(true)}
                  disabled={isProcessing}
                >
                  <i className="fas fa-upload me-1"></i>
                  Upload File
                </Button>
              </Card.Body>
            </Card>
          ) : (
            <Row>
              {files.map((file) => (
                <Col key={file.file_id} md={6} lg={4} className="mb-3">
                  <Card className="file-card h-100">
                    <Card.Body>
                      <div className="d-flex align-items-start mb-2">
                        <div className="file-icon me-2">
                          {getFileTypeIcon(file.file_type)}
                        </div>
                        <div className="flex-grow-1">
                          <h6 className="file-name mb-1" title={file.filename}>
                            {file.filename.length > 25 
                              ? file.filename.substring(0, 25) + '...' 
                              : file.filename
                            }
                          </h6>
                          <div className="file-meta text-muted small">
                            <div>{formatFileSize(file.file_size)}</div>
                            <div>{formatDate(file.upload_time)}</div>
                            {file.transcription_service && (
                              <div className="mt-1">
                                <Badge 
                                  bg={file.transcription_service === 'gemini' ? 'info' : 'secondary'} 
                                  className="text-uppercase"
                                  style={{ fontSize: '0.7rem' }}
                                >
                                  <i className={`fas ${file.transcription_service === 'gemini' ? 'fa-robot' : 'fa-microphone'} me-1`}></i>
                                  {file.transcription_service}
                                </Badge>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="mb-3">
                        {getStatusBadge(file.status, file.is_processing)}
                        {file.progress > 0 && file.progress < 100 && (
                          <div className="mt-2">
                            <div className="progress" style={{ height: '4px' }}>
                              <div
                                className="progress-bar"
                                style={{ width: `${file.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="d-flex gap-2">
                        <Button
                          variant="outline-primary"
                          size="sm"
                          className="flex-grow-1"
                          onClick={() => handleFileSelect(file)}
                          disabled={isProcessing || file.is_processing}
                        >
                          <i className="fas fa-play me-1"></i>
                          Select
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => {
                            setFileToDelete(file);
                            setShowDeleteModal(true);
                          }}
                          disabled={isProcessing || file.is_processing}
                        >
                          <i className="fas fa-trash"></i>
                        </Button>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          )}
        </>
        )}
      </div>

      {/* Upload Modal */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="fas fa-upload me-2"></i>
            Upload New File
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <FileUploadModal onFileSelect={onFileSelect} onClose={() => setShowUploadModal(false)} />
        </Modal.Body>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            <i className="fas fa-trash me-2"></i>
            Delete File
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {fileToDelete && (
            <div>
              <p>Are you sure you want to delete this file?</p>
              <div className="bg-light p-3 rounded">
                <strong>{fileToDelete.filename}</strong>
                <div className="text-muted small">
                  {formatFileSize(fileToDelete.file_size)} • {formatDate(fileToDelete.upload_time)}
                </div>
              </div>
              <p className="text-danger small mt-2">
                <i className="fas fa-exclamation-triangle me-1"></i>
                This action cannot be undone. All associated data will be permanently deleted.
              </p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDeleteFile}
            disabled={deleting}
          >
            {deleting ? (
              <>
                <Spinner size="sm" className="me-1" />
                Deleting...
              </>
            ) : (
              <>
                <i className="fas fa-trash me-1"></i>
                Delete
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Custom Styles */}
      <style>{`
        .file-card {
          transition: transform 0.2s ease, box-shadow 0.2s ease;
          cursor: pointer;
        }
        
        .file-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .file-icon {
          font-size: 1.5rem;
        }
        
        .file-name {
          font-weight: 600;
          color: var(--bs-dark);
        }
        
        .file-meta {
          font-size: 0.8rem;
          line-height: 1.2;
        }
        
        .progress {
          background-color: rgba(0, 0, 0, 0.1);
        }
        
        
        .file-manager .btn-link {
          text-decoration: none;
          color: var(--bs-primary);
        }
        
        .file-manager .btn-link:hover {
          color: var(--bs-primary);
          text-decoration: none;
        }
      `}</style>
    </div>
  );
};

// File Upload Modal Component
const FileUploadModal = ({ onFileSelect, onClose }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0] && !uploading) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0] && !uploading) {
      handleFile(e.target.files[0]);
    }
    // Clear the input to prevent duplicate triggers
    e.target.value = '';
  };

  const handleFile = async (file) => {
    try {
      console.log('FileManager: handleFile called with:', file);
      console.log('FileManager: file.name:', file.name);
      console.log('FileManager: file.type:', file.type);
      console.log('FileManager: file.size:', file.size);
      
      if (!file || !file.name) {
        throw new Error('Invalid file: no filename provided');
      }
      
      // Prevent duplicate uploads
      if (uploading) {
        console.log('FileManager: Upload already in progress, ignoring duplicate request');
        return;
      }
      
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      const response = await uploadAPI.uploadFile(file, (progress) => {
        setUploadProgress(progress);
      });

      const fileData = {
        file_id: response.data.file_id,
        filename: file.name,
        status: response.data.status,
        uploadedAt: new Date().toISOString()
      };

      onFileSelect(fileData);
      onClose();
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.response?.data?.error || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="file-upload-modal">
      <div className="text-center mb-3">
        <p className="text-muted">
          Supported formats: MP3, WAV, MP4, AVI, MOV, MKV, WebM, FLV
        </p>
        <p className="text-muted small">
          Maximum duration: 2 minutes | Maximum size: 100MB
        </p>
      </div>

      {error && (
        <Alert variant="danger" className="mb-3">
          <i className="fas fa-exclamation-triangle me-2"></i>
          {error}
        </Alert>
      )}

      {uploadProgress > 0 && (
        <div className="mb-3">
          <div className="d-flex justify-content-between mb-1">
            <small>Uploading...</small>
            <small>{uploadProgress}%</small>
          </div>
          <div className="progress">
            <div
              className="progress-bar"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      <div
        className={`drop-zone ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: '2px dashed #dee2e6',
          borderRadius: '0.375rem',
          padding: '2rem',
          textAlign: 'center',
          cursor: uploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
          backgroundColor: dragActive ? '#f8f9fa' : 'white',
          borderColor: dragActive ? '#007bff' : '#dee2e6'
        }}
        onClick={() => {
          if (!uploading) {
            document.getElementById('modal-file-input').click();
          }
        }}
      >
        <input
          id="modal-file-input"
          type="file"
          accept=".mp3,.wav,.mp4,.avi,.mov,.mkv,.webm,.flv"
          onChange={handleFileInput}
          style={{ display: 'none' }}
          disabled={uploading}
        />

        {uploading ? (
          <div>
            <Spinner animation="border" className="mb-2" />
            <p className="mb-0">Uploading file...</p>
          </div>
        ) : (
          <div>
            <i className="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <p className="mb-2">Drag and drop your file here, or</p>
            <Button variant="outline-primary" disabled={uploading}>
              Choose File
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileManager;
