"""Unit tests for audit logging functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.secrets.security.audit_logger import (
    AuditLogger, AuditEvent, AuditEventType, AuditLevel,
    FileAuditLogHandler, ConsoleAuditLogHandler,
    get_audit_logger, configure_audit_logging
)


class TestAuditEvent:
    """Test cases for AuditEvent."""
    
    def test_audit_event_creation(self):
        """Test audit event creation."""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_SUCCESS,
            timestamp="2023-01-01T00:00:00Z",
            level=AuditLevel.MEDIUM,
            message="User logged in",
            user_id="test_user"
        )
        
        assert event.event_type == AuditEventType.AUTH_SUCCESS
        assert event.level == AuditLevel.MEDIUM
        assert event.message == "User logged in"
        assert event.user_id == "test_user"
        assert event.process_id is not None
        assert event.thread_id is not None
    
    def test_audit_event_to_dict(self):
        """Test converting event to dictionary."""
        event = AuditEvent(
            event_type=AuditEventType.PASSWORD_ACCESSED,
            timestamp="2023-01-01T00:00:00Z",
            level=AuditLevel.HIGH,
            message="Password accessed",
            resource="test/password"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'password_accessed'
        assert event_dict['level'] == 'high'
        assert event_dict['message'] == "Password accessed"
        assert event_dict['resource'] == "test/password"
    
    def test_audit_event_to_json(self):
        """Test converting event to JSON."""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_FAILURE,
            timestamp="2023-01-01T00:00:00Z",
            level=AuditLevel.HIGH,
            message="Authentication failed"
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['event_type'] == 'auth_failure'
        assert parsed['level'] == 'high'
        assert parsed['message'] == "Authentication failed"


class TestFileAuditLogHandler:
    """Test cases for FileAuditLogHandler."""
    
    def test_file_handler_basic(self):
        """Test basic file handler operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileAuditLogHandler(temp_dir)
            
            event = AuditEvent(
                event_type=AuditEventType.APP_STARTED,
                timestamp="2023-01-01T00:00:00Z",
                level=AuditLevel.LOW,
                message="Application started"
            )
            
            handler.emit(event)
            
            # Check that log file was created
            log_files = list(Path(temp_dir).glob("audit-*.log"))
            assert len(log_files) == 1
            
            # Check log content
            with open(log_files[0], 'r') as f:
                content = f.read()
                assert 'app_started' in content
                assert 'Application started' in content
    
    def test_file_handler_rotation(self):
        """Test file rotation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create handler with small max file size
            handler = FileAuditLogHandler(temp_dir, max_file_size=100)
            
            # Emit many events to trigger rotation
            for i in range(20):
                event = AuditEvent(
                    event_type=AuditEventType.PASSWORD_ACCESSED,
                    timestamp="2023-01-01T00:00:00Z",
                    level=AuditLevel.MEDIUM,
                    message=f"Password accessed {i}"
                )
                handler.emit(event)
            
            # Check that backup files were created
            log_files = list(Path(temp_dir).glob("audit-*.log*"))
            assert len(log_files) > 1  # Should have main file + backups


class TestConsoleAuditLogHandler:
    """Test cases for ConsoleAuditLogHandler."""
    
    def test_console_handler_basic(self):
        """Test basic console handler."""
        handler = ConsoleAuditLogHandler(min_level=AuditLevel.LOW)
        
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            timestamp="2023-01-01T00:00:00Z",
            level=AuditLevel.CRITICAL,
            message="Security violation detected"
        )
        
        # Should not raise exceptions
        handler.emit(event)
    
    def test_console_handler_filtering(self):
        """Test console handler level filtering."""
        with patch('builtins.print') as mock_print:
            handler = ConsoleAuditLogHandler(min_level=AuditLevel.HIGH)
            
            # Low level event should be filtered
            low_event = AuditEvent(
                event_type=AuditEventType.APP_STARTED,
                timestamp="2023-01-01T00:00:00Z",
                level=AuditLevel.LOW,
                message="App started"
            )
            handler.emit(low_event)
            mock_print.assert_not_called()
            
            # High level event should be emitted
            high_event = AuditEvent(
                event_type=AuditEventType.SECURITY_VIOLATION,
                timestamp="2023-01-01T00:00:00Z",
                level=AuditLevel.CRITICAL,
                message="Security violation"
            )
            handler.emit(high_event)
            mock_print.assert_called()


class TestAuditLogger:
    """Test cases for AuditLogger."""
    
    def test_audit_logger_basic(self):
        """Test basic audit logger operations."""
        logger = AuditLogger()
        
        # Add a handler
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileAuditLogHandler(temp_dir)
            logger.add_handler(handler)
            
            # Log an event
            logger.log_event(
                AuditEventType.AUTH_SUCCESS,
                "User authenticated",
                AuditLevel.MEDIUM,
                user_id="test_user"
            )
            
            # Give worker thread time to process
            import time
            time.sleep(0.1)
            
            # Check that event was logged
            log_files = list(Path(temp_dir).glob("audit-*.log"))
            assert len(log_files) == 1
            
            with open(log_files[0], 'r') as f:
                content = f.read()
                assert 'auth_success' in content
                assert 'User authenticated' in content
        
        logger.close()
    
    def test_audit_logger_convenience_methods(self):
        """Test convenience logging methods."""
        logger = AuditLogger()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileAuditLogHandler(temp_dir)
            logger.add_handler(handler)
            
            # Test authentication logging
            logger.log_authentication(True, "user123", "password")
            logger.log_authentication(False, "user456", "totp")
            
            # Test password access logging
            logger.log_password_access("test/password", "accessed", "user123")
            
            # Test security event logging
            logger.log_security_event(
                AuditEventType.SUSPICIOUS_ACTIVITY,
                "Suspicious activity detected"
            )
            
            # Give worker thread time to process
            import time
            time.sleep(0.1)
            
            # Check that events were logged
            log_files = list(Path(temp_dir).glob("audit-*.log"))
            assert len(log_files) == 1
            
            with open(log_files[0], 'r') as f:
                content = f.read()
                assert 'auth_success' in content
                assert 'auth_failure' in content
                assert 'password_accessed' in content
                assert 'suspicious_activity' in content
        
        logger.close()
    
    def test_get_recent_events(self):
        """Test getting recent events."""
        logger = AuditLogger()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileAuditLogHandler(temp_dir)
            logger.add_handler(handler)
            
            # Log some events
            logger.log_event(AuditEventType.APP_STARTED, "App started")
            logger.log_event(AuditEventType.AUTH_SUCCESS, "Auth success")
            logger.log_event(AuditEventType.PASSWORD_ACCESSED, "Password accessed")
            
            # Give worker thread time to process
            import time
            time.sleep(0.1)
            
            # Get recent events
            events = logger.get_recent_events(count=10)
            
            # Should have at least the events we logged
            assert len(events) >= 3
            
            # Check event types
            event_types = [event.get('event_type') for event in events]
            assert 'app_started' in event_types
            assert 'auth_success' in event_types
            assert 'password_accessed' in event_types
        
        logger.close()
    
    def test_audit_logger_stats(self):
        """Test audit logger statistics."""
        logger = AuditLogger()
        
        stats = logger.get_stats()
        
        assert 'session_id' in stats
        assert 'handlers_count' in stats
        assert 'queue_size' in stats
        assert 'worker_running' in stats
        
        logger.close()


class TestAuditLoggerConfiguration:
    """Test audit logger configuration functions."""
    
    def test_configure_audit_logging(self):
        """Test audit logging configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            configure_audit_logging(
                log_dir=temp_dir,
                enable_console=True,
                enable_syslog=False
            )
            
            logger = get_audit_logger()
            
            # Should have file and console handlers
            assert len(logger.handlers) >= 1
            
            logger.close()
    
    def test_global_audit_logger(self):
        """Test global audit logger instance."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        # Should be the same instance
        assert logger1 is logger2
        
        logger1.close()