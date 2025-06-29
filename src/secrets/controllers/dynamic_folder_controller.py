"""
Dynamic Folder Controller for the redesigned UI with AdwExpanderRow folders.
This controller dynamically creates folder and password rows based on the password store data.
"""

import os
from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf
from ..models import PasswordEntry
from ..ui.widgets import FolderExpanderRow
from ..managers import get_favicon_manager


class DynamicFolderController:
    """Controller for managing dynamically created folder structure in the sidebar."""
    
    def __init__(self, password_store, toast_manager, folders_listbox, search_entry, on_selection_changed=None):
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.folders_listbox = folders_listbox
        self.search_entry = search_entry
        self.on_selection_changed = on_selection_changed
        
        # Store references to created widgets
        self.folder_rows = {}  # folder_path -> AdwExpanderRow
        self.password_rows = {}  # password_path -> AdwActionRow
        self.current_selection = None
        
        # Connect search functionality
        if self.search_entry:
            self.search_entry.connect("search-changed", self._on_search_entry_changed)
    
    def load_passwords(self):
        """Load and display passwords in the dynamic folder structure."""
        # Save current expansion state before clearing
        expansion_state = self._save_expansion_state()

        # Clear existing widgets
        self._clear_all_widgets()

        # Get password list from store
        raw_password_list = self.password_store.list_passwords()

        if not raw_password_list:
            self._handle_empty_password_list()
            return

        # Build dynamic folder structure
        self._build_dynamic_folder_structure(raw_password_list)

        # Restore expansion state
        self._restore_expansion_state(expansion_state)

    def refresh_password_display(self, password_path):
        """Refresh the display of a specific password after metadata changes."""
        # Find the password row in our dictionary and update its avatar
        if password_path in self.password_rows:
            password_row = self.password_rows[password_path]

            # Get updated metadata
            password_metadata = self.password_store.get_password_metadata(password_path)
            password_color = password_metadata["color"]
            password_icon = password_metadata["icon"]
            favicon_data = password_metadata["favicon_data"]

            # Get URL for favicon support
            url = self._extract_url_from_password(password_path)

            # Update the avatar with new color/icon and cached favicon
            password_row.set_avatar_color_and_icon(password_color, password_icon, url, favicon_data)

            print(f"Refreshed password display for: {password_path} with color: {password_color}, icon: {password_icon}")
        else:
            print(f"Password row not found for path: {password_path}")
            # Fallback to full reload if we can't find the specific row
            self.load_passwords()

    def _save_expansion_state(self):
        """Save the current expansion state of all folder rows."""
        expansion_state = {}
        for folder_path, folder_row in self.folder_rows.items():
            if hasattr(folder_row, 'get_expanded'):
                expansion_state[folder_path] = folder_row.get_expanded()
        return expansion_state

    def _restore_expansion_state(self, expansion_state):
        """Restore the expansion state of folder rows."""
        if not expansion_state:
            return

        for folder_path, was_expanded in expansion_state.items():
            if folder_path in self.folder_rows:
                folder_row = self.folder_rows[folder_path]
                if hasattr(folder_row, 'set_expanded'):
                    folder_row.set_expanded(was_expanded)
    
    def _clear_all_widgets(self):
        """Clear all existing folder and password widgets."""
        # Remove all children from the listbox
        child = self.folders_listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.folders_listbox.remove(child)
            child = next_child
        
        # Clear our references
        self.folder_rows.clear()
        self.password_rows.clear()
        self.current_selection = None
    
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
    
    def _build_dynamic_folder_structure(self, raw_password_list):
        """Build dynamic folder structure from password list and include empty folders."""
        # Group passwords by folder and separate root passwords
        folder_structure = {}
        root_passwords = []

        for password_path in sorted(raw_password_list):
            parts = password_path.split(os.sep)

            if len(parts) == 1:
                # Root level password - add to separate list
                root_passwords.append({
                    'name': parts[0],
                    'path': password_path
                })
            else:
                # Password in folder
                folder_name = parts[0]
                password_name = parts[-1]

                if folder_name not in folder_structure:
                    folder_structure[folder_name] = []

                folder_structure[folder_name].append({
                    'name': password_name,
                    'path': password_path
                })

        # Add empty folders that don't contain passwords
        all_folders = self.password_store.list_folders()
        for folder_path in all_folders:
            # Only show top-level folders for now (can be enhanced later for nested folders)
            if os.sep not in folder_path:  # Top-level folder
                if folder_path not in folder_structure:
                    folder_structure[folder_path] = []  # Empty folder

        # Create folder widgets first
        for folder_name, passwords in folder_structure.items():
            self._create_folder_widget(folder_name, passwords)

        # Create individual password rows for root passwords (after all folders)
        for password_data in root_passwords:
            self._create_root_password_widget(password_data)
    
    def _create_folder_widget(self, folder_name, passwords):
        """Create a FolderExpanderRow for a folder with its passwords."""
        # Store reference
        folder_path = folder_name if folder_name != "Root" else ""

        # Create folder expander row using the custom widget
        folder_row = FolderExpanderRow(folder_path=folder_path)
        folder_row.set_title(folder_name)
        folder_row.set_subtitle(f"{len(passwords)} password{'s' if len(passwords) != 1 else ''}")

        # Set avatar color and icon from metadata
        folder_metadata = self.password_store.get_folder_metadata(folder_path)
        folder_color = folder_metadata["color"]
        folder_icon = folder_metadata["icon"]
        folder_row.set_avatar_color_and_icon(folder_color, folder_icon)

        self.folder_rows[folder_path] = folder_row

        # Connect folder signals
        folder_row.connect("activate", self._on_folder_activated, folder_path)
        folder_row.connect("add-password-to-folder", self._on_add_password_to_folder_clicked, folder_path)
        folder_row.connect("edit-folder", self._on_folder_edit_clicked, folder_path, folder_name)
        folder_row.connect("remove-folder", self._on_folder_delete_clicked, folder_path, folder_name)

        # Create password rows within the folder
        for password_data in passwords:
            password_row = self._create_password_widget(password_data, folder_row)

        # Add folder to listbox
        self.folders_listbox.append(folder_row)
    
    def _create_password_widget(self, password_data, parent_folder):
        """Create a PasswordRow for a password."""
        from ..ui.widgets.password_row import PasswordRow

        password_row = PasswordRow()
        password_row.set_title(password_data['name'])
        password_row.set_subtitle(password_data['path'])

        # Set the password entry path for metadata saving
        password_row._password_entry = password_data['path']

        # Set avatar color and icon from metadata
        password_metadata = self.password_store.get_password_metadata(password_data['path'])
        password_color = password_metadata["color"]
        password_icon = password_metadata["icon"]
        favicon_data = password_metadata["favicon_data"]

        # Get URL for favicon support
        url = self._extract_url_from_password(password_data['path'])

        # Debug output
        if favicon_data:
            print(f"✓ Using cached favicon data for {password_data['name']} ({len(favicon_data)} chars)")
        elif url:
            print(f"🔄 No cached favicon for {password_data['name']}, will download from: {url}")

        # Set avatar with color, icon, URL, and cached favicon
        password_row.set_avatar_color_and_icon(password_color, password_icon, url, favicon_data)

        # Store reference
        password_path = password_data['path']
        self.password_rows[password_path] = password_row

        # Connect signals
        password_row.connect("activated", self._on_password_activated, password_path)

        # Add password row to folder
        parent_folder.add_row(password_row)

        return password_row

    def _create_root_password_widget(self, password_data):
        """Create a PasswordRow for a root-level password (not in a folder)."""
        from ..ui.widgets.password_row import PasswordRow

        password_row = PasswordRow()
        password_row.set_title(password_data['name'])
        password_row.set_subtitle(password_data['path'])

        # Set the password entry path for metadata saving
        password_row._password_entry = password_data['path']

        # Set avatar color and icon from metadata
        password_metadata = self.password_store.get_password_metadata(password_data['path'])
        password_color = password_metadata["color"]
        password_icon = password_metadata["icon"]
        favicon_data = password_metadata["favicon_data"]

        # Get URL for favicon support
        url = self._extract_url_from_password(password_data['path'])

        # Debug output
        if favicon_data:
            print(f"✓ Using cached favicon data for {password_data['name']} ({len(favicon_data)} chars)")
        elif url:
            print(f"🔄 No cached favicon for {password_data['name']}, will download from: {url}")

        # Set avatar with color, icon, URL, and cached favicon
        password_row.set_avatar_color_and_icon(password_color, password_icon, url, favicon_data)

        # Store reference
        password_path = password_data['path']
        self.password_rows[password_path] = password_row

        # Connect signals
        password_row.connect("activated", self._on_password_activated, password_path)

        # Add password row directly to listbox (not to a folder)
        self.folders_listbox.append(password_row)

        return password_row



    def _extract_url_from_password(self, password_path):
        """Extract URL from password content."""
        try:
            # Get password content
            success, content = self.password_store.get_password_content(password_path)
            if not success:
                return None

            # Look for URL in the content
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for direct URL (full URLs)
                if line.startswith(('http://', 'https://')):
                    print(f"Found direct URL for {password_path}: {line}")
                    # Convert HTTP to HTTPS for security
                    if line.startswith('http://'):
                        secure_url = 'https://' + line[7:]
                        print(f"Converted HTTP to HTTPS: {secure_url}")
                        return secure_url
                    return line

                # Check for URL field
                if line.lower().startswith('url:'):
                    url = line[4:].strip()
                    if url:
                        print(f"Found URL field for {password_path}: {url}")
                        return self._normalize_url(url)

                # Check for website field
                if line.lower().startswith('website:'):
                    url = line[8:].strip()
                    if url:
                        print(f"Found website field for {password_path}: {url}")
                        return self._normalize_url(url)

                # Check for domain-like patterns (contains dots and looks like a domain)
                # This handles legacy URLs saved without "url:" prefix
                if self._looks_like_domain(line):
                    print(f"Found domain-like pattern for {password_path}: {line}")
                    return self._normalize_url(line)

            return None
        except Exception:
            return None

    def _looks_like_domain(self, text):
        """Check if text looks like a domain name."""
        # Basic checks for domain-like patterns
        if not text or len(text) < 3:
            return False

        # Must contain at least one dot
        if '.' not in text:
            return False

        # Should not contain spaces
        if ' ' in text:
            return False

        # Should not contain common non-domain characters
        invalid_chars = ['@', '#', '?', '&', '=', '/', '\\', '"', "'", '<', '>']
        if any(char in text for char in invalid_chars):
            return False

        # Split by dots and check each part
        parts = text.split('.')
        if len(parts) < 2:
            return False

        # Each part should be reasonable length and contain valid characters
        for part in parts:
            if not part or len(part) > 63:  # DNS label limit
                return False
            if not part.replace('-', '').isalnum():  # Allow alphanumeric and hyphens
                return False
            if part.startswith('-') or part.endswith('-'):  # Hyphens can't be at start/end
                return False

        return True

    def _normalize_url(self, url):
        """Normalize a URL or domain to a proper HTTPS URL format."""
        if not url:
            return None

        url = url.strip()

        # Convert HTTP to HTTPS for security
        if url.startswith('http://'):
            url = 'https://' + url[7:]
            print(f"Converted HTTP to HTTPS: {url}")
            return url

        # If it already has HTTPS, return as-is
        if url.startswith('https://'):
            return url

        # Add https:// prefix for domain-like strings
        return f"https://{url}"



    def _on_folder_activated(self, folder_row, folder_path):
        """Handle folder activation."""
        self.current_selection = {
            'type': 'folder',
            'path': folder_path,
            'name': folder_row.get_title()
        }

        if self.on_selection_changed:
            # Create a PasswordEntry for the folder
            folder_entry = PasswordEntry(path=folder_path, is_folder=True)
            self.on_selection_changed(None)

    def _on_add_password_to_folder_clicked(self, folder_row, folder_path):
        """Handle add password to folder button click."""
        # Import here to avoid circular imports
        from gi.repository import GLib

        # Use GLib.idle_add to defer the call and trigger the main window's add password dialog
        GLib.idle_add(self._handle_add_password_to_folder_request, folder_path)

    def _on_folder_edit_clicked(self, folder_row, folder_path, folder_name):
        """Handle folder edit button click."""
        # Import here to avoid circular imports
        from gi.repository import GLib

        # Emit a custom signal or call a callback to handle folder editing
        # We'll use GLib.idle_add to defer the call to avoid potential issues
        GLib.idle_add(self._handle_folder_edit_request, folder_path, folder_name)

    def _on_folder_delete_clicked(self, button, folder_path, folder_name):
        """Handle folder delete button click."""
        # Import here to avoid circular imports
        from gi.repository import GLib

        # Emit a custom signal or call a callback to handle folder deletion
        # We'll use GLib.idle_add to defer the call to avoid potential issues
        GLib.idle_add(self._handle_folder_delete_request, folder_path, folder_name)

    def _handle_folder_edit_request(self, folder_path, folder_name):
        """Handle the actual folder edit request."""
        # For now, we'll emit a signal that the main window can catch
        # This allows the main window to handle the edit dialog
        if hasattr(self, 'edit_folder_requested'):
            self.edit_folder_requested(folder_path, folder_name)
        else:
            # Fallback: show a toast message
            self.toast_manager.show_info(f"Edit folder '{folder_name}' - functionality coming soon")
        return False  # Don't repeat the idle call

    def _handle_add_password_to_folder_request(self, folder_path):
        """Handle add password to folder request."""
        # Emit a signal that the main window can catch
        if hasattr(self, 'add_password_to_folder_requested'):
            self.add_password_to_folder_requested(folder_path)
        else:
            # Fallback: show a toast message
            self.toast_manager.show_info(f"Add password to folder '{folder_path}' - functionality coming soon")
        return False  # Don't repeat the idle call

    def _handle_folder_delete_request(self, folder_path, folder_name):
        """Handle the actual folder deletion request."""
        # Check if folder is empty
        success, is_empty, message = self.password_store.is_folder_empty(folder_path)

        if not success:
            self.toast_manager.show_error(f"Error checking folder: {message}")
            return False

        if not is_empty:
            self.toast_manager.show_warning(f"Cannot delete folder '{folder_name}': folder contains passwords. Remove all passwords first.")
            return False

        # Show confirmation dialog for empty folder
        self._show_delete_folder_confirmation(folder_path, folder_name)
        return False  # Don't repeat the idle call

    def _show_delete_folder_confirmation(self, folder_path, folder_name):
        """Show confirmation dialog for folder deletion."""
        # Import dialog utilities
        try:
            from ..utils.ui_utils import DialogManager, UIConstants
        except ImportError:
            # Fallback if utils not available
            self.toast_manager.show_error("Cannot show confirmation dialog")
            return

        # Create confirmation dialog (parent will be set when presenting)
        dialog = DialogManager.create_message_dialog(
            parent=None,  # Parent will be set when presenting
            heading=f"Delete folder '{folder_name}'?",
            body=f"Are you sure you want to permanently delete the empty folder '{folder_name}'?",
            dialog_type="question",
            default_size=UIConstants.SMALL_DIALOG
        )

        # Add response buttons
        DialogManager.add_dialog_response(dialog, "cancel", "_Cancel", "default")
        DialogManager.add_dialog_response(dialog, "delete", "_Delete", "destructive")
        dialog.set_default_response("cancel")

        # Connect response handler
        dialog.connect("response", self._on_delete_folder_response, folder_path, folder_name)

        # Present dialog (parent window will be set by main window)
        # For now, we'll emit a signal that the main window can catch
        if hasattr(self, 'delete_folder_requested'):
            self.delete_folder_requested(dialog, folder_path, folder_name)
        else:
            # Fallback: show dialog without parent
            dialog.present()

    def _on_delete_folder_response(self, dialog, response_id, folder_path, folder_name):
        """Handle folder deletion confirmation response."""
        if response_id == "delete":
            # Perform the actual deletion
            success, message = self.password_store.delete_folder(folder_path)

            if success:
                self.toast_manager.show_success(message)
                # Refresh the folder list
                self.load_passwords()
            else:
                self.toast_manager.show_error(f"Error deleting folder: {message}")

        dialog.close()
    
    def _on_password_activated(self, password_row, password_path):
        """Handle password row activation."""
        self._select_password(password_path)
    
    def _on_password_action_clicked(self, button, password_path):
        """Handle password action button click."""
        self._select_password(password_path)
    
    def _select_password(self, password_path):
        """Select a password and notify the parent."""
        self.current_selection = {
            'type': 'password',
            'path': password_path,
            'name': os.path.basename(password_path)
        }
        
        if self.on_selection_changed:
            # Create a PasswordEntry for the password
            password_entry = PasswordEntry(path=password_path, is_folder=False)
            self.on_selection_changed(None)
    
    def _on_search_entry_changed(self, search_entry):
        """Handle search entry changes."""
        query = search_entry.get_text().strip().lower()
        
        if not query:
            # Show all items
            self._show_all_items()
            return
        
        # Filter items based on query
        self._filter_items(query)
    
    def _show_all_items(self):
        """Show all folder and password items."""
        for folder_row in self.folder_rows.values():
            folder_row.set_visible(True)
        
        for password_row in self.password_rows.values():
            password_row.set_visible(True)
    
    def _filter_items(self, query):
        """Filter items based on search query."""
        # Filter folders and their passwords
        for folder_path, folder_row in self.folder_rows.items():
            folder_title = folder_row.get_title().lower()
            folder_matches = query in folder_title

            # Check passwords in this folder
            password_matches = False
            for password_path, password_row in self.password_rows.items():
                # Check if password belongs to this folder
                if folder_path and password_path.startswith(folder_path + "/"):
                    password_title = password_row.get_title().lower()
                    password_subtitle = password_row.get_subtitle().lower()

                    if query in password_title or query in password_subtitle:
                        password_matches = True
                        password_row.set_visible(True)
                    else:
                        password_row.set_visible(False)

            # Show folder if it matches or contains matching passwords
            folder_row.set_visible(folder_matches or password_matches)

        # Filter root passwords (passwords not in any folder)
        for password_path, password_row in self.password_rows.items():
            # Check if this is a root password (no "/" in path)
            if "/" not in password_path:
                password_title = password_row.get_title().lower()
                password_subtitle = password_row.get_subtitle().lower()

                if query in password_title or query in password_subtitle:
                    password_row.set_visible(True)
                else:
                    password_row.set_visible(False)
    
    def get_selected_item(self):
        """Get the currently selected item."""
        if self.current_selection:
            entry = PasswordEntry(
                path=self.current_selection['path'],
                is_folder=self.current_selection['type'] == 'folder'
            )
            return entry
        return None
    
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
