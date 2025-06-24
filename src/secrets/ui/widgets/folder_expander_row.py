"""
Folder expander row widget for displaying folders with their passwords.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject
from ...app_info import APP_ID


@Gtk.Template(resource_path=f'/{APP_ID.replace(".", "/")}/ui/widgets/folder_expander_row.ui')
class FolderExpanderRow(Adw.ExpanderRow):
    """Custom widget for displaying a folder with expandable password list."""
    
    __gtype_name__ = "FolderExpanderRow"
    
    # Template widgets
    folder_actions_box = Gtk.Template.Child()
    add_password_to_folder_button = Gtk.Template.Child()
    edit_folder_button = Gtk.Template.Child()
    remove_folder_button = Gtk.Template.Child()
    
    # Signals
    __gsignals__ = {
        'add-password-to-folder': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'edit-folder': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'remove-folder': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, folder_path=None, **kwargs):
        """
        Initialize the folder expander row.
        
        Args:
            folder_path: The folder path this row represents
        """
        super().__init__(**kwargs)
        self._folder_path = folder_path
        self._password_rows = []
        self._setup_signals()
        
        if folder_path:
            self.set_folder_path(folder_path)
    
    def _setup_signals(self):
        """Set up button signal connections."""
        self.add_password_to_folder_button.connect('clicked', self._on_add_password_clicked)
        self.edit_folder_button.connect('clicked', self._on_edit_folder_clicked)
        self.remove_folder_button.connect('clicked', self._on_remove_folder_clicked)
    
    def set_folder_path(self, folder_path):
        """
        Set the folder path for this row.
        
        Args:
            folder_path: The folder path to display
        """
        self._folder_path = folder_path
        
        if folder_path:
            # Extract folder name from path
            folder_name = folder_path.split('/')[-1] if '/' in folder_path else folder_path
            self.set_title(folder_name)
            self.set_subtitle(folder_path)
    
    def get_folder_path(self):
        """Get the folder path associated with this row."""
        return self._folder_path
    
    def add_password_row(self, password_row):
        """
        Add a password row to this folder.
        
        Args:
            password_row: The password row widget to add
        """
        self.add_row(password_row)
        self._password_rows.append(password_row)
        self._update_subtitle()
    
    def remove_password_row(self, password_row):
        """
        Remove a password row from this folder.
        
        Args:
            password_row: The password row widget to remove
        """
        if password_row in self._password_rows:
            self.remove(password_row)
            self._password_rows.remove(password_row)
            self._update_subtitle()
    
    def clear_password_rows(self):
        """Clear all password rows from this folder."""
        for row in self._password_rows.copy():
            self.remove(row)
        self._password_rows.clear()
        self._update_subtitle()
    
    def get_password_rows(self):
        """Get all password rows in this folder."""
        return self._password_rows.copy()
    
    def get_password_count(self):
        """Get the number of passwords in this folder."""
        return len(self._password_rows)
    
    def _update_subtitle(self):
        """Update the subtitle to show password count."""
        count = len(self._password_rows)
        if count == 0:
            subtitle = self._folder_path if self._folder_path else "Empty folder"
        elif count == 1:
            subtitle = f"{self._folder_path} • 1 password"
        else:
            subtitle = f"{self._folder_path} • {count} passwords"
        
        self.set_subtitle(subtitle)
    
    def _on_add_password_clicked(self, button):
        """Handle add password to folder button click."""
        self.emit('add-password-to-folder')
    
    def _on_edit_folder_clicked(self, button):
        """Handle edit folder button click."""
        self.emit('edit-folder')
    
    def _on_remove_folder_clicked(self, button):
        """Handle remove folder button click."""
        self.emit('remove-folder')
    
    def set_sensitive_actions(self, sensitive=True):
        """
        Set the sensitivity of action buttons.
        
        Args:
            sensitive: Whether the action buttons should be sensitive
        """
        self.add_password_to_folder_button.set_sensitive(sensitive)
        self.edit_folder_button.set_sensitive(sensitive)
        self.remove_folder_button.set_sensitive(sensitive)
    
    def expand_if_matches_search(self, search_term):
        """
        Expand this folder if any of its passwords match the search term.
        
        Args:
            search_term: The search term to check against
            
        Returns:
            bool: True if the folder was expanded due to matches
        """
        if not search_term:
            return False
        
        # Check if folder name matches
        folder_name = self._folder_path.split('/')[-1] if self._folder_path else ""
        if search_term.lower() in folder_name.lower():
            self.set_expanded(True)
            return True
        
        # Check if any password in this folder matches
        has_matching_password = False
        for password_row in self._password_rows:
            password_entry = password_row.get_password_entry()
            if password_entry and search_term.lower() in password_entry.name.lower():
                has_matching_password = True
                password_row.highlight_search_term(search_term)
        
        if has_matching_password:
            self.set_expanded(True)
            return True
        
        return False
    
    def clear_search_highlighting(self):
        """Clear search highlighting from all password rows."""
        for password_row in self._password_rows:
            password_row.highlight_search_term("")
