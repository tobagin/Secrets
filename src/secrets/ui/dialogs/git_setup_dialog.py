"""
Git setup dialog for configuring Git repository and remote connections.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, GLib
import threading
from typing import Optional

from ...managers.git_manager import GitManager, GitPlatformManager
from ...config import ConfigManager
from ...managers.toast_manager import ToastManager


class GitSetupDialog(Adw.Window):
    """Dialog for setting up Git repository and remote connections."""
    
    __gtype_name__ = "GitSetupDialog"
    
    # Signals
    __gsignals__ = {
        'setup-completed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, store_dir: str, config_manager: ConfigManager, 
                 toast_manager: ToastManager, **kwargs):
        super().__init__(**kwargs)
        
        self.store_dir = store_dir
        self.config_manager = config_manager
        self.toast_manager = toast_manager
        self.git_manager = GitManager(store_dir, config_manager, toast_manager)
        self.platform_manager = GitPlatformManager(config_manager)
        
        self.set_title("Git Repository Setup")
        self.set_default_size(600, 500)
        self.set_modal(True)
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Git Setup"))
        main_box.append(header_bar)
        
        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        main_box.append(content_box)
        
        # Status group
        status_group = Adw.PreferencesGroup()
        status_group.set_title("Current Status")
        content_box.append(status_group)
        
        self.status_row = Adw.ActionRow()
        self.status_row.set_title("Repository Status")
        self.status_icon = Gtk.Image()
        self.status_row.add_suffix(self.status_icon)
        status_group.add(self.status_row)
        
        # Repository setup group
        repo_group = Adw.PreferencesGroup()
        repo_group.set_title("Repository Configuration")
        repo_group.set_description("Configure your Git repository and remote connection")
        content_box.append(repo_group)
        
        # Repository type selection
        self.repo_type_row = Adw.ComboRow()
        self.repo_type_row.set_title("Repository Type")
        self.repo_type_row.set_subtitle("Choose how to set up your repository")
        
        repo_types = Gtk.StringList()
        repo_types.append("Initialize new local repository")
        repo_types.append("Connect to existing GitHub repository")
        repo_types.append("Connect to existing GitLab repository")
        repo_types.append("Connect to custom Git repository")
        
        self.repo_type_row.set_model(repo_types)
        self.repo_type_row.connect("notify::selected", self._on_repo_type_changed)
        repo_group.add(self.repo_type_row)
        
        # Remote URL entry
        self.remote_url_row = Adw.EntryRow()
        self.remote_url_row.set_title("Repository URL")
        self.remote_url_row.set_text("")
        self.remote_url_row.connect("changed", self._on_url_changed)
        repo_group.add(self.remote_url_row)
        
        # Platform-specific settings
        self.platform_group = Adw.PreferencesGroup()
        self.platform_group.set_title("Platform Settings")
        self.platform_group.set_visible(False)
        content_box.append(self.platform_group)
        
        # Username entry
        self.username_row = Adw.EntryRow()
        self.username_row.set_title("Username")
        self.username_row.set_text("")
        self.platform_group.add(self.username_row)
        
        # Token entry
        self.token_row = Adw.PasswordEntryRow()
        self.token_row.set_title("Access Token")
        self.token_row.set_text("")
        self.platform_group.add(self.token_row)
        
        # Repository info display
        self.repo_info_group = Adw.PreferencesGroup()
        self.repo_info_group.set_title("Repository Information")
        self.repo_info_group.set_visible(False)
        content_box.append(self.repo_info_group)
        
        self.repo_name_row = Adw.ActionRow()
        self.repo_name_row.set_title("Repository Name")
        self.repo_info_group.add(self.repo_name_row)
        
        self.repo_desc_row = Adw.ActionRow()
        self.repo_desc_row.set_title("Description")
        self.repo_info_group.add(self.repo_desc_row)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        content_box.append(button_box)
        
        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.connect("clicked", lambda w: self.close())
        button_box.append(self.cancel_button)
        
        self.test_button = Gtk.Button(label="Test Connection")
        self.test_button.set_sensitive(False)
        self.test_button.connect("clicked", self._on_test_connection)
        button_box.append(self.test_button)
        
        self.setup_button = Gtk.Button(label="Setup Repository")
        self.setup_button.set_sensitive(False)
        self.setup_button.add_css_class("suggested-action")
        self.setup_button.connect("clicked", self._on_setup_repository)
        button_box.append(self.setup_button)
    
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
        url = entry_row.get_text().strip()
        self._update_ui_for_url(url)
    
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
