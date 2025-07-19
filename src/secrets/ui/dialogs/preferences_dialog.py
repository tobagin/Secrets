import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
import logging
from ...config import ConfigManager, ThemeManager
from ...utils import DialogManager, UIConstants, AccessibilityHelper


@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/dialogs/preferences_dialog.ui')
class PreferencesDialog(Adw.PreferencesDialog):
    """Preferences dialog for the Secrets application."""
    
    __gtype_name__ = "PreferencesDialog"
    
    # Template pages
    general_page = Gtk.Template.Child()
    security_page = Gtk.Template.Child()
    search_page = Gtk.Template.Child()
    git_page = Gtk.Template.Child()
    logging_page = Gtk.Template.Child()
    
    # General page widgets
    appearance_group = Gtk.Template.Child()
    theme_row = Gtk.Template.Child()
    window_group = Gtk.Template.Child()
    remember_window_row = Gtk.Template.Child()
    
    # Security page widgets
    password_group = Gtk.Template.Child()
    auto_hide_row = Gtk.Template.Child()
    auto_hide_timeout_row = Gtk.Template.Child()
    clipboard_group = Gtk.Template.Child()
    clipboard_timeout_row = Gtk.Template.Child()
    confirmation_group = Gtk.Template.Child()
    confirm_delete_row = Gtk.Template.Child()
    require_password_name_row = Gtk.Template.Child()
    session_group = Gtk.Template.Child()
    lock_on_idle_row = Gtk.Template.Child()
    idle_timeout_row = Gtk.Template.Child()
    lock_on_screen_lock_row = Gtk.Template.Child()
    master_password_timeout_row = Gtk.Template.Child()
    advanced_group = Gtk.Template.Child()
    clear_memory_row = Gtk.Template.Child()
    require_master_for_export_row = Gtk.Template.Child()
    max_failed_attempts_row = Gtk.Template.Child()
    lockout_duration_row = Gtk.Template.Child()
    password_policy_group = Gtk.Template.Child()
    password_complexity_row = Gtk.Template.Child()
    password_min_length_row = Gtk.Template.Child()
    password_history_row = Gtk.Template.Child()
    password_expiry_row = Gtk.Template.Child()
    audit_group = Gtk.Template.Child()
    audit_enabled_row = Gtk.Template.Child()
    log_all_access_row = Gtk.Template.Child()
    audit_retention_row = Gtk.Template.Child()
    
    # Search page widgets
    search_options_group = Gtk.Template.Child()
    case_sensitive_row = Gtk.Template.Child()
    search_content_row = Gtk.Template.Child()
    search_filenames_row = Gtk.Template.Child()
    max_results_row = Gtk.Template.Child()
    
    # Git page widgets
    git_automation_group = Gtk.Template.Child()
    auto_pull_row = Gtk.Template.Child()
    auto_push_row = Gtk.Template.Child()
    git_status_group = Gtk.Template.Child()
    show_git_status_row = Gtk.Template.Child()
    git_timeout_row = Gtk.Template.Child()
    git_repo_group = Gtk.Template.Child()
    repo_setup_row = Gtk.Template.Child()
    repo_setup_button = Gtk.Template.Child()
    repo_status_row = Gtk.Template.Child()
    repo_status_button = Gtk.Template.Child()
    git_advanced_group = Gtk.Template.Child()
    auto_commit_row = Gtk.Template.Child()
    git_notifications_row = Gtk.Template.Child()
    check_remote_row = Gtk.Template.Child()
    remote_name_row = Gtk.Template.Child()
    default_branch_row = Gtk.Template.Child()
    commit_template_row = Gtk.Template.Child()
    
    # Logging page widgets
    logging_config_group = Gtk.Template.Child()
    log_level_row = Gtk.Template.Child()
    file_logging_row = Gtk.Template.Child()
    console_logging_row = Gtk.Template.Child()
    structured_logging_row = Gtk.Template.Child()
    log_rotation_group = Gtk.Template.Child()
    max_log_size_row = Gtk.Template.Child()
    backup_count_row = Gtk.Template.Child()
    log_retention_row = Gtk.Template.Child()
    compression_row = Gtk.Template.Child()
    log_location_group = Gtk.Template.Child()
    custom_log_dir_row = Gtk.Template.Child()
    log_directory_row = Gtk.Template.Child()
    log_directory_entry = Gtk.Template.Child()
    browse_log_dir_button = Gtk.Template.Child()
    log_permissions_row = Gtk.Template.Child()
    current_log_dir_row = Gtk.Template.Child()
    open_log_dir_button = Gtk.Template.Child()
    
    def __init__(self, parent_window, config_manager: ConfigManager, **kwargs):
        super().__init__(**kwargs)

        self.parent_window = parent_window
        self.config_manager = config_manager

        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, "Preferences dialog")
        AccessibilityHelper.set_accessible_description(self, "Dialog for configuring application preferences")

    def present(self, parent=None):
        """Present the dialog with proper transient parent handling."""
        if parent or self.parent_window:
            super().present(parent or self.parent_window)
        else:
            super().present()

        self.theme_manager = ThemeManager(self.config_manager)
        self.config = self.config_manager.get_config()

        self._setup_ui()
        self._load_current_settings()
        self._connect_signals()
        self._setup_dialog_behavior()
    
    def _setup_ui(self):
        """Setup additional UI elements that couldn't be defined in Blueprint."""
        # No additional UI setup needed since everything is in the Blueprint template
        pass
    
    def _connect_signals(self):
        """Connect signals for preference changes."""
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        self.remember_window_row.connect("notify::active", self._on_setting_changed)

        # Security signal connections
        self.auto_hide_row.connect("notify::active", self._on_setting_changed)
        self.auto_hide_timeout_row.connect("notify::value", self._on_setting_changed)
        self.clipboard_timeout_row.connect("notify::value", self._on_setting_changed)
        self.confirm_delete_row.connect("notify::active", self._on_setting_changed)
        self.require_password_name_row.connect("notify::active", self._on_setting_changed)
        self.lock_on_idle_row.connect("notify::active", self._on_setting_changed)
        self.idle_timeout_row.connect("notify::value", self._on_setting_changed)
        self.lock_on_screen_lock_row.connect("notify::active", self._on_setting_changed)
        self.master_password_timeout_row.connect("notify::value", self._on_setting_changed)
        self.clear_memory_row.connect("notify::active", self._on_setting_changed)
        self.require_master_for_export_row.connect("notify::active", self._on_setting_changed)
        self.max_failed_attempts_row.connect("notify::value", self._on_setting_changed)
        self.lockout_duration_row.connect("notify::value", self._on_setting_changed)

        # Password policy signal connections
        self.password_complexity_row.connect("notify::active", self._on_setting_changed)
        self.password_min_length_row.connect("notify::value", self._on_setting_changed)
        self.password_history_row.connect("notify::value", self._on_setting_changed)
        self.password_expiry_row.connect("notify::value", self._on_setting_changed)
        
        # Audit signal connections
        self.audit_enabled_row.connect("notify::active", self._on_setting_changed)
        self.log_all_access_row.connect("notify::active", self._on_setting_changed)
        self.audit_retention_row.connect("notify::value", self._on_setting_changed)

        # Search signal connections
        self.case_sensitive_row.connect("notify::active", self._on_setting_changed)
        self.search_content_row.connect("notify::active", self._on_setting_changed)
        self.search_filenames_row.connect("notify::active", self._on_setting_changed)
        self.max_results_row.connect("notify::value", self._on_setting_changed)

        # Git signal connections
        self.auto_pull_row.connect("notify::active", self._on_setting_changed)
        self.auto_push_row.connect("notify::active", self._on_setting_changed)
        self.show_git_status_row.connect("notify::active", self._on_setting_changed)
        self.git_timeout_row.connect("notify::value", self._on_setting_changed)
        self.auto_commit_row.connect("notify::active", self._on_setting_changed)
        self.git_notifications_row.connect("notify::active", self._on_setting_changed)
        self.check_remote_row.connect("notify::active", self._on_setting_changed)
        self.remote_name_row.connect("notify::text", self._on_setting_changed)
        self.default_branch_row.connect("notify::text", self._on_setting_changed)
        self.commit_template_row.connect("notify::text", self._on_setting_changed)

        # Logging signal connections
        self.log_level_row.connect("notify::selected", self._on_setting_changed)
        self.file_logging_row.connect("notify::active", self._on_setting_changed)
        self.console_logging_row.connect("notify::active", self._on_setting_changed)
        self.structured_logging_row.connect("notify::active", self._on_setting_changed)
        self.max_log_size_row.connect("notify::value", self._on_setting_changed)
        self.backup_count_row.connect("notify::value", self._on_setting_changed)
        self.log_retention_row.connect("notify::value", self._on_setting_changed)
        self.compression_row.connect("notify::active", self._on_setting_changed)
        self.custom_log_dir_row.connect("notify::active", self._on_setting_changed)
        self.log_directory_entry.connect("notify::text", self._on_setting_changed)
        self.log_permissions_row.connect("notify::text", self._on_setting_changed)

        # Button signal connections
        self.repo_setup_button.connect("clicked", self._on_git_setup_clicked)
        self.repo_status_button.connect("clicked", self._on_git_status_clicked)
        self.browse_log_dir_button.connect("clicked", self._on_browse_log_directory)
        self.open_log_dir_button.connect("clicked", self._on_open_log_directory)
    
    def _load_current_settings(self):
        """Load current settings from configuration into the UI."""
        # Load general settings
        theme_setting = getattr(self.config.ui, 'theme', 'auto')
        theme_map = {"auto": 0, "light": 1, "dark": 2}
        self.theme_row.set_selected(theme_map.get(theme_setting, 0))
        
        remember_window = getattr(self.config.ui, 'remember_window_state', True)
        self.remember_window_row.set_active(remember_window)

        # Load security settings
        self.auto_hide_row.set_active(getattr(self.config.security, 'auto_hide_passwords', True))
        self.auto_hide_timeout_row.set_value(getattr(self.config.security, 'auto_hide_timeout_seconds', 30))
        self.clipboard_timeout_row.set_value(getattr(self.config.security, 'clear_clipboard_timeout', 45))
        self.confirm_delete_row.set_active(getattr(self.config.security, 'require_confirmation_for_delete', True))
        self.require_password_name_row.set_active(getattr(self.config.security, 'require_password_name_for_delete', False))
        self.lock_on_idle_row.set_active(getattr(self.config.security, 'lock_on_idle', False))
        self.idle_timeout_row.set_value(getattr(self.config.security, 'idle_timeout_minutes', 15))
        self.lock_on_screen_lock_row.set_active(getattr(self.config.security, 'lock_on_screen_lock', True))
        self.master_password_timeout_row.set_value(getattr(self.config.security, 'master_password_timeout_minutes', 60))
        self.clear_memory_row.set_active(getattr(self.config.security, 'clear_memory_on_lock', False))
        self.require_master_for_export_row.set_active(getattr(self.config.security, 'require_master_password_for_export', True))
        self.max_failed_attempts_row.set_value(getattr(self.config.security, 'max_failed_unlock_attempts', 3))
        self.lockout_duration_row.set_value(getattr(self.config.security, 'lockout_duration_minutes', 5))
        
        # Password policy settings - using compliance config
        self.password_complexity_row.set_active(getattr(self.config.compliance, 'password_complexity_enabled', True))
        self.password_min_length_row.set_value(getattr(self.config.compliance, 'password_min_length', 12))
        self.password_history_row.set_value(getattr(self.config.compliance, 'password_history_count', 4))
        self.password_expiry_row.set_value(getattr(self.config.compliance, 'password_expiry_days', 90))
        
        # Audit settings - using compliance config
        self.audit_enabled_row.set_active(getattr(self.config.compliance, 'audit_enabled', False))
        self.log_all_access_row.set_active(getattr(self.config.compliance, 'log_all_access', False))
        self.audit_retention_row.set_value(getattr(self.config.compliance, 'audit_retention_days', 90))

        # Load search settings
        self.case_sensitive_row.set_active(getattr(self.config.search, 'case_sensitive', False))
        self.search_content_row.set_active(getattr(self.config.search, 'search_in_content', True))
        self.search_filenames_row.set_active(getattr(self.config.search, 'search_in_filenames', True))
        self.max_results_row.set_value(getattr(self.config.search, 'max_search_results', 100))

        # Load Git settings
        self.auto_pull_row.set_active(getattr(self.config.git, 'auto_pull_on_startup', False))
        self.auto_push_row.set_active(getattr(self.config.git, 'auto_push_on_changes', False))
        self.show_git_status_row.set_active(getattr(self.config.git, 'show_git_status', True))
        self.git_timeout_row.set_value(getattr(self.config.git, 'git_timeout_seconds', 30))
        self.auto_commit_row.set_active(getattr(self.config.git, 'auto_commit_on_changes', False))
        self.git_notifications_row.set_active(getattr(self.config.git, 'show_git_notifications', True))
        self.check_remote_row.set_active(getattr(self.config.git, 'check_remote_on_startup', True))
        self.remote_name_row.set_text(getattr(self.config.git, 'remote_name', 'origin'))
        self.default_branch_row.set_text(getattr(self.config.git, 'default_branch', 'main'))
        self.commit_template_row.set_text(getattr(self.config.git, 'commit_message_template', 'Update passwords'))

        # Load logging settings
        log_level = getattr(self.config.logging, 'log_level', 'WARNING')
        level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        self.log_level_row.set_selected(level_map.get(log_level, 2))
        
        self.file_logging_row.set_active(getattr(self.config.logging, 'enable_file_logging', True))
        self.console_logging_row.set_active(getattr(self.config.logging, 'enable_console_logging', True))
        self.structured_logging_row.set_active(getattr(self.config.logging, 'enable_structured_logging', True))
        
        # Rotation settings
        self.max_log_size_row.set_value(getattr(self.config.logging, 'max_log_file_size_mb', 10))
        self.backup_count_row.set_value(getattr(self.config.logging, 'backup_count', 5))
        self.log_retention_row.set_value(getattr(self.config.logging, 'log_retention_days', 30))
        self.compression_row.set_active(getattr(self.config.logging, 'enable_compression', True))
        
        # Location settings
        self.custom_log_dir_row.set_active(getattr(self.config.logging, 'use_custom_log_directory', False))
        self.log_directory_entry.set_text(getattr(self.config.logging, 'custom_log_directory', ''))
        self.log_permissions_row.set_text(getattr(self.config.logging, 'log_directory_permissions', '755'))
        
        # Update current log directory display
        current_dir = getattr(self.config.logging, 'custom_log_directory', '') or 'Default location'
        self.current_log_dir_row.set_subtitle(current_dir)

    def _setup_dialog_behavior(self):
        """Set up dialog behavior and keyboard shortcuts."""
        DialogManager.setup_dialog_keyboard_navigation(self)
        DialogManager.center_dialog_on_parent(self)

    def _on_theme_changed(self, combo_row, param):
        """Handle theme change."""
        selected = combo_row.get_selected()
        theme_map = {0: "auto", 1: "light", 2: "dark"}
        theme = theme_map.get(selected, "auto")
        
        self.theme_manager.set_theme(theme)
        self._save_setting("general", "theme", theme)

    def _on_setting_changed(self, widget, param=None):
        """Handle setting changes and save to configuration."""
        # This method will be called whenever a preference changes
        # You would implement the logic to save settings here
        logging.debug(f"Setting changed: {widget}")

    def _save_setting(self, section, key, value):
        """Save a setting to the configuration."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.config_manager.save_config()

    def _on_git_setup_clicked(self, button):
        """Handle git setup button click."""
        # Open git setup dialog
        logging.info("Opening Git setup dialog")

    def _on_git_status_clicked(self, button):
        """Handle git status button click."""
        # Open git status dialog
        logging.info("Opening Git status dialog")

    def _on_browse_log_directory(self, button):
        """Handle browse log directory button click."""
        # Open file chooser for directory selection
        logging.info("Opening directory chooser for log directory")

    def _on_open_log_directory(self, button):
        """Handle open log directory button click."""
        # Open the current log directory in file manager
        logging.info("Opening current log directory")