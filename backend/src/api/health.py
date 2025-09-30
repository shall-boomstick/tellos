"""
Health check endpoints for SawtFeel application.
Provides system health and readiness checks.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import psutil
import torch
import os
from datetime import datetime
import logging

from ..services.redis_client import redis_client
from ..services.file_manager import file_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns simple status for load balancers.
    """
    return {
        "status": "healthy",
        "service": "sawtfeel-backend",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with system information.
    """
    try:
        health_data = {
            "status": "healthy",
            "service": "sawtfeel-backend",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "system": await _get_system_health(),
            "services": await _get_services_health(),
            "storage": await _get_storage_health(),
            "ai_models": await _get_ai_models_health()
        }
        
        # Determine overall health status
        overall_status = "healthy"
        issues = []
        
        # Check system health
        if health_data["system"]["cpu_usage_percent"] > 90:
            issues.append("High CPU usage")
        if health_data["system"]["memory_usage_percent"] > 90:
            issues.append("High memory usage")
        if health_data["system"]["disk_usage_percent"] > 90:
            issues.append("High disk usage")
        
        # Check services health
        for service_name, service_health in health_data["services"].items():
            if not service_health.get("available", False):
                issues.append(f"{service_name} unavailable")
        
        # Check storage health
        if health_data["storage"]["total_size_mb"] > 5000:  # 5GB limit
            issues.append("Storage usage high")
        
        # Update status based on issues
        if issues:
            if len(issues) > 2 or any("unavailable" in issue for issue in issues):
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            health_data["issues"] = issues
        
        health_data["status"] = overall_status
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        return {
            "status": "unhealthy",
            "service": "sawtfeel-backend",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/health/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check - indicates if service is ready to handle requests.
    """
    try:
        readiness_checks = {
            "redis_connection": await _check_redis_connection(),
            "file_system": await _check_file_system(),
            "ai_models": await _check_ai_models_readiness(),
            "storage_space": await _check_storage_space()
        }
        
        # Service is ready if all checks pass
        all_ready = all(check["ready"] for check in readiness_checks.values())
        
        return {
            "ready": all_ready,
            "service": "sawtfeel-backend",
            "timestamp": datetime.now().isoformat(),
            "checks": readiness_checks
        }
        
    except Exception as e:
        logger.error(f"Error in readiness check: {e}")
        return {
            "ready": False,
            "service": "sawtfeel-backend",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check - indicates if service is alive and not deadlocked.
    """
    try:
        # Simple check that the service can respond
        current_time = datetime.now()
        
        # Check if we can perform basic operations
        test_operations = {
            "timestamp_generation": True,
            "memory_allocation": await _test_memory_allocation(),
            "file_system_access": await _test_file_system_access()
        }
        
        all_alive = all(test_operations.values())
        
        return {
            "alive": all_alive,
            "service": "sawtfeel-backend",
            "timestamp": current_time.isoformat(),
            "operations": test_operations
        }
        
    except Exception as e:
        logger.error(f"Error in liveness check: {e}")
        return {
            "alive": False,
            "service": "sawtfeel-backend",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

async def _get_system_health() -> Dict[str, Any]:
    """Get system health metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Load average (Unix systems only)
        load_avg = None
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            # Windows doesn't have getloadavg
            pass
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": round(memory.available / (1024 * 1024), 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2),
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
            "load_average": load_avg
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {"error": str(e)}

async def _get_services_health() -> Dict[str, Any]:
    """Get health status of external services."""
    services_health = {}
    
    # Redis health
    try:
        redis_available = await redis_client.ping()
        services_health["redis"] = {
            "available": redis_available,
            "type": "cache"
        }
    except Exception as e:
        services_health["redis"] = {
            "available": False,
            "type": "cache",
            "error": str(e)
        }
    
    return services_health

async def _get_storage_health() -> Dict[str, Any]:
    """Get storage health metrics."""
    try:
        storage_stats = file_manager.get_storage_stats()
        return storage_stats
    except Exception as e:
        logger.error(f"Error getting storage health: {e}")
        return {"error": str(e)}

async def _get_ai_models_health() -> Dict[str, Any]:
    """Get AI models health status."""
    models_health = {}
    
    # Check PyTorch availability
    models_health["pytorch"] = {
        "available": torch.cuda.is_available() if hasattr(torch, 'cuda') else False,
        "version": torch.__version__ if hasattr(torch, '__version__') else "unknown",
        "cuda_available": torch.cuda.is_available() if hasattr(torch, 'cuda') else False
    }
    
    # Check CUDA devices if available
    if torch.cuda.is_available():
        models_health["cuda"] = {
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
        }
    
    return models_health

async def _check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection."""
    try:
        ping_result = await redis_client.ping()
        return {
            "ready": ping_result,
            "type": "redis_connection"
        }
    except Exception as e:
        return {
            "ready": False,
            "type": "redis_connection",
            "error": str(e)
        }

async def _check_file_system() -> Dict[str, Any]:
    """Check file system readiness."""
    try:
        # Check if upload and cache directories exist and are writable
        upload_dir = "temp_uploads"
        cache_dir = "cache"
        
        upload_ready = os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK)
        cache_ready = os.path.exists(cache_dir) and os.access(cache_dir, os.W_OK)
        
        return {
            "ready": upload_ready and cache_ready,
            "type": "file_system",
            "upload_dir_ready": upload_ready,
            "cache_dir_ready": cache_ready
        }
    except Exception as e:
        return {
            "ready": False,
            "type": "file_system",
            "error": str(e)
        }

async def _check_ai_models_readiness() -> Dict[str, Any]:
    """Check AI models readiness."""
    try:
        # Check if required libraries are available
        pytorch_ready = torch is not None
        
        # Check if CUDA is available for GPU acceleration
        cuda_ready = torch.cuda.is_available() if pytorch_ready else False
        
        return {
            "ready": pytorch_ready,  # Minimum requirement
            "type": "ai_models",
            "pytorch_available": pytorch_ready,
            "cuda_available": cuda_ready
        }
    except Exception as e:
        return {
            "ready": False,
            "type": "ai_models",
            "error": str(e)
        }

async def _check_storage_space() -> Dict[str, Any]:
    """Check available storage space."""
    try:
        disk = psutil.disk_usage('/')
        free_space_gb = disk.free / (1024 * 1024 * 1024)
        
        # Require at least 1GB free space
        space_ready = free_space_gb > 1.0
        
        return {
            "ready": space_ready,
            "type": "storage_space",
            "free_space_gb": round(free_space_gb, 2),
            "minimum_required_gb": 1.0
        }
    except Exception as e:
        return {
            "ready": False,
            "type": "storage_space",
            "error": str(e)
        }

async def _test_memory_allocation() -> bool:
    """Test memory allocation capability."""
    try:
        # Allocate and deallocate a small amount of memory
        test_data = [0] * 1000  # Small list
        del test_data
        return True
    except Exception:
        return False

async def _test_file_system_access() -> bool:
    """Test file system access capability."""
    try:
        import tempfile
        
        # Create and delete a temporary file
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"health check test")
            tmp.flush()
        
        return True
    except Exception:
        return False

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics for monitoring.
    """
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "service": "sawtfeel-backend",
            "system_metrics": await _get_system_health(),
            "storage_metrics": await _get_storage_health(),
            "ai_metrics": await _get_ai_models_health()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
