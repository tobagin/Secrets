"""
Password List Controller - Manages the hierarchical password list view.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio, GObject
import os
from typing import Optional, Callable

from ..models import PasswordListItem
from ..managers import ToastManager


class PasswordListController:
    """Controls the password list view, search, and selection."""
    
    def __init__(self, 
                 password_store,
                 toast_manager: ToastManager,
                 treeview_scrolled_window: Gtk.ScrolledWindow,
                 search_entry: Gtk.SearchEntry,
                 on_selection_changed: Optional[Callable] = None):
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.treeview_scrolled_window = treeview_scrolled_window
        self.search_entry = search_entry
        self.on_selection_changed = on_selection_changed
        
        # ListView related properties
        self.list_view = None
        self.list_store = None
        self.tree_list_model = None
        self.selection_model = None
        
        # Connect search signal
        self.search_entry.connect("search-changed", self._on_search_entry_changed)
        
        # Build the list view
        self._build_listview()
    
    def _build_listview(self):
        """Build the hierarchical password list view with optimized performance."""
        self.list_store = Gio.ListStore.new(PasswordListItem)

        # TreeListModel setup with improved error handling
        def get_child_model_func(item, user_data):
            if item and item.is_folder and hasattr(item, 'children_model'):
                return item.children_model
            return None

        # Create the tree model with optimized expansion settings
        self.tree_list_model = Gtk.TreeListModel.new(
            self.list_store,
            passthrough=False,
            autoexpand=False,
            create_func=get_child_model_func,
            user_data=None
        )

        # Create an optimized factory for list items
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_list_item_setup)
        factory.connect("bind", self._on_list_item_bind)

        # Set up selection with better defaults
        self.selection_model = Gtk.SingleSelection(model=self.tree_list_model)
        self.selection_model.set_autoselect(False)  # Prevent automatic selection
        self.selection_model.connect("selection-changed", self._on_selection_changed)

        # Create the list view with improved scrolling behavior
        self.list_view = Gtk.ListView(model=self.selection_model, factory=factory)
        self.list_view.set_single_click_activate(False)  # Require double-click for activation

        # Add the list view to the scrolled window
        self.treeview_scrolled_window.set_child(self.list_view)

    def _on_list_item_setup(self, factory, list_item):
        """Setup list item widget."""
        # Use Adw.ActionRow for a nice look and feel
        row = Adw.ActionRow()
        list_item.set_child(row)

    def _on_list_item_bind(self, factory, list_item):
        """Bind data to list item widget."""
        row_widget = list_item.get_child()  # This is the Adw.ActionRow
        item_data = list_item.get_item()  # This is our PasswordListItem

        if item_data:
            row_widget.set_title(item_data.name)
            
            # Add icons to distinguish folders from password entries
            icon_name = "folder-symbolic" if item_data.is_folder else "dialog-password-symbolic"
            image = Gtk.Image.new_from_icon_name(icon_name)
            
            # Clear any existing prefix widgets to avoid duplicates when rows are reused
            for child in row_widget.get_prefix_widgets():
                row_widget.remove(child)
            
            row_widget.add_prefix(image)
            
            # Add subtle styling based on item type
            if item_data.is_folder:
                row_widget.add_css_class("folder-item")
            else:
                row_widget.add_css_class("password-item")

    def _on_selection_changed(self, selection_model, param):
        """Handle selection changes and notify parent."""
        if self.on_selection_changed:
            self.on_selection_changed(selection_model, param)

    def load_passwords(self):
        """Load and display passwords in the list."""
        self.list_store.remove_all()
        raw_password_list = self.password_store.list_passwords()

        # Check if no passwords were found and provide helpful feedback
        if not raw_password_list:
            self._handle_empty_password_list()
            return

        # Build hierarchical structure
        self._build_hierarchical_structure(raw_password_list)

    def _handle_empty_password_list(self):
        """Handle the case when no passwords are found."""
        # Check if there are .gpg files that couldn't be listed
        gpg_files_exist = False
        if self.password_store.store_dir and os.path.isdir(self.password_store.store_dir):
            for root, dirs, files in os.walk(self.password_store.store_dir):
                if any(f.endswith('.gpg') for f in files):
                    gpg_files_exist = True
                    break

        if gpg_files_exist:
            self.toast_manager.show_error("Password files exist but cannot be accessed. Check GPG setup.")
        else:
            self.toast_manager.show_info("No passwords found. Click '+' to add your first password.")

    def _build_hierarchical_structure(self, raw_password_list):
        """Build hierarchical structure from flat password list."""
        root_items_dict = {}

        for path_str in sorted(raw_password_list):
            parts = path_str.split(os.sep)
            current_parent_dict = root_items_dict
            current_parent_list_store = self.list_store
            current_path_prefix = ""

            for i, part_name in enumerate(parts):
                current_full_path = os.path.join(current_path_prefix, part_name) if current_path_prefix else part_name
                is_password_file = (i == len(parts) - 1)

                if part_name not in current_parent_dict:
                    is_folder = not is_password_file
                    new_item = PasswordListItem(name=part_name, full_path=current_full_path, is_folder=is_folder)
                    current_parent_dict[part_name] = new_item
                    current_parent_list_store.append(new_item)

                # Move to the next level
                item_obj = current_parent_dict[part_name]
                if not is_password_file:  # If it's a folder, prepare for its children
                    current_parent_dict = getattr(item_obj, '_children_dict_cache', {})
                    if not hasattr(item_obj, '_children_dict_cache'):
                        item_obj._children_dict_cache = current_parent_dict
                    current_parent_list_store = item_obj.children_model
                    current_path_prefix = item_obj.full_path

        # Clean up temporary caches
        self._cleanup_cache(self.list_store)

    def _cleanup_cache(self, store):
        """Clean up temporary caches used during hierarchy building."""
        for i in range(store.get_n_items()):
            item = store.get_item(i)
            if hasattr(item, '_children_dict_cache'):
                delattr(item, '_children_dict_cache')
            if item.is_folder and item.children_model:
                self._cleanup_cache(item.children_model)

    def _on_search_entry_changed(self, search_entry):
        """Handle search entry changes."""
        query = search_entry.get_text().strip()

        if not query:
            # If query is empty, reload the full hierarchical list
            self.load_passwords()
            return

        # If there's a query, perform search
        success, result = self.password_store.search_passwords(query)

        # Create a new flat ListStore for search results
        search_results_store = Gio.ListStore.new(PasswordListItem)

        if success:
            if result:  # If there are matching paths
                for path_str in sorted(result):
                    item = PasswordListItem(name=path_str, full_path=path_str, is_folder=False)
                    search_results_store.append(item)
                
                # Update the list view with search results
                self._update_list_with_search_results(search_results_store)
                self.toast_manager.show_info(f"Found {len(result)} matching items")
            else:  # No results found
                # Clear the list but show a message
                self._update_list_with_search_results(search_results_store)
                self.toast_manager.show_info("No matching passwords found")
        else:
            # result contains the error message
            self.toast_manager.show_error(f"Search error: {result}")
            # Restore full list on error
            self.load_passwords()

    def _update_list_with_search_results(self, search_results_store):
        """Update the list view with search results while preserving selection state."""
        # Save current selection if any
        selected_path = None
        selected_item = self.selection_model.get_selected_item()
        if selected_item:
            selected_path = selected_item.full_path
        
        # Replace the list store with search results
        self.list_store.remove_all()
        
        # Copy items from search results to main list store
        for i in range(search_results_store.get_n_items()):
            self.list_store.append(search_results_store.get_item(i))

    def get_selected_item(self):
        """Get the currently selected item."""
        if self.selection_model:
            return self.selection_model.get_selected_item()
        return None

    def clear_selection(self):
        """Clear the current selection."""
        if self.selection_model:
            self.selection_model.set_selected(Gtk.INVALID_LIST_POSITION)

    def focus_search(self):
        """Focus the search entry."""
        self.search_entry.grab_focus()

    def clear_search(self):
        """Clear the search entry and reload full list."""
        self.search_entry.set_text("")
        self.load_passwords()
