import React, { useState } from 'react'

const FileUpload = ({ onFileSelect, isUploading, error }) => {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file) => {
    onFileSelect(file)
  }

  return (
    <div className="file-upload">
      <div className="card">
        <h2>Upload Arabic Audio or Video File</h2>
        <p className="text-secondary">
          Supported formats: MP3, WAV, MP4, AVI, MOV, MKV, WebM, FLV
        </p>
        <p className="text-secondary">
          Maximum duration: 2 minutes | Maximum size: 100MB
        </p>

        <div
          className={`upload-zone ${dragActive ? 'drag-active' : ''} ${isUploading ? 'uploading' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {isUploading ? (
            <div className="upload-status">
              <div className="spinner"></div>
              <p>Uploading file...</p>
            </div>
          ) : (
            <div className="upload-content">
              <div className="upload-icon">📁</div>
              <p>Drag and drop your file here, or</p>
              <label className="btn btn-primary">
                Choose File
                <input
                  type="file"
                  accept=".mp3,.wav,.mp4,.avi,.mov,.mkv,.webm,.flv"
                  onChange={handleFileInput}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          )}
        </div>

        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
      </div>

    </div>
  )
}

export default FileUpload
