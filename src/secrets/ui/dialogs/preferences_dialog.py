import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
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
        
        # Git preferences page disabled for v0.8.6 - will be re-enabled in v0.9.x
        # git_page = Adw.PreferencesPage()
        # git_page.set_title("Git")
        # git_page.set_icon_name("software-update-available-symbolic")
        # self.add(git_page)

        # # Git automation group
        # git_automation_group = Adw.PreferencesGroup()
        # git_automation_group.set_title("Automation")
        # git_page.add(git_automation_group)

        # # Auto-pull on startup
        # self.auto_pull_row = Adw.SwitchRow()
        # self.auto_pull_row.set_title("Auto-pull on Startup")
        # self.auto_pull_row.set_subtitle("Automatically pull changes when the application starts")
        # git_automation_group.add(self.auto_pull_row)

        # # Auto-push on changes
        # self.auto_push_row = Adw.SwitchRow()
        # self.auto_push_row.set_title("Auto-push on Changes")
        # self.auto_push_row.set_subtitle("Automatically push changes after modifications")
        # git_automation_group.add(self.auto_push_row)

        # # Git status group
        # git_status_group = Adw.PreferencesGroup()
        # git_status_group.set_title("Status")
        # git_page.add(git_status_group)

        # # Show git status
        # self.show_git_status_row = Adw.SwitchRow()
        # self.show_git_status_row.set_title("Show Git Status")
        # self.show_git_status_row.set_subtitle("Display git repository status information")
        # git_status_group.add(self.show_git_status_row)

        # # Git timeout
        # self.git_timeout_row = Adw.SpinRow()
        # self.git_timeout_row.set_title("Git Timeout")
        # self.git_timeout_row.set_subtitle("Timeout for git operations in seconds")
        # git_timeout_adjustment = Gtk.Adjustment(value=30, lower=5, upper=120, step_increment=5)
        # self.git_timeout_row.set_adjustment(git_timeout_adjustment)
        # git_status_group.add(self.git_timeout_row)

        # # Repository management group
        # git_repo_group = Adw.PreferencesGroup()
        # git_repo_group.set_title("Repository Management")
        # git_page.add(git_repo_group)

        # # Repository setup button
        # self.repo_setup_row = Adw.ActionRow()
        # self.repo_setup_row.set_title("Repository Setup")
        # self.repo_setup_row.set_subtitle("Configure Git repository and remote connections")
        # setup_button = Gtk.Button(label="Setup")
        # setup_button.set_valign(Gtk.Align.CENTER)
        # setup_button.connect("clicked", self._on_git_setup_clicked)
        # self.repo_setup_row.add_suffix(setup_button)
        # git_repo_group.add(self.repo_setup_row)

        # # Repository status button
        # self.repo_status_row = Adw.ActionRow()
        # self.repo_status_row.set_title("Repository Status")
        # self.repo_status_row.set_subtitle("View Git repository status and history")
        # status_button = Gtk.Button(label="View Status")
        # status_button.set_valign(Gtk.Align.CENTER)
        # status_button.connect("clicked", self._on_git_status_clicked)
        # self.repo_status_row.add_suffix(status_button)
        # git_repo_group.add(self.repo_status_row)

        # # Advanced Git settings group
        # git_advanced_group = Adw.PreferencesGroup()
        # git_advanced_group.set_title("Advanced Settings")
        # git_page.add(git_advanced_group)

        # # Auto-commit on changes
        # self.auto_commit_row = Adw.SwitchRow()
        # self.auto_commit_row.set_title("Auto-commit Changes")
        # self.auto_commit_row.set_subtitle("Automatically commit changes before push/pull operations")
        # git_advanced_group.add(self.auto_commit_row)

        # # Show Git notifications
        # self.git_notifications_row = Adw.SwitchRow()
        # self.git_notifications_row.set_title("Show Git Notifications")
        # self.git_notifications_row.set_subtitle("Display notifications for Git operations")
        # git_advanced_group.add(self.git_notifications_row)

        # # Check remote on startup
        # self.check_remote_row = Adw.SwitchRow()
        # self.check_remote_row.set_title("Check Remote on Startup")
        # self.check_remote_row.set_subtitle("Check for remote changes when the application starts")
        # git_advanced_group.add(self.check_remote_row)
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect signals for preference changes."""
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        self.remember_window_row.connect("notify::active", self._on_setting_changed)
        self.auto_hide_row.connect("notify::active", self._on_setting_changed)
        self.auto_hide_timeout_row.connect("notify::value", self._on_setting_changed)
        self.clipboard_timeout_row.connect("notify::value", self._on_setting_changed)
        self.confirm_delete_row.connect("notify::active", self._on_setting_changed)
        self.case_sensitive_row.connect("notify::active", self._on_setting_changed)
        self.search_content_row.connect("notify::active", self._on_setting_changed)
        self.search_filenames_row.connect("notify::active", self._on_setting_changed)
        self.max_results_row.connect("notify::value", self._on_setting_changed)
        # Git signal connections disabled for v0.8.6
        # self.auto_pull_row.connect("notify::active", self._on_setting_changed)
        # self.auto_push_row.connect("notify::active", self._on_setting_changed)
        # self.show_git_status_row.connect("notify::active", self._on_setting_changed)
        # self.git_timeout_row.connect("notify::value", self._on_setting_changed)
        # self.auto_commit_row.connect("notify::active", self._on_setting_changed)
        # self.git_notifications_row.connect("notify::active", self._on_setting_changed)
        # self.check_remote_row.connect("notify::active", self._on_setting_changed)

        # Security signal connections
        self.lock_on_idle_row.connect("notify::active", self._on_setting_changed)
        self.idle_timeout_row.connect("notify::value", self._on_setting_changed)
        self.lock_on_screen_lock_row.connect("notify::active", self._on_setting_changed)
        self.master_password_timeout_row.connect("notify::value", self._on_setting_changed)
        self.clear_memory_row.connect("notify::active", self._on_setting_changed)
        self.require_master_for_export_row.connect("notify::active", self._on_setting_changed)
        self.max_failed_attempts_row.connect("notify::value", self._on_setting_changed)
        self.lockout_duration_row.connect("notify::value", self._on_setting_changed)
    
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
        self.lock_on_idle_row.set_active(self.config.security.lock_on_idle)
        self.idle_timeout_row.set_value(self.config.security.idle_timeout_minutes)
        self.lock_on_screen_lock_row.set_active(self.config.security.lock_on_screen_lock)
        self.master_password_timeout_row.set_value(self.config.security.master_password_timeout_minutes)
        self.clear_memory_row.set_active(self.config.security.clear_memory_on_lock)
        self.require_master_for_export_row.set_active(self.config.security.require_master_password_for_export)
        self.max_failed_attempts_row.set_value(self.config.security.max_failed_unlock_attempts)
        self.lockout_duration_row.set_value(self.config.security.lockout_duration_minutes)
        
        # Search settings
        self.case_sensitive_row.set_active(self.config.search.case_sensitive)
        self.search_content_row.set_active(self.config.search.search_in_content)
        self.search_filenames_row.set_active(self.config.search.search_in_filenames)
        self.max_results_row.set_value(self.config.search.max_search_results)

        # Git settings disabled for v0.8.6
        # self.auto_pull_row.set_active(self.config.git.auto_pull_on_startup)
        # self.auto_push_row.set_active(self.config.git.auto_push_on_changes)
        # self.show_git_status_row.set_active(self.config.git.show_git_status)
        # self.git_timeout_row.set_value(self.config.git.git_timeout_seconds)
        # self.auto_commit_row.set_active(self.config.git.auto_commit_on_changes)
        # self.git_notifications_row.set_active(self.config.git.show_git_notifications)
        # self.check_remote_row.set_active(self.config.git.check_remote_on_startup)
    
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
        self.config.security.lock_on_idle = self.lock_on_idle_row.get_active()
        self.config.security.idle_timeout_minutes = int(self.idle_timeout_row.get_value())
        self.config.security.lock_on_screen_lock = self.lock_on_screen_lock_row.get_active()
        self.config.security.master_password_timeout_minutes = int(self.master_password_timeout_row.get_value())
        self.config.security.clear_memory_on_lock = self.clear_memory_row.get_active()
        self.config.security.require_master_password_for_export = self.require_master_for_export_row.get_active()
        self.config.security.max_failed_unlock_attempts = int(self.max_failed_attempts_row.get_value())
        self.config.security.lockout_duration_minutes = int(self.lockout_duration_row.get_value())

        # Search settings
        self.config.search.case_sensitive = self.case_sensitive_row.get_active()
        self.config.search.search_in_content = self.search_content_row.get_active()
        self.config.search.search_in_filenames = self.search_filenames_row.get_active()
        self.config.search.max_search_results = int(self.max_results_row.get_value())

        # Git settings disabled for v0.8.6
        # self.config.git.auto_pull_on_startup = self.auto_pull_row.get_active()
        # self.config.git.auto_push_on_changes = self.auto_push_row.get_active()
        # self.config.git.show_git_status = self.show_git_status_row.get_active()
        # self.config.git.git_timeout_seconds = int(self.git_timeout_row.get_value())
        # self.config.git.auto_commit_on_changes = self.auto_commit_row.get_active()
        # self.config.git.show_git_notifications = self.git_notifications_row.get_active()
        # self.config.git.check_remote_on_startup = self.check_remote_row.get_active()
    
    def _save_settings(self):
        """Save settings to file."""
        self.config_manager.save_config(self.config)

    def _setup_dialog_behavior(self):
        """Set up keyboard navigation and focus management."""
        # Set up keyboard navigation
        DialogManager.setup_dialog_keyboard_navigation(self)

        # Center dialog on parent
        DialogManager.center_dialog_on_parent(self)

    # Git dialog methods disabled for v0.8.6
    # def _on_git_setup_clicked(self, button):
    #     """Handle Git setup button click."""
    #     from ..dialogs.git_setup_dialog import GitSetupDialog

    #     # Get the main window from the parent chain
    #     parent = self.get_transient_for()
    #     if parent and hasattr(parent, 'password_store'):
    #         dialog = GitSetupDialog(
    #             store_dir=parent.password_store.store_dir,
    #             config_manager=parent.config_manager,
    #             toast_manager=parent.toast_manager,
    #             transient_for=parent
    #         )
    #         dialog.connect("setup-completed", self._on_git_setup_completed)
    #         dialog.present()

    # def _on_git_status_clicked(self, button):
    #     """Handle Git status button click."""
    #     from ..dialogs.git_status_dialog import GitStatusDialog

    #     # Get the main window from the parent chain
    #     parent = self.get_transient_for()
    #     if parent and hasattr(parent, 'git_manager'):
    #         dialog = GitStatusDialog(
    #             git_manager=parent.git_manager,
    #             transient_for=parent
    #         )
    #         dialog.present()

    # def _on_git_setup_completed(self, dialog):
    #     """Handle Git setup completion."""
    #     # Refresh the current settings to reflect any changes
    #     self._load_current_settings()
