"""
Dynamic Folder Controller for the redesigned UI with AdwExpanderRow folders.
This controller dynamically creates folder and password rows based on the password store data.
"""

import os
import threading
from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf
from ..models import PasswordEntry
from ..ui.widgets import FolderExpanderRow
from ..managers import get_favicon_manager
from ..logging_system import get_logger, LogCategory


class DynamicFolderController:
    """Controller for managing dynamically created folder structure in the sidebar."""
    
    def __init__(self, password_store, toast_manager, folders_listbox, search_entry, on_selection_changed=None, parent_window=None):
        # Initialize logger for this controller
        self.logger = get_logger(LogCategory.UI, "DynamicFolderController")
        
        self.password_store = password_store
        self.toast_manager = toast_manager
        self.folders_listbox = folders_listbox
        self.search_entry = search_entry
        self.on_selection_changed = on_selection_changed
        self.parent_window = parent_window
        
        # Store references to created widgets
        self.folder_rows = {}  # folder_path -> AdwExpanderRow
        self.password_rows = {}  # password_path -> AdwActionRow
        self.current_selection = None
        
        # Threading for password loading
        self._loading_thread = None
        self._is_loading = False
        
        # Virtual scrolling optimization
        self._virtual_scrolling_enabled = True
        self._viewport_size = 20  # Number of items to render at once
        self._scroll_buffer = 5   # Extra items to render above/below viewport
        self._virtual_items = []  # All items data (not widgets)
        self._visible_range = (0, 0)  # (start_index, end_index) of visible items
        
        # Connect search functionality
        if self.search_entry:
            self.search_entry.connect("search-changed", self._on_search_entry_changed)
    
    def load_passwords(self):
        """Load and display passwords in the dynamic folder structure using threading."""
        # Cancel any existing loading thread
        if self._loading_thread and self._loading_thread.is_alive():
            self.logger.debug("Cancelling existing password loading thread")
            return  # Don't start a new load if one is already running
        
        # Set loading state
        self._is_loading = True
        
        # Save current expansion state before clearing
        expansion_state = self._save_expansion_state()

        # Clear existing widgets immediately on UI thread
        self._clear_all_widgets()
        
        # Show loading indicator if available
        self._show_loading_state()

        # Start background thread for password loading
        self._loading_thread = threading.Thread(
            target=self._load_passwords_background,
            args=(expansion_state,),
            daemon=True
        )
        self._loading_thread.start()

    def _load_passwords_background(self, expansion_state):
        """Background thread function for loading passwords."""
        try:
            self.logger.debug("Starting background password loading")
            
            # Get password list from store (this might be slow)
            raw_password_list = self.password_store.list_passwords()
            
            # Get all folders (this might also be slow)
            all_folders = self.password_store.list_folders()
            
            # Pre-load only basic metadata for passwords and folders (fast operations)
            password_metadata_cache = {}
            folder_metadata_cache = {}
            
            # Load only password metadata in background (URLs will be loaded lazily)
            for password_path in raw_password_list:
                try:
                    password_metadata_cache[password_path] = self.password_store.get_password_metadata(password_path)
                except Exception as e:
                    self.logger.warning(f"Failed to load metadata for {password_path}: {e}")
                    # Provide default metadata
                    password_metadata_cache[password_path] = {
                        "color": "#3584e4",  # Default blue
                        "icon": "dialog-password-symbolic",
                        "favicon_data": None
                    }
            
            # Load folder metadata in background
            for folder_path in all_folders:
                try:
                    folder_metadata_cache[folder_path] = self.password_store.get_folder_metadata(folder_path)
                except Exception as e:
                    self.logger.warning(f"Failed to load folder metadata for {folder_path}: {e}")
                    # Provide default metadata
                    folder_metadata_cache[folder_path] = {
                        "color": "#f66151",  # Default red
                        "icon": "folder-symbolic"
                    }
            
            # Schedule UI updates on main thread with pre-loaded data
            GLib.idle_add(self._complete_password_loading, raw_password_list, all_folders, expansion_state, password_metadata_cache, folder_metadata_cache)
            
        except Exception as e:
            self.logger.error("Error in background password loading", extra={
                'error': str(e),
                'tags': ['threading', 'password_loading']
            })
            # Schedule error handling on main thread
            GLib.idle_add(self._handle_loading_error, str(e))

    def _complete_password_loading(self, raw_password_list, all_folders, expansion_state, password_metadata_cache, folder_metadata_cache):
        """Complete password loading on the main UI thread."""
        try:
            self.logger.debug("Completing password loading on UI thread", extra={
                'password_count': len(raw_password_list),
                'folder_count': len(all_folders)
            })
            
            # Hide loading indicator
            self._hide_loading_state()
            
            if not raw_password_list:
                self._handle_empty_password_list()
                return False  # Don't repeat this idle call

            # Build dynamic folder structure on UI thread with pre-loaded metadata
            self._build_dynamic_folder_structure_with_data(raw_password_list, all_folders, password_metadata_cache, folder_metadata_cache)

            # Restore expansion state
            self._restore_expansion_state(expansion_state)
            
            self._is_loading = False
            self.logger.debug("Password loading completed successfully")
            
        except Exception as e:
            self.logger.error("Error completing password loading", extra={
                'error': str(e),
                'tags': ['ui_thread', 'password_loading']
            })
            self._handle_loading_error(str(e))
        
        return False  # Don't repeat this idle call

    def _show_loading_state(self):
        """Show loading indicator while passwords are being loaded."""
        # You could add a spinner or loading message here
        # For now, we'll just log the loading state
        self.logger.debug("Password loading started")

    def _hide_loading_state(self):
        """Hide loading indicator after passwords are loaded."""
        self.logger.debug("Password loading UI updates completed")

    def _handle_loading_error(self, error_message):
        """Handle errors that occur during password loading."""
        self._is_loading = False
        self.logger.error("Password loading failed", extra={'error': error_message})
        
        if self.toast_manager:
            self.toast_manager.show_error(f"Failed to load passwords: {error_message}")
        
        return False  # Don't repeat this idle call

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

            self.logger.info("Password display refreshed", extra={
                'password_path': password_path,
                'color': password_color,
                'icon': password_icon,
                'user_action': True
            })
        else:
            self.logger.warning("Password row not found for refresh", extra={
                'password_path': password_path
            })
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
        # Get all folders from password store (this will be called on UI thread)
        all_folders = self.password_store.list_folders()
        self._build_dynamic_folder_structure_with_data(raw_password_list, all_folders)

    def _build_dynamic_folder_structure_with_data(self, raw_password_list, all_folders, password_metadata_cache=None, folder_metadata_cache=None):
        """Build dynamic folder structure from pre-loaded password list and folder data."""
        # Store metadata caches for use by widget creation methods
        self._password_metadata_cache = password_metadata_cache or {}
        self._folder_metadata_cache = folder_metadata_cache or {}
        
        # Initialize URL cache for lazy loading
        self._password_url_cache = {}
        # Group passwords by their immediate parent folder
        folder_structure = {}
        root_passwords = []

        # Process passwords and group them by their immediate parent folder
        for password_path in sorted(raw_password_list):
            parts = password_path.split(os.sep)

            if len(parts) == 1:
                # Root level password - add to separate list
                root_passwords.append({
                    'name': parts[0],
                    'path': password_path
                })
            else:
                # Password in a folder - get immediate parent folder path
                folder_path = os.sep.join(parts[:-1])
                password_name = parts[-1]

                if folder_path not in folder_structure:
                    folder_structure[folder_path] = []

                folder_structure[folder_path].append({
                    'name': password_name,
                    'path': password_path
                })

        # Add all existing folders (both empty and with passwords)
        for folder_path in all_folders:
            if folder_path not in folder_structure:
                folder_structure[folder_path] = []  # Empty folder

        # Step 1: Create all folder widgets first (without passwords)
        for folder_path in sorted(folder_structure.keys()):
            self._create_empty_folder_widget(folder_path)

        # Step 2: Add passwords to their respective folders (in batches to avoid UI freeze)
        self._add_passwords_in_batches(folder_structure, root_passwords)

    def _add_passwords_in_batches(self, folder_structure, root_passwords):
        """Add passwords to folders in batches to avoid UI freezing."""
        # Prepare all password additions as a queue
        password_queue = []
        
        # Add folder passwords to queue
        for folder_path in sorted(folder_structure.keys()):
            passwords = folder_structure[folder_path]
            for password_data in passwords:
                password_queue.append(('folder', password_data, folder_path))
        
        # Add root passwords to queue
        for password_data in root_passwords:
            password_queue.append(('root', password_data, None))
        
        # Process passwords in small batches using idle callbacks
        self._process_password_batch(password_queue, 0)

    def _process_password_batch(self, password_queue, start_index, batch_size=5):
        """Process a batch of passwords on the UI thread."""
        end_index = min(start_index + batch_size, len(password_queue))
        
        # Process this batch
        for i in range(start_index, end_index):
            password_type, password_data, folder_path = password_queue[i]
            
            if password_type == 'folder':
                self._add_password_to_folder(password_data, folder_path)
            elif password_type == 'root':
                self._create_root_password_widget(password_data)
        
        # Schedule next batch if there are more passwords
        if end_index < len(password_queue):
            GLib.idle_add(self._process_password_batch, password_queue, end_index, batch_size)
            return False  # Don't repeat this specific call
        else:
            # All passwords processed
            self.logger.debug("All passwords added to UI")
            return False
    
    def _create_folder_widget(self, folder_path, passwords):
        """Create a FolderExpanderRow for a folder with its passwords."""
        # For subfolders, show the full path; for top-level folders, show just the name
        if '/' in folder_path:
            folder_display_name = folder_path  # Show full path like "websites/social"
        else:
            folder_display_name = folder_path  # Show just the name like "websites"

        # Create folder expander row using the custom widget
        folder_row = FolderExpanderRow(folder_path=folder_path)
        folder_row.set_title(folder_display_name)
        folder_row.set_subtitle(f"{len(passwords)} password{'s' if len(passwords) != 1 else ''}")

        # Set avatar color and icon from cached metadata
        folder_metadata = getattr(self, '_folder_metadata_cache', {}).get(folder_path)
        if folder_metadata:
            folder_color = folder_metadata["color"]
            folder_icon = folder_metadata["icon"]
        else:
            # Fallback to default values if cache miss
            folder_color = "#f66151"  # Default red
            folder_icon = "folder-symbolic"
        folder_row.set_avatar_color_and_icon(folder_color, folder_icon)

        self.folder_rows[folder_path] = folder_row

        # Connect folder signals
        folder_row.connect("activate", self._on_folder_activated, folder_path)
        folder_row.connect("add-password-to-folder", self._on_add_password_to_folder_clicked, folder_path)
        folder_row.connect("add-subfolder", self._on_add_subfolder_clicked, folder_path)
        folder_row.connect("edit-folder", self._on_folder_edit_clicked, folder_path, folder_display_name)
        folder_row.connect("remove-folder", self._on_folder_delete_clicked, folder_path, folder_display_name)

        # Create password rows within the folder
        for password_data in passwords:
            password_row = self._create_password_widget(password_data, folder_row)

        # Disable expansion for empty folders (no passwords)
        if len(passwords) == 0:
            folder_row.set_enable_expansion(False)

        # Add folder to listbox
        self.folders_listbox.append(folder_row)

    def _create_empty_folder_widget(self, folder_path):
        """Create a FolderExpanderRow for a folder without passwords initially."""
        # For subfolders, show the full path; for top-level folders, show just the name
        if '/' in folder_path:
            folder_display_name = folder_path  # Show full path like "websites/social"
        else:
            folder_display_name = folder_path  # Show just the name like "websites"

        # Create folder expander row using the custom widget
        folder_row = FolderExpanderRow(folder_path=folder_path)
        folder_row.set_title(folder_display_name)
        folder_row.set_subtitle("0 passwords")  # Will be updated when passwords are added

        # Set avatar color and icon from cached metadata
        folder_metadata = getattr(self, '_folder_metadata_cache', {}).get(folder_path)
        if folder_metadata:
            folder_color = folder_metadata["color"]
            folder_icon = folder_metadata["icon"]
        else:
            # Fallback to default values if cache miss
            folder_color = "#f66151"  # Default red
            folder_icon = "folder-symbolic"
        folder_row.set_avatar_color_and_icon(folder_color, folder_icon)

        self.folder_rows[folder_path] = folder_row

        # Connect folder signals
        folder_row.connect("activate", self._on_folder_activated, folder_path)
        folder_row.connect("add-password-to-folder", self._on_add_password_to_folder_clicked, folder_path)
        folder_row.connect("add-subfolder", self._on_add_subfolder_clicked, folder_path)
        folder_row.connect("edit-folder", self._on_folder_edit_clicked, folder_path, folder_display_name)
        folder_row.connect("remove-folder", self._on_folder_delete_clicked, folder_path, folder_display_name)

        # Start with expansion disabled (will be enabled if passwords are added)
        folder_row.set_enable_expansion(False)

        # Add folder to listbox
        self.folders_listbox.append(folder_row)

    def _add_password_to_folder(self, password_data, folder_path):
        """Add a password to an existing folder."""
        # Get the folder row
        if folder_path not in self.folder_rows:
            self.logger.warning(f"Folder {folder_path} not found when adding password {password_data['path']}")
            return

        folder_row = self.folder_rows[folder_path]
        
        # Create the password widget (but don't add it to the folder yet)
        password_row = self._create_password_widget_standalone(password_data)
        
        # Use the folder's method to properly add the password row
        folder_row.add_password_row(password_row)
        
        # Enable expansion now that the folder has passwords
        password_count = folder_row.get_password_count()
        if password_count > 0:
            folder_row.set_enable_expansion(True)

    def _create_password_widget_standalone(self, password_data):
        """Create a PasswordEntryRow for a password without adding it to a parent."""
        from ..ui.widgets.password_entry_row import PasswordEntryRow

        # Create a PasswordEntry object for the row
        password_entry = PasswordEntry(path=password_data['path'], is_folder=False)
        password_row = PasswordEntryRow(password_entry)

        # Set the password entry path for metadata saving
        password_row._password_entry = password_data['path']  # Keep for compatibility with favicon saving

        # Set avatar color and icon from cached metadata
        password_metadata = getattr(self, '_password_metadata_cache', {}).get(password_data['path'])
        if password_metadata:
            password_color = password_metadata["color"]
            password_icon = password_metadata["icon"]
            favicon_data = password_metadata["favicon_data"]
        else:
            # Fallback to default values if cache miss
            password_color = "#3584e4"  # Default blue
            password_icon = "dialog-password-symbolic"
            favicon_data = None

        # Set avatar with color and icon only (URL and favicon loaded lazily)
        password_row.set_avatar_color_and_icon(password_color, password_icon)
        
        # Set up lazy URL and favicon loading for when the password becomes visible
        password_row.set_lazy_url_loader(self._get_password_url_lazy, password_data['path'])

        # Store reference
        password_path = password_data['path']
        self.password_rows[password_path] = password_row

        # Connect signals
        password_row.connect("activated", self._on_password_activated, password_path)
        password_row.connect("copy-username", self._on_copy_username_clicked, password_path)
        password_row.connect("copy-password", self._on_copy_password_clicked, password_path)
        password_row.connect("copy-totp", self._on_copy_totp_clicked, password_path)
        password_row.connect("visit-url", self._on_visit_url_clicked)
        password_row.connect("edit-password", self._on_edit_password_clicked)
        password_row.connect("view-details", self._on_view_details_clicked)
        password_row.connect("remove-password", self._on_remove_password_clicked)

        return password_row
    
    def _create_password_widget(self, password_data, parent_folder):
        """Create a PasswordEntryRow for a password and add it to the parent folder."""
        # Create the password widget
        password_row = self._create_password_widget_standalone(password_data)
        
        # Add password row to folder using the proper method
        parent_folder.add_password_row(password_row)

        return password_row

    def _create_root_password_widget(self, password_data):
        """Create a PasswordEntryRow for a root-level password (not in a folder)."""
        # Create the password widget using the standalone method
        password_row = self._create_password_widget_standalone(password_data)

        # Add password row directly to listbox (not to a folder)
        self.folders_listbox.append(password_row)

        return password_row

    def _get_cached_url_from_password(self, password_path):
        """Get URL from password using cached metadata to avoid blocking operations."""
        return getattr(self, '_password_url_cache', {}).get(password_path)
    
    def _get_password_url_lazy(self, password_path):
        """Lazily load password URL when needed (e.g., when password becomes visible)."""
        # Check if already cached
        if password_path in self._password_url_cache:
            return self._password_url_cache[password_path]
        
        # Load URL in background thread to avoid blocking UI
        def load_url_background():
            try:
                url = self._extract_url_from_password(password_path)
                self._password_url_cache[password_path] = url
                
                # Update UI on main thread if URL was found
                if url and password_path in self.password_rows:
                    GLib.idle_add(self._update_password_favicon, password_path, url)
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract URL for {password_path}: {e}")
                self._password_url_cache[password_path] = None
        
        # Start background thread
        threading.Thread(target=load_url_background, daemon=True).start()
        return None  # Return None immediately, URL will be loaded asynchronously
    
    def _update_password_favicon(self, password_path, url):
        """Update password row with favicon after URL is loaded."""
        if password_path in self.password_rows:
            password_row = self.password_rows[password_path]
            
            # Get current metadata
            password_metadata = self._password_metadata_cache.get(password_path, {})
            password_color = password_metadata.get("color", "#3584e4")
            password_icon = password_metadata.get("icon", "dialog-password-symbolic")
            favicon_data = password_metadata.get("favicon_data")
            
            # Update avatar with URL and favicon
            password_row.set_avatar_color_and_icon(password_color, password_icon, url, favicon_data)
            
            self.logger.debug("Updated password favicon", extra={
                'password_path': password_path,
                'url': url,
                'tags': ['favicon', 'lazy_load']
            })
        
        return False  # Don't repeat this idle call

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
                    self.logger.debug("Found direct URL", extra={
                        'password_path': password_path,
                        'url': line,
                        'tags': ['url_extraction', 'direct_url']
                    })
                    # Convert HTTP to HTTPS for security
                    if line.startswith('http://'):
                        secure_url = 'https://' + line[7:]
                        self.logger.debug("Converted HTTP to HTTPS", extra={
                            'original_url': line,
                            'secure_url': secure_url,
                            'tags': ['url_extraction', 'security', 'http_to_https']
                        })
                        return secure_url
                    return line

                # Check for URL field
                if line.lower().startswith('url:'):
                    url = line[4:].strip()
                    if url:
                        self.logger.debug("Found URL field", extra={
                            'password_path': password_path,
                            'url': url,
                            'tags': ['url_extraction', 'url_field']
                        })
                        return self._normalize_url(url)

                # Check for website field
                if line.lower().startswith('website:'):
                    url = line[8:].strip()
                    if url:
                        self.logger.debug("Found website field", extra={
                            'password_path': password_path,
                            'url': url,
                            'tags': ['url_extraction', 'website_field']
                        })
                        return self._normalize_url(url)

                # Check for domain-like patterns (contains dots and looks like a domain)
                # This handles legacy URLs saved without "url:" prefix
                if self._looks_like_domain(line):
                    self.logger.debug("Found domain-like pattern", extra={
                        'password_path': password_path,
                        'domain': line,
                        'tags': ['url_extraction', 'domain_pattern']
                    })
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
            original_url = url
            url = 'https://' + url[7:]
            self.logger.debug("Normalized HTTP to HTTPS", extra={
                'original_url': original_url,
                'normalized_url': url,
                'tags': ['url_normalization', 'security', 'http_to_https']
            })
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

    def _on_add_subfolder_clicked(self, folder_row, folder_path):
        """Handle add subfolder button click."""
        # Import here to avoid circular imports
        from gi.repository import GLib

        # Use GLib.idle_add to defer the call and trigger the main window's add subfolder dialog
        GLib.idle_add(self._handle_add_subfolder_request, folder_path)

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

    def _handle_add_subfolder_request(self, folder_path):
        """Handle add subfolder request."""
        # Emit a signal that the main window can catch
        if hasattr(self, 'add_subfolder_requested'):
            self.add_subfolder_requested(folder_path)
        else:
            # Fallback: show a toast message
            self.toast_manager.show_info(f"Add subfolder to '{folder_path}' - functionality coming soon")
        return False  # Don't repeat the idle call

    def _handle_folder_delete_request(self, folder_path, folder_name):
        """Handle the actual folder deletion request."""
        # Check if folder is empty
        success, is_empty, message = self.password_store.is_folder_empty(folder_path)

        if not success:
            self.toast_manager.show_error(f"Error checking folder: {message}")
            return False

        if not is_empty:
            self._show_non_empty_folder_dialog(folder_path, folder_name)
            return False

        # Show confirmation dialog for empty folder
        self._show_delete_folder_confirmation(folder_path, folder_name)
        return False  # Don't repeat the idle call

    def _show_non_empty_folder_dialog(self, folder_path, folder_name):
        """Show AlertDialog for non-empty folder deletion attempt."""
        from gi.repository import Adw
        
        # Create AlertDialog for non-empty folder
        dialog = Adw.AlertDialog()
        dialog.set_heading(f"Cannot Delete Folder '{folder_name}'")
        dialog.set_body(f"The folder '{folder_name}' contains passwords and cannot be deleted.\n\nTo delete this folder, first remove all passwords from it.")
        
        # Add responses
        dialog.add_response("cancel", "_OK")
        dialog.set_default_response("cancel")
        
        # Present dialog with parent window
        if self.parent_window:
            dialog.present(self.parent_window)
        else:
            # Fallback: show dialog without parent
            dialog.present()

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
    
    def _on_copy_username_clicked(self, password_row, password_path):
        """Handle copy username signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'copy_username_callback') and self.copy_username_callback:
            self.copy_username_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"Copy username for {password_path}")
    
    def _on_copy_password_clicked(self, password_row, password_path):
        """Handle copy password signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'copy_password_callback') and self.copy_password_callback:
            self.copy_password_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"Copy password for {password_path}")
    
    def _on_copy_totp_clicked(self, password_row, password_path):
        """Handle copy TOTP signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'copy_totp_callback') and self.copy_totp_callback:
            self.copy_totp_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"Copy TOTP for {password_path}")
    
    def _on_visit_url_clicked(self, password_row, url):
        """Handle visit URL signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'visit_url_callback') and self.visit_url_callback:
            self.visit_url_callback(url)
        else:
            # Fallback - open URL directly
            try:
                import webbrowser
                webbrowser.open(url)
                self.toast_manager.show_success(f"Opening URL: {url}")
            except Exception as e:
                self.toast_manager.show_error(f"Failed to open URL: {e}")
    
    def _on_edit_password_clicked(self, password_row, password_path):
        """Handle edit password signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'edit_password_callback') and self.edit_password_callback:
            self.edit_password_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"Edit password for {password_path}")
    
    def _on_view_details_clicked(self, password_row, password_path):
        """Handle view details signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'view_details_callback') and self.view_details_callback:
            self.view_details_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"View details for {password_path}")
    
    def _on_remove_password_clicked(self, password_row, password_path):
        """Handle remove password signal from password row."""
        # Forward to callback if available
        if hasattr(self, 'remove_password_callback') and self.remove_password_callback:
            self.remove_password_callback(password_path)
        else:
            # Fallback
            self.toast_manager.show_info(f"Remove password for {password_path}")
    
    def set_action_callbacks(self, copy_username=None, copy_password=None, copy_totp=None, 
                            visit_url=None, edit_password=None, view_details=None, remove_password=None):
        """Set callback functions for password actions."""
        self.copy_username_callback = copy_username
        self.copy_password_callback = copy_password
        self.copy_totp_callback = copy_totp
        self.visit_url_callback = visit_url
        self.edit_password_callback = edit_password
        self.view_details_callback = view_details
        self.remove_password_callback = remove_password
