"""
Password row widget for displaying individual passwords in the list.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/widgets/password_row.ui')
class PasswordRow(Adw.ActionRow):
    """Custom widget for displaying a password entry in the list."""
    
    __gtype_name__ = "PasswordRow"
    
    # Template widgets
    password_icon = Gtk.Template.Child()
    password_actions_box = Gtk.Template.Child()
    copy_password_button = Gtk.Template.Child()
    edit_password_button = Gtk.Template.Child()
    remove_password_button = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'copy-password': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'edit-password': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'remove-password': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, password_entry=None, **kwargs):
        """
        Initialize the password row.
        
        Args:
            password_entry: The password entry data to display
        """
        super().__init__(**kwargs)
        self._password_entry = password_entry
        self._setup_signals()
        
        if password_entry:
            self.set_password_entry(password_entry)
    
    def _setup_signals(self):
        """Set up button signal connections."""
        self.copy_password_button.connect('clicked', self._on_copy_password_clicked)
        self.edit_password_button.connect('clicked', self._on_edit_password_clicked)
        self.remove_password_button.connect('clicked', self._on_remove_password_clicked)
    
    def set_password_entry(self, password_entry):
        """
        Set the password entry data for this row.
        
        Args:
            password_entry: The password entry data to display
        """
        self._password_entry = password_entry
        
        if password_entry:
            # Set the title to the password name
            self.set_title(password_entry.name)
            
            # Set subtitle based on available metadata
            subtitle_parts = []
            if hasattr(password_entry, 'username') and password_entry.username:
                subtitle_parts.append(f"User: {password_entry.username}")
            if hasattr(password_entry, 'url') and password_entry.url:
                subtitle_parts.append(f"URL: {password_entry.url}")
            
            if subtitle_parts:
                self.set_subtitle(" • ".join(subtitle_parts))
            else:
                self.set_subtitle(password_entry.path)
    
    def get_password_entry(self):
        """Get the password entry associated with this row."""
        return self._password_entry
    
    def _on_copy_password_clicked(self, button):
        """Handle copy password button click."""
        self.emit('copy-password')
    
    def _on_edit_password_clicked(self, button):
        """Handle edit password button click."""
        self.emit('edit-password')
    
    def _on_remove_password_clicked(self, button):
        """Handle remove password button click."""
        self.emit('remove-password')
    
    def set_sensitive_actions(self, sensitive=True):
        """
        Set the sensitivity of action buttons.
        
        Args:
            sensitive: Whether the action buttons should be sensitive
        """
        self.copy_password_button.set_sensitive(sensitive)
        self.edit_password_button.set_sensitive(sensitive)
        self.remove_password_button.set_sensitive(sensitive)
    
    def highlight_search_term(self, search_term):
        """
        Highlight search term in the row title and subtitle.
        
        Args:
            search_term: The term to highlight
        """
        if not search_term or not self._password_entry:
            return
        
        # Simple highlighting - in a real implementation you might want
        # to use markup for better highlighting
        title = self._password_entry.name
        if search_term.lower() in title.lower():
            # Add CSS class for highlighting
            self.add_css_class("search-highlight")
        else:
            self.remove_css_class("search-highlight")
