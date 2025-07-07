#!/usr/bin/env python3
"""
Test script to launch the Preferences Dialog with all enabled settings.

This tests the newly enabled security, compliance, search, and Git settings.
"""

import sys
import os

# Get the absolute path to the project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)

# Remove any conflicting secrets module from path
if 'secrets' in sys.modules:
    del sys.modules['secrets']

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio

# Import required modules
from secrets.config import ConfigManager
from secrets.ui.dialogs.preferences_dialog import PreferencesDialog

class TestPreferencesApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.tobagin.secrets.preferences_test")
        
    def do_activate(self):
        # Create a simple main window
        self.main_window = Adw.ApplicationWindow(application=self)
        self.main_window.set_title("Preferences Dialog Test")
        self.main_window.set_default_size(400, 300)
        
        # Create config manager
        self.config_manager = ConfigManager()
        
        # Create content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)
        
        # Add title
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Preferences Dialog Test</span>")
        content.append(title)
        
        # Add description
        description = Gtk.Label()
        description.set_text("Test the enhanced preferences dialog with all settings enabled:")
        content.append(description)
        
        # Add feature list
        features_label = Gtk.Label()
        features_text = """
• General Settings (Theme, Window)
• Security Settings (Auto-lock, Timeouts, Memory clearing)
• Compliance Settings (HIPAA, PCI DSS, GDPR, RBAC, Audit)
• Search Settings (Case sensitivity, Content search, Limits)
• Git Settings (Automation, Status, Repository management)
        """
        features_label.set_text(features_text)
        features_label.set_halign(Gtk.Align.START)
        content.append(features_label)
        
        # Add launch button
        launch_button = Gtk.Button(label="Open Preferences Dialog")
        launch_button.add_css_class("suggested-action")
        launch_button.connect("clicked", self.on_launch_clicked)
        content.append(launch_button)
        
        # Add status info
        status_label = Gtk.Label()
        config = self.config_manager.get_config()
        status_text = f"""Current Settings Summary:
• Theme: {config.ui.theme}
• Remember Window: {'Yes' if config.ui.remember_window_state else 'No'}
• Auto-hide Passwords: {'Yes' if config.security.auto_hide_passwords else 'No'}
• HIPAA: {'Enabled' if config.compliance.hipaa_enabled else 'Disabled'}
• PCI DSS: {'Enabled' if config.compliance.pci_dss_enabled else 'Disabled'}
• GDPR: {'Enabled' if config.compliance.gdpr_enabled else 'Disabled'}
• Case Sensitive Search: {'Yes' if config.search.case_sensitive else 'No'}
• Git Auto-pull: {'Yes' if config.git.auto_pull_on_startup else 'No'}"""
        status_label.set_text(status_text)
        status_label.set_halign(Gtk.Align.START)
        content.append(status_label)
        
        self.main_window.set_content(content)
        self.main_window.present()
        
    def on_launch_clicked(self, button):
        try:
            # Create and show preferences dialog
            dialog = PreferencesDialog(
                parent_window=self.main_window,
                config_manager=self.config_manager
            )
            dialog.present()
        except Exception as e:
            print(f"Error opening preferences dialog: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = TestPreferencesApp()
    app.run(sys.argv)