"""
Configuration management for the Secrets application.
"""
import gi
gi.require_version("Adw", "1")

import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from gi.repository import GLib, Adw

from .i18n import get_translation_function

# Get translation function
_ = get_translation_function()

# Logger for configuration management
logger = logging.getLogger(__name__)


@dataclass
class UIConfig:
    """UI-related configuration."""
    window_width: int = 800
    window_height: int = 600
    window_maximized: bool = False
    paned_position: int = 250
    auto_hide_password_timeout: int = 30
    show_icons: bool = True
    theme: str = "auto"  # "light", "dark", "auto"
    remember_window_state: bool = True


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    auto_hide_passwords: bool = True
    auto_hide_timeout_seconds: int = 30
    clear_clipboard_timeout: int = 45
    require_confirmation_for_delete: bool = True
    require_password_name_for_delete: bool = True
    lock_on_idle: bool = False
    idle_timeout_minutes: int = 15
    lock_on_screen_lock: bool = True
    master_password_timeout_minutes: int = 60
    require_master_password_for_export: bool = True
    clear_memory_on_lock: bool = True
    max_failed_unlock_attempts: int = 3
    lockout_duration_minutes: int = 5


@dataclass
class ComplianceConfig:
    """Compliance-related configuration."""
    # Framework enablement
    hipaa_enabled: bool = False
    pci_dss_enabled: bool = False
    gdpr_enabled: bool = False
    rbac_enabled: bool = False
    
    # Audit settings
    audit_enabled: bool = True
    audit_retention_days: int = 2190  # 6 years for HIPAA
    log_all_access: bool = True
    real_time_monitoring: bool = True
    
    # HIPAA specific (simplified for personal use)
    # Personal health info tracking reminder intervals
    health_data_review_days: int = 90
    backup_verification_days: int = 30
    
    # PCI DSS specific
    password_complexity_enabled: bool = True
    password_min_length: int = 12
    password_history_count: int = 4
    password_expiry_days: int = 90
    account_lockout_enabled: bool = True
    lockout_attempts: int = 6
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 15
    
    # GDPR specific (simplified for personal use)
    data_retention_enabled: bool = True
    data_export_enabled: bool = True
    
    # Encryption and key management (kept for personal security)
    encryption_algorithm: str = "AES-256"
    key_rotation_enabled: bool = True
    key_rotation_days: int = 365


@dataclass
class SearchConfig:
    """Search-related configuration."""
    case_sensitive: bool = False
    search_in_content: bool = True
    search_in_filenames: bool = True
    max_search_results: int = 100


@dataclass
class GitConfig:
    """Git-related configuration."""
    auto_pull_on_startup: bool = False
    auto_push_on_changes: bool = False
    show_git_status: bool = True
    git_timeout_seconds: int = 30

    # Repository configuration
    remote_url: str = ""
    remote_name: str = "origin"
    default_branch: str = "main"

    # Platform integration
    platform_type: str = ""  # "github", "gitlab", "gitea", "custom"
    platform_username: str = ""
    platform_token: str = ""  # For API access (stored securely)

    # Advanced settings
    auto_commit_on_changes: bool = False
    commit_message_template: str = "Update passwords from Secrets app"
    show_git_notifications: bool = True
    check_remote_on_startup: bool = True


@dataclass
class LoggingConfig:
    """Logging-related configuration with advanced rotation and management."""
    # Basic logging settings
    log_level: str = "WARNING"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    enable_structured_logging: bool = True
    enable_security_logging: bool = True
    
    # File rotation settings
    max_log_file_size_mb: int = 10
    backup_count: int = 5
    rotation_strategy: str = "size"  # "size", "time", "mixed"
    
    # Time-based rotation settings
    rotation_interval: str = "midnight"  # "midnight", "H", "D", "W0", "W1", etc.
    rotation_interval_count: int = 1  # How many intervals between rotations
    rotation_at_time: str = "00:00"  # Time to rotate for daily rotation (HH:MM)
    
    # Retention and cleanup settings
    log_retention_days: int = 30
    max_total_log_size_mb: int = 100
    enable_compression: bool = True
    compression_format: str = "gzip"  # "gzip", "bz2", "lzma"
    
    # Log file location settings
    custom_log_directory: str = ""  # Custom log directory (empty = use default)
    use_custom_log_directory: bool = False  # Enable custom log directory
    log_directory_permissions: str = "755"  # Directory permissions for custom log dir
    
    # Advanced management settings
    enable_automatic_cleanup: bool = True
    cleanup_check_interval_hours: int = 24
    enable_log_archiving: bool = False
    archive_directory: str = ""  # Custom archive location
    
    # Performance settings
    log_flush_interval_seconds: int = 5
    enable_async_logging: bool = False
    max_queue_size: int = 1000
    
    # Monitoring settings
    enable_log_monitoring: bool = True
    monitor_disk_usage: bool = True
    disk_usage_warning_threshold_percent: int = 85
    disk_usage_critical_threshold_percent: int = 95


@dataclass
class AppConfig:
    """Main application configuration."""
    ui: UIConfig
    security: SecurityConfig
    search: SearchConfig
    git: GitConfig
    compliance: ComplianceConfig
    logging: LoggingConfig
    last_selected_path: Optional[str] = None
    
    def __post_init__(self):
        """Ensure all nested configs are proper dataclass instances."""
        if isinstance(self.ui, dict):
            self.ui = UIConfig(**self.ui)
        if isinstance(self.security, dict):
            self.security = SecurityConfig(**self.security)
        if isinstance(self.search, dict):
            self.search = SearchConfig(**self.search)
        if isinstance(self.git, dict):
            self.git = GitConfig(**self.git)
        if isinstance(self.compliance, dict):
            self.compliance = ComplianceConfig(**self.compliance)
        if isinstance(self.logging, dict):
            self.logging = LoggingConfig(**self.logging)


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, app_id: str = "io.github.tobagin.secrets"):
        self.app_id = app_id
        self.config_dir = Path(GLib.get_user_config_dir()) / app_id
        self.config_file = self.config_dir / "config.json"
        self._config: Optional[AppConfig] = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                # Remove deprecated fields for Flatpak compatibility
                data.pop('password_store_dir', None)
                self._config = AppConfig(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Error loading config: {e}. Using defaults.", extra={
                    'config_file': str(self.config_file),
                    'error_type': type(e).__name__
                })
                self._config = self._create_default_config()
        else:
            self._config = self._create_default_config()
        
        return self._config
    
    def save_config(self, config: Optional[AppConfig] = None):
        """Save configuration to file."""
        if config is None:
            config = self._config
        
        if config is None:
            return
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}", extra={
                'config_file': str(self.config_file),
                'error_type': type(e).__name__
            })
    
    def _create_default_config(self) -> AppConfig:
        """Create default configuration."""
        return AppConfig(
            ui=UIConfig(),
            security=SecurityConfig(),
            search=SearchConfig(),
            git=GitConfig(),
            compliance=ComplianceConfig(),
            logging=LoggingConfig()
        )
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.ui, key):
                setattr(config.ui, key, value)
        self.save_config(config)
    
    def update_security_config(self, **kwargs):
        """Update security configuration."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.security, key):
                setattr(config.security, key, value)
        self.save_config(config)
    
    def update_compliance_config(self, **kwargs):
        """Update compliance configuration."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.compliance, key):
                setattr(config.compliance, key, value)
        self.save_config(config)
    
    def update_search_config(self, **kwargs):
        """Update search configuration."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.search, key):
                setattr(config.search, key, value)
        self.save_config(config)
    
    def update_git_config(self, **kwargs):
        """Update git configuration."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.git, key):
                setattr(config.git, key, value)
        self.save_config(config)
    
    def update_logging_config(self, **kwargs):
        """Update logging configuration and apply changes to logging system."""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.logging, key):
                setattr(config.logging, key, value)
        self.save_config(config)
        
        # Apply changes to logging system if it exists
        self._apply_logging_changes(config.logging)
    
    def _apply_logging_changes(self, logging_config):
        """Apply logging configuration changes to the active logging system."""
        try:
            from .logging_system import get_logging_system, set_log_level
            
            # Update log level
            if hasattr(logging_config, 'log_level'):
                set_log_level(logging_config.log_level)
            
            # Update logging system configuration if available
            logging_system = get_logging_system()
            if logging_system and hasattr(logging_system, 'update_configuration'):
                logging_system.update_configuration(logging_config)
                
        except ImportError:
            # Logging system not available, changes will be applied on next restart
            pass
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self._config = self._create_default_config()
        self.save_config()


class Constants:
    """Application constants."""
    
    # File extensions
    PASSWORD_FILE_EXTENSION = ".gpg"
    
    # Default paths
    DEFAULT_STORE_DIR = "~/.password-store"
    
    # UI Constants
    MIN_WINDOW_WIDTH = 400
    MIN_WINDOW_HEIGHT = 300
    DEFAULT_WINDOW_WIDTH = 800
    DEFAULT_WINDOW_HEIGHT = 600
    
    # Timeouts (in seconds)
    DEFAULT_AUTO_HIDE_TIMEOUT = 30
    DEFAULT_CLIPBOARD_TIMEOUT = 45
    DEFAULT_GIT_TIMEOUT = 30
    DEFAULT_IDLE_TIMEOUT_MINUTES = 15
    DEFAULT_MASTER_PASSWORD_TIMEOUT_MINUTES = 60
    DEFAULT_LOCKOUT_DURATION_MINUTES = 5
    MAX_FAILED_UNLOCK_ATTEMPTS = 3
    
    # Search limits
    MAX_SEARCH_RESULTS = 1000
    
    # Icons
    FOLDER_ICON = "folder-symbolic"
    PASSWORD_ICON = "dialog-password-symbolic"
    VISIBLE_ICON = "eye-open-negative-filled-symbolic"
    HIDDEN_ICON = "eye-not-looking-symbolic"
    
    # CSS Classes
    CSS_FOLDER_ITEM = "folder-item"
    CSS_PASSWORD_ITEM = "password-item"
    CSS_PASSWORD_VISIBLE = "password-visible"
    
    # Error Messages
    ERROR_PASS_NOT_FOUND = _("The 'pass' command was not found. Is it installed and in your PATH?")
    ERROR_STORE_NOT_INITIALIZED = _("Password store is not initialized")
    ERROR_INVALID_PATH = _("Invalid password path")
    ERROR_EMPTY_PATH = _("Password path cannot be empty")
    ERROR_EMPTY_CONTENT = _("Password content cannot be empty")

    # Success Messages
    SUCCESS_PASSWORD_COPIED = _("Password copied to clipboard")
    SUCCESS_USERNAME_COPIED = _("Username copied to clipboard")
    SUCCESS_ENTRY_DELETED = _("Password entry deleted successfully")
    SUCCESS_ENTRY_SAVED = _("Password entry saved successfully")
    SUCCESS_ENTRY_MOVED = _("Password entry moved successfully")
    
    # Validation Patterns
    VALID_PATH_PATTERN = r"^[^/].*[^/]$"  # No leading/trailing slashes
    GPG_ID_MIN_LENGTH = 8


class ThemeManager:
    """Manages application theming."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def apply_theme(self, theme: str = None):
        """Apply the specified theme or current config theme."""
        if theme is None:
            theme = self.config_manager.get_config().ui.theme

        # Apply Libadwaita color scheme
        style_manager = Adw.StyleManager.get_default()

        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:  # "auto"
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
    
    def get_available_themes(self) -> list:
        """Get list of available themes."""
        return ["light", "dark", "auto"]
    
    def set_theme(self, theme: str):
        """Set and apply theme."""
        if theme in self.get_available_themes():
            self.config_manager.update_ui_config(theme=theme)
            self.apply_theme(theme)
