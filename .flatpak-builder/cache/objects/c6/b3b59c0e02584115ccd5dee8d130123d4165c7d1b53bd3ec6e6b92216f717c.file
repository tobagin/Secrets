"""
Centralized error handling and logging system.
"""
import logging
import traceback
from typing import Optional, Dict, Any, Callable
from enum import Enum
from pathlib import Path
from gi.repository import GLib
from .config import ConfigManager


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    PASSWORD_STORE = "password_store"
    UI = "ui"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class SecretsError(Exception):
    """Base exception for Secrets application."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}


class PasswordStoreError(SecretsError):
    """Password store related errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.PASSWORD_STORE, severity, details)


class ValidationError(SecretsError):
    """Validation related errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.WARNING, details)


class UIError(SecretsError):
    """UI related errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.UI, severity, details)


class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self, config_manager: ConfigManager, app_id: str = "io.github.tobagin.secrets"):
        self.config_manager = config_manager
        self.app_id = app_id
        self.logger = self._setup_logger()
        self.error_callbacks: Dict[ErrorCategory, list] = {}
        self.global_error_callback: Optional[Callable] = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup application logger."""
        logger = logging.getLogger(self.app_id)
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory
        log_dir = Path(GLib.get_user_data_dir()) / self.app_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "secrets.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def handle_error(self, error: Exception, context: str = None) -> bool:
        """Handle an error with appropriate logging and user feedback."""
        if isinstance(error, SecretsError):
            return self._handle_secrets_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_secrets_error(self, error: SecretsError, context: str = None) -> bool:
        """Handle SecretsError instances."""
        log_message = f"[{error.category.value}] {error.message}"
        if context:
            log_message = f"{context}: {log_message}"
        
        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra={'details': error.details})
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message, extra={'details': error.details})
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message, extra={'details': error.details})
        else:
            self.logger.info(log_message, extra={'details': error.details})
        
        # Call category-specific callbacks
        if error.category in self.error_callbacks:
            for callback in self.error_callbacks[error.category]:
                try:
                    callback(error, context)
                except Exception as e:
                    self.logger.error(f"Error in error callback: {e}")
        
        # Call global callback
        if self.global_error_callback:
            try:
                self.global_error_callback(error, context)
            except Exception as e:
                self.logger.error(f"Error in global error callback: {e}")
        
        return True
    
    def _handle_generic_error(self, error: Exception, context: str = None) -> bool:
        """Handle generic Python exceptions."""
        error_msg = str(error)
        log_message = f"Unhandled exception: {error_msg}"
        if context:
            log_message = f"{context}: {log_message}"
        
        self.logger.error(log_message, exc_info=True)
        
        # Convert to SecretsError and handle
        secrets_error = SecretsError(
            message=error_msg,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            details={'traceback': traceback.format_exc()}
        )
        
        return self._handle_secrets_error(secrets_error, context)
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register a callback for specific error categories."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def set_global_error_callback(self, callback: Callable):
        """Set a global error callback that handles all errors."""
        self.global_error_callback = callback
    
    def log_info(self, message: str, context: str = None):
        """Log an info message."""
        log_message = f"{context}: {message}" if context else message
        self.logger.info(log_message)
    
    def log_warning(self, message: str, context: str = None):
        """Log a warning message."""
        log_message = f"{context}: {message}" if context else message
        self.logger.warning(log_message)
    
    def log_error(self, message: str, context: str = None):
        """Log an error message."""
        log_message = f"{context}: {message}" if context else message
        self.logger.error(log_message)


class ErrorReporter:
    """Handles error reporting and user feedback."""
    
    def __init__(self, error_handler: ErrorHandler, toast_manager=None):
        self.error_handler = error_handler
        self.toast_manager = toast_manager
        
        # Register as global error callback
        error_handler.set_global_error_callback(self._on_error)
    
    def _on_error(self, error: SecretsError, context: str = None):
        """Handle errors for user feedback."""
        if not self.toast_manager:
            return
        
        # Determine user message based on error
        user_message = self._get_user_friendly_message(error)
        
        # Show appropriate toast based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.toast_manager.show_error(f"Critical: {user_message}")
        elif error.severity == ErrorSeverity.ERROR:
            self.toast_manager.show_error(user_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.toast_manager.show_warning(user_message)
        else:
            self.toast_manager.show_info(user_message)
    
    def _get_user_friendly_message(self, error: SecretsError) -> str:
        """Convert technical error to user-friendly message."""
        category_messages = {
            ErrorCategory.PASSWORD_STORE: "Password store operation failed",
            ErrorCategory.UI: "Interface error occurred",
            ErrorCategory.NETWORK: "Network operation failed",
            ErrorCategory.FILE_SYSTEM: "File operation failed",
            ErrorCategory.VALIDATION: "Invalid input provided",
            ErrorCategory.CONFIGURATION: "Configuration error",
            ErrorCategory.UNKNOWN: "An unexpected error occurred"
        }
        
        base_message = category_messages.get(error.category, "An error occurred")
        
        # For validation errors, be more specific
        if error.category == ErrorCategory.VALIDATION:
            return error.message
        
        # For other errors, provide context if available
        if error.message and len(error.message) < 100:  # Keep it concise
            return error.message
        
        return base_message


def handle_exceptions(error_handler: ErrorHandler, context: str = None):
    """Decorator for handling exceptions in methods."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(e, context or func.__name__)
                return None
        return wrapper
    return decorator


# Global error handler instance (to be initialized by main application)
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> Optional[ErrorHandler]:
    """Get the global error handler instance."""
    return _global_error_handler


def set_error_handler(error_handler: ErrorHandler):
    """Set the global error handler instance."""
    global _global_error_handler
    _global_error_handler = error_handler
