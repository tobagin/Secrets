"""
Dependencies check page for the setup wizard.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
from ..password_store import PasswordStore
from ..app_info import APP_ID
import os
import subprocess
import shutil


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/data/dependencies_page.ui')
class DependenciesPage(Adw.NavigationPage):
    """
    Dependencies check page that verifies system requirements.
    
    Signals:
        continue-requested: Emitted when user clicks continue and all deps are ready
        install-pass-requested: Emitted when user wants to install pass
        create-directory-requested: Emitted when user wants to create store directory
        create-gpg-key-requested: Emitted when user wants to create GPG key
    """

    __gtype_name__ = "DependenciesPage"

    __gsignals__ = {
        'continue-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'install-pass-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'create-directory-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'create-gpg-key-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    # Template widgets
    pass_status_row = Gtk.Template.Child()
    gpg_status_row = Gtk.Template.Child()
    store_dir_status_row = Gtk.Template.Child()
    gpg_key_status_row = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    # Template buttons
    pass_install_button = Gtk.Template.Child()
    dir_create_button = Gtk.Template.Child()
    gpg_key_create_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize components
        self.password_store = PasswordStore()

        # Connect signals
        self._connect_signals()

        # Check dependencies on initialization
        self._check_dependencies()

    def _connect_signals(self):
        """Connect widget signals."""
        # Connect signals only after ensuring widgets are properly loaded
        if self.continue_button:
            self.continue_button.connect("clicked", self._on_continue_clicked)
        if self.pass_install_button:
            self.pass_status_row.connect("activated", self._on_install_pass_clicked)
        if self.dir_create_button:
            self.store_dir_status_row.connect("activated", self._on_create_directory_clicked)
        if self.gpg_key_create_button:
            self.gpg_key_status_row.connect("activated", self._on_create_gpg_key_clicked)

    def _check_dependencies(self):
        """Check if dependencies are installed and password store directory exists."""
        # Use simple checks to avoid hanging
        pass_installed = shutil.which('pass') is not None
        gpg_installed = shutil.which('gpg') is not None
        store_dir_exists = os.path.exists(os.path.expanduser("~/.password-store"))

        # Check for GPG keys
        try:
            result = subprocess.run(['gpg', '--batch', '--list-secret-keys', '--with-colons'],
                                  capture_output=True, text=True, timeout=3)
            has_gpg_keys = result.returncode == 0 and result.stdout.strip()
        except:
            has_gpg_keys = False

        # Update status rows and show/hide buttons as needed
        self._update_status_row(self.pass_status_row, pass_installed)
        if self.pass_install_button:
            self.pass_install_button.set_visible(not pass_installed)

        self._update_status_row(self.gpg_status_row, gpg_installed)

        self._update_status_row(self.store_dir_status_row, store_dir_exists)
        if self.dir_create_button:
            self.dir_create_button.set_visible(not store_dir_exists)

        self._update_status_row(self.gpg_key_status_row, has_gpg_keys)
        if self.gpg_key_create_button:
            self.gpg_key_create_button.set_visible(not has_gpg_keys)

        # Show continue/finish button only when everything is ready
        all_ready = pass_installed and gpg_installed and store_dir_exists and has_gpg_keys
        if self.continue_button:
            self.continue_button.set_visible(all_ready)

            if all_ready:
                # Check if password store is already initialized
                try:
                    store_initialized = self.password_store.is_initialized()
                    if store_initialized:
                        self.continue_button.set_label("Finish Setup")
                    else:
                        self.continue_button.set_label("Continue")
                except:
                    self.continue_button.set_label("Continue")

                self.continue_button.set_sensitive(True)

    def _update_status_row(self, row, is_installed):
        """Update a status row with installation status."""
        if not row:
            return

        # Clear CSS classes safely
        try:
            row.remove_css_class("success")
            row.remove_css_class("warning")
        except:
            pass  # Classes might not be applied yet

        if is_installed:
            # Set icon and styling for success
            try:
                row.set_icon_name("emblem-ok-symbolic")
                row.add_css_class("success")
            except:
                pass  # Fallback if icon setting fails
        else:
            # Set icon and styling for warning
            try:
                row.set_icon_name("dialog-warning-symbolic")
                row.add_css_class("warning")
            except:
                pass  # Fallback if icon setting fails

    def recheck_dependencies(self):
        """Public method to recheck dependencies (called from wizard)."""
        self._check_dependencies()

    # Event handlers
    def _on_continue_clicked(self, _button):
        """Handle continue button click."""
        self.emit("continue-requested")

    def _on_install_pass_clicked(self, _button):
        """Handle install pass button click."""
        self.emit("install-pass-requested")

    def _on_create_directory_clicked(self, button):
        """Handle create directory button click."""
        button.set_sensitive(False)
        button.set_label("Creating...")

        try:
            store_dir = os.path.expanduser("~/.password-store")
            os.makedirs(store_dir, exist_ok=True)
            
            # Show success and recheck dependencies
            GLib.timeout_add_seconds(1, self._recheck_after_directory_creation)

        except Exception as e:
            # Show error and restore button
            button.set_sensitive(True)
            button.set_label("Create")
            # Could emit an error signal here

    def _on_create_gpg_key_clicked(self, _button):
        """Handle create GPG key button click."""
        self.emit("create-gpg-key-requested")

    def _recheck_after_directory_creation(self):
        """Recheck dependencies after directory creation."""
        self._check_dependencies()
        return False  # Don't repeat timeout
