import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
import logging
from ...config import ConfigManager, ThemeManager
from ...utils import DialogManager, UIConstants, AccessibilityHelper


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences dialog for the Secrets application."""
    
    __gtype_name__ = "PreferencesDialog"
    
    def __init__(self, parent_window, config_manager: ConfigManager, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title("Preferences")
        self.set_default_size(*UIConstants.LARGE_DIALOG)



        # Set up accessibility
        AccessibilityHelper.set_accessible_name(self, "Preferences dialog")
        AccessibilityHelper.set_accessible_description(self, "Dialog for configuring application preferences")

        self.config_manager = config_manager
        self.theme_manager = ThemeManager(config_manager)
        self.config = config_manager.get_config()

        self._setup_ui()
        self._load_current_settings()
        self._connect_signals()
        self._setup_dialog_behavior()
    
    def _setup_ui(self):
        """Setup the preferences UI."""
        # General preferences page
        general_page = Adw.PreferencesPage()
        general_page.set_title("General")
        general_page.set_icon_name("preferences-system-symbolic")
        self.add(general_page)
        
        # Appearance group
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title("Appearance")
        general_page.add(appearance_group)
        
        # Theme selection
        self.theme_row = Adw.ComboRow()
        self.theme_row.set_title("Theme")
        self.theme_row.set_subtitle("Choose the application theme")
        
        theme_model = Gtk.StringList()
        theme_model.append("Auto (Follow System)")
        theme_model.append("Light")
        theme_model.append("Dark")
        self.theme_row.set_model(theme_model)
        
        appearance_group.add(self.theme_row)
        
        # Window group
        window_group = Adw.PreferencesGroup()
        window_group.set_title("Window")
        general_page.add(window_group)
        
        # Remember window size
        self.remember_window_row = Adw.SwitchRow()
        self.remember_window_row.set_title("Remember Window Size")
        self.remember_window_row.set_subtitle("Restore window size and position on startup")
        window_group.add(self.remember_window_row)
        
        # Security preferences page
        security_page = Adw.PreferencesPage()
        security_page.set_title("Security")
        security_page.set_icon_name("security-high-symbolic")
        self.add(security_page)

        # Password display group
        password_group = Adw.PreferencesGroup()
        password_group.set_title("Password Display")
        security_page.add(password_group)

        # Auto-hide passwords
        self.auto_hide_row = Adw.SwitchRow()
        self.auto_hide_row.set_title("Auto-hide Passwords")
        self.auto_hide_row.set_subtitle("Automatically hide passwords after a timeout")
        password_group.add(self.auto_hide_row)

        # Auto-hide timeout
        self.auto_hide_timeout_row = Adw.SpinRow()
        self.auto_hide_timeout_row.set_title("Auto-hide Timeout")
        self.auto_hide_timeout_row.set_subtitle("Seconds before passwords are automatically hidden")
        adjustment = Gtk.Adjustment(value=30, lower=5, upper=300, step_increment=5)
        self.auto_hide_timeout_row.set_adjustment(adjustment)
        password_group.add(self.auto_hide_timeout_row)

        # Clipboard group
        clipboard_group = Adw.PreferencesGroup()
        clipboard_group.set_title("Clipboard")
        security_page.add(clipboard_group)

        # Clear clipboard timeout
        self.clipboard_timeout_row = Adw.SpinRow()
        self.clipboard_timeout_row.set_title("Clear Clipboard Timeout")
        self.clipboard_timeout_row.set_subtitle("Seconds before clipboard is automatically cleared")
        clipboard_adjustment = Gtk.Adjustment(value=45, lower=10, upper=300, step_increment=5)
        self.clipboard_timeout_row.set_adjustment(clipboard_adjustment)
        clipboard_group.add(self.clipboard_timeout_row)

        # Confirmation group
        confirmation_group = Adw.PreferencesGroup()
        confirmation_group.set_title("Confirmations")
        security_page.add(confirmation_group)

        # Require confirmation for delete
        self.confirm_delete_row = Adw.SwitchRow()
        self.confirm_delete_row.set_title("Confirm Deletions")
        self.confirm_delete_row.set_subtitle("Show confirmation dialog before deleting passwords")
        confirmation_group.add(self.confirm_delete_row)

        # Require password name for delete
        self.require_password_name_row = Adw.SwitchRow()
        self.require_password_name_row.set_title("Require Password Name for Deletion")
        self.require_password_name_row.set_subtitle("Require typing the password name before deletion")
        confirmation_group.add(self.require_password_name_row)

        # Session security group
        session_group = Adw.PreferencesGroup()
        session_group.set_title("Session Security")
        security_page.add(session_group)

        # Lock on idle
        self.lock_on_idle_row = Adw.SwitchRow()
        self.lock_on_idle_row.set_title("Lock on Idle")
        self.lock_on_idle_row.set_subtitle("Automatically lock the application when idle")
        session_group.add(self.lock_on_idle_row)

        # Idle timeout
        self.idle_timeout_row = Adw.SpinRow()
        self.idle_timeout_row.set_title("Idle Timeout")
        self.idle_timeout_row.set_subtitle("Minutes of inactivity before locking")
        idle_adjustment = Gtk.Adjustment(value=15, lower=1, upper=120, step_increment=1)
        self.idle_timeout_row.set_adjustment(idle_adjustment)
        session_group.add(self.idle_timeout_row)

        # Lock on screen lock
        self.lock_on_screen_lock_row = Adw.SwitchRow()
        self.lock_on_screen_lock_row.set_title("Lock on Screen Lock")
        self.lock_on_screen_lock_row.set_subtitle("Lock application when system screen locks")
        session_group.add(self.lock_on_screen_lock_row)

        # Master password timeout
        self.master_password_timeout_row = Adw.SpinRow()
        self.master_password_timeout_row.set_title("Master Password Timeout")
        self.master_password_timeout_row.set_subtitle("Minutes before requiring master password re-entry (0 = never)")
        master_pw_adjustment = Gtk.Adjustment(value=60, lower=0, upper=480, step_increment=15)
        self.master_password_timeout_row.set_adjustment(master_pw_adjustment)
        session_group.add(self.master_password_timeout_row)

        # Advanced security group
        advanced_group = Adw.PreferencesGroup()
        advanced_group.set_title("Advanced Security")
        security_page.add(advanced_group)

        # Clear memory on lock
        self.clear_memory_row = Adw.SwitchRow()
        self.clear_memory_row.set_title("Clear Memory on Lock")
        self.clear_memory_row.set_subtitle("Clear sensitive data from memory when locked")
        advanced_group.add(self.clear_memory_row)

        # Require master password for export
        self.require_master_for_export_row = Adw.SwitchRow()
        self.require_master_for_export_row.set_title("Require Master Password for Export")
        self.require_master_for_export_row.set_subtitle("Require master password when exporting data")
        advanced_group.add(self.require_master_for_export_row)

        # Failed unlock attempts
        self.max_failed_attempts_row = Adw.SpinRow()
        self.max_failed_attempts_row.set_title("Max Failed Unlock Attempts")
        self.max_failed_attempts_row.set_subtitle("Maximum failed unlock attempts before lockout")
        failed_attempts_adjustment = Gtk.Adjustment(value=3, lower=1, upper=10, step_increment=1)
        self.max_failed_attempts_row.set_adjustment(failed_attempts_adjustment)
        advanced_group.add(self.max_failed_attempts_row)

        # Lockout duration
        self.lockout_duration_row = Adw.SpinRow()
        self.lockout_duration_row.set_title("Lockout Duration")
        self.lockout_duration_row.set_subtitle("Minutes to lock out after too many failed attempts")
        lockout_adjustment = Gtk.Adjustment(value=5, lower=1, upper=60, step_increment=1)
        self.lockout_duration_row.set_adjustment(lockout_adjustment)
        advanced_group.add(self.lockout_duration_row)
        
        # Master Password Policy group
        password_policy_group = Adw.PreferencesGroup()
        password_policy_group.set_title("Master Password Policy")
        password_policy_group.set_description("Security requirements for the master password")
        security_page.add(password_policy_group)
        
        # Password complexity
        self.password_complexity_row = Adw.SwitchRow()
        self.password_complexity_row.set_title("Enforce Password Complexity")
        self.password_complexity_row.set_subtitle("Require strong passwords with mixed characters")
        password_policy_group.add(self.password_complexity_row)
        
        # Minimum password length
        self.password_min_length_row = Adw.SpinRow()
        self.password_min_length_row.set_title("Minimum Password Length")
        self.password_min_length_row.set_subtitle("Minimum characters required for passwords")
        min_length_adjustment = Gtk.Adjustment(value=12, lower=8, upper=32, step_increment=1)
        self.password_min_length_row.set_adjustment(min_length_adjustment)
        password_policy_group.add(self.password_min_length_row)
        
        # Password history
        self.password_history_row = Adw.SpinRow()
        self.password_history_row.set_title("Password History")
        self.password_history_row.set_subtitle("Number of previous passwords to remember")
        history_adjustment = Gtk.Adjustment(value=4, lower=0, upper=12, step_increment=1)
        self.password_history_row.set_adjustment(history_adjustment)
        password_policy_group.add(self.password_history_row)
        
        # Password expiry
        self.password_expiry_row = Adw.SpinRow()
        self.password_expiry_row.set_title("Password Expiry (Days)")
        self.password_expiry_row.set_subtitle("Days before password change reminder (0 = never)")
        expiry_adjustment = Gtk.Adjustment(value=90, lower=0, upper=365, step_increment=30)
        self.password_expiry_row.set_adjustment(expiry_adjustment)
        password_policy_group.add(self.password_expiry_row)
        
        # Audit & Monitoring group
        audit_group = Adw.PreferencesGroup()
        audit_group.set_title("Audit &amp; Monitoring")
        audit_group.set_description("Security event logging and monitoring")
        security_page.add(audit_group)
        
        # Enable audit logging
        self.audit_enabled_row = Adw.SwitchRow()
        self.audit_enabled_row.set_title("Enable Audit Logging")
        self.audit_enabled_row.set_subtitle("Log security events and access attempts")
        audit_group.add(self.audit_enabled_row)
        
        # Log all access
        self.log_all_access_row = Adw.SwitchRow()
        self.log_all_access_row.set_title("Log All Password Access")
        self.log_all_access_row.set_subtitle("Create detailed logs of all password access")
        audit_group.add(self.log_all_access_row)
        
        # Audit retention
        self.audit_retention_row = Adw.SpinRow()
        self.audit_retention_row.set_title("Audit Log Retention (Days)")
        self.audit_retention_row.set_subtitle("How long to keep audit logs")
        retention_adjustment = Gtk.Adjustment(value=90, lower=30, upper=2190, step_increment=30)
        self.audit_retention_row.set_adjustment(retention_adjustment)
        audit_group.add(self.audit_retention_row)
        
        # Search preferences page
        search_page = Adw.PreferencesPage()
        search_page.set_title("Search")
        search_page.set_icon_name("system-search-symbolic")
        self.add(search_page)

        # Search options group
        search_options_group = Adw.PreferencesGroup()
        search_options_group.set_title("Search Options")
        search_page.add(search_options_group)

        # Case sensitive search
        self.case_sensitive_row = Adw.SwitchRow()
        self.case_sensitive_row.set_title("Case Sensitive")
        self.case_sensitive_row.set_subtitle("Make searches case sensitive")
        search_options_group.add(self.case_sensitive_row)

        # Search in content
        self.search_content_row = Adw.SwitchRow()
        self.search_content_row.set_title("Search in Content")
        self.search_content_row.set_subtitle("Include password content in search")
        search_options_group.add(self.search_content_row)

        # Search in filenames
        self.search_filenames_row = Adw.SwitchRow()
        self.search_filenames_row.set_title("Search in Filenames")
        self.search_filenames_row.set_subtitle("Include filenames in search")
        search_options_group.add(self.search_filenames_row)

        # Max search results
        self.max_results_row = Adw.SpinRow()
        self.max_results_row.set_title("Maximum Results")
        self.max_results_row.set_subtitle("Maximum number of search results to display")
        results_adjustment = Gtk.Adjustment(value=100, lower=10, upper=1000, step_increment=10)
        self.max_results_row.set_adjustment(results_adjustment)
        search_options_group.add(self.max_results_row)
        
        # Git preferences page
        git_page = Adw.PreferencesPage()
        git_page.set_title("Git")
        git_page.set_icon_name("software-update-available-symbolic")
        self.add(git_page)

        # Git automation group
        git_automation_group = Adw.PreferencesGroup()
        git_automation_group.set_title("Automation")
        git_page.add(git_automation_group)

        # Auto-pull on startup
        self.auto_pull_row = Adw.SwitchRow()
        self.auto_pull_row.set_title("Auto-pull on Startup")
        self.auto_pull_row.set_subtitle("Automatically pull changes when the application starts")
        git_automation_group.add(self.auto_pull_row)

        # Auto-push on changes
        self.auto_push_row = Adw.SwitchRow()
        self.auto_push_row.set_title("Auto-push on Changes")
        self.auto_push_row.set_subtitle("Automatically push changes after modifications")
        git_automation_group.add(self.auto_push_row)

        # Git status group
        git_status_group = Adw.PreferencesGroup()
        git_status_group.set_title("Status")
        git_page.add(git_status_group)

        # Show git status
        self.show_git_status_row = Adw.SwitchRow()
        self.show_git_status_row.set_title("Show Git Status")
        self.show_git_status_row.set_subtitle("Display git repository status information")
        git_status_group.add(self.show_git_status_row)

        # Git timeout
        self.git_timeout_row = Adw.SpinRow()
        self.git_timeout_row.set_title("Git Timeout")
        self.git_timeout_row.set_subtitle("Timeout for git operations in seconds")
        git_timeout_adjustment = Gtk.Adjustment(value=30, lower=5, upper=120, step_increment=5)
        self.git_timeout_row.set_adjustment(git_timeout_adjustment)
        git_status_group.add(self.git_timeout_row)

        # Repository management group
        git_repo_group = Adw.PreferencesGroup()
        git_repo_group.set_title("Repository Management")
        git_page.add(git_repo_group)

        # Repository setup button
        self.repo_setup_row = Adw.ActionRow()
        self.repo_setup_row.set_title("Repository Setup")
        self.repo_setup_row.set_subtitle("Configure Git repository and remote connections")
        setup_button = Gtk.Button(label="Setup")
        setup_button.set_valign(Gtk.Align.CENTER)
        setup_button.connect("clicked", self._on_git_setup_clicked)
        self.repo_setup_row.add_suffix(setup_button)
        git_repo_group.add(self.repo_setup_row)

        # Repository status button
        self.repo_status_row = Adw.ActionRow()
        self.repo_status_row.set_title("Repository Status")
        self.repo_status_row.set_subtitle("View Git repository status and history")
        status_button = Gtk.Button(label="View Status")
        status_button.set_valign(Gtk.Align.CENTER)
        status_button.connect("clicked", self._on_git_status_clicked)
        self.repo_status_row.add_suffix(status_button)
        git_repo_group.add(self.repo_status_row)

        # Advanced Git settings group
        git_advanced_group = Adw.PreferencesGroup()
        git_advanced_group.set_title("Advanced Settings")
        git_page.add(git_advanced_group)

        # Auto-commit on changes
        self.auto_commit_row = Adw.SwitchRow()
        self.auto_commit_row.set_title("Auto-commit Changes")
        self.auto_commit_row.set_subtitle("Automatically commit changes before push/pull operations")
        git_advanced_group.add(self.auto_commit_row)

        # Show Git notifications
        self.git_notifications_row = Adw.SwitchRow()
        self.git_notifications_row.set_title("Show Git Notifications")
        self.git_notifications_row.set_subtitle("Display notifications for Git operations")
        git_advanced_group.add(self.git_notifications_row)

        # Check remote on startup
        self.check_remote_row = Adw.SwitchRow()
        self.check_remote_row.set_title("Check Remote on Startup")
        self.check_remote_row.set_subtitle("Check for remote changes when the application starts")
        git_advanced_group.add(self.check_remote_row)
        
        # Remote name
        self.remote_name_row = Adw.EntryRow()
        self.remote_name_row.set_title("Remote Name")
        self.remote_name_row.set_text("origin")
        git_advanced_group.add(self.remote_name_row)
        
        # Default branch
        self.default_branch_row = Adw.EntryRow()
        self.default_branch_row.set_title("Default Branch")
        self.default_branch_row.set_text("main")
        git_advanced_group.add(self.default_branch_row)
        
        # Commit message template
        self.commit_template_row = Adw.EntryRow()
        self.commit_template_row.set_title("Commit Message Template")
        self.commit_template_row.set_text("Update passwords")
        git_advanced_group.add(self.commit_template_row)
        
        # Logging preferences page
        logging_page = Adw.PreferencesPage()
        logging_page.set_title("Logging")
        logging_page.set_icon_name("dialog-information-symbolic")
        self.add(logging_page)

        # Logging configuration group
        logging_config_group = Adw.PreferencesGroup()
        logging_config_group.set_title("Logging Configuration")
        logging_config_group.set_description("Control application logging behavior")
        logging_page.add(logging_config_group)

        # Log level selection
        self.log_level_row = Adw.ComboRow()
        self.log_level_row.set_title("Log Level")
        self.log_level_row.set_subtitle("Set the minimum level for log messages")
        
        log_level_model = Gtk.StringList()
        log_level_model.append("DEBUG")
        log_level_model.append("INFO")
        log_level_model.append("WARNING")
        log_level_model.append("ERROR")
        log_level_model.append("CRITICAL")
        self.log_level_row.set_model(log_level_model)
        
        logging_config_group.add(self.log_level_row)

        # Enable file logging
        self.file_logging_row = Adw.SwitchRow()
        self.file_logging_row.set_title("Enable File Logging")
        self.file_logging_row.set_subtitle("Save log messages to files")
        logging_config_group.add(self.file_logging_row)

        # Enable console logging
        self.console_logging_row = Adw.SwitchRow()
        self.console_logging_row.set_title("Enable Console Logging")
        self.console_logging_row.set_subtitle("Display log messages in console")
        logging_config_group.add(self.console_logging_row)

        # Enable structured logging
        self.structured_logging_row = Adw.SwitchRow()
        self.structured_logging_row.set_title("Enable Structured Logging")
        self.structured_logging_row.set_subtitle("Use JSON format for log messages")
        logging_config_group.add(self.structured_logging_row)

        # Log rotation group
        log_rotation_group = Adw.PreferencesGroup()
        log_rotation_group.set_title("Log Rotation")
        log_rotation_group.set_description("Configure log file rotation and retention")
        logging_page.add(log_rotation_group)

        # Max log file size
        self.max_log_size_row = Adw.SpinRow()
        self.max_log_size_row.set_title("Max Log File Size (MB)")
        self.max_log_size_row.set_subtitle("Maximum size before log rotation")
        log_size_adjustment = Gtk.Adjustment(value=10, lower=1, upper=100, step_increment=1)
        self.max_log_size_row.set_adjustment(log_size_adjustment)
        log_rotation_group.add(self.max_log_size_row)

        # Log backup count
        self.backup_count_row = Adw.SpinRow()
        self.backup_count_row.set_title("Backup Count")
        self.backup_count_row.set_subtitle("Number of backup log files to keep")
        backup_adjustment = Gtk.Adjustment(value=5, lower=1, upper=20, step_increment=1)
        self.backup_count_row.set_adjustment(backup_adjustment)
        log_rotation_group.add(self.backup_count_row)

        # Log retention days
        self.log_retention_row = Adw.SpinRow()
        self.log_retention_row.set_title("Log Retention (Days)")
        self.log_retention_row.set_subtitle("How long to keep log files")
        retention_adjustment = Gtk.Adjustment(value=30, lower=1, upper=365, step_increment=1)
        self.log_retention_row.set_adjustment(retention_adjustment)
        log_rotation_group.add(self.log_retention_row)

        # Enable compression
        self.compression_row = Adw.SwitchRow()
        self.compression_row.set_title("Enable Log Compression")
        self.compression_row.set_subtitle("Compress rotated log files to save space")
        log_rotation_group.add(self.compression_row)

        # Log file location group
        log_location_group = Adw.PreferencesGroup()
        log_location_group.set_title("Log File Location")
        log_location_group.set_description("Configure where log files are stored")
        logging_page.add(log_location_group)

        # Use custom log directory
        self.custom_log_dir_row = Adw.SwitchRow()
        self.custom_log_dir_row.set_title("Use Custom Log Directory")
        self.custom_log_dir_row.set_subtitle("Store logs in a custom location instead of default")
        log_location_group.add(self.custom_log_dir_row)

        # Custom log directory path
        self.log_directory_row = Adw.ActionRow()
        self.log_directory_row.set_title("Log Directory Path")
        self.log_directory_row.set_subtitle("Location to store log files (leave empty for default)")
        
        self.log_directory_entry = Gtk.Entry()
        self.log_directory_entry.set_placeholder_text("e.g., /var/log/secrets or ~/logs")
        self.log_directory_entry.set_hexpand(True)
        self.log_directory_entry.set_valign(Gtk.Align.CENTER)
        
        # Browse button for directory selection
        browse_button = Gtk.Button()
        browse_button.set_icon_name("document-open-symbolic")
        browse_button.set_tooltip_text("Browse for directory")
        browse_button.set_valign(Gtk.Align.CENTER)
        browse_button.connect("clicked", self._on_browse_log_directory)
        
        self.log_directory_row.add_suffix(self.log_directory_entry)
        self.log_directory_row.add_suffix(browse_button)
        log_location_group.add(self.log_directory_row)

        # Directory permissions
        self.log_permissions_row = Adw.EntryRow()
        self.log_permissions_row.set_title("Directory Permissions")
        self.log_permissions_row.set_text("755")
        self.log_permissions_row.set_input_hints(Gtk.InputHints.NO_SPELLCHECK)
        log_location_group.add(self.log_permissions_row)

        # Current log directory display
        self.current_log_dir_row = Adw.ActionRow()
        self.current_log_dir_row.set_title("Current Log Directory")
        self.current_log_dir_row.set_subtitle("Location where logs are currently stored")
        
        open_log_dir_button = Gtk.Button()
        open_log_dir_button.set_label("Open")
        open_log_dir_button.set_valign(Gtk.Align.CENTER)
        open_log_dir_button.connect("clicked", self._on_open_log_directory)
        
        self.current_log_dir_row.add_suffix(open_log_dir_button)
        log_location_group.add(self.current_log_dir_row)

        # Application preferences page removed for Flatpak compatibility
        # All application-specific settings are now handled through standard locations
    
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
        
        # Log file location signal connections
        self.custom_log_dir_row.connect("notify::active", self._on_setting_changed)
        self.log_directory_entry.connect("changed", self._on_setting_changed)
        self.log_permissions_row.connect("notify::text", self._on_setting_changed)

    
    def _load_current_settings(self):
        """Load current settings into the UI."""
        # Theme
        theme_map = {"auto": 0, "light": 1, "dark": 2}
        self.theme_row.set_selected(theme_map.get(self.config.ui.theme, 0))
        
        # UI settings
        self.remember_window_row.set_active(self.config.ui.remember_window_state)
        
        # Security settings
        self.auto_hide_row.set_active(self.config.security.auto_hide_passwords)
        self.auto_hide_timeout_row.set_value(self.config.security.auto_hide_timeout_seconds)
        self.clipboard_timeout_row.set_value(self.config.security.clear_clipboard_timeout)
        self.confirm_delete_row.set_active(self.config.security.require_confirmation_for_delete)
        self.require_password_name_row.set_active(self.config.security.require_password_name_for_delete)
        self.lock_on_idle_row.set_active(self.config.security.lock_on_idle)
        self.idle_timeout_row.set_value(self.config.security.idle_timeout_minutes)
        self.lock_on_screen_lock_row.set_active(self.config.security.lock_on_screen_lock)
        self.master_password_timeout_row.set_value(self.config.security.master_password_timeout_minutes)
        self.clear_memory_row.set_active(self.config.security.clear_memory_on_lock)
        self.require_master_for_export_row.set_active(self.config.security.require_master_password_for_export)
        self.max_failed_attempts_row.set_value(self.config.security.max_failed_unlock_attempts)
        self.lockout_duration_row.set_value(self.config.security.lockout_duration_minutes)

        # Password policy settings (from compliance)
        self.password_complexity_row.set_active(self.config.compliance.password_complexity_enabled)
        self.password_min_length_row.set_value(self.config.compliance.password_min_length)
        self.password_history_row.set_value(self.config.compliance.password_history_count)
        self.password_expiry_row.set_value(self.config.compliance.password_expiry_days)
        
        # Audit settings
        self.audit_enabled_row.set_active(self.config.compliance.audit_enabled)
        self.log_all_access_row.set_active(self.config.compliance.log_all_access)
        self.audit_retention_row.set_value(self.config.compliance.audit_retention_days)

        # Search settings
        self.case_sensitive_row.set_active(self.config.search.case_sensitive)
        self.search_content_row.set_active(self.config.search.search_in_content)
        self.search_filenames_row.set_active(self.config.search.search_in_filenames)
        self.max_results_row.set_value(self.config.search.max_search_results)

        # Git settings
        self.auto_pull_row.set_active(self.config.git.auto_pull_on_startup)
        self.auto_push_row.set_active(self.config.git.auto_push_on_changes)
        self.show_git_status_row.set_active(self.config.git.show_git_status)
        self.git_timeout_row.set_value(self.config.git.git_timeout_seconds)
        self.auto_commit_row.set_active(self.config.git.auto_commit_on_changes)
        self.git_notifications_row.set_active(self.config.git.show_git_notifications)
        self.check_remote_row.set_active(self.config.git.check_remote_on_startup)
        self.remote_name_row.set_text(self.config.git.remote_name)
        self.default_branch_row.set_text(self.config.git.default_branch)
        self.commit_template_row.set_text(self.config.git.commit_message_template)

        # Logging settings
        log_level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        self.log_level_row.set_selected(log_level_map.get(self.config.logging.log_level, 2))
        self.file_logging_row.set_active(self.config.logging.enable_file_logging)
        self.console_logging_row.set_active(self.config.logging.enable_console_logging)
        self.structured_logging_row.set_active(self.config.logging.enable_structured_logging)
        self.max_log_size_row.set_value(self.config.logging.max_log_file_size_mb)
        self.backup_count_row.set_value(self.config.logging.backup_count)
        self.log_retention_row.set_value(self.config.logging.log_retention_days)
        self.compression_row.set_active(self.config.logging.enable_compression)
        
        # Log file location settings
        self.custom_log_dir_row.set_active(self.config.logging.use_custom_log_directory)
        self.log_directory_entry.set_text(self.config.logging.custom_log_directory)
        self.log_permissions_row.set_text(self.config.logging.log_directory_permissions)
        
        # Update current log directory display
        self._update_current_log_directory_display()
        
        # Application settings - password store directory removed for Flatpak compatibility
    
    def _on_theme_changed(self, combo_row, param):
        """Handle theme change."""
        selected = combo_row.get_selected()
        theme_map = {0: "auto", 1: "light", 2: "dark"}
        theme = theme_map.get(selected, "auto")
        
        self.config.ui.theme = theme
        self.theme_manager.apply_theme(theme)
        self._save_settings()
    
    def _on_setting_changed(self, widget, param):
        """Handle setting changes."""
        self._save_current_settings()
        self._save_settings()
    
    def _save_current_settings(self):
        """Save current UI settings to config."""
        # UI settings
        self.config.ui.remember_window_state = self.remember_window_row.get_active()

        # Security settings
        self.config.security.auto_hide_passwords = self.auto_hide_row.get_active()
        self.config.security.auto_hide_timeout_seconds = int(self.auto_hide_timeout_row.get_value())
        self.config.security.clear_clipboard_timeout = int(self.clipboard_timeout_row.get_value())
        self.config.security.require_confirmation_for_delete = self.confirm_delete_row.get_active()
        self.config.security.require_password_name_for_delete = self.require_password_name_row.get_active()
        self.config.security.lock_on_idle = self.lock_on_idle_row.get_active()
        self.config.security.idle_timeout_minutes = int(self.idle_timeout_row.get_value())
        self.config.security.lock_on_screen_lock = self.lock_on_screen_lock_row.get_active()
        self.config.security.master_password_timeout_minutes = int(self.master_password_timeout_row.get_value())
        self.config.security.clear_memory_on_lock = self.clear_memory_row.get_active()
        self.config.security.require_master_password_for_export = self.require_master_for_export_row.get_active()
        self.config.security.max_failed_unlock_attempts = int(self.max_failed_attempts_row.get_value())
        self.config.security.lockout_duration_minutes = int(self.lockout_duration_row.get_value())
        
        # Password policy settings (saved to compliance config)
        self.config.compliance.password_complexity_enabled = self.password_complexity_row.get_active()
        self.config.compliance.password_min_length = int(self.password_min_length_row.get_value())
        self.config.compliance.password_history_count = int(self.password_history_row.get_value())
        self.config.compliance.password_expiry_days = int(self.password_expiry_row.get_value())
        
        # Audit settings
        self.config.compliance.audit_enabled = self.audit_enabled_row.get_active()
        self.config.compliance.log_all_access = self.log_all_access_row.get_active()
        self.config.compliance.audit_retention_days = int(self.audit_retention_row.get_value())

        # Search settings
        self.config.search.case_sensitive = self.case_sensitive_row.get_active()
        self.config.search.search_in_content = self.search_content_row.get_active()
        self.config.search.search_in_filenames = self.search_filenames_row.get_active()
        self.config.search.max_search_results = int(self.max_results_row.get_value())

        # Git settings
        self.config.git.auto_pull_on_startup = self.auto_pull_row.get_active()
        self.config.git.auto_push_on_changes = self.auto_push_row.get_active()
        self.config.git.show_git_status = self.show_git_status_row.get_active()
        self.config.git.git_timeout_seconds = int(self.git_timeout_row.get_value())
        self.config.git.auto_commit_on_changes = self.auto_commit_row.get_active()
        self.config.git.show_git_notifications = self.git_notifications_row.get_active()
        self.config.git.check_remote_on_startup = self.check_remote_row.get_active()
        self.config.git.remote_name = self.remote_name_row.get_text()
        self.config.git.default_branch = self.default_branch_row.get_text()
        self.config.git.commit_message_template = self.commit_template_row.get_text()

        # Logging settings
        log_level_map = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR", 4: "CRITICAL"}
        self.config.logging.log_level = log_level_map.get(self.log_level_row.get_selected(), "WARNING")
        self.config.logging.enable_file_logging = self.file_logging_row.get_active()
        self.config.logging.enable_console_logging = self.console_logging_row.get_active()
        self.config.logging.enable_structured_logging = self.structured_logging_row.get_active()
        self.config.logging.max_log_file_size_mb = int(self.max_log_size_row.get_value())
        self.config.logging.backup_count = int(self.backup_count_row.get_value())
        self.config.logging.log_retention_days = int(self.log_retention_row.get_value())
        self.config.logging.enable_compression = self.compression_row.get_active()
        
        # Log file location settings
        self.config.logging.use_custom_log_directory = self.custom_log_dir_row.get_active()
        self.config.logging.custom_log_directory = self.log_directory_entry.get_text()
        self.config.logging.log_directory_permissions = self.log_permissions_row.get_text()
    
    def _save_settings(self):
        """Save settings to file."""
        self.config_manager.save_config(self.config)
        
        # Apply logging changes immediately
        self.config_manager._apply_logging_changes(self.config.logging)


    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)

    def _on_git_setup_clicked(self, button):
        """Handle Git setup button click."""
        try:
            from ..dialogs.git_setup_dialog import GitSetupDialog

            # Get the main window from the parent chain
            parent = self.get_transient_for()
            if parent and hasattr(parent, 'password_store'):
                dialog = GitSetupDialog(
                    store_dir=parent.password_store.store_dir,
                    config_manager=parent.config_manager,
                    toast_manager=parent.toast_manager,
                    transient_for=parent
                )
                dialog.connect("setup-completed", self._on_git_setup_completed)
                dialog.present()
        except ImportError:
            logging.warning(
                "Git setup dialog not available - Git features disabled",
                extra={
                    "component": "PreferencesDialog",
                    "method": "_on_git_setup_clicked",
                    "feature": "git_setup",
                    "ui_context": "preferences"
                }
            )

    def _on_git_status_clicked(self, button):
        """Handle Git status button click."""
        try:
            from ..dialogs.git_status_dialog import GitStatusDialog

            # Get the main window from the parent chain
            parent = self.get_transient_for()
            if parent and hasattr(parent, 'git_manager'):
                dialog = GitStatusDialog(
                    git_manager=parent.git_manager,
                    transient_for=parent
                )
                dialog.present()
        except ImportError:
            logging.warning(
                "Git status dialog not available - Git features disabled",
                extra={
                    "component": "PreferencesDialog",
                    "method": "_on_git_status_clicked",
                    "feature": "git_status",
                    "ui_context": "preferences"
                }
            )

    def _on_git_setup_completed(self, dialog):
        """Handle Git setup completion."""
        
    def _update_current_log_directory_display(self):
        """Update the display of the current log directory."""
        try:
            from ...logging_system import get_logging_system
            logging_system = get_logging_system()
            if logging_system:
                current_dir = str(logging_system.log_dir)
                self.current_log_dir_row.set_subtitle(current_dir)
            else:
                # Fallback to showing the configured directory
                if self.config.logging.use_custom_log_directory and self.config.logging.custom_log_directory:
                    self.current_log_dir_row.set_subtitle(self.config.logging.custom_log_directory)
                else:
                    from gi.repository import GLib
                    default_dir = f"{GLib.get_user_data_dir()}/io.github.tobagin.secrets/logs"
                    self.current_log_dir_row.set_subtitle(default_dir)
        except Exception as e:
            self.current_log_dir_row.set_subtitle("Unable to determine current directory")
            logging.warning(f"Could not determine current log directory: {e}")
    
    def _on_browse_log_directory(self, button):
        """Handle browse button click for log directory selection."""
        dialog = Gtk.FileChooserDialog(
            title="Select Log Directory",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.ACCEPT)
        
        # Set current directory if configured
        current_path = self.log_directory_entry.get_text()
        if current_path:
            try:
                from pathlib import Path
                path = Path(current_path).expanduser()
                if path.exists():
                    dialog.set_current_folder(Gio.File.new_for_path(str(path)))
            except Exception:
                pass  # Ignore invalid paths
        
        dialog.connect("response", self._on_log_directory_selected)
        dialog.present()
    
    def _on_log_directory_selected(self, dialog, response):
        """Handle log directory selection response."""
        if response == Gtk.ResponseType.ACCEPT:
            selected_file = dialog.get_file()
            if selected_file:
                path = selected_file.get_path()
                if path:
                    self.log_directory_entry.set_text(path)
        dialog.destroy()
    
    def _on_open_log_directory(self, button):
        """Handle opening the current log directory."""
        try:
            from ...logging_system import get_logging_system
            logging_system = get_logging_system()
            if logging_system and logging_system.log_dir.exists():
                log_dir = str(logging_system.log_dir)
            else:
                # Fallback to configured directory
                if self.config.logging.use_custom_log_directory and self.config.logging.custom_log_directory:
                    log_dir = self.config.logging.custom_log_directory
                else:
                    from gi.repository import GLib
                    log_dir = f"{GLib.get_user_data_dir()}/io.github.tobagin.secrets/logs"
            
            # Open the directory in file manager
            import subprocess
            subprocess.run(["xdg-open", log_dir], check=False)
        except Exception as e:
            logging.error(f"Could not open log directory: {e}")
            # Show error toast if available
            if hasattr(self, 'toast_overlay'):
                toast = Adw.Toast.new("Could not open log directory")
                self.toast_overlay.add_toast(toast)
    
    # Password store directory browse methods removed for Flatpak compatibility
    
