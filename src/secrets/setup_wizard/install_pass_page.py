"""
Install Pass page for the setup wizard.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
import threading

from ..app_info import APP_ID
from ..utils import SystemSetupHelper


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/setup/install_pass_page.ui")
class InstallPassPage(Adw.NavigationPage):
    """Page for installing Pass and GPG packages."""
    
    __gtype_name__ = 'InstallPassPage'
    
    # Template widgets
    toolbar_view = Gtk.Template.Child()
    status_listbox = Gtk.Template.Child()
    update = Gtk.Template.Child()
    install_pass = Gtk.Template.Child()
    verify = Gtk.Template.Child()
    bottom_bar = Gtk.Template.Child()
    install_button = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'installation-complete': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'installation-cancelled': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.install_button.connect("clicked", self._on_install_clicked)
    
    def _on_install_clicked(self, button):
        """Handle install button click."""
        self._start_installation()
    
    def _start_installation(self):
        """Start the pass installation process."""
        self.install_button.set_sensitive(False)
        self.install_button.set_label("Installing...")

        # Update status rows to show progress
        self.update.set_icon_name("view-refresh-symbolic")
        self.install_pass.set_icon_name("folder-download-symbolic")
        self.verify.set_icon_name("dialog-question-symbolic")
        
        def install_pass():
            try:
                # Get system status and installation commands
                status = SystemSetupHelper.get_system_status()
                
                if not status['distro_supported']:
                    GLib.idle_add(self._on_install_error, 
                                "Unsupported distribution. Please install pass manually.")
                    return
                
                commands = status['installation_commands']
                if not commands:
                    GLib.idle_add(self._on_install_error,
                                "No installation commands available.")
                    return
                
                # Update progress - Step 1: Update
                GLib.idle_add(self._update_step_status, self.update, "in-progress", "Updating package database...")

                # Run update command if available
                if 'update' in commands:
                    result = SystemSetupHelper.run_installation_command(commands['update'])
                    if not result['success']:
                        # For update commands, we can often continue even if they "fail"
                        GLib.idle_add(self._update_step_status, self.update, "warning", "Update completed with warnings")
                    else:
                        GLib.idle_add(self._update_step_status, self.update, "success", "Package database updated successfully")
                else:
                    GLib.idle_add(self._update_step_status, self.update, "success", "No update needed")

                # Update progress - Step 2: Install
                GLib.idle_add(self._update_step_status, self.install_pass, "in-progress", "Installing pass and GPG...")
                
                # Run installation command
                result = SystemSetupHelper.run_installation_command(commands['install_both'])
                if result['success']:
                    GLib.idle_add(self._update_step_status, self.install_pass, "success", "Pass and GPG installed successfully")
                    # Update progress - Step 3: Verify
                    GLib.idle_add(self._update_step_status, self.verify, "in-progress", "Verifying installation...")
                    # Simple verification - check if commands exist
                    import shutil
                    if shutil.which('pass') and shutil.which('gpg'):
                        GLib.idle_add(self._update_step_status, self.verify, "success", "Installation verified successfully")
                        GLib.idle_add(self._on_install_success)
                    else:
                        GLib.idle_add(self._update_step_status, self.verify, "error", "Verification failed")
                        GLib.idle_add(self._on_install_error, "Installation verification failed")
                else:
                    GLib.idle_add(self._update_step_status, self.install_pass, "error", f"Installation failed: {result['error']}")
                    GLib.idle_add(self._on_install_error, f"Installation failed: {result['error']}")
                    
            except Exception as e:
                GLib.idle_add(self._on_install_error, f"Installation error: {str(e)}")
        
        # Start installation in background thread
        thread = threading.Thread(target=install_pass)
        thread.daemon = True
        thread.start()
    
    def _update_step_status(self, row, status, message):
        """Update the status of a step row."""
        if status == "in-progress":
            row.set_icon_name("view-refresh-symbolic")
        elif status == "success":
            row.set_icon_name("checkmark-symbolic")
        elif status == "error":
            row.set_icon_name("dialog-error-symbolic")
        elif status == "warning":
            row.set_icon_name("dialog-warning-symbolic")

        row.set_subtitle(message)

    def _on_install_success(self):
        """Handle successful installation."""
        self.install_button.set_label("Installation Complete")
        self.install_button.set_sensitive(False)

        # Emit completion signal
        self.emit('installation-complete')

    def _on_install_error(self, error_message):
        """Handle installation error."""
        self.install_button.set_sensitive(True)
        self.install_button.set_label("Retry Installation")
    
    def reset_state(self):
        """Reset the page to initial state."""
        self.install_button.set_sensitive(True)
        self.install_button.set_label("Start Installation")

        # Reset all step rows
        self.update.set_icon_name("view-refresh-symbolic")
        self.update.set_subtitle("This will update the packages database on your system")

        self.install_pass.set_icon_name("folder-download-symbolic")
        self.install_pass.set_subtitle("This will install the required packages on your system")

        self.verify.set_icon_name("dialog-question-symbolic")
        self.verify.set_subtitle("This will verify packages were installed on your system")
