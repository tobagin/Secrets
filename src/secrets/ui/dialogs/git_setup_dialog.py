"""
Git setup dialog for configuring Git repository and remote connections.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GLib
import threading
from typing import Optional

from ...app_info import APP_ID
from ...managers.git_manager import GitManager, GitPlatformManager
from ...config import ConfigManager
from ...managers.toast_manager import ToastManager


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/dialogs/git_setup_dialog.ui')
class GitSetupDialog(Adw.Window):
    """Dialog for setting up Git repository and remote connections."""
    
    __gtype_name__ = "GitSetupDialog"
    
    # Signals
    __gsignals__ = {
        'setup-completed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    # Template widgets
    welcome_banner = Gtk.Template.Child()
    status_row = Gtk.Template.Child()
    status_icon = Gtk.Template.Child()
    git_status_row = Gtk.Template.Child()
    git_check_spinner = Gtk.Template.Child()
    platform_combo = Gtk.Template.Child()
    remote_url_row = Gtk.Template.Child()
    repo_name_entry = Gtk.Template.Child()
    platform_group = Gtk.Template.Child()
    username_row = Gtk.Template.Child()
    token_row = Gtk.Template.Child()
    token_help_button = Gtk.Template.Child()
    repo_options_group = Gtk.Template.Child()
    private_repo_switch = Gtk.Template.Child()
    auto_sync_switch = Gtk.Template.Child()
    progress_group = Gtk.Template.Child()
    progress_row = Gtk.Template.Child()
    progress_spinner = Gtk.Template.Child()
    test_button = Gtk.Template.Child()
    setup_button = Gtk.Template.Child()
    
    def __init__(self, store_dir: str, config_manager: ConfigManager, 
                 toast_manager: ToastManager, **kwargs):
        super().__init__(**kwargs)
        
        self.store_dir = store_dir
        self.config_manager = config_manager
        self.toast_manager = toast_manager
        self.git_manager = GitManager(store_dir, config_manager, toast_manager)
        self.platform_manager = GitPlatformManager(config_manager)
        
        self._setup_platforms()
        self._check_git_availability()
        self._load_current_settings()
        self._setup_signals()
    
    def _setup_platforms(self):
        """Set up Git platform options."""
        if self.platform_combo is None:
            print("Warning: platform_combo widget not found in template")
            return
            
        platforms = Gtk.StringList()
        platforms.append("Select a platform...")
        platforms.append("GitHub")
        platforms.append("GitLab")
        platforms.append("Codeberg")
        platforms.append("BitBucket")
        platforms.append("Custom Git Server")
        
        self.platform_combo.set_model(platforms)
        self.platform_combo.set_selected(0)
    
    def _check_git_availability(self):
        """Check if Git is available on the system."""
        def check_git():
            try:
                import subprocess
                result = subprocess.run(['git', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0, result.stdout.strip()
            except Exception as e:
                return False, str(e)
        
        def on_git_check_complete(success, message):
            GLib.idle_add(self._update_git_status, success, message)
        
        # Run git check in thread to avoid blocking UI
        threading.Thread(target=lambda: on_git_check_complete(*check_git()), daemon=True).start()
    
    def _update_git_status(self, success, message):
        """Update Git status in UI."""
        self.git_check_spinner.set_spinning(False)
        
        if success:
            self.git_status_row.set_subtitle(f"Git is available ({message})")
            # Replace spinner with success icon
            icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            self.git_status_row.remove(self.git_check_spinner)
            self.git_status_row.add_suffix(icon)
        else:
            self.git_status_row.set_subtitle("Git is not installed or not available")
            # Replace spinner with error icon
            icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
            self.git_status_row.remove(self.git_check_spinner)
            self.git_status_row.add_suffix(icon)
    
    def _setup_signals(self):
        """Setup additional signal connections."""
        self.token_help_button.connect("clicked", self._on_token_help_clicked)
        
        # Connect all signals manually since template callbacks aren't working
        if hasattr(self, 'platform_combo') and self.platform_combo:
            self.platform_combo.connect("notify::selected", self._on_platform_changed)
        
        if hasattr(self, 'remote_url_row') and self.remote_url_row:
            self.remote_url_row.connect("changed", self._on_url_changed)
            
        if hasattr(self, 'test_button') and self.test_button:
            self.test_button.connect("clicked", self._on_test_connection)
            
        if hasattr(self, 'setup_button') and self.setup_button:
            self.setup_button.connect("clicked", self._on_setup_repository)
        
        # Connect cancel button
        cancel_button = self.get_template_child(GitSetupDialog, "cancel_button")
        if cancel_button:
            cancel_button.connect("clicked", self._on_cancel_clicked)
    
    
    def _on_platform_changed(self, combo_row, param):
        """Handle platform selection change."""
        selected = combo_row.get_selected()
        
        if selected == 0:  # "Select a platform..."
            self.platform_group.set_visible(False)
            self.repo_options_group.set_visible(False)
            self.remote_url_row.set_text("https://")
            return
        
        platform_urls = {
            1: "https://github.com/username/passwords.git",  # GitHub
            2: "https://gitlab.com/username/passwords.git",  # GitLab
            3: "https://codeberg.org/username/passwords.git",  # Codeberg
            4: "https://bitbucket.org/username/passwords.git",  # BitBucket
            5: "https://git.example.com/username/passwords.git"  # Custom
        }
        
        if selected in platform_urls:
            self.remote_url_row.set_text(platform_urls[selected])
            self.platform_group.set_visible(True)
            self.repo_options_group.set_visible(True)
            self._validate_form()
    
    def _on_token_help_clicked(self, button):
        """Show help for creating access tokens."""
        selected = self.platform_combo.get_selected()
        
        help_urls = {
            1: "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token",
            2: "https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html",
            3: "https://docs.codeberg.org/advanced/access-token/",
            4: "https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/",
            5: "Check your Git server documentation for creating access tokens"
        }
        
        if selected in help_urls:
            message = f"Create an access token at:\n{help_urls[selected]}"
            self.toast_manager.show_info(message)
    
    def _validate_form(self):
        """Validate form inputs and enable/disable buttons."""
        url = self.remote_url_row.get_text().strip()
        username = self.username_row.get_text().strip()
        token = self.token_row.get_text().strip()
        
        # Basic validation
        url_valid = url and url.startswith(('http://', 'https://')) and len(url) > 10
        auth_valid = username and token
        
        # Enable test button if URL is valid
        self.test_button.set_sensitive(url_valid)
        
        # Enable setup button if URL and auth are valid
        self.setup_button.set_sensitive(url_valid and auth_valid)
    
    def _load_current_settings(self):
        """Load current Git settings."""
        status = self.git_manager.get_status()
        config = self.config_manager.get_config()
        
        # Update status display
        if status.is_repo:
            if status.has_remote:
                self.status_row.set_subtitle(f"Repository with remote: {status.remote_url}")
                self.status_icon.set_from_icon_name("emblem-ok-symbolic")
            else:
                self.status_row.set_subtitle("Local repository (no remote)")
                self.status_icon.set_from_icon_name("dialog-warning-symbolic")
        else:
            self.status_row.set_subtitle("No Git repository")
            self.status_icon.set_from_icon_name("dialog-error-symbolic")
        
        # Load existing remote URL
        if config.git.remote_url:
            self.remote_url_row.set_text(config.git.remote_url)
            self._update_ui_for_url(config.git.remote_url)
        
        # Load platform settings
        if config.git.platform_username:
            self.username_row.set_text(config.git.platform_username)
    
    def _on_cancel_clicked(self, button):
        """Handle cancel button click."""
        self.close()
    
    def _on_repo_type_changed(self, combo_row, param):
        """Handle repository type selection change."""
        selected = combo_row.get_selected()
        
        if selected == 0:  # Local only
            self.remote_url_row.set_visible(False)
            self.platform_group.set_visible(False)
            self.repo_info_group.set_visible(False)
            self.setup_button.set_sensitive(True)
        else:
            self.remote_url_row.set_visible(True)
            self._update_ui_for_selection(selected)
    
    def _update_ui_for_selection(self, selected: int):
        """Update UI based on repository type selection."""
        if selected == 1:  # GitHub
            self.remote_url_row.set_text("")
            self.platform_group.set_visible(True)
            self.token_row.set_text("")
        elif selected == 2:  # GitLab
            self.remote_url_row.set_text("")
            self.platform_group.set_visible(True)
            self.token_row.set_text("")
        elif selected == 3:  # Custom
            self.remote_url_row.set_text("")
            self.platform_group.set_visible(False)

        self.repo_info_group.set_visible(False)
    
    def _on_url_changed(self, entry_row):
        """Handle URL change."""
        self._validate_form()
    
    def _update_ui_for_url(self, url: str):
        """Update UI based on URL."""
        if url:
            valid, message = self.platform_manager.validate_repository_url(url)
            self.test_button.set_sensitive(valid)
            self.setup_button.set_sensitive(valid)
            
            if valid:
                platform_info = self.platform_manager.get_platform_info(url)
                if platform_info['type'] in ['github', 'gitlab']:
                    self.platform_group.set_visible(True)
        else:
            self.test_button.set_sensitive(False)
            self.setup_button.set_sensitive(False)
    
    def _on_test_connection(self, button):
        """Test the repository connection."""
        url = self.remote_url_row.get_text().strip()
        token = self.token_row.get_text().strip() if self.token_row.get_visible() else None
        
        button.set_sensitive(False)
        button.set_label("Testing...")
        
        def test_worker():
            try:
                repo_info = self.platform_manager.get_repository_info(url, token)
                GLib.idle_add(self._on_test_complete, repo_info, button)
            except Exception as e:
                GLib.idle_add(self._on_test_complete, {'error': str(e)}, button)
        
        threading.Thread(target=test_worker, daemon=True).start()
    
    def _on_test_complete(self, repo_info: dict, button: Gtk.Button):
        """Handle test completion."""
        button.set_sensitive(True)
        button.set_label("Test Connection")
        
        if 'error' in repo_info:
            self.toast_manager.show_error(f"Connection test failed: {repo_info['error']}")
            self.repo_info_group.set_visible(False)
        else:
            self.toast_manager.show_success("Connection test successful")
            
            # Update repository info display
            self.repo_name_row.set_subtitle(repo_info.get('name', 'Unknown'))
            self.repo_desc_row.set_subtitle(repo_info.get('description', 'No description'))
            self.repo_info_group.set_visible(True)
    
    def _on_setup_repository(self, button):
        """Set up the repository."""
        selected = self.repo_type_row.get_selected()
        url = self.remote_url_row.get_text().strip() if selected > 0 else None
        
        button.set_sensitive(False)
        button.set_label("Setting up...")
        
        def setup_worker():
            try:
                success, message = self.git_manager.setup_repository(url, init_if_needed=True)
                GLib.idle_add(self._on_setup_complete, success, message, button)
            except Exception as e:
                GLib.idle_add(self._on_setup_complete, False, str(e), button)
        
        threading.Thread(target=setup_worker, daemon=True).start()
    
    def _on_setup_complete(self, success: bool, message: str, button: Gtk.Button):
        """Handle setup completion."""
        button.set_sensitive(True)
        button.set_label("Setup Repository")
        
        if success:
            # Save platform settings
            username = self.username_row.get_text().strip()
            token = self.token_row.get_text().strip()
            
            if username or token:
                config = self.config_manager.get_config()
                config.git.platform_username = username
                config.git.platform_token = token  # Note: In production, this should be encrypted
                self.config_manager.save_config(config)
            
            self.toast_manager.show_success(message)
            self.emit('setup-completed')
            self.close()
        else:
            self.toast_manager.show_error(f"Setup failed: {message}")