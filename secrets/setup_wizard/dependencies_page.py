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


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/setup/dependencies_page.ui')
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
        'create-directory-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'create-gpg-key-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    # Template widgets (only the ones we need)
    dependencies_listbox = Gtk.Template.Child()
    store_dir_status_row = Gtk.Template.Child()
    gpg_key_status_row = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    # Template buttons (only the ones we need)
    dir_create_button = Gtk.Template.Child()
    gpg_key_create_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize components
        self.password_store = PasswordStore()

        # Store the created GPG key ID for later use
        self.created_gpg_key_id = None

        # Connect signals
        self._connect_signals()

        # Check dependencies on initialization
        self._check_dependencies()

    def _connect_signals(self):
        """Connect widget signals."""
        # Connect signals only after ensuring widgets are properly loaded
        if self.continue_button:
            self.continue_button.connect("clicked", self._on_continue_clicked)
        if self.dir_create_button:
            self.dir_create_button.connect("clicked", self._on_create_directory_clicked)
        if self.gpg_key_create_button:
            self.gpg_key_create_button.connect("clicked", self._on_create_gpg_key_clicked)

    def _check_dependencies(self):
        """Check dependencies and update UI with proper dependency ordering."""
        # Since we're running in Flatpak with bundled pass/gpg, we only need to check:
        # 1. GPG keys exist
        # 2. Password store is initialized

        # Check for GPG keys
        try:
            result = subprocess.run(['gpg', '--batch', '--list-secret-keys', '--with-colons'],
                                  capture_output=True, text=True, timeout=3)
            has_gpg_keys = result.returncode == 0 and result.stdout.strip()
        except:
            has_gpg_keys = False

        # Check if password store is initialized (has .gpg-id file)
        store_dir_exists = os.path.exists(os.path.expanduser("~/.password-store"))
        store_initialized = False
        if store_dir_exists:
            gpg_id_file = os.path.join(os.path.expanduser("~/.password-store"), ".gpg-id")
            store_initialized = os.path.exists(gpg_id_file)

        # Update status rows (only the ones we have)
        self._update_status_row(self.gpg_key_status_row, has_gpg_keys)
        self._update_status_row(self.store_dir_status_row, store_initialized)

        # Update button states
        self._update_button_states(has_gpg_keys, store_initialized)

        # Enable continue button only when everything is ready
        all_ready = has_gpg_keys and store_initialized
        if self.continue_button:
            self.continue_button.set_sensitive(all_ready)
            if all_ready:
                self.continue_button.set_label("Finish Setup")
            else:
                self.continue_button.set_label("Continue")



    def _update_status_row(self, row, is_installed):
        """Update a status row with installation status."""
        if not row:
            return

        # CSS styling will be handled in UI files

        if is_installed:
            # Set icon and styling for success
            try:
                row.set_icon_name("checkmark-symbolic")
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

    def _update_button_states(self, has_gpg_keys, store_initialized):
        """Update button states based on dependency requirements."""

        # GPG Key Create Button: Show only if no GPG keys exist, always enabled since pass/gpg are bundled
        if self.gpg_key_create_button:
            self.gpg_key_create_button.set_visible(not has_gpg_keys)
            self.gpg_key_create_button.set_sensitive(not has_gpg_keys)

        # Directory Create Button: Enable only if GPG key exists
        if self.dir_create_button:
            self.dir_create_button.set_visible(not store_initialized)
            # Enable only if we have GPG keys but store is not initialized
            self.dir_create_button.set_sensitive(has_gpg_keys and not store_initialized)

    def recheck_dependencies(self):
        """Public method to recheck dependencies (called from wizard)."""
        self._check_dependencies()

    def set_created_gpg_key_id(self, gpg_key_id):
        """Store the GPG key ID that was created for later use in store initialization."""
        self.created_gpg_key_id = gpg_key_id
        # Recheck dependencies to update button states
        self._check_dependencies()

    # Event handlers
    def _on_continue_clicked(self, _button):
        """Handle continue button click."""
        self.emit("continue-requested")



    def _on_create_directory_clicked(self, button):
        """Handle create directory button click and initialize password store."""
        button.set_sensitive(False)
        button.set_label("Creating...")

        try:
            store_dir = os.path.expanduser("~/.password-store")
            os.makedirs(store_dir, exist_ok=True)

            # Initialize the password store with the created GPG key
            if self.created_gpg_key_id:
                button.set_label("Initializing...")
                success, message = self.password_store.init_store(self.created_gpg_key_id)
                if success:
                    button.set_label("Completed")
                    # Show success and recheck dependencies
                    GLib.timeout_add_seconds(1, self._recheck_after_directory_creation)
                else:
                    # Show error and restore button
                    button.set_sensitive(True)
                    button.set_label("Retry")
                    print(f"Failed to initialize password store: {message}")
            else:
                # No GPG key ID available - this shouldn't happen with proper dependency logic
                button.set_sensitive(True)
                button.set_label("Create")
                print("No GPG key ID available for initialization")

        except Exception as e:
            # Show error and restore button
            button.set_sensitive(True)
            button.set_label("Create")
            print(f"Error creating directory: {e}")

    def _on_create_gpg_key_clicked(self, _button):
        """Handle create GPG key button click."""
        self.emit("create-gpg-key-requested")

    def _recheck_after_directory_creation(self):
        """Recheck dependencies after directory creation."""
        self._check_dependencies()
        return False  # Don't repeat timeout
