"""
Password list component for the main window.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GObject, Gio
from ...app_info import APP_ID


class PasswordListComponent(GObject.Object):
    """
    Component that manages the password list functionality.
    """
    
    def __init__(self, container, search_entry, scrolled_window):
        """
        Initialize the password list component.
        
        Args:
            container: The main container widget
            search_entry: The search entry widget
            scrolled_window: The scrolled window containing the tree view
        """
        super().__init__()
        self.container = container
        self.search_entry = search_entry
        self.scrolled_window = scrolled_window
        
        # Will be set by the controller
        self.tree_view = None
        self.list_store = None
        self.filter_model = None
        
    def setup_tree_view(self, tree_view, list_store, filter_model):
        """
        Set up the tree view and models.
        
        Args:
            tree_view: The tree view widget
            list_store: The list store model
            filter_model: The filter model for searching
        """
        self.tree_view = tree_view
        self.list_store = list_store
        self.filter_model = filter_model
        
        # Add the tree view to the scrolled window
        self.scrolled_window.set_child(tree_view)
    
    def connect_search_signals(self, search_handler):
        """
        Connect search-related signals.
        
        Args:
            search_handler: Function to handle search changes
        """
        if self.search_entry:
            self.search_entry.connect("search-changed", search_handler)
    
    def get_search_text(self):
        """
        Get the current search text.
        
        Returns:
            str: The search text
        """
        if self.search_entry:
            return self.search_entry.get_text()
        return ""
    
    def clear_search(self):
        """Clear the search entry."""
        if self.search_entry:
            self.search_entry.set_text("")
    
    def focus_search(self):
        """Focus the search entry."""
        if self.search_entry:
            self.search_entry.grab_focus()
    
    def set_loading_state(self, loading):
        """
        Set the loading state of the component.
        
        Args:
            loading: Whether the component is in loading state
        """
        if self.search_entry:
            self.search_entry.set_sensitive(not loading)
        if self.tree_view:
            self.tree_view.set_sensitive(not loading)
    
    def refresh_list(self):
        """Refresh the password list."""
        if self.filter_model:
            self.filter_model.refilter()
    
    def get_selected_item(self):
        """
        Get the currently selected item.
        
        Returns:
            The selected item or None
        """
        if not self.tree_view:
            return None
            
        selection = self.tree_view.get_selection()
        if selection:
            return selection.get_selected_item()
        return None
    
    def set_placeholder_text(self, text):
        """
        Set the placeholder text for the search entry.
        
        Args:
            text: The placeholder text
        """
        if self.search_entry:
            self.search_entry.set_placeholder_text(text)
