import React, { useState, useEffect } from 'react';
import { Card, ProgressBar, Badge, Spinner } from 'react-bootstrap';

const ProcessingStatus = ({ isProcessing, isConnected, fileId }) => {
  const [processingSteps, setProcessingSteps] = useState([
    { id: 'upload', name: 'File Upload', status: 'completed', progress: 100 },
    { id: 'extract', name: 'Audio Extraction', status: 'pending', progress: 0 },
    { id: 'transcribe', name: 'Transcription Setup', status: 'pending', progress: 0 },
    { id: 'emotion', name: 'Emotion Analysis Setup', status: 'pending', progress: 0 },
    { id: 'websocket', name: 'WebSocket Connection', status: 'pending', progress: 0 },
    { id: 'ready', name: 'Ready for Playback', status: 'pending', progress: 0 }
  ]);

  const [overallProgress, setOverallProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('upload');

  // Update processing steps based on status
  useEffect(() => {
    if (isProcessing) {
      // Simulate processing steps
      const stepSequence = [
        { step: 'extract', delay: 1000 },
        { step: 'transcribe', delay: 2000 },
        { step: 'emotion', delay: 3000 },
        { step: 'websocket', delay: 4000 },
        { step: 'ready', delay: 5000 }
      ];

      let currentIndex = 0;
      const updateStep = () => {
        if (currentIndex < stepSequence.length) {
          const { step, delay } = stepSequence[currentIndex];
          
          setProcessingSteps(prev => prev.map(s => 
            s.id === step 
              ? { ...s, status: 'in-progress', progress: 0 }
              : s.id === currentStep
                ? { ...s, status: 'completed', progress: 100 }
                : s
          ));
          
          setCurrentStep(step);
          
          // Simulate progress for current step
          let progress = 0;
          const progressInterval = setInterval(() => {
            progress += 20;
            setProcessingSteps(prev => prev.map(s => 
              s.id === step 
                ? { ...s, progress: Math.min(progress, 100) }
                : s
            ));
            
            if (progress >= 100) {
              clearInterval(progressInterval);
              setProcessingSteps(prev => prev.map(s => 
                s.id === step 
                  ? { ...s, status: 'completed', progress: 100 }
                  : s
              ));
            }
          }, delay / 5);
          
          currentIndex++;
          setTimeout(updateStep, delay);
        }
      };
      
      updateStep();
    } else if (isConnected) {
      // All steps completed
      setProcessingSteps(prev => prev.map(s => ({ ...s, status: 'completed', progress: 100 })));
      setCurrentStep('ready');
    }
  }, [isProcessing, isConnected]);

  // Calculate overall progress
  useEffect(() => {
    const totalProgress = processingSteps.reduce((sum, step) => sum + step.progress, 0);
    const averageProgress = totalProgress / processingSteps.length;
    setOverallProgress(averageProgress);
  }, [processingSteps]);

  // Get step status color
  const getStepStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in-progress': return 'primary';
      case 'pending': return 'secondary';
      case 'error': return 'danger';
      default: return 'secondary';
    }
  };

  // Get step status icon
  const getStepStatusIcon = (status) => {
    switch (status) {
      case 'completed': return 'fa-check-circle';
      case 'in-progress': return 'fa-spinner fa-spin';
      case 'pending': return 'fa-clock';
      case 'error': return 'fa-exclamation-circle';
      default: return 'fa-clock';
    }
  };

  // Get overall status
  const getOverallStatus = () => {
    if (isConnected && !isProcessing) return 'ready';
    if (isProcessing) return 'processing';
    if (!isConnected) return 'disconnected';
    return 'pending';
  };

  const overallStatus = getOverallStatus();

  return (
    <Card className="processing-status">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">Processing Status</h6>
          <div className="d-flex align-items-center">
            <Badge 
              bg={overallStatus === 'ready' ? 'success' : overallStatus === 'processing' ? 'primary' : 'danger'}
              className="me-2"
            >
              {overallStatus === 'ready' ? 'Ready' : overallStatus === 'processing' ? 'Processing' : 'Disconnected'}
            </Badge>
            {fileId && (
              <small className="text-muted">File ID: {fileId}</small>
            )}
          </div>
        </div>

        {/* Overall Progress */}
        <div className="mb-4">
          <div className="d-flex justify-content-between mb-1">
            <small>Overall Progress</small>
            <small>{Math.round(overallProgress)}%</small>
          </div>
          <ProgressBar 
            now={overallProgress} 
            variant={overallStatus === 'ready' ? 'success' : 'primary'}
            animated={isProcessing}
          />
        </div>

        {/* Processing Steps */}
        <div className="processing-steps">
          {processingSteps.map((step, index) => (
            <div key={step.id} className="processing-step mb-3">
              <div className="d-flex align-items-center mb-2">
                <div className="step-icon me-3">
                  <i 
                    className={`fas ${getStepStatusIcon(step.status)} ${
                      step.status === 'in-progress' ? 'text-primary' : 
                      step.status === 'completed' ? 'text-success' : 
                      'text-muted'
                    }`}
                  ></i>
                </div>
                <div className="flex-grow-1">
                  <div className="step-name fw-bold">{step.name}</div>
                  <div className="step-status">
                    <Badge bg={getStepStatusColor(step.status)} size="sm">
                      {step.status === 'in-progress' ? 'In Progress' :
                       step.status === 'completed' ? 'Completed' :
                       step.status === 'error' ? 'Error' : 'Pending'}
                    </Badge>
                  </div>
                </div>
                <div className="step-progress">
                  <small className="text-muted">{step.progress}%</small>
                </div>
              </div>
              
              {/* Step Progress Bar */}
              <ProgressBar
                now={step.progress}
                variant={getStepStatusColor(step.status)}
                size="sm"
                animated={step.status === 'in-progress'}
              />
            </div>
          ))}
        </div>

        {/* Current Status Message */}
        <div className="status-message mt-3">
          {overallStatus === 'ready' && (
            <div className="alert alert-success mb-0">
              <i className="fas fa-check-circle me-2"></i>
              Processing complete! You can now play the video with real-time translation and emotion analysis.
            </div>
          )}
          
          {overallStatus === 'processing' && (
            <div className="alert alert-info mb-0">
              <Spinner animation="border" size="sm" className="me-2" />
              Processing your file... This may take a few moments depending on the file size.
            </div>
          )}
          
          {overallStatus === 'disconnected' && (
            <div className="alert alert-warning mb-0">
              <i className="fas fa-exclamation-triangle me-2"></i>
              Connection lost. Please check your internet connection and try again.
            </div>
          )}
        </div>

        {/* Processing Tips */}
        {isProcessing && (
          <div className="processing-tips mt-3">
            <div className="card bg-light">
              <div className="card-body p-2">
                <h6 className="card-title mb-2">
                  <i className="fas fa-lightbulb me-2"></i>
                  Processing Tips
                </h6>
                <ul className="mb-0 small text-muted">
                  <li>Larger files take longer to process</li>
                  <li>Keep this tab open during processing</li>
                  <li>You'll be notified when processing is complete</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default ProcessingStatus;
