"""
Create GPG Key page for the setup wizard.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, GObject
import threading

from ..app_info import APP_ID
from ..utils import GPGSetupHelper


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/setup/create_gpg_page.ui')
class CreateGpgPage(Adw.NavigationPage):
    """Page for creating a GPG key."""
    
    __gtype_name__ = 'CreateGpgPage'
    
    # Template widgets
    toolbar_view = Gtk.Template.Child()
    form_listbox = Gtk.Template.Child()
    name_row = Gtk.Template.Child()
    email_row = Gtk.Template.Child()
    passphrase_row = Gtk.Template.Child()
    bottom_bar = Gtk.Template.Child()
    create_button = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'gpg-created': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'creation-cancelled': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.create_button.connect("clicked", self._on_create_clicked)

        # Connect text change signals to validate form
        self.name_row.connect("notify::text", self._on_form_changed)
        self.email_row.connect("notify::text", self._on_form_changed)

        # Initial validation
        self._validate_form()
    
    def _on_create_clicked(self, button):
        """Handle create button click."""
        self._start_gpg_creation()
    
    def _on_form_changed(self, widget, param):
        """Handle form field changes."""
        self._validate_form()
    
    def _validate_form(self):
        """Validate the form and enable/disable create button."""
        name = self.name_row.get_text().strip()
        email = self.email_row.get_text().strip()
        
        # Basic validation
        valid = bool(name and email and '@' in email and '.' in email)
        self.create_button.set_sensitive(valid)
    
    def _start_gpg_creation(self):
        """Start the GPG key creation process."""
        # Get form values
        name = self.name_row.get_text().strip()
        email = self.email_row.get_text().strip()
        passphrase = self.passphrase_row.get_text().strip()
        
        # Validate input
        if not name or not email:
            self._show_error("Please enter both name and email")
            return
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            self._show_error("Please enter a valid email address")
            return
        
        self.create_button.set_sensitive(False)
        self.create_button.set_label("Creating GPG Key...")
        
        def create_gpg_key():
            try:
                # Create GPG key using the correct method name
                success, result = GPGSetupHelper.create_gpg_key_batch(name, email, passphrase)

                if success:
                    GLib.idle_add(self._on_creation_success, result)
                else:
                    GLib.idle_add(self._on_creation_error, result)

            except Exception as e:
                GLib.idle_add(self._on_creation_error, f"GPG creation error: {str(e)}")
        
        # Start GPG creation in background thread
        thread = threading.Thread(target=create_gpg_key)
        thread.daemon = True
        thread.start()
    
    def _on_creation_success(self, success_message):
        """Handle successful GPG key creation."""
        self.create_button.set_label("GPG Key Created")

        # Get the email from the form (which is the GPG key ID)
        email = self.email_row.get_text().strip()

        # Emit success signal with the email as GPG ID
        self.emit('gpg-created', email)
    
    def _on_creation_error(self, error_message):
        """Handle GPG key creation error."""
        self.create_button.set_sensitive(True)
        self.create_button.set_label("Retry Creation")
        self._show_error(f"GPG creation failed: {error_message}")
    
    def _show_error(self, message):
        """Show an error message (placeholder for toast)."""
        # This would typically show a toast, but for now just print
        print(f"Error: {message}")
    
    def reset_state(self):
        """Reset the page to initial state."""
        self.name_row.set_text("")
        self.email_row.set_text("")
        self.passphrase_row.set_text("")
        self.create_button.set_sensitive(False)
        self.create_button.set_label("Create GPG Key")
    
    def set_default_values(self, name="", email=""):
        """Set default values for the form."""
        if name:
            self.name_row.set_text(name)
        if email:
            self.email_row.set_text(email)
        self._validate_form()
