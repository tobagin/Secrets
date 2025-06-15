"""
Static Folder Controller for the redesigned UI with AdwExpanderRow folders.
This controller manages the static folder structure defined in the UI file.
"""

import os
from gi.repository import Gtk, Adw, GLib
from ..models import PasswordEntry


class StaticFolderController:
    """Controller for managing the static folder structure in the sidebar."""
    
    def __init__(self, password_store, toast_manager, folders_listbox, search_entry, on_selection_changed=None):
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.folders_listbox = folders_listbox
        self.search_entry = search_entry
        self.on_selection_changed = on_selection_changed
        
        # Store references to folder and password rows
        self.folder_rows = {}
        self.password_rows = {}
        self.current_selection = None
        
        # Connect search functionality
        if self.search_entry:
            self.search_entry.connect("search-changed", self._on_search_entry_changed)
        
        # Initialize the folder structure
        self._initialize_folder_structure()
    
    def _initialize_folder_structure(self):
        """Initialize the static folder structure with real password data."""
        # Get all folders from the listbox
        child = self.folders_listbox.get_first_child()
        while child:
            if isinstance(child, Adw.ExpanderRow):
                folder_id = child.get_buildable_id()
                if folder_id:
                    self.folder_rows[folder_id] = child
                    # Connect folder selection
                    child.connect("activate", self._on_folder_activated)
                    
                    # Get password rows within this folder
                    self._collect_password_rows(child, folder_id)
            
            child = child.get_next_sibling()
    
    def _collect_password_rows(self, folder_row, folder_id):
        """Collect password rows from a folder."""
        # Iterate through the folder's children to find password rows
        for i in range(folder_row.get_n_rows()):
            try:
                password_row = folder_row.get_row_at_index(i)
                if isinstance(password_row, Adw.ActionRow):
                    password_id = password_row.get_buildable_id()
                    if password_id:
                        self.password_rows[password_id] = password_row
                        # Connect password selection
                        password_row.connect("activated", self._on_password_activated)
            except:
                pass  # Skip if row doesn't exist
    
    def _on_folder_activated(self, folder_row):
        """Handle folder activation."""
        folder_id = folder_row.get_buildable_id()
        self.current_selection = {
            'type': 'folder',
            'id': folder_id,
            'title': folder_row.get_title(),
            'subtitle': folder_row.get_subtitle()
        }
        
        if self.on_selection_changed:
            # Create a mock PasswordEntry for folder
            folder_entry = PasswordEntry(path=folder_id, is_folder=True)
            self.on_selection_changed(None)  # Pass None since we don't have a selection model
    
    def _on_password_activated(self, password_row):
        """Handle password activation."""
        password_id = password_row.get_buildable_id()
        self.current_selection = {
            'type': 'password',
            'id': password_id,
            'title': password_row.get_title(),
            'subtitle': password_row.get_subtitle()
        }
        
        if self.on_selection_changed:
            # Create a mock PasswordEntry for password
            password_entry = PasswordEntry(path=password_id, is_folder=False)
            self.on_selection_changed(None)  # Pass None since we don't have a selection model
    
    def _on_search_entry_changed(self, search_entry):
        """Handle search entry changes."""
        query = search_entry.get_text().strip().lower()
        
        if not query:
            # Show all folders and passwords
            self._show_all_items()
            return
        
        # Filter folders and passwords based on query
        self._filter_items(query)
    
    def _show_all_items(self):
        """Show all folders and password items."""
        for folder_row in self.folder_rows.values():
            folder_row.set_visible(True)
        
        for password_row in self.password_rows.values():
            password_row.set_visible(True)
    
    def _filter_items(self, query):
        """Filter items based on search query."""
        for folder_id, folder_row in self.folder_rows.items():
            folder_title = folder_row.get_title().lower()
            folder_subtitle = folder_row.get_subtitle().lower() if folder_row.get_subtitle() else ""
            
            # Check if folder matches
            folder_matches = query in folder_title or query in folder_subtitle
            
            # Check if any password in folder matches
            password_matches = False
            for password_id, password_row in self.password_rows.items():
                if password_id.startswith(folder_id):
                    password_title = password_row.get_title().lower()
                    password_subtitle = password_row.get_subtitle().lower() if password_row.get_subtitle() else ""
                    
                    if query in password_title or query in password_subtitle:
                        password_matches = True
                        password_row.set_visible(True)
                    else:
                        password_row.set_visible(False)
            
            # Show folder if it matches or contains matching passwords
            folder_row.set_visible(folder_matches or password_matches)
    
    def get_selected_item(self):
        """Get the currently selected item."""
        if self.current_selection:
            # Create a mock PasswordEntry based on current selection
            entry = PasswordEntry(
                path=self.current_selection['id'],
                is_folder=self.current_selection['type'] == 'folder'
            )
            return entry
        return None
    
    def load_passwords(self):
        """Load and populate the folder structure with real password data."""
        # Get real password data from the store
        raw_password_list = self.password_store.list_passwords()
        
        if not raw_password_list:
            self.toast_manager.show_info("No passwords found. Click '+' to add your first password.")
            return
        
        # Update the static UI with real data
        self._populate_folders_with_data(raw_password_list)
    
    def _populate_folders_with_data(self, password_list):
        """Populate the static folder structure with real password data."""
        # Group passwords by folder
        folder_data = {}
        
        for password_path in password_list:
            parts = password_path.split(os.sep)
            if len(parts) > 1:
                folder_name = parts[0]
                password_name = parts[-1]
                
                if folder_name not in folder_data:
                    folder_data[folder_name] = []
                folder_data[folder_name].append({
                    'name': password_name,
                    'path': password_path
                })
        
        # Update folder titles and populate with real data
        folder_keys = list(self.folder_rows.keys())
        folder_names = list(folder_data.keys())
        
        for i, (folder_id, folder_row) in enumerate(self.folder_rows.items()):
            if i < len(folder_names):
                folder_name = folder_names[i]
                passwords = folder_data[folder_name]
                
                # Update folder title
                folder_row.set_title(folder_name)
                folder_row.set_subtitle(f"{len(passwords)} passwords")
                
                # Update password rows in this folder
                self._update_password_rows_in_folder(folder_id, passwords)
            else:
                # Hide unused folders
                folder_row.set_visible(False)
    
    def _update_password_rows_in_folder(self, folder_id, passwords):
        """Update password rows within a specific folder."""
        # Get password rows for this folder
        folder_password_rows = [
            (pid, row) for pid, row in self.password_rows.items() 
            if pid.startswith(folder_id)
        ]
        
        for i, (password_id, password_row) in enumerate(folder_password_rows):
            if i < len(passwords):
                password_data = passwords[i]
                password_row.set_title(password_data['name'])
                password_row.set_subtitle(password_data['path'])
                password_row.set_visible(True)
            else:
                # Hide unused password rows
                password_row.set_visible(False)
    
    def clear_selection(self):
        """Clear the current selection."""
        self.current_selection = None
    
    def focus_search(self):
        """Focus the search entry."""
        if self.search_entry:
            self.search_entry.grab_focus()
    
    def clear_search(self):
        """Clear the search entry and show all items."""
        if self.search_entry:
            self.search_entry.set_text("")
        self._show_all_items()
