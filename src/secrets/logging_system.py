"""
Centralized logging system for the Secrets application.
Provides structured logging with configurable levels, formatters, and handlers.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timezone, time
from enum import Enum
import json
import threading
import traceback
import socket
import uuid
import platform
import psutil
import gzip
import bz2
import lzma
import shutil
import time as time_module
import sched
import queue
from gi.repository import GLib

from .config import ConfigManager
from .i18n import get_translation_function
from .build_info import is_production_build, filter_log_level_for_production, should_enable_debug_features

# Get translation function
_ = get_translation_function()


class LogLevel(Enum):
    """Log levels for the application."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogCategory(Enum):
    """Categories for organizing log messages."""
    APPLICATION = "application"
    UI = "ui"
    PASSWORD_STORE = "password_store"
    SECURITY = "security"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    GIT = "git"
    COMPLIANCE = "compliance"
    IMPORT_EXPORT = "import_export"
    CLIPBOARD = "clipboard"
    SEARCH = "search"
    BACKUP = "backup"
    SETUP = "setup"


class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Enhanced rotating file handler with compression support."""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, compression_format='gzip'):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compression_format = compression_format.lower()
        self.supported_formats = {'gzip': gzip, 'bz2': bz2, 'lzma': lzma}
        
        if self.compression_format not in self.supported_formats:
            raise ValueError(f"Unsupported compression format: {compression_format}")
    
    def doRollover(self):
        """Enhanced rollover with compression support."""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            # Compress and move existing backups
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i+1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            # Compress the current log file
            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if os.path.exists(dfn):
                os.remove(dfn)
            
            # Compress the current log file
            self._compress_file(self.baseFilename, dfn)
            
        if not self.delay:
            self.stream = self._open()
    
    def _compress_file(self, source_path: str, dest_path: str):
        """Compress a log file using the specified compression format."""
        try:
            compression_module = self.supported_formats[self.compression_format]
            
            # Add appropriate extension
            extensions = {'gzip': '.gz', 'bz2': '.bz2', 'lzma': '.xz'}
            compressed_dest = f"{dest_path}{extensions[self.compression_format]}"
            
            with open(source_path, 'rb') as f_in:
                with compression_module.open(compressed_dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the original file after successful compression
            os.remove(source_path)
            
        except Exception as e:
            # Fallback to regular rename if compression fails
            os.rename(source_path, dest_path)
            logging.getLogger(__name__).warning(f"Failed to compress log file {source_path}: {e}")


class TimedCompressingRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Enhanced timed rotating file handler with compression support."""
    
    def __init__(self, filename, when='h', interval=1, backupCount=0, 
                 encoding=None, delay=False, utc=False, atTime=None,
                 compression_format='gzip'):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)
        self.compression_format = compression_format.lower()
        self.supported_formats = {'gzip': gzip, 'bz2': bz2, 'lzma': lzma}
        
        if self.compression_format not in self.supported_formats:
            raise ValueError(f"Unsupported compression format: {compression_format}")
    
    def doRollover(self):
        """Enhanced rollover with compression support."""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time_module.time())
        dstNow = time_module.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time_module.gmtime(t)
        else:
            timeTuple = time_module.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time_module.localtime(t + addend)
        
        dfn = self.rotation_filename(f"{self.baseFilename}.{time_module.strftime(self.suffix, timeTuple)}")
        
        if os.path.exists(dfn):
            os.remove(dfn)
        
        # Compress the current log file
        self._compress_file(self.baseFilename, dfn)
        
        if self.backupCount > 0:
            self._cleanup_old_files()
        
        if not self.delay:
            self.stream = self._open()
        
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        
        self.rolloverAt = newRolloverAt
    
    def _compress_file(self, source_path: str, dest_path: str):
        """Compress a log file using the specified compression format."""
        try:
            compression_module = self.supported_formats[self.compression_format]
            
            # Add appropriate extension
            extensions = {'gzip': '.gz', 'bz2': '.bz2', 'lzma': '.xz'}
            compressed_dest = f"{dest_path}{extensions[self.compression_format]}"
            
            with open(source_path, 'rb') as f_in:
                with compression_module.open(compressed_dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the original file after successful compression
            os.remove(source_path)
            
        except Exception as e:
            # Fallback to regular rename if compression fails
            os.rename(source_path, dest_path)
            logging.getLogger(__name__).warning(f"Failed to compress log file {source_path}: {e}")
    
    def _cleanup_old_files(self):
        """Clean up old compressed log files."""
        # Find all log files matching our pattern
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)
        
        # Include compressed extensions
        extensions = ['.gz', '.bz2', '.xz']
        
        for fileName in fileNames:
            if fileName.startswith(prefix):
                suffix = fileName[plen:]
                # Remove compression extension if present
                for ext in extensions:
                    if suffix.endswith(ext):
                        suffix = suffix[:-len(ext)]
                        break
                
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        
        for s in result:
            os.remove(s)


class LogRotationManager:
    """Advanced log rotation and management system."""
    
    def __init__(self, config_manager: ConfigManager, log_dir: Path):
        self.config_manager = config_manager
        self.log_dir = log_dir
        self.config = config_manager.get_config().logging
        self._scheduler = sched.scheduler(time_module.time, time_module.sleep)
        self._cleanup_thread = None
        self._monitoring_thread = None
        self._stop_event = threading.Event()
        
        # Create archive directory if needed
        if self.config.enable_log_archiving and self.config.archive_directory:
            self.archive_dir = Path(self.config.archive_directory)
            self.archive_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.archive_dir = self.log_dir / "archive"
            if self.config.enable_log_archiving:
                self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def create_handler(self, log_file: Path, handler_type: str = "main") -> logging.Handler:
        """Create an appropriate handler based on configuration."""
        config = self.config
        
        # Handler-specific configurations
        handler_configs = {
            "main": {
                "max_bytes": config.max_log_file_size_mb * 1024 * 1024,
                "backup_count": config.backup_count,
                "level": logging.DEBUG
            },
            "error": {
                "max_bytes": 5 * 1024 * 1024,  # 5MB
                "backup_count": max(3, config.backup_count // 2),
                "level": logging.ERROR
            },
            "security": {
                "max_bytes": 20 * 1024 * 1024,  # 20MB
                "backup_count": max(10, config.backup_count * 2),
                "level": logging.INFO
            }
        }
        
        handler_config = handler_configs.get(handler_type, handler_configs["main"])
        
        if config.rotation_strategy == "time":
            return self._create_time_handler(log_file, handler_config)
        elif config.rotation_strategy == "mixed":
            return self._create_mixed_handler(log_file, handler_config)
        else:  # Default to size-based
            return self._create_size_handler(log_file, handler_config)
    
    def _create_size_handler(self, log_file: Path, handler_config: Dict) -> logging.Handler:
        """Create a size-based rotating handler."""
        if self.config.enable_compression:
            handler = CompressingRotatingFileHandler(
                filename=str(log_file),
                maxBytes=handler_config["max_bytes"],
                backupCount=handler_config["backup_count"],
                compression_format=self.config.compression_format
            )
        else:
            handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=handler_config["max_bytes"],
                backupCount=handler_config["backup_count"]
            )
        
        handler.setLevel(handler_config["level"])
        return handler
    
    def _create_time_handler(self, log_file: Path, handler_config: Dict) -> logging.Handler:
        """Create a time-based rotating handler."""
        # Parse rotation time
        at_time = None
        if self.config.rotation_at_time:
            try:
                hour, minute = map(int, self.config.rotation_at_time.split(':'))
                at_time = time(hour=hour, minute=minute)
            except ValueError:
                pass  # Use default (midnight)
        
        if self.config.enable_compression:
            handler = TimedCompressingRotatingFileHandler(
                filename=str(log_file),
                when=self.config.rotation_interval,
                interval=self.config.rotation_interval_count,
                backupCount=handler_config["backup_count"],
                atTime=at_time,
                compression_format=self.config.compression_format
            )
        else:
            handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(log_file),
                when=self.config.rotation_interval,
                interval=self.config.rotation_interval_count,
                backupCount=handler_config["backup_count"],
                atTime=at_time
            )
        
        handler.setLevel(handler_config["level"])
        return handler
    
    def _create_mixed_handler(self, log_file: Path, handler_config: Dict) -> logging.Handler:
        """Create a mixed size and time-based handler (size takes precedence)."""
        # For mixed strategy, we'll use size-based with additional time-based cleanup
        handler = self._create_size_handler(log_file, handler_config)
        
        # Mixed strategy relies on automatic cleanup for time-based rotation
        return handler
    
    def _schedule_time_based_cleanup(self):
        """Schedule time-based cleanup (used internally)."""
        # This is handled by the monitoring thread in start_management()
        pass
    
    def start_management(self):
        """Start the log management background tasks."""
        if self.config.enable_automatic_cleanup:
            self._start_cleanup_thread()
        
        if self.config.enable_log_monitoring:
            self._start_monitoring_thread()
    
    def stop_management(self):
        """Stop the log management background tasks."""
        self._stop_event.set()
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
    
    def _start_cleanup_thread(self):
        """Start the automatic cleanup thread."""
        def cleanup_worker():
            while not self._stop_event.is_set():
                try:
                    self.perform_maintenance()
                    self._stop_event.wait(self.config.cleanup_check_interval_hours * 3600)
                except Exception as e:
                    logging.getLogger(__name__).error(f"Error in cleanup thread: {e}")
                    self._stop_event.wait(3600)  # Wait 1 hour on error
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _start_monitoring_thread(self):
        """Start the log monitoring thread."""
        def monitoring_worker():
            while not self._stop_event.is_set():
                try:
                    self.check_disk_usage()
                    self.check_log_sizes()
                    self._stop_event.wait(300)  # Check every 5 minutes
                except Exception as e:
                    logging.getLogger(__name__).error(f"Error in monitoring thread: {e}")
                    self._stop_event.wait(600)  # Wait 10 minutes on error
        
        self._monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        self._monitoring_thread.start()
    
    def perform_maintenance(self):
        """Perform comprehensive log maintenance."""
        logger = logging.getLogger(__name__)
        
        # Clean up old files
        cleaned_files = self._cleanup_old_logs()
        
        # Archive old logs if enabled
        archived_files = []
        if self.config.enable_log_archiving:
            archived_files = self._archive_old_logs()
        
        # Check total log size and clean up if needed
        size_cleaned = self._enforce_total_size_limit()
        
        # Log maintenance summary
        if cleaned_files or archived_files or size_cleaned:
            logger.info("Log maintenance completed", extra={
                'cleaned_files_count': len(cleaned_files),
                'archived_files_count': len(archived_files),
                'size_cleanup_mb': round(size_cleaned / (1024 * 1024), 2),
                'maintenance_type': 'automatic'
            })
    
    def _cleanup_old_logs(self) -> List[str]:
        """Clean up logs older than retention period."""
        current_time = time_module.time()
        cutoff_time = current_time - (self.config.log_retention_days * 24 * 60 * 60)
        
        cleaned_files = []
        
        # Include compressed file extensions
        patterns = ["*.log*", "*.gz", "*.bz2", "*.xz"]
        
        for pattern in patterns:
            for log_file in self.log_dir.glob(pattern):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        cleaned_files.append(str(log_file))
                except (OSError, IOError) as e:
                    logging.getLogger(__name__).warning(f"Failed to clean up log file {log_file}: {e}")
        
        return cleaned_files
    
    def _archive_old_logs(self) -> List[str]:
        """Archive old logs to archive directory."""
        if not self.config.enable_log_archiving:
            return []
        
        # Archive logs older than 7 days but within retention period
        current_time = time_module.time()
        archive_cutoff = current_time - (7 * 24 * 60 * 60)  # 7 days
        retention_cutoff = current_time - (self.config.log_retention_days * 24 * 60 * 60)
        
        archived_files = []
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_time = log_file.stat().st_mtime
                if retention_cutoff < file_time < archive_cutoff:
                    # Move to archive
                    archive_path = self.archive_dir / log_file.name
                    shutil.move(str(log_file), str(archive_path))
                    archived_files.append(str(log_file))
            except (OSError, IOError) as e:
                logging.getLogger(__name__).warning(f"Failed to archive log file {log_file}: {e}")
        
        return archived_files
    
    def _enforce_total_size_limit(self) -> int:
        """Enforce total log size limit by removing oldest files."""
        max_total_size = self.config.max_total_log_size_mb * 1024 * 1024
        
        # Get all log files with their sizes and modification times
        log_files = []
        total_size = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                stat = log_file.stat()
                log_files.append((log_file, stat.st_size, stat.st_mtime))
                total_size += stat.st_size
            except (OSError, IOError):
                continue
        
        if total_size <= max_total_size:
            return 0
        
        # Sort by modification time (oldest first)
        log_files.sort(key=lambda x: x[2])
        
        size_to_remove = total_size - max_total_size
        size_removed = 0
        
        for log_file, file_size, _ in log_files:
            if size_removed >= size_to_remove:
                break
            
            try:
                log_file.unlink()
                size_removed += file_size
            except (OSError, IOError) as e:
                logging.getLogger(__name__).warning(f"Failed to remove log file {log_file}: {e}")
        
        return size_removed
    
    def check_disk_usage(self):
        """Monitor disk usage and issue warnings."""
        if not self.config.monitor_disk_usage:
            return
        
        try:
            stat = shutil.disk_usage(self.log_dir)
            total_space = stat.total
            free_space = stat.free
            used_percent = ((total_space - free_space) / total_space) * 100
            
            logger = logging.getLogger(__name__)
            
            if used_percent >= self.config.disk_usage_critical_threshold_percent:
                logger.critical("Critical disk usage detected", extra={
                    'disk_usage_percent': round(used_percent, 2),
                    'free_space_mb': round(free_space / (1024 * 1024), 2),
                    'log_directory': str(self.log_dir),
                    'monitoring_type': 'disk_usage'
                })
            elif used_percent >= self.config.disk_usage_warning_threshold_percent:
                logger.warning("High disk usage detected", extra={
                    'disk_usage_percent': round(used_percent, 2),
                    'free_space_mb': round(free_space / (1024 * 1024), 2),
                    'log_directory': str(self.log_dir),
                    'monitoring_type': 'disk_usage'
                })
        
        except OSError as e:
            logging.getLogger(__name__).error(f"Failed to check disk usage: {e}")
    
    def check_log_sizes(self):
        """Monitor individual log file sizes."""
        logger = logging.getLogger(__name__)
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                size = log_file.stat().st_size
                size_mb = size / (1024 * 1024)
                
                # Warn if approaching rotation size
                max_size_mb = self.config.max_log_file_size_mb
                if size_mb > max_size_mb * 0.9:  # 90% of max size
                    logger.debug("Log file approaching rotation size", extra={
                        'log_file': str(log_file),
                        'current_size_mb': round(size_mb, 2),
                        'max_size_mb': max_size_mb,
                        'monitoring_type': 'file_size'
                    })
            
            except (OSError, IOError):
                continue
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """Get detailed rotation and management status."""
        status = {
            'rotation_strategy': self.config.rotation_strategy,
            'compression_enabled': self.config.enable_compression,
            'compression_format': self.config.compression_format,
            'automatic_cleanup_enabled': self.config.enable_automatic_cleanup,
            'monitoring_enabled': self.config.enable_log_monitoring,
            'log_files': {},
            'total_size_mb': 0,
            'archive_status': {}
        }
        
        # Collect log file information
        total_size = 0
        for log_file in self.log_dir.glob("*.log*"):
            try:
                stat = log_file.stat()
                size = stat.st_size
                total_size += size
                
                status['log_files'][log_file.name] = {
                    'size_mb': round(size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'compressed': log_file.suffix in ['.gz', '.bz2', '.xz']
                }
            except (OSError, IOError):
                continue
        
        status['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        # Archive status
        if self.config.enable_log_archiving and self.archive_dir.exists():
            archive_size = 0
            archive_count = 0
            for archive_file in self.archive_dir.glob("*"):
                try:
                    archive_size += archive_file.stat().st_size
                    archive_count += 1
                except (OSError, IOError):
                    continue
            
            status['archive_status'] = {
                'enabled': True,
                'directory': str(self.archive_dir),
                'file_count': archive_count,
                'total_size_mb': round(archive_size / (1024 * 1024), 2)
            }
        else:
            status['archive_status'] = {'enabled': False}
        
        return status


class StructuredFormatter(logging.Formatter):
    """Enhanced structured formatter with comprehensive parsing capabilities."""
    
    def __init__(self, include_extra=True, include_context=True, format_version="1.1"):
        super().__init__()
        self.include_extra = include_extra
        self.include_context = include_context
        self.format_version = format_version
        self.hostname = socket.gethostname()
        self.session_id = str(uuid.uuid4())[:8]  # Short session identifier
        
        # Cache system information for performance
        self._system_info = self._get_system_info()
        self._app_version = self._get_app_version()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for enhanced context."""
        try:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor() or 'unknown',
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine()
            }
        except Exception:
            return {'platform': 'unknown'}
    
    def _get_app_version(self) -> str:
        """Get application version from meson.build as single source of truth."""
        from .version import get_version
        return get_version()
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            }
        except Exception:
            return {}
    
    def _get_environment_context(self) -> Dict[str, Any]:
        """Get environment-specific context."""
        env_context = {
            'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            'home': os.getenv('HOME', os.getenv('USERPROFILE', 'unknown')),
            'pwd': os.getcwd(),
            'python_path': sys.executable
        }
        
        # Add development vs production indicators
        if os.getenv('MESON_BUILD_ROOT'):
            env_context['environment'] = 'development'
            env_context['build_root'] = os.getenv('MESON_BUILD_ROOT')
        elif os.getenv('FLATPAK_ID'):
            env_context['environment'] = 'flatpak'
            env_context['flatpak_id'] = os.getenv('FLATPAK_ID')
        else:
            env_context['environment'] = 'system'
        
        return env_context
    
    def format(self, record):
        # Core structured log data following common logging standards
        log_data = {
            # Standard fields for log parsing
            '@timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            '@version': self.format_version,
            'level': record.levelname,
            'level_no': record.levelno,
            'message': record.getMessage(),
            
            # Enhanced source information
            'logger': {
                'name': record.name,
                'module': record.module or 'unknown',
                'function': record.funcName or 'unknown',
                'line': record.lineno,
                'file': record.pathname,
                'filename': record.filename,
                'relative_path': os.path.relpath(record.pathname) if record.pathname else 'unknown'
            },
            
            # Enhanced process and thread information
            'process': {
                'id': record.process,
                'name': record.processName if hasattr(record, 'processName') else 'secrets',
                'thread_id': record.thread,
                'thread_name': record.threadName if hasattr(record, 'threadName') else 'MainThread'
            },
            
            # Enhanced application context
            'application': {
                'name': 'secrets',
                'version': self._app_version,
                'hostname': self.hostname,
                'session_id': self.session_id
            },
            
            # System context (cached for performance)
            'system': self._system_info if self.include_context else {}
        }
        
        # Add environment context for enhanced debugging
        if self.include_context:
            log_data['environment'] = self._get_environment_context()
            
            # Add memory information for performance monitoring
            memory_info = self._get_memory_info()
            if memory_info:
                log_data['performance'] = {
                    'memory': memory_info
                }
        
        # Add timing information for performance analysis
        if self.include_context:
            log_data['timing'] = {
                'created': record.created,
                'relative_created': record.relativeCreated,
                'msecs': record.msecs
            }
        
        # Add category if available (from our LogCategory system)
        if hasattr(record, 'category'):
            log_data['category'] = record.category.value if hasattr(record.category, 'value') else str(record.category)
        
        # Add user action flag for audit purposes
        if hasattr(record, 'user_action'):
            log_data['user_action'] = record.user_action
            
        # Add security event flag for compliance
        if hasattr(record, 'security_event'):
            log_data['security_event'] = record.security_event
        
        # Enhanced exception handling with structured data
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_data['exception'] = {
                'type': exc_type.__name__ if exc_type else None,
                'message': str(exc_value) if exc_value else None,
                'traceback': self.formatException(record.exc_info),
                'traceback_lines': traceback.format_exception(exc_type, exc_value, exc_traceback) if exc_traceback else []
            }
        
        # Add stack info if present
        if record.stack_info:
            log_data['stack_info'] = record.stack_info
        
        # Process extra fields with structured organization
        if self.include_extra and hasattr(record, '__dict__'):
            reserved_fields = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'message', 'exc_info',
                'exc_text', 'stack_info', 'category', 'user_action', 'security_event'
            }
            
            # Organize extra fields by type for better parsing
            structured_extra = {
                'data': {},
                'metrics': {},
                'tags': []
            }
            
            for key, value in record.__dict__.items():
                if key not in reserved_fields:
                    # Categorize extra fields for better parsing
                    if key.endswith('_count') or key.endswith('_time') or key.endswith('_size'):
                        structured_extra['metrics'][key] = value
                    elif key.startswith('tag_') or key == 'tags':
                        if isinstance(value, list):
                            structured_extra['tags'].extend(value)
                        else:
                            structured_extra['tags'].append(value)
                    else:
                        structured_extra['data'][key] = value
            
            # Only add non-empty sections
            if structured_extra['data']:
                log_data['data'] = structured_extra['data']
            if structured_extra['metrics']:
                log_data['metrics'] = structured_extra['metrics']
            if structured_extra['tags']:
                log_data['tags'] = structured_extra['tags']
        
        return json.dumps(log_data, default=self._json_serializer, ensure_ascii=False, separators=(',', ':'))
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return str(obj)  # Convert complex objects to string
        elif isinstance(obj, Exception):
            return {
                'type': type(obj).__name__,
                'message': str(obj),
                'args': obj.args
            }
        else:
            return str(obj)


class HumanReadableFormatter(logging.Formatter):
    """Enhanced human-readable formatter for console output with detailed context."""
    
    def __init__(self, include_location=True, include_thread=False, include_process=False):
        self.include_location = include_location
        self.include_thread = include_thread
        self.include_process = include_process
        
        # Build format string based on options
        fmt_parts = ['%(asctime)s', '[%(levelname)8s]']
        
        if include_process:
            fmt_parts.append('(%(process)d)')
        if include_thread:
            fmt_parts.append('[%(threadName)s]')
            
        fmt_parts.extend(['%(name)s', ': %(message)s'])
        
        super().__init__(
            fmt=' '.join(fmt_parts),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        # Enhance logger name with category and location info
        enhanced_name = record.name
        
        # Add category prefix if available
        if hasattr(record, 'category'):
            enhanced_name = f"{record.category.value}:{enhanced_name}"
        
        # Add location information for debugging
        if self.include_location and record.funcName and record.funcName != '<module>':
            location = f"{record.module or 'unknown'}:{record.funcName}:{record.lineno}"
            enhanced_name = f"{enhanced_name}[{location}]"
        
        # Store original name and restore after formatting
        original_name = record.name
        record.name = enhanced_name
        
        # Format the record
        formatted = super().format(record)
        
        # Add contextual information if available
        context_parts = []
        
        # Add user action indicator
        if hasattr(record, 'user_action') and record.user_action:
            context_parts.append("👤USER")
        
        # Add security event indicator
        if hasattr(record, 'security_event') and record.security_event:
            context_parts.append("🔒SECURITY")
        
        # Add tags if present
        if hasattr(record, 'tags') and record.tags:
            tags_str = ','.join(record.tags[:3])  # Limit to first 3 tags
            context_parts.append(f"#{tags_str}")
        
        # Add performance indicators
        if hasattr(record, 'execution_time'):
            context_parts.append(f"⏱{record.execution_time:.3f}s")
        
        # Append context if any
        if context_parts:
            formatted += f" [{' '.join(context_parts)}]"
        
        # Restore original name
        record.name = original_name
        
        return formatted


class LoggingSystem:
    """Centralized logging system for the Secrets application."""
    
    def __init__(self, config_manager: ConfigManager, app_id: str = "io.github.tobagin.secrets"):
        self.config_manager = config_manager
        self.app_id = app_id
        self.config = config_manager.get_config()
        
        # Create log directory
        self.log_dir = self._get_log_directory()
        self._ensure_log_directory()
        
        # Initialize advanced rotation manager
        self.rotation_manager = LogRotationManager(config_manager, self.log_dir)
        
        # Threading lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Initialize logging
        self._setup_root_logger()
        self._setup_application_loggers()
        self._setup_external_loggers()
        
        # Start log management background tasks
        self.rotation_manager.start_management()
        
        # Get the main application logger
        self.logger = logging.getLogger(app_id)
        
    def _setup_root_logger(self):
        """Configure the root logger."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)  # Only show warnings and errors from external libs
        
        # Console handler for root logger (errors only)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(console_handler)
    
    def _setup_application_loggers(self):
        """Setup loggers for the Secrets application."""
        # Main application logger
        app_logger = logging.getLogger(self.app_id)
        
        # Set appropriate log level based on production mode
        if is_production_build():
            app_logger.setLevel(logging.INFO)  # No DEBUG in production
        else:
            app_logger.setLevel(logging.DEBUG)
            
        app_logger.propagate = False  # Don't propagate to root logger
        
        # Clear any existing handlers
        app_logger.handlers.clear()
        
        # File handlers
        self._add_file_handlers(app_logger)
        
        # Console handler (configurable level)
        self._add_console_handler(app_logger)
        
        # Setup category-specific loggers
        for category in LogCategory:
            category_logger = logging.getLogger(f"{self.app_id}.{category.value}")
            category_logger.setLevel(logging.DEBUG)
            category_logger.propagate = True  # Propagate to app logger
    
    def _add_file_handlers(self, logger: logging.Logger):
        """Add enhanced file handlers using the rotation manager."""
        with self._lock:
            # Main log file with advanced rotation
            main_log_file = self.log_dir / "secrets.log"
            file_handler = self.rotation_manager.create_handler(main_log_file, "main")
            
            # Set file handler level based on config and production mode
            requested_level = self.config.logging.log_level.upper()
            filtered_level = filter_log_level_for_production(requested_level)
            config_level = getattr(logging, filtered_level, logging.INFO)
            
            if is_production_build():
                file_handler.setLevel(max(config_level, logging.INFO))  # No DEBUG in production files
            else:
                file_handler.setLevel(min(config_level, logging.DEBUG))  # File can be more verbose in dev
            
            # Use structured or human-readable formatter based on config
            if self.config.logging.enable_structured_logging:
                file_handler.setFormatter(StructuredFormatter(include_extra=True, include_context=True))
            else:
                file_handler.setFormatter(HumanReadableFormatter())
            
            logger.addHandler(file_handler)
            
            # Error log file with enhanced rotation
            error_log_file = self.log_dir / "errors.log"
            error_handler = self.rotation_manager.create_handler(error_log_file, "error")
            
            # Always use structured format for error logs for better analysis
            error_handler.setFormatter(StructuredFormatter(include_extra=True, include_context=True))
            logger.addHandler(error_handler)
            
            # Security audit log with enhanced rotation
            security_log_file = self.log_dir / "security.log"
            security_handler = self.rotation_manager.create_handler(security_log_file, "security")
            
            # Always use structured format for security logs for compliance
            security_handler.setFormatter(StructuredFormatter(include_extra=True, include_context=True))
            
            # Add filter to only log security-related messages
            security_handler.addFilter(lambda record: 
                hasattr(record, 'category') and 
                record.category in [LogCategory.SECURITY, LogCategory.COMPLIANCE])
            
            logger.addHandler(security_handler)
    
    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler to a logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Set console log level based on configuration or environment
        console_level = self._get_console_log_level()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(HumanReadableFormatter())
        
        logger.addHandler(console_handler)
    
    def _get_console_log_level(self) -> int:
        """Determine console log level from config or environment."""
        # In production mode, ignore debug environment variables for security
        if not is_production_build():
            # Check environment variable first (for development only)
            env_level = os.environ.get('SECRETS_LOG_LEVEL', '').upper()
            if env_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                return getattr(logging, env_level)
            
            # Check if running in development mode
            if should_enable_debug_features():
                return logging.DEBUG
        
        # Use config setting if available (with production filtering)
        requested_level = self.config.logging.log_level.upper()
        filtered_level = filter_log_level_for_production(requested_level)
        if filtered_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            return getattr(logging, filtered_level)
        
        # Default based on build mode
        return logging.WARNING if is_production_build() else logging.INFO
    
    def _setup_external_loggers(self):
        """Configure logging for external libraries."""
        # Reduce verbosity of external libraries
        external_loggers = [
            'gi.repository',
            'urllib3',
            'requests',
            'PIL',
            'matplotlib',
            'asyncio'
        ]
        
        for logger_name in external_loggers:
            ext_logger = logging.getLogger(logger_name)
            ext_logger.setLevel(logging.WARNING)
    
    def get_logger(self, category: LogCategory = None, name: str = None) -> logging.Logger:
        """Get a logger for a specific category or name with enhanced contextual information."""
        if category:
            logger_name = f"{self.app_id}.{category.value}"
            if name:
                logger_name = f"{logger_name}.{name}"
        elif name:
            logger_name = f"{self.app_id}.{name}"
        else:
            logger_name = self.app_id
        
        logger = logging.getLogger(logger_name)
        
        # Create enhanced adapter that adds comprehensive contextual info
        class EnhancedContextAdapter(logging.LoggerAdapter):
            def __init__(self, logger, extra, category=None):
                super().__init__(logger, extra)
                self.category = category
                self._caller_cache = {}
            
            def process(self, msg, kwargs):
                # Get caller information automatically
                import inspect
                frame = inspect.currentframe()
                try:
                    # Go up the stack to find the actual caller (skip logging internals)
                    caller_frame = frame.f_back.f_back.f_back
                    if caller_frame:
                        caller_info = {
                            'caller_file': caller_frame.f_code.co_filename,
                            'caller_function': caller_frame.f_code.co_name,
                            'caller_line': caller_frame.f_lineno,
                            'caller_module': inspect.getmodule(caller_frame).__name__ if inspect.getmodule(caller_frame) else 'unknown'
                        }
                    else:
                        caller_info = {}
                except Exception:
                    caller_info = {}
                finally:
                    del frame
                
                # Set up extra context
                extra = kwargs.setdefault('extra', {})
                
                # Add category if available
                if self.category:
                    extra['category'] = self.category
                
                # Add caller context to extra data
                if caller_info:
                    extra.update(caller_info)
                
                # Add automatic timing for performance monitoring
                import time
                extra['log_time'] = time.time()
                
                return msg, kwargs
        
        # Return enhanced adapter
        return EnhancedContextAdapter(logger, {}, category)
    
    def log_startup(self):
        """Log application startup information."""
        logger = self.get_logger(LogCategory.APPLICATION)
        logger.info("Secrets application starting up", extra={
            'app_id': self.app_id,
            'log_dir': str(self.log_dir),
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        })
    
    def log_shutdown(self):
        """Log application shutdown and stop rotation management."""
        logger = self.get_logger(LogCategory.APPLICATION)
        logger.info("Secrets application shutting down", extra={
            'shutdown_reason': 'normal',
            'total_log_files': len(list(self.log_dir.glob("*.log*"))),
            'rotation_status': self.rotation_manager.get_rotation_status()
        })
        
        # Stop the rotation manager background tasks
        self.rotation_manager.stop_management()
    
    def log_user_action(self, action: str, category: LogCategory, **kwargs):
        """Log user actions for audit purposes."""
        logger = self.get_logger(category)
        logger.info(f"User action: {action}", extra={
            'action': action,
            'user_action': True,
            **kwargs
        })
    
    def log_security_event(self, event: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log security-related events."""
        logger = self.get_logger(LogCategory.SECURITY)
        log_method = getattr(logger, level.name.lower())
        log_method(f"Security event: {event}", extra={
            'security_event': True,
            'event': event,
            **kwargs
        })
    
    def log_error_with_context(self, error: Exception, context: str, category: LogCategory = None):
        """Log errors with additional context."""
        logger = self.get_logger(category or LogCategory.APPLICATION)
        logger.error(f"Error in {context}: {str(error)}", extra={
            'error_type': type(error).__name__,
            'context': context,
            'error_details': str(error)
        }, exc_info=True)
    
    def cleanup_old_logs(self, days: int = None):
        """Clean up log files older than specified days using the rotation manager."""
        if days is None:
            days = self.config.logging.log_retention_days
        
        # Update config temporarily for this cleanup
        original_retention = self.config.logging.log_retention_days
        self.config.logging.log_retention_days = days
        
        try:
            self.rotation_manager.perform_maintenance()
        finally:
            # Restore original retention setting
            self.config.logging.log_retention_days = original_retention
    
    def force_log_rotation(self):
        """Force immediate rotation of all log files."""
        logger = logging.getLogger(self.app_id)
        
        for handler in logger.handlers:
            if hasattr(handler, 'doRollover'):
                try:
                    handler.doRollover()
                    self.logger.info(f"Forced rotation for handler: {type(handler).__name__}")
                except Exception as e:
                    self.logger.error(f"Failed to rotate handler {type(handler).__name__}: {e}")
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """Get detailed rotation and management status."""
        return self.rotation_manager.get_rotation_status()
    
    def perform_maintenance(self):
        """Perform comprehensive log maintenance."""
        self.rotation_manager.perform_maintenance()
    
    def check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage and return status."""
        try:
            stat = shutil.disk_usage(self.log_dir)
            total_space = stat.total
            free_space = stat.free
            used_percent = ((total_space - free_space) / total_space) * 100
            
            return {
                'total_space_mb': round(total_space / (1024 * 1024), 2),
                'free_space_mb': round(free_space / (1024 * 1024), 2),
                'used_percent': round(used_percent, 2),
                'warning_threshold': self.config.logging.disk_usage_warning_threshold_percent,
                'critical_threshold': self.config.logging.disk_usage_critical_threshold_percent,
                'status': 'critical' if used_percent >= self.config.logging.disk_usage_critical_threshold_percent
                         else 'warning' if used_percent >= self.config.logging.disk_usage_warning_threshold_percent
                         else 'normal'
            }
        except OSError as e:
            return {'error': str(e), 'status': 'error'}
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about log files."""
        stats = {
            'log_dir': str(self.log_dir),
            'files': {},
            'total_size': 0
        }
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_stat = log_file.stat()
                stats['files'][log_file.name] = {
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                }
                stats['total_size'] += file_stat.st_size
            except OSError:
                continue
        
        return stats
    
    def set_log_level(self, level: Union[str, LogLevel, int]):
        """Dynamically change the log level for console output."""
        if isinstance(level, str):
            level = level.upper()
            if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                level_int = getattr(logging, level)
            else:
                raise ValueError(f"Invalid log level: {level}")
        elif isinstance(level, LogLevel):
            level_int = level.value
        elif isinstance(level, int):
            level_int = level
        else:
            raise ValueError(f"Invalid log level type: {type(level)}")
        
        # Update config
        self.config.logging.log_level = logging.getLevelName(level_int)
        self.config_manager.save_config(self.config)
        
        # Update all console handlers
        app_logger = logging.getLogger(self.app_id)
        for handler in app_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level_int)
        
        self.logger.info(f"Log level changed to {logging.getLevelName(level_int)}")
    
    def update_configuration(self, logging_config):
        """Update logging system configuration at runtime."""
        self.config.logging = logging_config
        
        # Update log level
        if hasattr(logging_config, 'log_level'):
            level_int = getattr(logging, logging_config.log_level.upper(), logging.WARNING)
            
            # Update console handlers
            app_logger = logging.getLogger(self.app_id)
            for handler in app_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(level_int)
        
        # Update file logging settings
        if hasattr(logging_config, 'enable_file_logging'):
            app_logger = logging.getLogger(self.app_id)
            for handler in app_logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    if not logging_config.enable_file_logging:
                        app_logger.removeHandler(handler)
                        handler.close()
            
            # Re-add file handlers if enabled
            if logging_config.enable_file_logging and not any(
                isinstance(h, logging.FileHandler) for h in app_logger.handlers
            ):
                self._add_file_handlers(app_logger)
        
        # Update structured logging
        if hasattr(logging_config, 'enable_structured_logging'):
            app_logger = logging.getLogger(self.app_id)
            for handler in app_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    if logging_config.enable_structured_logging:
                        handler.setFormatter(StructuredFormatter(include_extra=True, include_context=True))
                    else:
                        handler.setFormatter(HumanReadableFormatter())
        
        self.logger.info("Logging configuration updated", extra={
            'log_level': logging_config.log_level,
            'file_logging': getattr(logging_config, 'enable_file_logging', True),
            'structured_logging': getattr(logging_config, 'enable_structured_logging', True)
        })
    
    def get_current_log_level(self) -> str:
        """Get the current log level."""
        return self.config.logging.log_level
    
    def get_available_log_levels(self) -> List[str]:
        """Get list of available log levels."""
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def _get_log_directory(self) -> Path:
        """Get the log directory based on configuration."""
        if self.config.logging.use_custom_log_directory and self.config.logging.custom_log_directory:
            # Use custom directory if configured and path is provided
            custom_path = Path(self.config.logging.custom_log_directory).expanduser()
            if custom_path.is_absolute():
                return custom_path
            else:
                # If relative path, make it relative to user data directory
                return Path(GLib.get_user_data_dir()) / custom_path
        else:
            # Use default directory
            return Path(GLib.get_user_data_dir()) / self.app_id / "logs"
    
    def _ensure_log_directory(self):
        """Ensure the log directory exists with proper permissions."""
        try:
            # Create directory with parents if needed
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Set permissions if using custom directory
            if self.config.logging.use_custom_log_directory:
                try:
                    permissions = int(self.config.logging.log_directory_permissions, 8)
                    os.chmod(self.log_dir, permissions)
                except (ValueError, OSError) as e:
                    self.logger.warning(f"Could not set log directory permissions: {e}", extra={
                        'log_dir': str(self.log_dir),
                        'permissions': self.config.logging.log_directory_permissions,
                        'error_type': type(e).__name__
                    })
        except OSError as e:
            # Fall back to default directory if custom directory fails
            if self.config.logging.use_custom_log_directory:
                self.logger.error(f"Failed to create custom log directory, falling back to default: {e}", extra={
                    'custom_log_dir': str(self.log_dir),
                    'error_type': type(e).__name__
                })
                # Use default directory as fallback
                self.log_dir = Path(GLib.get_user_data_dir()) / self.app_id / "logs"
                try:
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                except OSError as fallback_error:
                    self.logger.critical(f"Failed to create default log directory: {fallback_error}", extra={
                        'default_log_dir': str(self.log_dir),
                        'error_type': type(fallback_error).__name__
                    })
                    raise
            else:
                self.logger.critical(f"Failed to create log directory: {e}", extra={
                    'log_dir': str(self.log_dir),
                    'error_type': type(e).__name__
                })
                raise

    def is_level_enabled(self, level: Union[str, LogLevel, int]) -> bool:
        """Check if a specific log level is enabled."""
        if isinstance(level, str):
            level = level.upper()
            level_int = getattr(logging, level, None)
            if level_int is None:
                return False
        elif isinstance(level, LogLevel):
            level_int = level.value
        elif isinstance(level, int):
            level_int = level
        else:
            return False
        
        current_level = getattr(logging, self.config.logging.log_level.upper(), logging.WARNING)
        return level_int >= current_level


# Global logging system instance
_logging_system: Optional[LoggingSystem] = None


def initialize_logging(config_manager: ConfigManager, app_id: str = "io.github.tobagin.secrets") -> LoggingSystem:
    """Initialize the global logging system."""
    global _logging_system
    _logging_system = LoggingSystem(config_manager, app_id)
    _logging_system.log_startup()
    return _logging_system


def get_logging_system() -> Optional[LoggingSystem]:
    """Get the global logging system instance."""
    return _logging_system


def get_logger(category: LogCategory = None, name: str = None) -> logging.Logger:
    """Convenience function to get a logger."""
    if _logging_system:
        return _logging_system.get_logger(category, name)
    else:
        # Fallback to basic logger if system not initialized
        return logging.getLogger(name or "secrets.fallback")


def set_log_level(level: Union[str, LogLevel, int]):
    """Set the global log level."""
    if _logging_system:
        _logging_system.set_log_level(level)
    else:
        raise RuntimeError("Logging system not initialized. Call initialize_logging() first.")


def get_current_log_level() -> str:
    """Get the current global log level."""
    if _logging_system:
        return _logging_system.get_current_log_level()
    else:
        return "WARNING"  # Default fallback


def get_available_log_levels() -> List[str]:
    """Get available log levels."""
    return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def is_level_enabled(level: Union[str, LogLevel, int]) -> bool:
    """Check if a log level is enabled."""
    if _logging_system:
        return _logging_system.is_level_enabled(level)
    else:
        # Fallback: only WARNING and above enabled
        if isinstance(level, str):
            level_int = getattr(logging, level.upper(), logging.CRITICAL)
        elif isinstance(level, LogLevel):
            level_int = level.value
        else:
            level_int = level
        return level_int >= logging.WARNING


def shutdown_logging():
    """Shutdown the logging system."""
    global _logging_system
    if _logging_system:
        _logging_system.log_shutdown()
        # Give time for the shutdown message to be written
        import time
        time.sleep(0.1)
        
        # Shutdown all handlers
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        
        _logging_system = None


def log_execution_time(func):
    """Decorator to automatically log function execution time."""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Get logger for the function's module
        module_name = func.__module__.split('.')[-1] if func.__module__ else 'unknown'
        logger = get_logger(name=f"{module_name}.{func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.debug(f"Function {func.__name__} completed", extra={
                'execution_time': execution_time,
                'function_name': func.__name__,
                'module_name': module_name,
                'success': True,
                'tags': ['performance', 'execution_time']
            })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(f"Function {func.__name__} failed", extra={
                'execution_time': execution_time,
                'function_name': func.__name__,
                'module_name': module_name,
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'tags': ['performance', 'execution_time', 'error']
            })
            
            raise
    
    return wrapper


class LogContext:
    """Context manager for adding contextual information to all logs within a block."""
    
    def __init__(self, **context):
        self.context = context
        self.logger = get_logger()
        
    def __enter__(self):
        # Store original process method if it exists
        if hasattr(self.logger, 'process'):
            self.original_process = self.logger.process
        else:
            self.original_process = None
            
        # Create new process method that adds our context
        def enhanced_process(msg, kwargs):
            extra = kwargs.setdefault('extra', {})
            extra.update(self.context)
            
            if self.original_process:
                return self.original_process(msg, kwargs)
            else:
                return msg, kwargs
        
        self.logger.process = enhanced_process
        return self.logger
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original process method
        if self.original_process:
            self.logger.process = self.original_process
        elif hasattr(self.logger, 'process'):
            delattr(self.logger, 'process')


# Version Management Functions (moved to version.py module for better organization)


def get_current_version() -> str:
    """Get the current application version from meson.build."""
    from .version import get_version
    return get_version()


def validate_version_consistency() -> Dict[str, Any]:
    """Validate version consistency across all files."""
    from .version import get_version
    version = get_version()
    results = {
        'meson_version': version,
        'consistent': True,
        'issues': []
    }
    
    # Check __init__.py
    try:
        from . import __version__
        if __version__ != version:
            results['consistent'] = False
            results['issues'].append(f"__init__.py version mismatch: {__version__} vs {version}")
    except ImportError:
        results['issues'].append("Could not import __version__ from __init__.py")
    
    # Check app_info.py
    try:
        from .app_info import VERSION
        if VERSION != version:
            results['consistent'] = False
            results['issues'].append(f"app_info.py version mismatch: {VERSION} vs {version}")
    except ImportError:
        results['issues'].append("Could not import VERSION from app_info.py")
    
    return results


def log_version_info():
    """Log version information at startup."""
    from .version import get_version
    logger = get_logger(LogCategory.APPLICATION, "version")
    version_info = validate_version_consistency()
    version = get_version()
    
    logger.info(f"Application version: {version}", extra={
        'version': version,
        'version_source': 'meson.build',
        'version_consistent': version_info['consistent'],
        'version_issues': version_info['issues'] if version_info['issues'] else None
    })
    
    if not version_info['consistent']:
        logger.warning("Version inconsistency detected", extra={
            'meson_version': version_info['meson_version'],
            'issues': version_info['issues']
        })