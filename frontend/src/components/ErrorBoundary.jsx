import React from 'react';
import { Alert, Button, Card } from 'react-bootstrap';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // You can also log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div className="error-boundary">
          <Card className="border-danger">
            <Card.Header className="bg-danger text-white">
              <h5 className="mb-0">
                <i className="fas fa-exclamation-triangle me-2"></i>
                Something went wrong
              </h5>
            </Card.Header>
            <Card.Body>
              <Alert variant="danger">
                <h6>An error occurred while rendering the component</h6>
                <p className="mb-0">
                  The application encountered an unexpected error. This might be due to a 
                  temporary issue or a bug in the code.
                </p>
              </Alert>

              {/* Error Details (only in development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="error-details mt-3">
                  <h6>Error Details (Development Mode)</h6>
                  <pre className="bg-light p-3 rounded" style={{ fontSize: '0.8em' }}>
                    <strong>Error:</strong> {this.state.error.toString()}
                    {this.state.errorInfo && (
                      <>
                        <br />
                        <strong>Component Stack:</strong>
                        <br />
                        {this.state.errorInfo.componentStack}
                      </>
                    )}
                  </pre>
                </div>
              )}

              {/* Action Buttons */}
              <div className="d-flex gap-2 mt-3">
                <Button variant="primary" onClick={this.handleRetry}>
                  <i className="fas fa-redo me-2"></i>
                  Try Again
                </Button>
                <Button variant="outline-secondary" onClick={this.handleReload}>
                  <i className="fas fa-refresh me-2"></i>
                  Reload Page
                </Button>
              </div>

              {/* Help Text */}
              <div className="mt-3">
                <small className="text-muted">
                  If the problem persists, please try refreshing the page or contact support.
                </small>
              </div>
            </Card.Body>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easier usage
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

// Hook for error boundary functionality
export const useErrorHandler = () => {
  const handleError = (error, errorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // You can add additional error handling logic here
    // For example, sending to an error reporting service
  };

  return { handleError };
};

export default ErrorBoundary;
