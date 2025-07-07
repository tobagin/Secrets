#!/usr/bin/env python3
"""
Test script to launch the Compliance Dashboard directly.

This bypasses the UI component import issue and allows testing the compliance dashboard.
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
from secrets.ui.dialogs.compliance_dashboard_dialog import ComplianceDashboardDialog

class TestApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.tobagin.secrets.test")
        
    def do_activate(self):
        # Create a simple main window
        self.main_window = Adw.ApplicationWindow(application=self)
        self.main_window.set_title("Compliance Dashboard Test")
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
        title.set_markup("<span size='x-large' weight='bold'>Compliance Dashboard Test</span>")
        content.append(title)
        
        # Add launch button
        launch_button = Gtk.Button(label="Open Compliance Dashboard")
        launch_button.add_css_class("suggested-action")
        launch_button.connect("clicked", self.on_launch_clicked)
        content.append(launch_button)
        
        # Add status info
        status_label = Gtk.Label()
        config = self.config_manager.get_config()
        status_text = f"""Current Compliance Status:
• HIPAA: {'Enabled' if config.compliance.hipaa_enabled else 'Disabled'}
• PCI DSS: {'Enabled' if config.compliance.pci_dss_enabled else 'Disabled'}
• GDPR: {'Enabled' if config.compliance.gdpr_enabled else 'Disabled'}
• RBAC: {'Enabled' if config.compliance.rbac_enabled else 'Disabled'}
• Audit: {'Enabled' if config.compliance.audit_enabled else 'Disabled'}"""
        status_label.set_text(status_text)
        content.append(status_label)
        
        self.main_window.set_content(content)
        self.main_window.present()
        
    def on_launch_clicked(self, button):
        try:
            # Create and show compliance dashboard
            dialog = ComplianceDashboardDialog(
                parent_window=self.main_window,
                config_manager=self.config_manager
            )
            dialog.present()
        except Exception as e:
            print(f"Error opening compliance dashboard: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = TestApp()
    app.run(sys.argv)