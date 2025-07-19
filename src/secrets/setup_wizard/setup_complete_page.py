"""
Setup Complete page for the setup wizard.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject

from ..app_info import APP_ID


@Gtk.Template(resource_path="/io/github/tobagin/secrets/ui/setup/setup_complete_page.ui")
class SetupCompletePage(Adw.NavigationPage):
    """Page shown when setup is complete."""
    
    __gtype_name__ = 'SetupCompletePage'
    
    # Template widgets
    toolbar_view = Gtk.Template.Child()
    success_box = Gtk.Template.Child()
    success_icon = Gtk.Template.Child()
    success_title = Gtk.Template.Child()
    success_desc = Gtk.Template.Child()
    bottom_bar = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'close-wizard': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, wizard=None, **kwargs):
        super().__init__(**kwargs)
        self.wizard = wizard
        self._connect_signals()

    def _connect_signals(self):
        """Connect widget signals."""
        if self.start_button:
            self.start_button.connect("clicked", self._on_start_clicked)

    def _on_start_clicked(self, button):
        """Handle start button click - close the wizard."""
        if self.wizard:
            self.wizard.complete_setup()
        else:
            self.emit('close-wizard')
    
    def set_completion_message(self, title="Setup Complete!", description="Your password manager is now ready to use."):
        """Set custom completion message."""
        self.success_title.set_text(title)
        self.success_desc.set_text(description)
    
    def set_completion_icon(self, icon_name="io.github.tobagin.secrets-verified-symbolic"):
        """Set custom completion icon."""
        self.success_icon.set_from_icon_name(icon_name)
