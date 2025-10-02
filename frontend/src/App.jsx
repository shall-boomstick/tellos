import React, { useState, useEffect } from 'react'
import './styles/light.css'
import './styles/dark.css'
import './styles/mobile.css'
import FileUpload from './components/FileUpload'
import FileManager from './components/FileManager'
import RealtimeInterface from './pages/RealtimeInterface'
import ThemeToggle from './components/ThemeToggle'
import themeService, { subscribeToTheme } from './services/theme'
import { uploadAPI } from './services/api'

function App() {
  const [currentFile, setCurrentFile] = useState(null)
  const [theme, setTheme] = useState(themeService.getTheme())
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)

  // Subscribe to theme changes
  useEffect(() => {
    const unsubscribe = subscribeToTheme((newTheme) => {
      setTheme(newTheme)
    })

    return unsubscribe
  }, [])

  const handleFileSelect = async (fileOrData) => {
    // Check if it's a File object (new upload) or file data (existing file)
    if (fileOrData instanceof File) {
      // New file upload
      setIsUploading(true)
      setError(null)
      
      try {
        console.log('Uploading file:', fileOrData.name)
        const response = await uploadAPI.uploadFile(fileOrData)
        
        const fileData = {
          file_id: response.data.file_id,
          filename: fileOrData.name,
          status: response.data.status,
          uploadedAt: new Date().toISOString()
        }
        
        setCurrentFile(fileData)
        console.log('File uploaded successfully:', fileData)
        
      } catch (err) {
        console.error('Upload failed:', err)
        setError(err.response?.data?.error || 'Upload failed. Please try again.')
      } finally {
        setIsUploading(false)
      }
    } else {
      // Existing file selected
      setCurrentFile(fileOrData)
      setError(null)
    }
  }

  const handleNewUpload = () => {
    setCurrentFile(null)
    setError(null)
  }

  const toggleTheme = () => {
    themeService.toggleTheme()
  }

  return (
    <div className={`app ${theme}`}>
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <h1>SawtFeel</h1>
            <p className="tagline">Arabic Audio Emotion Analysis</p>
          </div>
          <div className="header-actions">
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
          </div>
        </div>
      </header>
      
      <main className="app-main">
        <RealtimeInterface 
          fileData={currentFile} 
          onNewUpload={handleNewUpload}
          onFileSelect={handleFileSelect}
          isUploading={isUploading}
          error={error}
        />
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2024 SawtFeel - Arabic Audio Emotion Analysis</p>
      </footer>
    </div>
  )
}

export default App
