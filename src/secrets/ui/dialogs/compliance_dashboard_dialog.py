"""Compliance dashboard dialog for managing regulatory compliance."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class ComplianceDashboardDialog(Adw.Window):
    """Dialog for managing compliance frameworks and settings."""
    
    def __init__(self, parent_window=None, config_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_window = parent_window
        self.config_manager = config_manager
        
        self.set_title("Compliance Dashboard")
        self.set_default_size(600, 400)
        self.set_modal(True)
        self.set_transient_for(parent_window)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Header
        header_label = Gtk.Label(label="Compliance Dashboard")
        header_label.add_css_class("title-1")
        main_box.append(header_label)
        
        # Status info
        if self.config_manager and hasattr(self.config_manager, 'compliance'):
            config = self.config_manager.compliance
            status_text = f"""Current Compliance Status:
• HIPAA: {'Enabled' if config.hipaa_enabled else 'Disabled'}
• PCI DSS: {'Enabled' if config.pci_dss_enabled else 'Disabled'}
• GDPR: {'Enabled' if config.gdpr_enabled else 'Disabled'}
• RBAC: {'Enabled' if config.rbac_enabled else 'Disabled'}
• Audit: {'Enabled' if config.audit_enabled else 'Disabled'}"""
        else:
            status_text = "Compliance configuration not available"
            
        status_label = Gtk.Label(label=status_text)
        status_label.set_wrap(True)
        status_label.set_halign(Gtk.Align.START)
        main_box.append(status_label)
        
        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.add_css_class("suggested-action")
        close_button.connect("clicked", self._on_close)
        main_box.append(close_button)
        
        self.set_content(main_box)
        
    def _on_close(self, button):
        """Handle close button click."""
        self.close()