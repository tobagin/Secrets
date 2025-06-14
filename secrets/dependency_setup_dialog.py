"""
Dependency Setup Dialog for the Secrets application.
Handles installation of pass and GPG across different Linux distributions.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
import subprocess
import threading
from .system_setup_helper import SystemSetupHelper
from .gpg_setup_helper import GPGSetupHelper


class DependencySetupDialog(Adw.Window):
    """Dialog to help users install pass and GPG dependencies."""
    
    __gtype_name__ = "DependencySetupDialog"
    
    def __init__(self, parent_window=None, missing_deps=None, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("Install Required Dependencies")
        self.set_default_size(600, 700)
        self.set_modal(True)
        
        if parent_window:
            self.set_transient_for(parent_window)
        
        self.missing_deps = missing_deps or []
        self.system_status = SystemSetupHelper.get_system_status()
        self.setup_helper = GPGSetupHelper()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Adw.WindowTitle(title="Install Dependencies"))
        main_box.append(header_bar)
        
        # Toast overlay for messages
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)
        
        # Scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.toast_overlay.set_child(scrolled)
        
        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        scrolled.set_child(content_box)
        
        # Status page for explanation
        self._add_status_page(content_box)
        
        # System information
        self._add_system_info(content_box)
        
        # Installation options
        self._add_installation_options(content_box)
        
        # Manual instructions (if needed)
        if not self.system_status['distro_supported']:
            self._add_manual_instructions(content_box)
    
    def _add_status_page(self, container):
        """Add status page explaining what's needed."""
        status_page = Adw.StatusPage()
        status_page.set_icon_name("system-software-install-symbolic")
        
        missing_items = []
        if 'pass' in self.missing_deps:
            missing_items.append("pass (password manager)")
        if 'gpg' in self.missing_deps:
            missing_items.append("GPG (encryption)")
        
        title = f"Missing Dependencies: {', '.join(missing_items)}"
        description = "Install required software to use the password manager."
        
        status_page.set_title(title)
        status_page.set_description(description)
        container.append(status_page)
    
    def _add_system_info(self, container):
        """Add system information group."""
        info_group = Adw.PreferencesGroup()
        info_group.set_title("System Information")
        container.append(info_group)
        
        # Operating system
        os_row = Adw.ActionRow()
        os_row.set_title("Operating System")
        os_row.set_subtitle(f"{self.system_status['os']}")
        info_group.add(os_row)
        
        # Distribution
        if self.system_status['distro']:
            distro = self.system_status['distro']
            distro_row = Adw.ActionRow()
            distro_row.set_title("Distribution")
            distro_row.set_subtitle(f"{distro.name} {distro.version}")
            info_group.add(distro_row)
            
            # Package manager
            pm_row = Adw.ActionRow()
            pm_row.set_title("Package Manager")
            pm_row.set_subtitle(distro.package_manager)
            info_group.add(pm_row)
        
        # Current status
        status_row = Adw.ActionRow()
        status_row.set_title("Current Status")
        
        status_parts = []
        if self.system_status['pass_installed']:
            status_parts.append("✅ pass installed")
        else:
            status_parts.append("❌ pass missing")
        
        if self.system_status['gpg_installed']:
            status_parts.append("✅ GPG installed")
        else:
            status_parts.append("❌ GPG missing")
        
        status_row.set_subtitle(" | ".join(status_parts))
        info_group.add(status_row)
    
    def _add_installation_options(self, container):
        """Add installation options."""
        if not self.system_status['can_install']:
            return
        
        install_group = Adw.PreferencesGroup()
        install_group.set_title("Installation Options")
        container.append(install_group)
        
        # Automatic installation (recommended)
        auto_row = Adw.ActionRow()
        auto_row.set_title("Automatic Installation (Recommended)")
        auto_row.set_subtitle("Install dependencies automatically")
        
        auto_button = Gtk.Button(label="Install Now")
        auto_button.set_valign(Gtk.Align.CENTER)
        auto_button.add_css_class("suggested-action")
        auto_button.connect("clicked", self._on_auto_install_clicked)
        auto_row.add_suffix(auto_button)
        install_group.add(auto_row)
        
        # Show commands
        commands_row = Adw.ActionRow()
        commands_row.set_title("Show Installation Commands")
        commands_row.set_subtitle("View the commands that will be executed")
        
        show_commands_button = Gtk.Button(label="Show Commands")
        show_commands_button.set_valign(Gtk.Align.CENTER)
        show_commands_button.connect("clicked", self._on_show_commands_clicked)
        commands_row.add_suffix(show_commands_button)
        install_group.add(commands_row)
        
        # Skip installation
        skip_row = Adw.ActionRow()
        skip_row.set_title("Skip Installation")
        skip_row.set_subtitle("Continue with limited functionality")
        
        skip_button = Gtk.Button(label="Skip")
        skip_button.set_valign(Gtk.Align.CENTER)
        skip_button.connect("clicked", self._on_skip_clicked)
        skip_row.add_suffix(skip_button)
        install_group.add(skip_row)
    
    def _add_manual_instructions(self, container):
        """Add manual installation instructions for unsupported systems."""
        manual_group = Adw.PreferencesGroup()
        manual_group.set_title("Manual Installation Required")
        container.append(manual_group)

        # Use shorter instructions to prevent GTK measurement warnings
        short_instructions = "Install 'pass' and 'gnupg' packages manually using your package manager"

        instructions_row = Adw.ActionRow()
        instructions_row.set_title("Installation Instructions")
        instructions_row.set_subtitle(short_instructions)
        manual_group.add(instructions_row)
    
    def _on_auto_install_clicked(self, button):
        """Handle automatic installation."""
        if not self.system_status['can_install']:
            self.toast_overlay.add_toast(Adw.Toast.new("Automatic installation not available"))
            return
        
        # Disable button during installation
        button.set_sensitive(False)
        button.set_label("Installing...")
        
        # Start installation in background thread
        def install_packages():
            try:
                commands = self.system_status['installation_commands']
                
                # Update package database if needed
                if 'update' in commands:
                    GLib.idle_add(self._update_status, "Updating package database...")
                    result = subprocess.run(commands['update'], shell=True, 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode != 0:
                        GLib.idle_add(self._installation_failed, 
                                    f"Failed to update package database: {result.stderr}")
                        return
                
                # Install packages
                GLib.idle_add(self._update_status, "Installing dependencies...")
                result = subprocess.run(commands['install_both'], shell=True,
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    GLib.idle_add(self._installation_succeeded)
                else:
                    GLib.idle_add(self._installation_failed, 
                                f"Installation failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                GLib.idle_add(self._installation_failed, "Installation timed out")
            except Exception as e:
                GLib.idle_add(self._installation_failed, f"Installation error: {e}")
        
        thread = threading.Thread(target=install_packages)
        thread.daemon = True
        thread.start()
    
    def _update_status(self, message):
        """Update status message during installation."""
        self.toast_overlay.add_toast(Adw.Toast.new(message))
    
    def _installation_succeeded(self):
        """Handle successful installation."""
        self.toast_overlay.add_toast(Adw.Toast.new("Dependencies installed successfully!"))
        
        # Close dialog after a short delay
        GLib.timeout_add_seconds(2, self._close_and_continue)
    
    def _installation_failed(self, error_message):
        """Handle failed installation."""
        self.toast_overlay.add_toast(Adw.Toast.new(f"Installation failed: {error_message}"))
        
        # Re-enable the install button
        # Note: This is simplified - in a real implementation you'd need to track the button reference
    
    def _close_and_continue(self):
        """Close dialog and signal to continue setup."""
        self.emit("dependencies-installed")
        self.close()
        return False
    
    def _on_show_commands_clicked(self, button):
        """Show the installation commands that would be executed."""
        from .ui_utils import DialogManager

        commands = self.system_status['installation_commands']

        commands_text = "The following commands will be executed:\n\n"
        if 'update' in commands:
            commands_text += f"1. Update package database:\n   {commands['update']}\n\n"
        commands_text += f"2. Install dependencies:\n   {commands['install_both']}"

        dialog = DialogManager.create_message_dialog(
            parent=self,
            heading="Installation Commands",
            body=commands_text,
            dialog_type="info",
            default_size=(550, 350)
        )
        # Add response button using the AlertDialog API
        DialogManager.add_dialog_response(dialog, "ok", "_OK", "suggested")
        dialog.connect("response", lambda _d, _r: None)

        # Ensure proper dialog behavior
        DialogManager.setup_dialog_keyboard_navigation(dialog)
        DialogManager.center_dialog_on_parent(dialog, self)

        dialog.present()
    
    def _on_skip_clicked(self, button):
        """Handle skip installation."""
        self.close()


# Add custom signal
from gi.repository import GObject
GObject.signal_new("dependencies-installed", DependencySetupDialog, 
                   GObject.SignalFlags.RUN_FIRST, None, ())
