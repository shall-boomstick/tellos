"""
SawtFeel Backend - Arabic Audio Emotion Analysis
FastAPI application with WebSocket support for real-time processing.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import API routers
from .api.upload import router as upload_router
from .api.processing import router as processing_router
from .api.websocket import router as websocket_router
from .api.realtime_websocket import router as realtime_websocket_router
from .api.health import router as health_router
from .api.video_streaming import router as video_router

app = FastAPI(
    title="SawtFeel API",
    description="Arabic Audio Emotion Analysis API",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sawtfeel-backend"}

# API routes
app.include_router(upload_router, prefix="/api")
app.include_router(processing_router, prefix="/api")
app.include_router(websocket_router)  # WebSocket routes don't need /api prefix
app.include_router(realtime_websocket_router)  # Real-time WebSocket routes
app.include_router(health_router, prefix="/api")
app.include_router(video_router)  # Video streaming routes

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
