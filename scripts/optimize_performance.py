#!/usr/bin/env python3
"""
Performance optimization script for real-time video processing system
Automatically optimizes system performance based on current load and usage patterns
"""

import os
import sys
import time
import psutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import argparse
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from services.cache_service import CacheService
from services.realtime_processor import RealtimeProcessor
from services.video_metadata import VideoMetadataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Performance optimization manager"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or 'performance_config.json'
        self.config = self.load_config()
        self.cache_service = CacheService()
        self.realtime_processor = RealtimeProcessor()
        self.video_service = VideoMetadataService()
        self.optimization_thread = None
        self.running = False
        
    def load_config(self) -> Dict[str, Any]:
        """Load performance configuration"""
        default_config = {
            'cache': {
                'max_size': 1000,
                'ttl': 300,
                'cleanup_interval': 60
            },
            'processing': {
                'max_workers': 4,
                'batch_size': 10,
                'timeout': 30
            },
            'memory': {
                'max_usage': 80,
                'cleanup_threshold': 70,
                'gc_interval': 30
            },
            'network': {
                'connection_pool_size': 10,
                'timeout': 5,
                'retry_attempts': 3
            },
            'monitoring': {
                'enabled': True,
                'interval': 10,
                'metrics_retention': 3600
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return {**default_config, **config}
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save performance configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def optimize_cache(self):
        """Optimize cache performance"""
        try:
            # Get cache statistics
            stats = self.cache_service.get_cache_stats()
            
            # Clean up expired entries
            self.cache_service.clear_cache()
            
            # Optimize cache size based on memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self.config['memory']['cleanup_threshold']:
                # Reduce cache size when memory is high
                new_max_size = max(100, self.config['cache']['max_size'] // 2)
                self.config['cache']['max_size'] = new_max_size
                logger.info(f"Reduced cache size to {new_max_size} due to high memory usage")
            
            logger.info("Cache optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        try:
            import gc
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self.config['memory']['max_usage']:
                logger.warning(f"High memory usage detected: {memory_percent}%")
                
                # Clear caches
                self.cache_service.clear_cache()
                
                # Force garbage collection again
                gc.collect()
                
                logger.info("Memory cleanup completed")
            
            logger.info("Memory optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
    
    def optimize_processing(self):
        """Optimize processing performance"""
        try:
            # Get current CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Adjust worker count based on CPU usage
            if cpu_percent > 80:
                # Reduce workers when CPU is high
                new_workers = max(1, self.config['processing']['max_workers'] - 1)
                self.config['processing']['max_workers'] = new_workers
                logger.info(f"Reduced worker count to {new_workers} due to high CPU usage")
            elif cpu_percent < 50:
                # Increase workers when CPU is low
                new_workers = min(8, self.config['processing']['max_workers'] + 1)
                self.config['processing']['max_workers'] = new_workers
                logger.info(f"Increased worker count to {new_workers} due to low CPU usage")
            
            # Optimize batch size based on system load
            if cpu_percent > 70:
                # Reduce batch size when system is under load
                new_batch_size = max(5, self.config['processing']['batch_size'] - 1)
                self.config['processing']['batch_size'] = new_batch_size
                logger.info(f"Reduced batch size to {new_batch_size} due to high CPU usage")
            elif cpu_percent < 40:
                # Increase batch size when system is idle
                new_batch_size = min(20, self.config['processing']['batch_size'] + 1)
                self.config['processing']['batch_size'] = new_batch_size
                logger.info(f"Increased batch size to {new_batch_size} due to low CPU usage")
            
            logger.info("Processing optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing processing: {e}")
    
    def optimize_network(self):
        """Optimize network performance"""
        try:
            # Check network connections
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            # Adjust connection pool size based on active connections
            if active_connections > 50:
                # Reduce pool size when many connections are active
                new_pool_size = max(5, self.config['network']['connection_pool_size'] - 1)
                self.config['network']['connection_pool_size'] = new_pool_size
                logger.info(f"Reduced connection pool size to {new_pool_size}")
            elif active_connections < 10:
                # Increase pool size when few connections are active
                new_pool_size = min(20, self.config['network']['connection_pool_size'] + 1)
                self.config['network']['connection_pool_size'] = new_pool_size
                logger.info(f"Increased connection pool size to {new_pool_size}")
            
            logger.info("Network optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing network: {e}")
    
    def run_optimization_cycle(self):
        """Run a single optimization cycle"""
        try:
            logger.info("Starting optimization cycle")
            
            # Get current metrics
            metrics = self.get_system_metrics()
            logger.info(f"System metrics: CPU={metrics.get('cpu_percent', 0)}%, "
                       f"Memory={metrics.get('memory_percent', 0)}%")
            
            # Run optimizations
            self.optimize_cache()
            self.optimize_memory()
            self.optimize_processing()
            self.optimize_network()
            
            # Save updated configuration
            self.save_config(self.config)
            
            logger.info("Optimization cycle completed")
        except Exception as e:
            logger.error(f"Error in optimization cycle: {e}")
    
    def start_monitoring(self):
        """Start continuous performance monitoring and optimization"""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        self.running = True
        self.optimization_thread = threading.Thread(target=self._monitoring_loop)
        self.optimization_thread.daemon = True
        self.optimization_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.run_optimization_cycle()
                time.sleep(self.config['monitoring']['interval'])
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        try:
            metrics = self.get_system_metrics()
            
            # Get cache statistics
            cache_stats = self.cache_service.get_cache_stats()
            
            # Get processing statistics
            processing_stats = {
                'max_workers': self.config['processing']['max_workers'],
                'batch_size': self.config['processing']['batch_size'],
                'timeout': self.config['processing']['timeout']
            }
            
            # Get memory statistics
            memory_stats = {
                'max_usage': self.config['memory']['max_usage'],
                'cleanup_threshold': self.config['memory']['cleanup_threshold'],
                'current_usage': metrics.get('memory_percent', 0)
            }
            
            report = {
                'timestamp': time.time(),
                'system_metrics': metrics,
                'cache_stats': cache_stats,
                'processing_stats': processing_stats,
                'memory_stats': memory_stats,
                'config': self.config
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {}
    
    def save_performance_report(self, report: Dict[str, Any], filename: str = None):
        """Save performance report to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"performance_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Performance report saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving performance report: {e}")
    
    def optimize_for_load(self, load_type: str):
        """Optimize system for specific load type"""
        try:
            if load_type == 'high':
                # Optimize for high load
                self.config['processing']['max_workers'] = 2
                self.config['processing']['batch_size'] = 5
                self.config['cache']['max_size'] = 500
                self.config['memory']['cleanup_threshold'] = 60
                logger.info("Optimized for high load")
            elif load_type == 'low':
                # Optimize for low load
                self.config['processing']['max_workers'] = 8
                self.config['processing']['batch_size'] = 20
                self.config['cache']['max_size'] = 2000
                self.config['memory']['cleanup_threshold'] = 80
                logger.info("Optimized for low load")
            elif load_type == 'balanced':
                # Optimize for balanced load
                self.config['processing']['max_workers'] = 4
                self.config['processing']['batch_size'] = 10
                self.config['cache']['max_size'] = 1000
                self.config['memory']['cleanup_threshold'] = 70
                logger.info("Optimized for balanced load")
            else:
                logger.warning(f"Unknown load type: {load_type}")
                return
            
            self.save_config(self.config)
        except Exception as e:
            logger.error(f"Error optimizing for load: {e}")
    
    def cleanup_old_files(self, max_age_days: int = 7):
        """Clean up old temporary files"""
        try:
            temp_dirs = [
                'temp_uploads',
                'videos',
                'cache'
            ]
            
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file_path in Path(temp_dir).rglob('*'):
                        if file_path.is_file():
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > max_age_seconds:
                                file_path.unlink()
                                logger.info(f"Deleted old file: {file_path}")
            
            logger.info("File cleanup completed")
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Performance optimization script')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--optimize', help='Optimize for specific load type (high/low/balanced)')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old files')
    parser.add_argument('--interval', type=int, default=10, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = PerformanceOptimizer(args.config)
    
    if args.interval:
        optimizer.config['monitoring']['interval'] = args.interval
    
    try:
        if args.monitor:
            # Start continuous monitoring
            optimizer.start_monitoring()
            logger.info("Performance monitoring started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                optimizer.stop_monitoring()
        elif args.optimize:
            # Optimize for specific load type
            optimizer.optimize_for_load(args.optimize)
        elif args.report:
            # Generate performance report
            report = optimizer.generate_performance_report()
            optimizer.save_performance_report(report)
        elif args.cleanup:
            # Clean up old files
            optimizer.cleanup_old_files()
        else:
            # Run single optimization cycle
            optimizer.run_optimization_cycle()
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

