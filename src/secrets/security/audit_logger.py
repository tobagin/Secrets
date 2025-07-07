"""Audit logging system for security events."""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import threading
import queue
import hashlib

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOCKED = "auth_locked"
    AUTH_UNLOCKED = "auth_unlocked"
    
    # Two-factor authentication
    TWO_FA_ENABLED = "two_fa_enabled"
    TWO_FA_DISABLED = "two_fa_disabled"
    TWO_FA_SUCCESS = "two_fa_success"
    TWO_FA_FAILURE = "two_fa_failure"
    
    # Password operations
    PASSWORD_ACCESSED = "password_accessed"
    PASSWORD_CREATED = "password_created"
    PASSWORD_MODIFIED = "password_modified"
    PASSWORD_DELETED = "password_deleted"
    PASSWORD_COPIED = "password_copied"
    
    # Configuration changes
    CONFIG_CHANGED = "config_changed"
    SECURITY_SETTINGS_CHANGED = "security_settings_changed"
    
    # File operations
    FILE_IMPORTED = "file_imported"
    FILE_EXPORTED = "file_exported"
    
    # Git operations
    GIT_PUSH = "git_push"
    GIT_PULL = "git_pull"
    GIT_SYNC = "git_sync"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    KEYRING_ACCESS = "keyring_access"
    HARDWARE_KEY_USED = "hardware_key_used"
    
    # Compliance events
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    COMPLIANCE_VIOLATION = "compliance_violation"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    COMPLIANCE_EVENT = "compliance_event"
    
    # Application events
    APP_STARTED = "app_started"
    APP_STOPPED = "app_stopped"
    APP_CRASHED = "app_crashed"


class AuditLevel(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: AuditEventType
    timestamp: str
    level: AuditLevel
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    process_id: Optional[int] = None
    thread_id: Optional[int] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.process_id is None:
            self.process_id = os.getpid()
        if self.thread_id is None:
            self.thread_id = threading.get_ident()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(',', ':'))


class AuditLogFormatter:
    """Formats audit events for different outputs."""
    
    @staticmethod
    def format_json(event: AuditEvent) -> str:
        """Format event as JSON."""
        return event.to_json()
    
    @staticmethod
    def format_human_readable(event: AuditEvent) -> str:
        """Format event for human reading."""
        timestamp = event.timestamp
        level = event.level.value.upper()
        event_type = event.event_type.value
        message = event.message
        
        base = f"[{timestamp}] {level} {event_type}: {message}"
        
        if event.resource:
            base += f" (resource: {event.resource})"
        
        if event.details:
            details_str = ", ".join(f"{k}={v}" for k, v in event.details.items())
            base += f" [{details_str}]"
        
        return base
    
    @staticmethod
    def format_syslog(event: AuditEvent) -> str:
        """Format event for syslog."""
        # RFC 3164 syslog format
        timestamp = event.timestamp
        hostname = "secrets-app"
        tag = "secrets-audit"
        
        return f"{timestamp} {hostname} {tag}: {event.to_json()}"


class AuditLogHandler:
    """Base class for audit log handlers."""
    
    def __init__(self, formatter: Optional[AuditLogFormatter] = None):
        """Initialize handler."""
        self.formatter = formatter or AuditLogFormatter()
    
    def emit(self, event: AuditEvent):
        """Emit an audit event."""
        raise NotImplementedError
    
    def close(self):
        """Close the handler."""
        pass


class FileAuditLogHandler(AuditLogHandler):
    """Audit log handler that writes to files."""
    
    def __init__(self, log_dir: Union[str, Path], 
                 formatter: Optional[AuditLogFormatter] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        Initialize file handler.
        
        Args:
            log_dir: Directory to store log files
            formatter: Log formatter
            max_file_size: Maximum size of each log file
            backup_count: Number of backup files to keep
        """
        super().__init__(formatter)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self._current_file = None
        self._lock = threading.Lock()
    
    def _get_current_log_file(self) -> Path:
        """Get current log file path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit-{date_str}.log"
    
    def _rotate_if_needed(self, log_file: Path):
        """Rotate log file if it's too large."""
        if log_file.exists() and log_file.stat().st_size > self.max_file_size:
            # Rotate files
            for i in range(self.backup_count - 1, 0, -1):
                old_file = log_file.with_suffix(f".log.{i}")
                new_file = log_file.with_suffix(f".log.{i + 1}")
                if old_file.exists():
                    if new_file.exists():
                        new_file.unlink()
                    old_file.rename(new_file)
            
            # Move current file to .1
            backup_file = log_file.with_suffix(".log.1")
            if backup_file.exists():
                backup_file.unlink()
            log_file.rename(backup_file)
    
    def emit(self, event: AuditEvent):
        """Write event to log file."""
        with self._lock:
            try:
                log_file = self._get_current_log_file()
                self._rotate_if_needed(log_file)
                
                formatted_event = self.formatter.format_json(event)
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(formatted_event + '\n')
                
                # Set secure permissions
                os.chmod(log_file, 0o600)
                
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")


class SyslogAuditLogHandler(AuditLogHandler):
    """Audit log handler that writes to syslog."""
    
    def __init__(self, facility: str = "local0"):
        """Initialize syslog handler."""
        super().__init__()
        self.facility = facility
        try:
            import syslog
            self.syslog = syslog
            syslog.openlog("secrets-audit", syslog.LOG_PID, getattr(syslog, f"LOG_{facility.upper()}"))
        except ImportError:
            logger.warning("Syslog not available")
            self.syslog = None
    
    def emit(self, event: AuditEvent):
        """Write event to syslog."""
        if not self.syslog:
            return
        
        try:
            formatted_event = self.formatter.format_syslog(event)
            
            # Map audit levels to syslog priorities
            priority_map = {
                AuditLevel.LOW: self.syslog.LOG_INFO,
                AuditLevel.MEDIUM: self.syslog.LOG_WARNING,
                AuditLevel.HIGH: self.syslog.LOG_ERR,
                AuditLevel.CRITICAL: self.syslog.LOG_CRIT
            }
            
            priority = priority_map.get(event.level, self.syslog.LOG_INFO)
            self.syslog.syslog(priority, formatted_event)
            
        except Exception as e:
            logger.error(f"Failed to write to syslog: {e}")


class ConsoleAuditLogHandler(AuditLogHandler):
    """Audit log handler that writes to console."""
    
    def __init__(self, min_level: AuditLevel = AuditLevel.MEDIUM):
        """Initialize console handler."""
        super().__init__()
        self.min_level = min_level
    
    def emit(self, event: AuditEvent):
        """Write event to console."""
        # Check if event meets minimum level
        level_order = {
            AuditLevel.LOW: 0,
            AuditLevel.MEDIUM: 1,
            AuditLevel.HIGH: 2,
            AuditLevel.CRITICAL: 3
        }
        
        if level_order[event.level] < level_order[self.min_level]:
            return
        
        try:
            formatted_event = self.formatter.format_human_readable(event)
            print(formatted_event, file=sys.stderr)
        except Exception as e:
            logger.error(f"Failed to write to console: {e}")


class AuditLogger:
    """Main audit logging system."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.handlers: List[AuditLogHandler] = []
        self._event_queue = queue.Queue()
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._session_id = self._generate_session_id()
        self._start_worker()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = str(int(time.time()))
        pid = str(os.getpid())
        random_data = os.urandom(8).hex()
        session_data = f"{timestamp}-{pid}-{random_data}"
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]
    
    def _start_worker(self):
        """Start background worker thread."""
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def _worker_loop(self):
        """Background worker loop to process events."""
        while not self._stop_event.is_set():
            try:
                # Wait for events with timeout
                event = self._event_queue.get(timeout=1.0)
                
                # Emit event to all handlers
                for handler in self.handlers:
                    try:
                        handler.emit(event)
                    except Exception as e:
                        logger.error(f"Handler failed to emit event: {e}")
                
                self._event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audit worker error: {e}")
    
    def add_handler(self, handler: AuditLogHandler):
        """Add an audit log handler."""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: AuditLogHandler):
        """Remove an audit log handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
            handler.close()
    
    def log_event(self, event_type: AuditEventType, message: str,
                  level: AuditLevel = AuditLevel.MEDIUM,
                  resource: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  user_id: Optional[str] = None):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            message: Event message
            level: Event severity level
            resource: Resource being accessed
            details: Additional event details
            user_id: User ID (if applicable)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        event = AuditEvent(
            event_type=event_type,
            timestamp=timestamp,
            level=level,
            message=message,
            resource=resource,
            details=details or {},
            user_id=user_id,
            session_id=self._session_id
        )
        
        # Queue event for processing
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            logger.error("Audit event queue is full, dropping event")
    
    def log_authentication(self, success: bool, user_id: Optional[str] = None,
                          method: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log authentication event."""
        event_type = AuditEventType.AUTH_SUCCESS if success else AuditEventType.AUTH_FAILURE
        level = AuditLevel.MEDIUM if success else AuditLevel.HIGH
        message = f"Authentication {'succeeded' if success else 'failed'}"
        
        if method:
            message += f" using {method}"
        
        event_details = details or {}
        if method:
            event_details['method'] = method
        
        self.log_event(event_type, message, level, user_id=user_id, details=event_details)
    
    def log_password_access(self, password_path: str, operation: str,
                           user_id: Optional[str] = None, 
                           details: Optional[Dict[str, Any]] = None):
        """Log password access event."""
        event_map = {
            'accessed': AuditEventType.PASSWORD_ACCESSED,
            'created': AuditEventType.PASSWORD_CREATED,
            'modified': AuditEventType.PASSWORD_MODIFIED,
            'deleted': AuditEventType.PASSWORD_DELETED,
            'copied': AuditEventType.PASSWORD_COPIED
        }
        
        event_type = event_map.get(operation, AuditEventType.PASSWORD_ACCESSED)
        level = AuditLevel.MEDIUM if operation == 'accessed' else AuditLevel.HIGH
        message = f"Password {operation}: {password_path}"
        
        self.log_event(event_type, message, level, resource=password_path,
                      user_id=user_id, details=details)
    
    def log_security_event(self, event_type: AuditEventType, message: str,
                          level: AuditLevel = AuditLevel.HIGH,
                          details: Optional[Dict[str, Any]] = None):
        """Log security-related event."""
        self.log_event(event_type, message, level, details=details)
    
    def audit_compliance_event(self, framework: str, event_type: str,
                              requirement_id: Optional[str] = None,
                              violation_id: Optional[str] = None,
                              severity: Optional[str] = None,
                              details: Optional[Dict[str, Any]] = None):
        """Log compliance-related event."""
        # Map event types to audit event types
        event_map = {
            'assessment_completed': AuditEventType.COMPLIANCE_ASSESSMENT,
            'violation_detected': AuditEventType.COMPLIANCE_VIOLATION,
            'violation_resolved': AuditEventType.COMPLIANCE_VIOLATION,
            'requirement_implemented': AuditEventType.COMPLIANCE_REQUIREMENT,
        }
        
        audit_event_type = event_map.get(event_type, AuditEventType.COMPLIANCE_EVENT)
        
        # Determine audit level based on event type and severity
        if event_type == 'violation_detected':
            level = AuditLevel.CRITICAL if severity == 'critical' else AuditLevel.HIGH
        elif event_type == 'assessment_completed':
            level = AuditLevel.MEDIUM
        else:
            level = AuditLevel.LOW
        
        # Build message
        message = f"Compliance event ({framework}): {event_type}"
        if requirement_id:
            message += f" - Requirement: {requirement_id}"
        if violation_id:
            message += f" - Violation: {violation_id}"
        
        # Combine details
        event_details = {
            'framework': framework,
            'compliance_event_type': event_type,
        }
        if requirement_id:
            event_details['requirement_id'] = requirement_id
        if violation_id:
            event_details['violation_id'] = violation_id
        if severity:
            event_details['severity'] = severity
        if details:
            event_details.update(details)
        
        self.log_event(audit_event_type, message, level, details=event_details)
    
    def log_application_event(self, event_type: AuditEventType, message: str,
                             details: Optional[Dict[str, Any]] = None):
        """Log application lifecycle event."""
        level = AuditLevel.CRITICAL if event_type == AuditEventType.APP_CRASHED else AuditLevel.LOW
        self.log_event(event_type, message, level, details=details)
    
    def get_recent_events(self, count: int = 100, 
                         event_types: Optional[List[AuditEventType]] = None,
                         min_level: Optional[AuditLevel] = None) -> List[Dict[str, Any]]:
        """
        Get recent audit events from file logs.
        
        Args:
            count: Maximum number of events to return
            event_types: Filter by event types
            min_level: Minimum severity level
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        # Find file handlers
        file_handlers = [h for h in self.handlers if isinstance(h, FileAuditLogHandler)]
        
        for handler in file_handlers:
            try:
                log_file = handler._get_current_log_file()
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                event_data = json.loads(line.strip())
                                
                                # Apply filters
                                if event_types:
                                    if event_data.get('event_type') not in [et.value for et in event_types]:
                                        continue
                                
                                if min_level:
                                    level_order = {
                                        'low': 0, 'medium': 1, 'high': 2, 'critical': 3
                                    }
                                    event_level = level_order.get(event_data.get('level', 'low'), 0)
                                    min_level_order = level_order[min_level.value]
                                    if event_level < min_level_order:
                                        continue
                                
                                events.append(event_data)
                                
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Failed to read audit log: {e}")
        
        # Sort by timestamp and return most recent
        events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return events[:count]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            'session_id': self._session_id,
            'handlers_count': len(self.handlers),
            'queue_size': self._event_queue.qsize(),
            'worker_running': self._worker_thread.is_alive() if self._worker_thread else False
        }
    
    def close(self):
        """Close audit logger and all handlers."""
        # Stop worker thread
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        
        # Close all handlers
        for handler in self.handlers:
            handler.close()
        
        self.handlers.clear()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def configure_audit_logging(log_dir: Optional[str] = None,
                           enable_console: bool = True,
                           enable_syslog: bool = False,
                           console_min_level: AuditLevel = AuditLevel.MEDIUM):
    """
    Configure audit logging with default handlers.
    
    Args:
        log_dir: Directory for log files (None to disable file logging)
        enable_console: Whether to enable console logging
        enable_syslog: Whether to enable syslog logging
        console_min_level: Minimum level for console output
    """
    audit_logger = get_audit_logger()
    
    # Add file handler
    if log_dir:
        file_handler = FileAuditLogHandler(log_dir)
        audit_logger.add_handler(file_handler)
    
    # Add console handler
    if enable_console:
        console_handler = ConsoleAuditLogHandler(console_min_level)
        audit_logger.add_handler(console_handler)
    
    # Add syslog handler
    if enable_syslog:
        syslog_handler = SyslogAuditLogHandler()
        audit_logger.add_handler(syslog_handler)


# Convenience functions for common events
def audit_auth_success(user_id: Optional[str] = None, method: Optional[str] = None):
    """Log successful authentication."""
    get_audit_logger().log_authentication(True, user_id, method)


def audit_auth_failure(user_id: Optional[str] = None, method: Optional[str] = None):
    """Log failed authentication."""
    get_audit_logger().log_authentication(False, user_id, method)


def audit_password_access(path: str, operation: str, user_id: Optional[str] = None):
    """Log password access."""
    get_audit_logger().log_password_access(path, operation, user_id)


def audit_security_event(message: str, level: AuditLevel = AuditLevel.HIGH):
    """Log security event."""
    get_audit_logger().log_security_event(AuditEventType.SECURITY_VIOLATION, message, level)


def audit_app_start():
    """Log application start."""
    get_audit_logger().log_application_event(AuditEventType.APP_STARTED, "Application started")


def audit_app_stop():
    """Log application stop."""
    get_audit_logger().log_application_event(AuditEventType.APP_STOPPED, "Application stopped")


def audit_compliance_event(framework: str, event_type: str, **kwargs):
    """Log compliance event."""
    get_audit_logger().audit_compliance_event(framework, event_type, **kwargs)