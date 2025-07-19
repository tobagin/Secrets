"""Compliance dashboard dialog for managing regulatory compliance."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


@Gtk.Template(resource_path='/io/github/tobagin/secrets/ui/dialogs/compliance_dashboard_dialog.ui')
class ComplianceDashboardDialog(Adw.Window):
    """Dialog for managing compliance frameworks and settings."""
    
    __gtype_name__ = "ComplianceDashboardDialog"
    
    # Template widgets
    main_box = Gtk.Template.Child()
    header_label = Gtk.Template.Child()
    status_label = Gtk.Template.Child()
    close_button = Gtk.Template.Child()
    
    def __init__(self, parent_window=None, config_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_window = parent_window
        self.config_manager = config_manager
        
        self.set_transient_for(parent_window)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        # Update status info based on config
        if self.config_manager and hasattr(self.config_manager, 'compliance'):
            config = self.config_manager.compliance
            status_text = f"""Current Compliance Status:
• HIPAA: {'Enabled' if config.hipaa_enabled else 'Disabled'}
• PCI DSS: {'Enabled' if config.pci_dss_enabled else 'Disabled'}
• GDPR: {'Enabled' if config.gdpr_enabled else 'Disabled'}
• RBAC: {'Enabled' if config.rbac_enabled else 'Disabled'}
• Audit: {'Enabled' if config.audit_enabled else 'Disabled'}"""
            self.status_label.set_label(status_text)
    
    def _connect_signals(self):
        """Connect signal handlers."""
        self.close_button.connect("clicked", self._on_close)
        
    def _on_close(self, button):
        """Handle close button click."""
        self.close()